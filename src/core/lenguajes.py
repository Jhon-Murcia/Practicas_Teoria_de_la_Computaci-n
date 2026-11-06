"""Operaciones básicas sobre cadenas y lenguajes (Práctica 1).

Todas las funciones de este módulo son puras: no dependen de Flet ni de
ningún otro componente de la interfaz, de modo que pueden probarse con
pytest y reutilizarse desde cualquier práctica posterior.

Convenciones adoptadas
----------------------
* La cadena vacía se representa internamente con ``""`` y se muestra como
  ``λ`` (constante :data:`LAMBDA`).
* Los prefijos y los sufijos de una cadena ``w`` incluyen a ``λ`` y a la propia
  ``w``: ``w = λw = wλ``, así que ``λ`` es a la vez prefijo y sufijo de toda
  cadena. Una cadena de longitud ``n`` tiene exactamente ``n + 1`` prefijos y
  ``n + 1`` sufijos.
* Las subcadenas también incluyen a ``λ``. Una cadena de longitud ``n`` tiene a
  lo sumo ``n(n + 1)/2 + 1`` subcadenas distintas.
* Los lenguajes generados se devuelven en orden canónico (por longitud y,
  dentro de cada longitud, en el orden del alfabeto dado).
"""

from __future__ import annotations

from itertools import product
from typing import Iterable, Sequence

LAMBDA = "λ"
"""Símbolo con el que se muestra la cadena vacía."""

LIMITE_CADENAS = 200_000
"""Número máximo de cadenas que el programa acepta generar."""


class LimiteExcedido(ValueError):
    """Se lanza cuando una operación generaría más de :data:`LIMITE_CADENAS`."""

    def __init__(self, cantidad: int, limite: int = LIMITE_CADENAS):
        self.cantidad = cantidad
        self.limite = limite
        super().__init__(
            f"La operación generaría {cantidad:,} cadenas y el límite es "
            f"{limite:,}. Reduzca la longitud máxima o el tamaño del alfabeto."
        )


# ---------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------

def mostrar(cadena: str) -> str:
    """Devuelve la cadena lista para mostrarse: ``""`` se escribe ``λ``."""
    return LAMBDA if cadena == "" else cadena


def normalizar(cadena: str) -> str:
    """Interpreta ``λ`` escrita por el usuario como la cadena vacía."""
    cadena = cadena.strip()
    return "" if cadena in (LAMBDA, "lambda", "ε") else cadena


def parsear_alfabeto(texto: str) -> list[str]:
    """Convierte ``"a, b, c"`` o ``"a b c"`` en ``["a", "b", "c"]``.

    Se eliminan los duplicados conservando el orden. Se rechaza ``λ`` porque
    la cadena vacía no es un símbolo del alfabeto.
    """
    piezas = [p.strip() for p in texto.replace(",", " ").split()]
    simbolos: list[str] = []
    for p in piezas:
        if not p:
            continue
        if p in (LAMBDA, "ε", "lambda"):
            raise ValueError("λ representa la cadena vacía y no puede ser un símbolo del alfabeto.")
        if p not in simbolos:
            simbolos.append(p)
    if not simbolos:
        raise ValueError("El alfabeto debe tener al menos un símbolo.")
    return simbolos


def parsear_lenguaje(texto: str) -> list[str]:
    """Convierte ``"ab, ba, λ"`` en ``["ab", "ba", ""]`` sin duplicados."""
    resultado: list[str] = []
    for pieza in texto.split(","):
        cadena = normalizar(pieza)
        if pieza.strip() == "" and cadena == "":
            continue
        if cadena not in resultado:
            resultado.append(cadena)
    return resultado


def ordenar_canonico(cadenas: Iterable[str], alfabeto: Sequence[str] | None = None) -> list[str]:
    """Ordena por longitud y después lexicográficamente (orden *shortlex*).

    Si se da un alfabeto de símbolos de un carácter, se respeta su orden.
    """
    if alfabeto and all(len(s) == 1 for s in alfabeto):
        rango = {s: i for i, s in enumerate(alfabeto)}
        return sorted(set(cadenas), key=lambda w: (len(w), [rango.get(c, len(rango)) for c in w], w))
    return sorted(set(cadenas), key=lambda w: (len(w), w))


# ---------------------------------------------------------------------------
# Operaciones sobre cadenas
# ---------------------------------------------------------------------------

def prefijos(w: str) -> list[str]:
    """Todos los prefijos de ``w``, de ``λ`` a ``w`` (``|w| + 1`` en total)."""
    return [w[:i] for i in range(len(w) + 1)]


def sufijos(w: str) -> list[str]:
    """Todos los sufijos de ``w``, de ``λ`` a ``w`` (``|w| + 1`` en total)."""
    return [w[i:] for i in range(len(w), -1, -1)]


def prefijos_propios(w: str) -> list[str]:
    """Prefijos distintos de la propia ``w``."""
    return prefijos(w)[:-1]


def sufijos_propios(w: str) -> list[str]:
    """Sufijos distintos de la propia ``w``."""
    return sufijos(w)[:-1]


def subcadenas(w: str) -> list[str]:
    """Todas las subcadenas distintas de ``w``, incluida ``λ``.

    Se recorren todos los pares ``0 <= i <= j <= n`` y se conserva la primera
    aparición de cada subcadena; el resultado se ordena por longitud.
    """
    vistas: dict[str, None] = {"": None}
    n = len(w)
    for longitud in range(1, n + 1):
        for i in range(n - longitud + 1):
            vistas.setdefault(w[i:i + longitud], None)
    return list(vistas)


