"""Expresiones regulares de la teoría (notación del curso).

Notación: ``+`` unión, yuxtaposición para la concatenación, ``*`` cerradura de
Kleene, ``λ`` palabra vacía y ``∅`` lenguaje vacío. Precedencia: ``*`` >
concatenación > ``+``; los paréntesis agrupan.

Extensiones declaradas (Práctica 4):

* ``\\c`` escribe el carácter ``c`` como símbolo, aunque sea un operador:
  ``\\+``, ``\\*``, ``\\(``, ``\\)``, ``\\\\``, ``\\{`` y ``\\ `` (espacio).
  Los espacios sin escapar se ignoran.
* ``{D}`` es una **clase de símbolos** declarada aparte, por ejemplo
  ``D = [0-9]`` (equivale a 0+1+…+9). Una clase siempre es un conjunto de
  símbolos individuales, es decir, una unión de casos básicos.

Este módulo contiene el árbol sintáctico, el analizador, constructores que
**simplifican** con leyes algebraicas (Hopcroft, Motwani y Ullman, 2007,
sec. 3.4), la escritura en la notación del curso y en la de ``re`` de Python,
la pertenencia por **derivadas de Brzozowski** (verificación independiente de
los autómatas) y un generador de cadenas del lenguaje.
"""

from __future__ import annotations

import random
import re as _re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


class ER:
    """Nodo de una expresión regular."""

    def __str__(self) -> str:
        return a_texto(self)

    # Azúcar para escribir expresiones en el código: r + s, r & s (concat), ~r (estrella)
    def __add__(self, otra: "ER") -> "ER":
        return union(self, otra)

    def __and__(self, otra: "ER") -> "ER":
        return concat(self, otra)

    def __invert__(self) -> "ER":
        return estrella(self)


@dataclass(frozen=True, eq=True)
class Vacio(ER):
    pass


@dataclass(frozen=True, eq=True)
class Lambda(ER):
    pass


@dataclass(frozen=True, eq=True)
class Simbolo(ER):
    s: str


@dataclass(frozen=True, eq=True)
class Clase(ER):
    """Conjunto de símbolos con nombre: equivale a la unión de esos símbolos."""
    nombre: str
    simbolos: tuple


@dataclass(frozen=True, eq=True)
class Union(ER):
    partes: tuple


@dataclass(frozen=True, eq=True)
class Concat(ER):
    partes: tuple


@dataclass(frozen=True, eq=True)
class Estrella(ER):
    r: ER


VACIO = Vacio()
LAMBDA = Lambda()

OPERADORES = set("+*()λ∅\\{}ε")


def sim(s: str) -> ER:
    return LAMBDA if s == "" else Simbolo(s)


# ---------------------------------------------------------------------------
# Constructores con simplificación
# ---------------------------------------------------------------------------

def anulable(r: ER) -> bool:
    """¿λ ∈ L(r)?"""
    if isinstance(r, (Lambda, Estrella)):
        return True
    if isinstance(r, (Vacio, Simbolo, Clase)):
        return False
    if isinstance(r, Union):
        return any(anulable(p) for p in r.partes)
    return all(anulable(p) for p in r.partes)


def union(*rs: ER) -> ER:
    partes: list[ER] = []
    for r in rs:
        for p in (r.partes if isinstance(r, Union) else (r,)):
            if isinstance(p, Vacio) or p in partes:
                continue
            partes.append(p)
    if not partes:
        return VACIO
    # λ + r = r si λ ∈ L(r)
    if LAMBDA in partes and any(anulable(p) for p in partes if p != LAMBDA):
        partes.remove(LAMBDA)
    # λ + r r* = r*   y   λ + r* r = r*
    if LAMBDA in partes:
        for p in list(partes):
            if isinstance(p, Concat) and len(p.partes) == 2:
                x, y = p.partes
                if (isinstance(y, Estrella) and y.r == x) or (isinstance(x, Estrella) and x.r == y):
                    partes.remove(LAMBDA)
                    partes[partes.index(p)] = Estrella(x if isinstance(y, Estrella) else y)
                    break
    if len(partes) == 1:
        return partes[0]
    return Union(tuple(partes))


def concat(*rs: ER) -> ER:
    partes: list[ER] = []
    for r in rs:
        if isinstance(r, Vacio):
            return VACIO
        for p in (r.partes if isinstance(r, Concat) else (r,)):
            if isinstance(p, Lambda):
                continue
            partes.append(p)
    # r* r* = r*
    i = 0
    while i + 1 < len(partes):
        if isinstance(partes[i], Estrella) and partes[i] == partes[i + 1]:
            del partes[i + 1]
        else:
            i += 1
    if not partes:
        return LAMBDA
    if len(partes) == 1:
        return partes[0]
    return Concat(tuple(partes))


