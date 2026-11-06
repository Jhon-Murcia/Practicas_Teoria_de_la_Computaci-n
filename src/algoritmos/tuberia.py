"""Cadena completa de conversiones a partir de una expresión regular.

ER → AFN-λ (Thompson) → AFN sin λ → AFD (subconjuntos) → AFD mínimo.
Reutiliza los algoritmos de la Práctica 3 sin modificarlos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.automata import Automata
from core.expresion_regular import ER, a_texto, analizar, analizar_clases
from algoritmos.eliminacion_lambda import eliminar_lambda
from algoritmos.minimizacion import minimizar
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
    minimo.nombre = f"AFD mínimo de {nombre}"
    return Resultado(r, [
        Etapa("AFN-λ (Thompson)", afn_l, p0),
        Etapa("AFN sin λ", afn, p1),
        Etapa("AFD (subconjuntos)", afd, p2),
        Etapa("AFD mínimo", minimo, p3),
    ])


def desde_texto(texto: str, clases_texto: str = "") -> Resultado:
    clases = analizar_clases(clases_texto) if clases_texto.strip() else {}
    return desde_expresion(analizar(texto, clases), texto.strip())
