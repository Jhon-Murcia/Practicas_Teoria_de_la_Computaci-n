"""Cuadros de la simulación gráfica (Práctica 5, ejercicio 3.2).

La simulación (:mod:`core.simulacion`) calcula el recorrido; este módulo lo
traduce a lo que el lienzo debe resaltar en cada posición de la cinta, sin
depender de la interfaz. El cuadro ``k`` corresponde a haber leído los ``k``
primeros símbolos:

* ``activos``: estados que se resaltan (uno solo en un AFD; el conjunto de
  estados activos en un AFND o AFND-λ).
* ``transiciones``: transiciones usadas para llegar a ese cuadro, incluidas las
  λ recorridas por la clausura. ``aristas`` son los pares (origen, destino) que
  se dibujan resaltados.
* ``leido`` y ``pendiente``: la cadena separada en la parte ya consumida y la
  que falta.
* ``veredicto``: ``None`` mientras quedan símbolos; al final, ``True`` si la
  cadena se acepta y ``False`` si se rechaza.

Así el dibujo sólo pinta cuadros y las pruebas comparan los cuadros con el
recorrido del simulador.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.simulacion import Resultado


@dataclass(frozen=True)
class Cuadro:
    indice: int
    activos: frozenset[str]
    transiciones: tuple[tuple[str, str, str], ...]
    leido: tuple[str, ...]
    pendiente: tuple[str, ...]
    simbolo: Optional[str]
    veredicto: Optional[bool]

    @property
    def aristas(self) -> frozenset[tuple[str, str]]:
        return frozenset((o, d) for o, _, d in self.transiciones)

    @property
    def terminado(self) -> bool:
        return self.veredicto is not None


def cuadros(r: Resultado) -> list[Cuadro]:
    """Un cuadro por cada símbolo leído, más la configuración inicial."""
    n = len(r.pasos)
    lista = [Cuadro(0, r.inicio, tuple(r.lambda_inicio), (), tuple(r.simbolos), None,
                    _veredicto(r) if n == 0 else None)]
    for k, p in enumerate(r.pasos, start=1):
        lista.append(Cuadro(k, p.despues, tuple(p.transiciones + p.transiciones_lambda),
                            tuple(r.simbolos[:k]), tuple(r.simbolos[k:]), p.simbolo,
                            _veredicto(r) if k == n else None))
    return lista


def _veredicto(r: Resultado) -> bool:
    # Un símbolo fuera de Σ detiene la simulación: la cadena se rechaza.
    return False if r.error else r.aceptada


def recorrido(r: Resultado) -> list[frozenset[str]]:
    """Secuencia de conjuntos que se resaltan, cuadro por cuadro."""
    return [c.activos for c in cuadros(r)]