def estrella(r: ER) -> ER:
    if isinstance(r, (Vacio, Lambda)):
        return LAMBDA
    if isinstance(r, Estrella):
        return r
    if isinstance(r, Union) and LAMBDA in r.partes:
        return estrella(union(*[p for p in r.partes if p != LAMBDA]))
    return Estrella(r)


def simplificar(r: ER) -> ER:
    """Reconstruye la expresión aplicando los constructores que simplifican."""
    if isinstance(r, Union):
        return union(*[simplificar(p) for p in r.partes])
    if isinstance(r, Concat):
        return concat(*[simplificar(p) for p in r.partes])
    if isinstance(r, Estrella):
        return estrella(simplificar(r.r))
    return r


def expandir(r: ER) -> ER:
    """Sustituye cada clase por la unión explícita de sus símbolos."""
    if isinstance(r, Clase):
        return Union(tuple(Simbolo(s) for s in r.simbolos)) if len(r.simbolos) > 1 else (
            Simbolo(r.simbolos[0]) if r.simbolos else VACIO)
    if isinstance(r, Union):
        return Union(tuple(expandir(p) for p in r.partes))
    if isinstance(r, Concat):
        return Concat(tuple(expandir(p) for p in r.partes))
    if isinstance(r, Estrella):
        return Estrella(expandir(r.r))
    return r


# ---------------------------------------------------------------------------
# Escritura
# ---------------------------------------------------------------------------

def _precedencia(r: ER) -> int:
    if isinstance(r, Union):
        return 0
    if isinstance(r, Concat):
        return 1
    if isinstance(r, Estrella):
        return 2
    return 3


def escapar(s: str) -> str:
    """Escribe un símbolo de modo que el analizador lo lea igual."""
    return "".join("\\" + c if c in OPERADORES or c.isspace() else c for c in s)


def a_texto(r: ER) -> str:
    """Notación del curso con el mínimo de paréntesis."""
    if isinstance(r, Vacio):
        return "∅"
    if isinstance(r, Lambda):
        return "λ"
    if isinstance(r, Simbolo):
        return escapar(r.s)
    if isinstance(r, Clase):
        return "{" + r.nombre + "}"
    if isinstance(r, Union):
        return "+".join(a_texto(p) for p in r.partes)
    if isinstance(r, Concat):
        return "".join(f"({a_texto(p)})" if _precedencia(p) < 1 else a_texto(p) for p in r.partes)
    hijo = r.r
    interior = a_texto(hijo)
    return f"({interior})*" if _precedencia(hijo) < 2 or (isinstance(hijo, Simbolo) and len(hijo.s) > 1) \
        else f"{interior}*"


def _es_atomico(p: str) -> bool:
    """¿La expresión de ``re`` admite un cuantificador sin agruparla?"""
    if len(p) == 1 or (len(p) == 2 and p[0] == "\\"):
        return True
    if p.startswith("[") and p.endswith("]") and p.count("]") - p.count("\\]") == 1:
        return True
    if p.startswith("(?:") and p.endswith(")"):
        nivel = 0
        for k, c in enumerate(p):
            if c == "\\":
                continue
            if c == "(" and (k == 0 or p[k - 1] != "\\"):
                nivel += 1
            elif c == ")" and p[k - 1] != "\\":
                nivel -= 1
                if nivel == 0 and k != len(p) - 1:
                    return False
        return True
    return False


def _agrupar(p: str) -> str:
    return p if _es_atomico(p) else f"(?:{p})"


def a_python(r: ER) -> str:
    """Traducción a la sintaxis de ``re`` (para usar con ``re.fullmatch``)."""
    if isinstance(r, Vacio):
        return "(?!)"          # no coincide con nada
    if isinstance(r, Lambda):
        return ""
    if isinstance(r, Simbolo):
        return _re.escape(r.s)
    if isinstance(r, Clase):
        return _clase_python(r.simbolos)
    if isinstance(r, Union):
        opcional = any(isinstance(p, Lambda) for p in r.partes)
        partes = [p for p in r.partes if not isinstance(p, Lambda)]
        caracteres = [p for p in partes if (isinstance(p, Simbolo) and len(p.s) == 1) or isinstance(p, Clase)]
        if partes and len(caracteres) == len(partes):
            # Unión de símbolos sueltos y clases: una sola clase [...]
            cuerpo = _clase_python([c for p in partes for c in ((p.s,) if isinstance(p, Simbolo) else p.simbolos)])
        elif len(partes) == 1:
            cuerpo = a_python(partes[0])
        else:
            cuerpo = "(?:" + "|".join(a_python(p) for p in partes) + ")"
        return _agrupar(cuerpo) + "?" if opcional else cuerpo
    if isinstance(r, Concat):
        return "".join(a_python(p) if not isinstance(p, Union) or _es_atomico(a_python(p)) or
                       a_python(p).endswith("?") else f"(?:{a_python(p)})" for p in r.partes)
    return _agrupar(a_python(r.r)) + "*"


