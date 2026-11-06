"""Equivalencia de autómatas finitos.

Dos AFD son equivalentes si y sólo si sus AFD mínimos (completos y sin
estados inaccesibles) **coinciden salvo el nombre de los estados**, porque el
AFD mínimo de un lenguaje regular es único salvo isomorfismo (teorema de
Myhill-Nerode; Hopcroft, Motwani y Ullman, 2007, sec. 4.4.4).

El isomorfismo se busca recorriendo ambos mínimos en paralelo desde sus
estados iniciales: como son deterministas, la correspondencia está forzada.
Si no son equivalentes se busca además un **contraejemplo**: la cadena más
corta que uno acepta y el otro no, con un recorrido en anchura del autómata
producto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.automata import Automata
from algoritmos.minimizacion import completar, minimizar
from algoritmos.subconjuntos import construir_afd


@dataclass
class Comparacion:
    equivalentes: bool
    minimo1: Automata
    minimo2: Automata
    correspondencia: dict[str, str] = field(default_factory=dict)
    motivo: str = ""
    contraejemplo: Optional[str] = None
    acepta1: Optional[bool] = None


def a_afd(a: Automata) -> Automata:
    return a.copia() if a.es_determinista() else construir_afd(a)[0]


def _con_alfabeto(a: Automata, alfabeto: list[str]) -> Automata:
    b = a.copia()
    for s in alfabeto:
        if s not in b.alfabeto:
            b.alfabeto.append(s)
    return b


def isomorfismo(m1: Automata, m2: Automata) -> tuple[Optional[dict[str, str]], str]:
    """Correspondencia de estados entre dos AFD completos, o el motivo de fallo."""
    if len(m1.estados) != len(m2.estados):
        return None, f"Los AFD mínimos tienen {len(m1.estados)} y {len(m2.estados)} estados."
    if set(m1.alfabeto) != set(m2.alfabeto):
        return None, "Los alfabetos son distintos."
    mapa = {m1.inicial: m2.inicial}
    cola = [m1.inicial]
    while cola:
        p = cola.pop(0)
        q = mapa[p]
        if (p in m1.aceptacion) != (q in m2.aceptacion):
            return None, f"{p} y {q} se corresponden, pero sólo uno es de aceptación."
        for s in m1.alfabeto:
            dp = next(iter(m1.destinos(p, s)))
            dq = next(iter(m2.destinos(q, s)))
            if dp in mapa:
                if mapa[dp] != dq:
                    return None, f"Con «{s}», {p} va a {dp} (↔ {mapa[dp]}) pero {q} va a {dq}."
            else:
                if dq in mapa.values():
                    return None, f"{dq} ya corresponde a otro estado."
                mapa[dp] = dq
                cola.append(dp)
    return mapa, "Los AFD mínimos coinciden salvo el nombre de los estados."


def contraejemplo(a1: Automata, a2: Automata) -> Optional[tuple[str, bool]]:
    """Cadena más corta aceptada por exactamente uno de los dos AFD completos."""
    inicio = (a1.inicial, a2.inicial)
    vistos = {inicio: ""}
    cola = [inicio]
    alfabeto = sorted(set(a1.alfabeto) | set(a2.alfabeto))
    while cola:
        p, q = cola.pop(0)
        w = vistos[(p, q)]
        if (p in a1.aceptacion) != (q in a2.aceptacion):
            return w, p in a1.aceptacion
        for s in alfabeto:
            par = (next(iter(a1.destinos(p, s))), next(iter(a2.destinos(q, s))))
            if par not in vistos:
                vistos[par] = w + s
                cola.append(par)
    return None


def comparar(a1: Automata, a2: Automata) -> Comparacion:
    alfabeto = list(dict.fromkeys(list(a1.alfabeto) + list(a2.alfabeto)))
    d1 = completar(_con_alfabeto(a_afd(a1), alfabeto))[0]
    d2 = completar(_con_alfabeto(a_afd(a2), alfabeto))[0]
    m1 = minimizar(d1, conservar_sumidero=True)[0]
    m2 = minimizar(d2, conservar_sumidero=True)[0]
    mapa, motivo = isomorfismo(m1, m2)
    if mapa is not None:
        return Comparacion(True, m1, m2, mapa, motivo)
    ce = contraejemplo(m1, m2)
    comp = Comparacion(False, m1, m2, {}, motivo)
    if ce is not None:
        comp.contraejemplo, comp.acepta1 = ce
    return comp


def equivalentes(a1: Automata, a2: Automata) -> bool:
    return comparar(a1, a2).equivalentes
