"""Disposición automática de los estados en el plano.

Los autómatas que producen los algoritmos (subconjuntos, minimización,
Thompson…) no traen coordenadas. Se colocan por **capas**: la capa de un
estado es su distancia (en número de transiciones) desde el inicial, de modo
que el diagrama se lee de izquierda a derecha como un recorrido en anchura.
Los estados inaccesibles van en una última columna.
"""

from __future__ import annotations

import math

from core.automata import Automata

SEP_X = 170.0
SEP_Y = 120.0
MARGEN = 90.0


def capas(a: Automata) -> list[list[str]]:
    if not a.estados:
        return []
    sucesores: dict[str, list[str]] = {q: [] for q in a.estados}
    for q, _, d in a.lista_transiciones():
        if d not in sucesores[q]:
            sucesores[q].append(d)
    nivel: dict[str, int] = {}
    inicio = a.inicial if a.inicial in a.estados else a.estados[0]
    nivel[inicio] = 0
    cola = [inicio]
    while cola:
        q = cola.pop(0)
        for d in sucesores[q]:
            if d not in nivel:
                nivel[d] = nivel[q] + 1
                cola.append(d)
    resto = [q for q in a.estados if q not in nivel]
    maximo = max(nivel.values()) if nivel else 0
    for q in resto:
        nivel[q] = maximo + 1
    grupos: dict[int, list[str]] = {}
    for q in a.estados:
        grupos.setdefault(nivel[q], []).append(q)
    return [grupos[k] for k in sorted(grupos)]


def disponer(a: Automata, origen: tuple[float, float] = (MARGEN, MARGEN)) -> dict[str, tuple[float, float]]:
    """Posiciones por capas, centradas verticalmente."""
    columnas = capas(a)
    if not columnas:
        return {}
    alto = max(len(c) for c in columnas)
    pos: dict[str, tuple[float, float]] = {}
    for i, col in enumerate(columnas):
        desplazamiento = (alto - len(col)) * SEP_Y / 2
        for j, q in enumerate(col):
            pos[q] = (origen[0] + i * SEP_X, origen[1] + desplazamiento + j * SEP_Y)
    return pos


def disponer_circulo(a: Automata, centro=(320.0, 260.0), radio: float | None = None) -> dict[str, tuple[float, float]]:
    n = len(a.estados)
    if n == 0:
        return {}
    radio = radio or max(110.0, 46.0 * n / math.pi)
    return {q: (centro[0] + radio * math.cos(2 * math.pi * i / n - math.pi),
                centro[1] + radio * math.sin(2 * math.pi * i / n - math.pi))
            for i, q in enumerate(a.estados)}


def asegurar_posiciones(a: Automata) -> None:
    """Completa las posiciones que falten sin mover las existentes."""
    faltan = [q for q in a.estados if q not in a.posiciones]
    if not faltan:
        return
    if len(faltan) == len(a.estados):
        a.posiciones = disponer(a)
        return
    nuevas = disponer(a)
    max_y = max((y for _, y in a.posiciones.values()), default=0.0)
    for i, q in enumerate(faltan):
        a.posiciones[q] = (nuevas[q][0], max_y + SEP_Y + (i // 6) * SEP_Y)