def _clase_python(simbolos) -> str:
    """``[...]`` compacto: tramos consecutivos de 3 o más caracteres como rango."""
    cs = sorted(set(simbolos), key=ord)
    if len(cs) == 1:
        return _re.escape(cs[0])
    partes, i = [], 0
    while i < len(cs):
        j = i
        while j + 1 < len(cs) and ord(cs[j + 1]) == ord(cs[j]) + 1:
            j += 1
        if j - i >= 2:
            partes.append(f"{_escapar_clase(cs[i])}-{_escapar_clase(cs[j])}")
        else:
            partes.extend(_escapar_clase(c) for c in cs[i:j + 1])
        i = j + 1
    return "[" + "".join(partes) + "]"


def _escapar_clase(c: str) -> str:
    return "\\" + c if c in "\\]^-[" else c


def tamano(r: ER) -> int:
    """Número de símbolos y operadores (medida de longitud de la expresión)."""
    if isinstance(r, (Union, Concat)):
        return sum(tamano(p) for p in r.partes) + len(r.partes) - 1
    if isinstance(r, Estrella):
        return tamano(r.r) + 1
    return 1


def simbolos(r: ER) -> set[str]:
    if isinstance(r, Simbolo):
        return {r.s}
    if isinstance(r, Clase):
        return set(r.simbolos)
    if isinstance(r, (Union, Concat)):
        return set().union(*[simbolos(p) for p in r.partes])
    if isinstance(r, Estrella):
        return simbolos(r.r)
    return set()


def arbol_texto(r: ER) -> list[str]:
    """Árbol sintáctico como líneas de texto con conectores."""
    lineas: list[str] = []

    def etiqueta(n: ER) -> str:
        if isinstance(n, Union):
            return "+  (unión)"
        if isinstance(n, Concat):
            return "·  (concatenación)"
        if isinstance(n, Estrella):
            return "*  (cerradura)"
        if isinstance(n, Clase):
            return f"{{{n.nombre}}}  (clase de {len(n.simbolos)} símbolos)"
        return a_texto(n)

    def hijos(n: ER) -> tuple:
        if isinstance(n, (Union, Concat)):
            return n.partes
        if isinstance(n, Estrella):
            return (n.r,)
        return ()

    def visitar(n: ER, prefijo: str, ultimo: bool, raiz: bool) -> None:
        lineas.append(("" if raiz else prefijo + ("└── " if ultimo else "├── ")) + etiqueta(n))
        hs = hijos(n)
        for i, h in enumerate(hs):
            visitar(h, "" if raiz else prefijo + ("    " if ultimo else "│   "), i == len(hs) - 1, False)

    visitar(r, "", True, True)
    return lineas


# ---------------------------------------------------------------------------
# Análisis sintáctico
# ---------------------------------------------------------------------------

class ErrorSintaxis(ValueError):
    """Expresión mal formada; ``posicion`` empieza en 1."""

    def __init__(self, mensaje: str, posicion: int, texto: str = ""):
        self.mensaje = mensaje
        self.posicion = posicion
        self.texto = texto
        super().__init__(f"Posición {posicion}: {mensaje}")

    def marca(self) -> str:
        """El texto con una flecha bajo la posición del error."""
        return f"{self.texto}\n{' ' * (self.posicion - 1)}^"


@dataclass
class _Token:
    tipo: str          # sim | lambda | vacio | clase | + | * | ( | ) | fin
    valor: str
    pos: int           # 1-based


