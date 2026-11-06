"""Construcción de subconjuntos: de un AFN a un AFD equivalente.

Sólo se construyen los subconjuntos **alcanzables** desde el inicial
(Rabin y Scott, 1959; Hopcroft, Motwani y Ullman, 2007, sec. 2.3.5, donde
se describe esta «evaluación perezosa»):

    D0 := λ-clausura({q0});  pendientes := [D0]
    mientras haya pendientes:
        S := pendientes.extraer()
        para cada a ∈ Σ:
            T := λ-clausura( ∪_{q ∈ S} δ(q, a) )
            δ_D(S, a) := T
            si T es nuevo: agregarlo a pendientes
    F_D := { S : S ∩ F ≠ ∅ }

Si el AFN tiene transiciones λ se aplica la λ-clausura (así también funciona
directamente sobre un AFN-λ). El conjunto vacío ∅, si aparece, es el estado de
error del AFD. El AFD resultante es completo.

Coste: a lo sumo 2^|Q| subconjuntos; por cada uno y cada símbolo se unen hasta
|Q| conjuntos de destinos: O(2^|Q| · |Σ| · |Q|²) en el peor caso.
"""

from __future__ import annotations

from core.automata import Automata
from core.disposicion import disponer
from algoritmos.cerradura import cerradura
from algoritmos.pasos import Paso, conjunto

VACIO = "∅"


def nombre_subconjunto(estados, orden) -> str:
    if not estados:
        return VACIO
    return "{" + ",".join(sorted(estados, key=lambda q: (orden(q), q))) + "}"


def construir_afd(a: Automata) -> tuple[Automata, list[Paso], list[list[str]]]:
    if a.inicial is None:
        raise ValueError("El autómata no tiene estado inicial.")
    orden = a._orden
    nombre = lambda S: nombre_subconjunto(S, orden)  # noqa: E731
    inicial = cerradura(a, {a.inicial})
    afd = Automata(nombre=f"{a.nombre} (AFD)")
    afd.alfabeto = list(a.alfabeto)
    afd.agregar_estado(nombre(inicial))
    afd.inicial = nombre(inicial)
    pendientes = [inicial]
    vistos = {inicial: nombre(inicial)}
    tabla = [["Subconjunto", *a.alfabeto, "¿Acepta?"]]
    pasos: list[Paso] = [Paso(
        f"Estado inicial del AFD: λ-clausura({{{a.inicial}}}) = {conjunto(inicial, orden)}",
        "Se parte del subconjunto inicial; la cola contiene los subconjuntos aún no procesados.",
        _foto(afd), {nombre(inicial)}, set(), tabla=[r[:] for r in tabla])]

    while pendientes:
        S = pendientes.pop(0)
        nS = vistos[S]
        fila = [nS]
        nuevos: list[str] = []
        detalles = []
        aristas = set()
        for s in a.alfabeto:
            movidos = set()
            for q in S:
                movidos |= a.destinos(q, s)
            T = cerradura(a, movidos)
            if T not in vistos:
                vistos[T] = nombre(T)
                afd.agregar_estado(vistos[T])
                pendientes.append(T)
                nuevos.append(vistos[T])
            afd.agregar_transicion(nS, s, vistos[T])
            aristas.add((nS, vistos[T]))
            fila.append(vistos[T])
            detalles.append(f"δ({conjunto(S, orden)}, {s}) = λ-cl({conjunto(movidos, orden)}) = {conjunto(T, orden)}"
                            + ("  ← nuevo" if vistos[T] in nuevos else ""))
        acepta = bool(S & a.aceptacion)
        if acepta:
            afd.aceptacion.add(nS)
        fila.append("sí: contiene " + ", ".join(sorted(S & a.aceptacion, key=orden)) if acepta else "no")
        tabla.append(fila)
        pasos.append(Paso(
            f"Se procesa {conjunto(S, orden)}",
            "\n".join(detalles) + (f"\nSubconjuntos nuevos: {', '.join(nuevos)}." if nuevos else
                                   "\nNo aparecen subconjuntos nuevos.")
            + (f"\nCola: {', '.join(vistos[P] for P in pendientes) or 'vacía'}."),
            _foto(afd), {nS, *nuevos}, aristas, tabla=[r[:] for r in tabla],
            tipo="nuevo" if nuevos else "info"))

    aceptacion = [vistos[S] for S in vistos if S & a.aceptacion]
    pasos.append(Paso(
        "Estados de aceptación del AFD",
        "Un subconjunto es de aceptación si contiene algún estado de aceptación del AFN: "
        + (", ".join(aceptacion) if aceptacion else "ninguno") + "."
        + (f"\n{VACIO} es el estado de error: una vez en él no se sale."
           if frozenset() in vistos else ""),
        _foto(afd), set(aceptacion), set(), tabla=[r[:] for r in tabla], tipo="exito"))
    afd.posiciones = disponer(afd)
    return afd, pasos, tabla


def _foto(afd: Automata) -> Automata:
    c = afd.copia()
    c.posiciones = disponer(c)
    return c
