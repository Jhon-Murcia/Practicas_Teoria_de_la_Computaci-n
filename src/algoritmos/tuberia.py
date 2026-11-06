"""Cadena completa de conversiones a partir de una expresión regular.

ER → AFN-λ (Thompson) → AFN sin λ → AFD (subconjuntos) → AFD mínimo.
Reutiliza los algoritmos de la Práctica 3 sin modificarlos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.automata import Automata
from core.disposicion import disponer
from core.expresion_regular import ER, a_texto, analizar, analizar_clases
from algoritmos.eliminacion_lambda import eliminar_lambda
from algoritmos.minimizacion import minimizar, renombrar_canonico
from algoritmos.pasos import Paso
from algoritmos.subconjuntos import construir_afd
from algoritmos.thompson import thompson


@dataclass
class Etapa:
    titulo: str
    automata: Automata
    pasos: list[Paso] = field(default_factory=list)


@dataclass
class Resultado:
    expresion: ER
    etapas: list[Etapa]

    @property
    def afn_lambda(self) -> Automata:
        return self.etapas[0].automata

    @property
    def afd(self) -> Automata:
        return self.etapas[2].automata

    @property
    def minimo(self) -> Automata:
        return self.etapas[3].automata


def desde_expresion(r: ER, nombre: Optional[str] = None) -> Resultado:
    nombre = nombre or a_texto(r)
    afn_l, p0 = thompson(r, f"AFN-λ de {nombre}")
    afn, p1, _ = eliminar_lambda(afn_l)
    afn.nombre = f"AFN de {nombre}"
    afd, p2, _ = construir_afd(afn)
    afd.nombre = f"AFD de {nombre}"
    minimo, p3, _ = minimizar(afd)
    # Los nombres heredados de los subconjuntos y de los bloques son ilegibles
    # ([{s3,s5},{s7}]…): el AFD mínimo se renombra q0, q1, … en orden de
    # recorrido en anchura, y la correspondencia queda registrada como un paso.
    renombrado = renombrar_canonico(minimo)
    renombrado.posiciones = disponer(renombrado)
    tabla = [["Estado", "Bloque del AFD mínimo"]]
    nombres = dict(zip(_orden_bfs(minimo), renombrado.estados))
    tabla += [[nombres[q], q] for q in _orden_bfs(minimo)]
    p3.append(Paso("Renombrado de estados",
                   "Los estados del AFD mínimo se renombran q0, q1, … en orden de recorrido en anchura desde el "
                   "inicial; la tabla da la correspondencia con los bloques.", renombrado,
                   set(renombrado.estados), set(), tabla=tabla, tipo="exito"))
    minimo = renombrado
    minimo.nombre = f"AFD mínimo de {nombre}"
    return Resultado(r, [
        Etapa("AFN-λ (Thompson)", afn_l, p0),
        Etapa("AFN sin λ", afn, p1),
        Etapa("AFD (subconjuntos)", afd, p2),
        Etapa("AFD mínimo", minimo, p3),
    ])


def _orden_bfs(a: Automata) -> list[str]:
    """El mismo orden que usa ``renombrar_canonico``."""
    orden: list[str] = []
    cola = [a.inicial] if a.inicial else []
    while cola:
        q = cola.pop(0)
        if q in orden:
            continue
        orden.append(q)
        for s in sorted(a.alfabeto):
            for d in sorted(a.destinos(q, s), key=a._orden):
                if d not in orden:
                    cola.append(d)
    return orden + [q for q in a.estados if q not in orden]


def desde_texto(texto: str, clases_texto: str = "") -> Resultado:
    clases = analizar_clases(clases_texto) if clases_texto.strip() else {}
    return desde_expresion(analizar(texto, clases), texto.strip())