def _tokenizar(texto: str) -> list[_Token]:
    tokens: list[_Token] = []
    i = 0
    while i < len(texto):
        c = texto[i]
        pos = i + 1
        if c.isspace():
            i += 1
            continue
        if c == "\\":
            if i + 1 >= len(texto):
                raise ErrorSintaxis("La barra invertida \\ debe ir seguida del carácter que escapa.", pos, texto)
            tokens.append(_Token("sim", texto[i + 1], pos))
            i += 2
            continue
        if c in "+*()":
            tokens.append(_Token(c, c, pos))
        elif c in "λε":
            tokens.append(_Token("lambda", c, pos))
        elif c in "∅Ø":
            tokens.append(_Token("vacio", c, pos))
        elif c == "{":
            fin = texto.find("}", i)
            if fin == -1:
                raise ErrorSintaxis("Falta cerrar con } el nombre de la clase.", pos, texto)
            nombre = texto[i + 1:fin].strip()
            if not nombre:
                raise ErrorSintaxis("El nombre de la clase entre llaves está vacío.", pos, texto)
            tokens.append(_Token("clase", nombre, pos))
            i = fin + 1
            continue
        elif c == "}":
            raise ErrorSintaxis("Llave de cierre } sin apertura.", pos, texto)
        else:
            tokens.append(_Token("sim", c, pos))
        i += 1
    tokens.append(_Token("fin", "", len(texto) + 1))
    return tokens


class _Analizador:
    INICIO_FACTOR = {"sim", "lambda", "vacio", "clase", "("}

    def __init__(self, texto: str, clases: dict[str, Clase]):
        self.texto = texto
        self.clases = clases
        self.tokens = _tokenizar(texto)
        self.i = 0

    @property
    def actual(self) -> _Token:
        return self.tokens[self.i]

    def error(self, mensaje: str, pos: Optional[int] = None) -> ErrorSintaxis:
        return ErrorSintaxis(mensaje, pos or self.actual.pos, self.texto)

    def analizar(self) -> ER:
        if self.actual.tipo == "fin":
            raise self.error("La expresión está vacía (use λ para la palabra vacía).", 1)
        r = self.union()
        t = self.actual
        if t.tipo == ")":
            raise self.error("Paréntesis de cierre ) sin su apertura.")
        if t.tipo != "fin":
            raise self.error(f"Símbolo inesperado «{t.valor}».")
        return r

    def union(self) -> ER:
        partes = [self.concatenacion("+")]
        while self.actual.tipo == "+":
            mas = self.actual
            self.i += 1
            if self.actual.tipo not in self.INICIO_FACTOR:
                raise self.error("Falta el operando derecho de la unión +.", mas.pos)
            partes.append(self.concatenacion("+"))
        return partes[0] if len(partes) == 1 else Union(tuple(partes))

    def concatenacion(self, contexto: str) -> ER:
        t = self.actual
        if t.tipo not in self.INICIO_FACTOR:
            if t.tipo == "+":
                raise self.error("Falta el operando izquierdo de la unión +.")
            if t.tipo == "*":
                raise self.error("La cerradura * no tiene a qué aplicarse.")
            if t.tipo == ")":
                raise self.error("Paréntesis vacíos o expresión incompleta antes de ).")
            raise self.error("Falta un operando.")
        partes = []
        while self.actual.tipo in self.INICIO_FACTOR:
            partes.append(self.factor())
        return partes[0] if len(partes) == 1 else Concat(tuple(partes))

    def factor(self) -> ER:
        r = self.atomo()
        while self.actual.tipo == "*":
            self.i += 1
            r = Estrella(r)
        return r

    def atomo(self) -> ER:
        t = self.actual
        if t.tipo == "sim":
            self.i += 1
            return Simbolo(t.valor)
        if t.tipo == "lambda":
            self.i += 1
            return LAMBDA
        if t.tipo == "vacio":
            self.i += 1
            return VACIO
        if t.tipo == "clase":
            if t.valor not in self.clases:
                raise self.error(f"La clase {{{t.valor}}} no está declarada.")
            self.i += 1
            return self.clases[t.valor]
        # t.tipo == "("
        self.i += 1
        if self.actual.tipo == ")":
            raise self.error("Paréntesis vacíos: escriba λ si quiere la palabra vacía.", t.pos)
        r = self.union()
        if self.actual.tipo != ")":
            raise self.error(f"Falta cerrar el paréntesis abierto en la posición {t.pos}.",
                             self.actual.pos if self.actual.tipo != "fin" else t.pos)
        self.i += 1
        return r


def analizar(texto: str, clases: Optional[dict[str, Clase]] = None) -> ER:
    """Convierte el texto en un árbol sintáctico, sin simplificar.

    Lanza :class:`ErrorSintaxis` con la posición del primer error.
    """
    return _Analizador(texto, clases or {}).analizar()


def rango(desde: str, hasta: str) -> list[str]:
    return [chr(c) for c in range(ord(desde), ord(hasta) + 1)]


