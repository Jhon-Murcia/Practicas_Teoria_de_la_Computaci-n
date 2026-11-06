"""λ-clausura de un estado y de un conjunto de estados.

λ-clausura(q) es el menor conjunto que contiene a q y que es cerrado bajo las
transiciones λ: si p ∈ λ-clausura(q) y r ∈ δ(p, λ), entonces r ∈ λ-clausura(q).
Se calcula con un recorrido en profundidad sobre las aristas λ
(Hopcroft, Motwani y Ullman, 2007, sec. 2.5.3).

Coste: cada estado entra una vez en la pila y cada arista λ se examina una
vez, O(|Q| + |δ_λ|) por estado; O(|Q|·(|Q| + |δ_λ|)) para la tabla completa.
"""

from __future__ import annotations

from core.automata import LAMBDA, Automata
from algoritmos.pasos import Paso, conjunto


def cerradura(a: Automata, estados) -> frozenset[str]:
    resultado = set(estados)
    pila = list(estados)
    while pila:
        q = pila.pop()
        for d in a.destinos(q, LAMBDA):
            if d not in resultado:
                resultado.add(d)
                pila.append(d)
    return frozenset(resultado)


def cerradura_con_pasos(a: Automata, q: str) -> tuple[frozenset[str], list[Paso]]:
    """λ-clausura de un estado registrando cada estado procesado."""
    resultado = {q}
    pila = [q]
    pasos = [Paso(f"Inicio: λ-clausura({q}) ⊇ {{{q}}}",
                  "Todo estado pertenece a su propia λ-clausura (se alcanza con cero transiciones λ).",
                  a, {q}, set(), tabla=[["Pila", "Clausura parcial"], [conjunto(pila, a._orden), conjunto(resultado, a._orden)]])]
    while pila:
        p = pila.pop()
        destinos = sorted(a.destinos(p, LAMBDA), key=a._orden)
        nuevos = [d for d in destinos if d not in resultado]
        for d in nuevos:
            resultado.add(d)
            pila.append(d)
        if destinos:
            detalle = (f"δ({p}, λ) = {conjunto(destinos, a._orden)}. "
                       + (f"Se agregan {', '.join(nuevos)}." if nuevos else "Todos ya estaban en la clausura."))
        else:
            detalle = f"{p} no tiene transiciones λ."
        pasos.append(Paso(f"Se procesa {p}", detalle, a, set(resultado), {(p, d) for d in destinos},
                          tabla=[["Pila", "Clausura parcial"],
                                 [conjunto(pila, a._orden), conjunto(resultado, a._orden)]],
                          tipo="nuevo" if nuevos else "info"))
    final = frozenset(resultado)
    pasos.append(Paso(f"λ-clausura({q}) = {conjunto(final, a._orden)}",
                      "La pila quedó vacía: ningún estado nuevo es alcanzable con transiciones λ.",
                      a, set(final), set(), tipo="exito"))
    return final, pasos


def tabla_cerraduras(a: Automata) -> dict[str, frozenset[str]]:
    return {q: cerradura(a, {q}) for q in a.estados}
