"""Minimización de AFD.

1. **Estados inaccesibles.** Se eliminan los que no se alcanzan desde q0.
2. **Completar δ.** Si δ es parcial se agrega un estado sumidero, porque la
   ausencia de transición equivale a ir a un estado de rechazo.
3. **Refinamiento de particiones** (algoritmo de Moore; Hopcroft, Motwani y
   Ullman, 2007, sec. 4.4): P0 = {F, Q − F}. En cada ronda, dos estados del
   mismo bloque se separan si, para algún símbolo, van a bloques distintos.
   Se repite hasta que la partición no cambia; cada bloque final es un estado
   del AFD mínimo. La partición final corresponde a la relación de
   Myhill-Nerode restringida al autómata.
4. Si el AFD de entrada era parcial, el bloque «muerto» (no acepta nada) se
   quita del resultado, de modo que el AFD mínimo nunca tiene más estados que
   el AFD del que procede.

También se ofrece el método de la **tabla de pares distinguibles**
(sec. 4.4.1): se marcan los pares {p, q} con p ∈ F y q ∉ F; después, se marca
{p, q} si para algún a el par {δ(p, a), δ(q, a)} ya está marcado.

Coste del refinamiento: cada ronda revisa |Q|·|Σ| transiciones y hay a lo
sumo |Q| rondas: O(|Q|²·|Σ|). (El algoritmo de Hopcroft logra
O(|Q|·|Σ|·log|Q|) procesando sólo el bloque más pequeño.)
"""

from __future__ import annotations

from itertools import combinations
from typing import Optional

from core.automata import Automata
from core.disposicion import disponer
from algoritmos.pasos import Paso, conjunto

SUMIDERO = "⊥"


def eliminar_inaccesibles(a: Automata) -> tuple[Automata, list[str]]:
    quitados = a.inaccesibles()
    b = a.copia()
    for q in quitados:
        b.eliminar_estado(q)
    return b, quitados


def completar(a: Automata, nombre: str = SUMIDERO) -> tuple[Automata, Optional[str]]:
    """Agrega un sumidero si δ es parcial. Devuelve el autómata y el sumidero."""
    if a.es_completo():
        return a.copia(), None
    b = a.copia()
    while nombre in b.estados:
        nombre += "'"
    faltan = b.faltantes()
    b.agregar_estado(nombre)
    for q, s in faltan:
        b.agregar_transicion(q, s, nombre)
    for s in b.alfabeto:
        b.agregar_transicion(nombre, s, nombre)
    return b, nombre


def _verificar_afd(a: Automata) -> None:
    conflictos = a.conflictos_determinismo()
    if conflictos:
        q, s, motivo = conflictos[0]
        raise ValueError(f"El autómata no es determinista: {motivo}. Conviértalo primero a AFD.")
    if a.inicial is None:
        raise ValueError("El autómata no tiene estado inicial.")


def _destino(a: Automata, q: str, s: str) -> str:
    return next(iter(a.destinos(q, s)))


def refinar(a: Automata) -> list[list[frozenset[str]]]:
    """Rondas de la partición de un AFD completo (la última es la estable)."""
    F = frozenset(q for q in a.estados if q in a.aceptacion)
    N = frozenset(q for q in a.estados if q not in a.aceptacion)
    particion = [b for b in (F, N) if b]
    rondas = [particion]
    while True:
        bloque_de = {q: i for i, b in enumerate(particion) for q in b}
        nueva: list[frozenset[str]] = []
        for b in particion:
            grupos: dict[tuple, set[str]] = {}
            for q in sorted(b, key=a._orden):
                firma = tuple(bloque_de[_destino(a, q, s)] for s in a.alfabeto)
                grupos.setdefault(firma, set()).add(q)
            nueva.extend(frozenset(g) for g in grupos.values())
        if len(nueva) == len(particion):
            return rondas
        particion = nueva
        rondas.append(particion)


def _nombre_bloque(bloque, orden) -> str:
    miembros = sorted(bloque, key=lambda q: (orden(q), q))
    return miembros[0] if len(miembros) == 1 else "[" + ",".join(miembros) + "]"