def _conjunto_de_definicion(nombre: str, definicion: str, previas: dict[str, Clase]) -> tuple:
    """Interpreta ``[a-z0-9_]`` o una unión de símbolos y clases."""
    d = definicion.strip()
    if d.startswith("[") and d.endswith("]"):
        cuerpo, simbolos, i = d[1:-1], [], 0
        while i < len(cuerpo):
            c = cuerpo[i]
            if c == "\\" and i + 1 < len(cuerpo):
                simbolos.append(cuerpo[i + 1])
                i += 2
                continue
            if i + 2 < len(cuerpo) and cuerpo[i + 1] == "-":
                if ord(cuerpo[i + 2]) < ord(c):
                    raise ValueError(f"Clase {nombre}: el rango {c}-{cuerpo[i + 2]} está invertido.")
                simbolos.extend(rango(c, cuerpo[i + 2]))
                i += 3
                continue
            simbolos.append(c)
            i += 1
        if not simbolos:
            raise ValueError(f"Clase {nombre}: los corchetes están vacíos.")
        return tuple(dict.fromkeys(simbolos))
    try:
        r = analizar(d, previas)
    except ErrorSintaxis as exc:
        raise ValueError(f"Clase {nombre}, {exc}") from exc
    partes = r.partes if isinstance(r, Union) else (r,)
    simbolos: list[str] = []
    for p in partes:
        if isinstance(p, Simbolo):
            simbolos.append(p.s)
        elif isinstance(p, Clase):
            simbolos.extend(p.simbolos)
        else:
            raise ValueError(f"Clase {nombre}: debe ser un conjunto de símbolos (p. ej. 0+1+2 o [0-9]).")
    return tuple(dict.fromkeys(simbolos))


def analizar_clases(texto: str) -> dict[str, Clase]:
    """Lee declaraciones ``NOMBRE = definición``, una por línea.

    La definición es ``[...]`` con rangos (``[a-z0-9]``) o una unión de símbolos
    y de clases ya declaradas (``{M}+{m}``). Las líneas vacías o que empiezan
    con ``#`` se ignoran.
    """
    clases: dict[str, Clase] = {}
    for n, linea in enumerate(texto.splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if "=" not in linea:
            raise ValueError(f"Línea {n}: use el formato NOMBRE = definición.")
        nombre, definicion = (x.strip() for x in linea.split("=", 1))
        if not nombre or any(c in OPERADORES or c.isspace() for c in nombre):
            raise ValueError(f"Línea {n}: nombre de clase inválido «{nombre}».")
        clases[nombre] = Clase(nombre, _conjunto_de_definicion(nombre, definicion, clases))
    return clases


# ---------------------------------------------------------------------------
# Pertenencia por derivadas de Brzozowski
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def derivada(r: ER, a: str) -> ER:
    """D_a(r) = { w : aw ∈ L(r) }."""
    if isinstance(r, (Vacio, Lambda)):
        return VACIO
    if isinstance(r, Simbolo):
        return LAMBDA if r.s == a else VACIO
    if isinstance(r, Clase):
        return LAMBDA if a in r.simbolos else VACIO
    if isinstance(r, Union):
        return union(*[derivada(p, a) for p in r.partes])
    if isinstance(r, Estrella):
        return concat(derivada(r.r, a), r)
    cabeza, resto = r.partes[0], concat(*r.partes[1:])
    d = concat(derivada(cabeza, a), resto)
    return union(d, derivada(resto, a)) if anulable(cabeza) else d


def pertenece(r: ER, cadena: list[str] | str) -> bool:
    for a in cadena:
        r = derivada(r, a)
        if isinstance(r, Vacio):
            return False
    return anulable(r)


# ---------------------------------------------------------------------------
# Generación de cadenas del lenguaje (para pruebas)
# ---------------------------------------------------------------------------

def muestra(r: ER, rnd: random.Random, max_repeticiones: int = 3) -> Optional[str]:
    """Una cadena aleatoria de L(r), o ``None`` si L(r) = ∅."""
    if isinstance(r, Vacio):
        return None
    if isinstance(r, Lambda):
        return ""
    if isinstance(r, Simbolo):
        return r.s
    if isinstance(r, Clase):
        return rnd.choice(r.simbolos)
    if isinstance(r, Union):
        opciones = list(r.partes)
        rnd.shuffle(opciones)
        for p in opciones:
            w = muestra(p, rnd, max_repeticiones)
            if w is not None:
                return w
        return None
    if isinstance(r, Concat):
        partes = []
        for p in r.partes:
            w = muestra(p, rnd, max_repeticiones)
            if w is None:
                return None
            partes.append(w)
        return "".join(partes)
    veces = rnd.randint(0, max_repeticiones)
    piezas = [muestra(r.r, rnd, max_repeticiones) for _ in range(veces)]
    return "".join(p for p in piezas if p is not None)
