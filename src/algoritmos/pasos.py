"""Representación neutral de un paso de un algoritmo, para mostrarlo.

Un paso puede llevar una «foto» del autómata en ese momento, qué estados y
aristas resaltar, etiquetas adicionales bajo los estados (por ejemplo, el
bloque de la partición al que pertenecen) y una tabla.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.automata import Automata


@dataclass
class Paso:
    titulo: str
    detalle: str = ""
    automata: Optional[Automata] = None
    estados: set[str] = field(default_factory=set)
    aristas: set[tuple[str, str]] = field(default_factory=set)
    etiquetas: dict[str, str] = field(default_factory=dict)
    tabla: Optional[list[list[str]]] = None    # la primera fila es el encabezado
    tipo: str = "info"                         # info | nuevo | exito | aviso


def conjunto(estados, orden=None) -> str:
    """``{q0, q1}`` con un orden estable; ``∅`` si es vacío."""
    if not estados:
        return "∅"
    clave = (lambda q: (orden(q), q)) if orden else None
    return "{" + ", ".join(sorted(estados, key=clave)) + "}"
