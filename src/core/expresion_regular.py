"""Expresiones regulares de la teoría (notación del curso).

Notación: ``+`` unión, yuxtaposición para la concatenación, ``*`` cerradura de
Kleene, ``λ`` palabra vacía y ``∅`` lenguaje vacío. Precedencia: ``*`` >
concatenación > ``+``.

Este módulo define el árbol sintáctico y las operaciones que no dependen del
análisis del texto:

* Constructores que **simplifican** con leyes algebraicas (Hopcroft, Motwani y
  Ullman, 2007, sec. 3.4): ∅ + r = r, r + r = r, ∅r = r∅ = ∅, λr = rλ = r,
  ∅* = λ, λ* = λ, (r*)* = r*, (λ + r)* = r*, λ + rr* = r*, y λ + r = r si λ ∈ L(r).
* Escritura con el mínimo de paréntesis según la precedencia.
* Traducción a la sintaxis del módulo ``re`` de Python.
* Pertenencia de una cadena mediante **derivadas de Brzozowski**, que sirve
  como verificación independiente de los autómatas construidos.

El analizador sintáctico del texto se agrega en la Práctica 4.
"""

from __future__ import annotations

import re as _re
from dataclasses import dataclass
from functools import lru_cache


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


def sim(s: str) -> ER:
    return LAMBDA if s == "" else Simbolo(s)


# ---------------------------------------------------------------------------
# Constructores con simplificación
# ---------------------------------------------------------------------------

def anulable(r: ER) -> bool:
    """¿λ ∈ L(r)?"""
    if isinstance(r, (Lambda, Estrella)):
        return True
    if isinstance(r, (Vacio, Simbolo)):
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


def a_texto(r: ER) -> str:
    """Notación del curso con el mínimo de paréntesis."""
    if isinstance(r, Vacio):
        return "∅"
    if isinstance(r, Lambda):
        return "λ"
    if isinstance(r, Simbolo):
        return r.s
    if isinstance(r, Union):
        return "+".join(a_texto(p) for p in r.partes)
    if isinstance(r, Concat):
        return "".join(f"({a_texto(p)})" if _precedencia(p) < 1 else a_texto(p) for p in r.partes)
    hijo = r.r
    interior = a_texto(hijo)
    return f"({interior})*" if _precedencia(hijo) < 2 or (isinstance(hijo, Simbolo) and len(hijo.s) > 1) \
        else f"{interior}*"


def a_python(r: ER) -> str:
    """Traducción a la sintaxis de ``re`` (para usar con ``re.fullmatch``)."""
    if isinstance(r, Vacio):
        return "(?!)"          # no coincide con nada
    if isinstance(r, Lambda):
        return ""
    if isinstance(r, Simbolo):
        return _re.escape(r.s)
    if isinstance(r, Union):
        partes = [a_python(p) for p in r.partes]
        # Unión de símbolos de un carácter: clase [abc]
        if all(isinstance(p, Simbolo) and len(p.s) == 1 for p in r.partes):
            return "[" + "".join(_escapar_clase(p.s) for p in r.partes) + "]"
        return "(?:" + "|".join(partes) + ")"
    if isinstance(r, Concat):
        return "".join(a_python(p) for p in r.partes)
    hijo = a_python(r.r)
    simple = isinstance(r.r, Simbolo) and len(r.r.s) == 1
    clase = isinstance(r.r, Union) and hijo.startswith("[")
    return f"{hijo}*" if simple or clase else f"(?:{hijo})*"


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
    if isinstance(r, (Union, Concat)):
        return set().union(*[simbolos(p) for p in r.partes])
    if isinstance(r, Estrella):
        return simbolos(r.r)
    return set()


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