def minimizar(a: Automata, conservar_sumidero: bool = False) -> tuple[Automata, list[Paso], dict]:
    """AFD mínimo con los pasos (inaccesibles, completar, cada ronda, resultado)."""
    _verificar_afd(a)
    pasos: list[Paso] = []
    original_completo = a.es_completo()
    accesible, quitados = eliminar_inaccesibles(a)
    pasos.append(Paso(
        "1. Estados inaccesibles",
        (f"Se eliminan {', '.join(quitados)}: no se alcanzan desde {a.inicial}." if quitados
         else f"Todos los estados se alcanzan desde {a.inicial}."),
        a, set(accesible.estados), set(), {q: "inaccesible" for q in quitados},
        tipo="nuevo" if quitados else "info"))
    completo, sumidero = completar(accesible)
    if sumidero:
        completo.posiciones = dict(accesible.posiciones)
        completo.posiciones[sumidero] = _pos_sumidero(accesible)
    pasos.append(Paso(
        "2. Completar la función de transición",
        (f"δ es parcial: se agrega el sumidero {sumidero} y las transiciones que faltaban van a él."
         if sumidero else "δ ya es total; no hace falta un sumidero."),
        completo, {sumidero} if sumidero else set(), set(), tipo="nuevo" if sumidero else "info"))

    rondas = refinar(completo)
    orden = completo._orden
    for i, particion in enumerate(rondas):
        etiquetas = {q: f"B{j}" for j, b in enumerate(particion) for q in b}
        filas = [["Estado", "Bloque", *[f"δ(·,{s})→" for s in completo.alfabeto]]]
        for q in completo.estados:
            filas.append([q, etiquetas[q], *[etiquetas[_destino(completo, q, s)] for s in completo.alfabeto]])
        texto_part = "  ".join(f"B{j} = {conjunto(b, orden)}" for j, b in enumerate(particion))
        if i == 0:
            titulo = "3. Partición inicial P0 = {F, Q − F}"
            detalle = f"Se separan los de aceptación de los demás.\n{texto_part}"
            separados: set[str] = set()
        else:
            previa = rondas[i - 1]
            divididos = [b for b in previa if b not in particion]
            separados = set().union(*divididos) if divididos else set()
            titulo = f"Ronda {i}: P{i}"
            detalle = ("Se dividen los bloques cuyos estados van, con algún símbolo, a bloques distintos de "
                       f"P{i - 1}: " + ", ".join(conjunto(b, orden) for b in divididos) + f".\n{texto_part}")
        pasos.append(Paso(titulo, detalle, completo, separados, set(), etiquetas, filas,
                          tipo="nuevo" if i else "info"))
    estable = rondas[-1]
    pasos.append(Paso(f"Ronda {len(rondas)}: la partición no cambia",
                      f"P{len(rondas) - 1} es estable: sus {len(estable)} bloques son las clases de estados "
                      "equivalentes (indistinguibles).",
                      completo, set(), set(), {q: f"B{j}" for j, b in enumerate(estable) for q in b},
                      tipo="info"))

    # Construcción del AFD mínimo: un estado por bloque.
    nombre_de = {q: _nombre_bloque(b, orden) for b in estable for q in b}
    minimo = Automata(nombre=f"{a.nombre} (mínimo)", alfabeto=list(completo.alfabeto))
    for b in sorted(estable, key=lambda b: min(orden(q) for q in b)):
        minimo.agregar_estado(_nombre_bloque(b, orden))
    minimo.inicial = nombre_de[completo.inicial]
    for b in estable:
        rep = next(iter(b))
        for s in completo.alfabeto:
            minimo.agregar_transicion(nombre_de[rep], s, nombre_de[_destino(completo, rep, s)])
        if rep in completo.aceptacion:
            minimo.aceptacion.add(nombre_de[rep])
    muertos = estados_muertos(minimo)
    quitados_muertos: list[str] = []
    if not original_completo and not conservar_sumidero:
        for q in muertos:
            if q != minimo.inicial:
                minimo.eliminar_estado(q)
                quitados_muertos.append(q)
    minimo.posiciones = disponer(minimo)
    equivalentes = [sorted(b, key=orden) for b in estable if len(b) > 1]
    pasos.append(Paso(
        "Resultado: AFD mínimo",
        f"{len(a.estados)} estados originales → {len(minimo.estados)} en el AFD mínimo."
        + (f"\nEstados equivalentes fusionados: " + "; ".join("{" + ", ".join(e) + "}" for e in equivalentes)
           if equivalentes else "\nNo había estados equivalentes.")
        + (f"\nSe omite el estado de error {', '.join(quitados_muertos)} porque el AFD original era parcial."
           if quitados_muertos else ""),
        minimo, set(minimo.estados), set(), tipo="exito"))
    info = {"inaccesibles": quitados, "sumidero": sumidero, "rondas": rondas, "equivalentes": equivalentes,
            "completo": completo, "muertos_quitados": quitados_muertos}
    return minimo, pasos, info


