"""Eliminación de transiciones λ: de un AFN-λ a un AFN equivalente sin λ.

Construcción (Hopcroft, Motwani y Ullman, 2007, sec. 2.5.5; aquí sin pasar
por subconjuntos, conservando los mismos estados):

* Q' = Q, Σ' = Σ, q0' = q0.
* δ'(q, a) = λ-clausura( ∪_{p ∈ λ-clausura(q)} δ(p, a) ).
* F' = { q ∈ Q : λ-clausura(q) ∩ F ≠ ∅ }.

Así, leer *a* desde q en el AFN equivale a «moverse por λ, leer a, moverse por
λ» en el AFN-λ, y q acepta λ si alguna computación λ desde q llega a F.

Coste: con las clausuras precalculadas, para cada q y cada a se unen a lo sumo
|Q| conjuntos de destinos y sus clausuras: O(|Q|³·|Σ|) en el peor caso.
"""

from __future__ import annotations

from core.automata import LAMBDA, Automata
from algoritmos.cerradura import tabla_cerraduras
from algoritmos.pasos import Paso, conjunto


def eliminar_lambda(a: Automata) -> tuple[Automata, list[Paso], dict]:
    clausuras = tabla_cerraduras(a)
    orden = a._orden
    pasos: list[Paso] = []
    tabla = [["q", "λ-clausura(q)"]] + [[q, conjunto(clausuras[q], orden)] for q in a.estados]
    pasos.append(Paso("1. λ-clausura de cada estado",
                      "Se calcula la λ-clausura de todos los estados; es la base de la construcción.",
                      a, set(), set(), {q: conjunto(clausuras[q], orden) for q in a.estados}, tabla))

    nuevo = Automata(list(a.estados), list(a.alfabeto), a.inicial, set(), {}, f"{a.nombre} (sin λ)",
                     a.descripcion, dict(a.posiciones))
    # Foto de trabajo: parte del original y va recibiendo las transiciones nuevas.
    trabajo = a.copia()
    originales = {(q, s, d) for q, s, d in a.lista_transiciones() if s != LAMBDA}
    agregadas: list[tuple[str, str, str]] = []
    filas = [["q", *a.alfabeto]]
    for q in a.estados:
        fila = [q]
        aristas_nuevas: set[tuple[str, str]] = set()
        explicacion = []
        for s in a.alfabeto:
            movidos = set()
            for p in clausuras[q]:
                movidos |= a.destinos(p, s)
            destinos = set()
            for d in movidos:
                destinos |= clausuras[d]
            for d in destinos:
                nuevo.agregar_transicion(q, s, d)
                if (q, s, d) not in originales:
                    agregadas.append((q, s, d))
                    trabajo.agregar_transicion(q, s, d)
                    aristas_nuevas.add((q, d))
            fila.append(conjunto(destinos, orden))
            if destinos:
                explicacion.append(f"δ'({q},{s}) = λ-cl(δ({conjunto(clausuras[q], orden)},{s})) = "
                                   f"λ-cl({conjunto(movidos, orden)}) = {conjunto(destinos, orden)}")
        filas.append(fila)
        pasos.append(Paso(f"2. Transiciones desde {q}",
                          "\n".join(explicacion) or f"Desde λ-clausura({q}) no se lee ningún símbolo.",
                          trabajo.copia(), {q} | set(clausuras[q]), aristas_nuevas,
                          tabla=[r[:] for r in filas], tipo="nuevo" if aristas_nuevas else "info"))

    nuevas_finales = []
    for q in a.estados:
        if clausuras[q] & a.aceptacion:
            nuevo.aceptacion.add(q)
            if q not in a.aceptacion:
                nuevas_finales.append(q)
    trabajo.aceptacion = set(nuevo.aceptacion)
    pasos.append(Paso("3. Estados de aceptación",
                      "F' = {q : λ-clausura(q) ∩ F ≠ ∅}. "
                      + (f"Pasan a ser de aceptación: {', '.join(nuevas_finales)}." if nuevas_finales
                         else "Ningún estado nuevo pasa a ser de aceptación."),
                      trabajo.copia(), set(nuevas_finales), set(),
                      {q: "∈ F'" for q in nuevo.aceptacion}, tipo="nuevo" if nuevas_finales else "info"))
    lambdas = [(q, d) for q, s, d in a.lista_transiciones() if s == LAMBDA]
    pasos.append(Paso("4. Se eliminan las transiciones λ",
                      f"Se quitan {len(lambdas)} transiciones λ. El AFN resultante reconoce el mismo lenguaje.",
                      nuevo, set(), set(), tipo="exito"))
    info = {"clausuras": clausuras, "agregadas": agregadas, "nuevas_finales": nuevas_finales,
            "eliminadas": lambdas}
    return nuevo, pasos, info