def max_subcadenas_distintas(n: int) -> int:
    """Cota superior de subcadenas distintas de una cadena de longitud ``n``.

    Hay ``n - k + 1`` posiciones para cada longitud ``k = 1..n`` más la cadena
    vacía: ``n(n + 1)/2 + 1``. La cota se alcanza cuando todos los símbolos de
    la cadena son distintos.
    """
    if n < 0:
        raise ValueError("La longitud no puede ser negativa.")
    return n * (n + 1) // 2 + 1


def longitud(w: str) -> int:
    return len(w)


def reflexion(w: str) -> str:
    """Cadena inversa ``w^R``."""
    return w[::-1]


def potencia_cadena(w: str, n: int) -> str:
    """``w^n``; por definición ``w^0 = λ``."""
    if n < 0:
        raise ValueError("El exponente debe ser un entero no negativo.")
    return w * n


# ---------------------------------------------------------------------------
# Potencias y cerraduras del alfabeto
# ---------------------------------------------------------------------------

def contar_potencia(k: int, n: int) -> int:
    """``|Σ^n| = |Σ|^n``."""
    return k ** n


def contar_cerradura(k: int, n: int, positiva: bool = False) -> int:
    """Número de cadenas de longitud ``<= n`` en ``Σ*`` (o ``Σ⁺``)."""
    inicio = 1 if positiva else 0
    return sum(k ** i for i in range(inicio, n + 1))


def potencia_alfabeto(alfabeto: Sequence[str], n: int) -> list[str]:
    """``Σ^n``: todas las cadenas de longitud exactamente ``n``.

    ``Σ^0 = {λ}`` porque la única cadena de longitud cero es la vacía.
    """
    if n < 0:
        raise ValueError("La longitud debe ser un entero no negativo.")
    total = contar_potencia(len(alfabeto), n)
    if total > LIMITE_CADENAS:
        raise LimiteExcedido(total)
    return ["".join(t) for t in product(alfabeto, repeat=n)]


def _cerradura(alfabeto: Sequence[str], n: int, positiva: bool) -> list[str]:
    if n < 0:
        raise ValueError("La longitud máxima debe ser un entero no negativo.")
    if not alfabeto:
        raise ValueError("El alfabeto debe tener al menos un símbolo.")
    total = contar_cerradura(len(alfabeto), n, positiva)
    if total > LIMITE_CADENAS:
        raise LimiteExcedido(total)
    resultado: list[str] = []
    for i in range(1 if positiva else 0, n + 1):
        resultado.extend("".join(t) for t in product(alfabeto, repeat=i))
    return resultado


def cerradura_kleene(alfabeto: Sequence[str], n: int) -> list[str]:
    """``Σ*`` truncada a longitud ``n``: ``Σ^0 ∪ Σ^1 ∪ … ∪ Σ^n``."""
    return _cerradura(alfabeto, n, positiva=False)


def cerradura_positiva(alfabeto: Sequence[str], n: int) -> list[str]:
    """``Σ⁺`` truncada a longitud ``n``: ``Σ^1 ∪ … ∪ Σ^n`` (sin ``λ``)."""
    return _cerradura(alfabeto, n, positiva=True)


def agrupar_por_longitud(cadenas: Iterable[str]) -> dict[int, list[str]]:
    """Agrupa las cadenas por su longitud, conservando el orden de llegada."""
    grupos: dict[int, list[str]] = {}
    for w in cadenas:
        grupos.setdefault(len(w), []).append(w)
    return dict(sorted(grupos.items()))


# ---------------------------------------------------------------------------
# Operaciones sobre lenguajes finitos
# ---------------------------------------------------------------------------

def _verificar(cantidad: int) -> None:
    if cantidad > LIMITE_CADENAS:
        raise LimiteExcedido(cantidad)


def concatenacion(l1: Iterable[str], l2: Iterable[str]) -> list[str]:
    """``L1·L2 = {xy | x ∈ L1, y ∈ L2}``."""
    a, b = list(dict.fromkeys(l1)), list(dict.fromkeys(l2))
    _verificar(len(a) * len(b))
    return ordenar_canonico(x + y for x in a for y in b)


def potencia_lenguaje(lenguaje: Iterable[str], n: int) -> list[str]:
    """``L^n``; por definición ``L^0 = {λ}``."""
    if n < 0:
        raise ValueError("El exponente debe ser un entero no negativo.")
    base = list(dict.fromkeys(lenguaje))
    resultado = [""]
    for _ in range(n):
        _verificar(len(resultado) * len(base))
        resultado = list(dict.fromkeys(x + y for x in resultado for y in base))
    return ordenar_canonico(resultado)


def reflexion_lenguaje(lenguaje: Iterable[str]) -> list[str]:
    """``L^R = {w^R | w ∈ L}``."""
    return ordenar_canonico(reflexion(w) for w in lenguaje)


def union(l1: Iterable[str], l2: Iterable[str]) -> list[str]:
    return ordenar_canonico(set(l1) | set(l2))


def interseccion(l1: Iterable[str], l2: Iterable[str]) -> list[str]:
    return ordenar_canonico(set(l1) & set(l2))


def diferencia(l1: Iterable[str], l2: Iterable[str]) -> list[str]:
    return ordenar_canonico(set(l1) - set(l2))


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------

def reporte_texto(titulo: str, cadenas: Sequence[str], detalles: dict[str, object] | None = None) -> str:
    """Construye el contenido de un archivo de texto con los resultados.

    Una cadena por línea; la vacía se escribe ``λ``.
    """
    lineas = [titulo, "=" * len(titulo)]
    for clave, valor in (detalles or {}).items():
        lineas.append(f"{clave}: {valor}")
    lineas.append(f"Total de cadenas: {len(cadenas)}")
    lineas.append("")
    lineas.extend(mostrar(w) for w in cadenas)
    return "\n".join(lineas) + "\n"