def estados_muertos(a: Automata) -> list[str]:
    """Estados desde los que no se alcanza ningún estado de aceptación."""
    vivos = set(a.aceptacion)
    cambio = True
    while cambio:
        cambio = False
        for (q, _), ds in a.transiciones.items():
            if q not in vivos and ds & vivos:
                vivos.add(q)
                cambio = True
    return [q for q in a.estados if q not in vivos]


def _pos_sumidero(a: Automata) -> tuple[float, float]:
    if not a.posiciones:
        return (400.0, 400.0)
    xs = [x for x, _ in a.posiciones.values()]
    ys = [y for _, y in a.posiciones.values()]
    return ((min(xs) + max(xs)) / 2, max(ys) + 130)


def tabla_distinguibles(a: Automata) -> tuple[list[dict[tuple[str, str], int]], list[str]]:
    """Método de la tabla: ronda en que se marca cada par (0 = distinguido por F).

    Devuelve la lista de rondas (cada una con los pares marcados hasta ella) y
    el orden de los estados del AFD completo y sin inaccesibles.
    """
    _verificar_afd(a)
    b, _ = eliminar_inaccesibles(a)
    c, _ = completar(b)
    estados = list(c.estados)
    marcados: dict[tuple[str, str], int] = {}
    for p, q in combinations(estados, 2):
        if (p in c.aceptacion) != (q in c.aceptacion):
            marcados[(p, q)] = 0
    rondas = [dict(marcados)]
    ronda = 0
    while True:
        ronda += 1
        nuevos = {}
        for p, q in combinations(estados, 2):
            if (p, q) in marcados:
                continue
            for s in c.alfabeto:
                x, y = _destino(c, p, s), _destino(c, q, s)
                if x != y and ((x, y) in marcados or (y, x) in marcados):
                    nuevos[(p, q)] = ronda
                    break
        if not nuevos:
            return rondas, estados
        marcados.update(nuevos)
        rondas.append(dict(marcados))


def renombrar_canonico(a: Automata, prefijo: str = "q") -> Automata:
    """Renombra los estados q0, q1, … en orden de recorrido en anchura."""
    orden: list[str] = []
    if a.inicial is not None:
        cola = [a.inicial]
        while cola:
            q = cola.pop(0)
            if q in orden:
                continue
            orden.append(q)
            for s in sorted(a.alfabeto):
                for d in sorted(a.destinos(q, s), key=a._orden):
                    if d not in orden:
                        cola.append(d)
    orden += [q for q in a.estados if q not in orden]
    nuevo = {q: f"{prefijo}{i}" for i, q in enumerate(orden)}
    b = Automata(nombre=a.nombre, alfabeto=list(a.alfabeto), descripcion=a.descripcion)
    for q in orden:
        b.agregar_estado(nuevo[q])
    b.inicial = nuevo[a.inicial] if a.inicial else None
    b.aceptacion = {nuevo[q] for q in a.aceptacion}
    for q, s, d in a.lista_transiciones():
        b.agregar_transicion(nuevo[q], s, nuevo[d])
    b.posiciones = {nuevo[q]: p for q, p in a.posiciones.items() if q in nuevo}
    return b
