"""Geometría del diagrama de un autómata (funciones puras, sin Flet).

Calcula dónde van las flechas, las curvas, los bucles y las etiquetas en
coordenadas del «mundo»; el lienzo sólo las transforma a pantalla y las dibuja.

* Arista simple: recta entre los bordes de los dos círculos.
* Aristas en ambos sentidos (p → q y q → p): cada una se curva hacia su lado
  con una Bézier cuadrática, para que no se superpongan.
* Bucle (q → q): Bézier cúbica por encima del estado.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

RADIO = 26.0
CURVATURA = 34.0
PUNTA = 11.0


@dataclass
class Arista:
    origen: str
    destino: str
    etiqueta: str
    tipo: str                         # "recta" | "curva" | "bucle"
    inicio: tuple[float, float]
    fin: tuple[float, float]
    control1: tuple[float, float] | None
    control2: tuple[float, float] | None
    punta: list[tuple[float, float]]  # triángulo de la flecha
    pos_etiqueta: tuple[float, float]

    def contiene_etiqueta(self, x: float, y: float, tolerancia: float = 14.0) -> bool:
        ex, ey = self.pos_etiqueta
        ancho = max(18.0, 7.2 * len(self.etiqueta)) / 2 + 4
        return abs(x - ex) <= ancho and abs(y - ey) <= tolerancia

    def distancia(self, x: float, y: float) -> float:
        """Distancia aproximada del punto a la curva (muestreo de 24 puntos)."""
        return min(math.dist((x, y), p) for p in self.muestras(24))

    def muestras(self, n: int = 24) -> list[tuple[float, float]]:
        pts = []
        for i in range(n + 1):
            t = i / n
            if self.tipo == "recta":
                pts.append(_lerp(self.inicio, self.fin, t))
            elif self.tipo == "curva":
                pts.append(_bezier2(self.inicio, self.control1, self.fin, t))
            else:
                pts.append(_bezier3(self.inicio, self.control1, self.control2, self.fin, t))
        return pts


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _bezier2(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def _bezier3(p0, p1, p2, p3, t):
    u = 1 - t
    a, b, c, d = u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _unitario(dx: float, dy: float) -> tuple[float, float]:
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def punta_flecha(fin: tuple[float, float], direccion: tuple[float, float], largo: float = PUNTA) -> list[tuple[float, float]]:
    ux, uy = _unitario(*direccion)
    nx, ny = -uy, ux
    bx, by = fin[0] - ux * largo, fin[1] - uy * largo
    return [fin, (bx + nx * largo * 0.48, by + ny * largo * 0.48), (bx - nx * largo * 0.48, by - ny * largo * 0.48)]


def arista(origen: str, destino: str, etiqueta: str, p: tuple[float, float], q: tuple[float, float],
           curvar: bool, radio: float = RADIO) -> Arista:
    if origen == destino:
        cx, cy = p
        ini = (cx - radio * 0.5, cy - radio * 0.87)
        fin = (cx + radio * 0.5, cy - radio * 0.87)
        c1 = (cx - radio * 1.25, cy - radio * 2.7)
        c2 = (cx + radio * 1.25, cy - radio * 2.7)
        tope = _bezier3(ini, c1, c2, fin, 0.5)
        return Arista(origen, destino, etiqueta, "bucle", ini, fin, c1, c2,
                      punta_flecha(fin, (fin[0] - c2[0], fin[1] - c2[1])), (tope[0], tope[1] - 11))
    ux, uy = _unitario(q[0] - p[0], q[1] - p[1])
    nx, ny = -uy, ux
    if not curvar:
        ini = (p[0] + ux * radio, p[1] + uy * radio)
        fin = (q[0] - ux * radio, q[1] - uy * radio)
        medio = _lerp(ini, fin, 0.5)
        # La etiqueta se separa de la línea hacia el lado «izquierdo» del sentido.
        lado = 13 if abs(ux) > 0.3 else 16
        return Arista(origen, destino, etiqueta, "recta", ini, fin, None, None,
                      punta_flecha(fin, (ux, uy)), (medio[0] + nx * lado, medio[1] + ny * lado))
    medio = _lerp(p, q, 0.5)
    control = (medio[0] + nx * CURVATURA * 2, medio[1] + ny * CURVATURA * 2)
    d1 = _unitario(control[0] - p[0], control[1] - p[1])
    d2 = _unitario(control[0] - q[0], control[1] - q[1])
    ini = (p[0] + d1[0] * radio, p[1] + d1[1] * radio)
    fin = (q[0] + d2[0] * radio, q[1] + d2[1] * radio)
    pico = _bezier2(ini, control, fin, 0.5)
    return Arista(origen, destino, etiqueta, "curva", ini, fin, control, None,
                  punta_flecha(fin, (fin[0] - control[0], fin[1] - control[1])),
                  (pico[0] + nx * 12, pico[1] + ny * 12))


def resumir_simbolos(simbolos: list[str], mostrar=lambda s: s) -> str:
    """Etiqueta de una arista: los tramos consecutivos de 3 o más caracteres se
    resumen como rango (``0, 1, …, 9`` → ``0–9``; ``a, b, c`` → ``a–c``)."""
    simples = sorted({s for s in simbolos if len(s) == 1 and s.isalnum()}, key=ord)
    otros = [s for s in simbolos if s not in simples]
    partes: list[str] = [mostrar(s) for s in otros if s == ""]
    i = 0
    while i < len(simples):
        j = i
        while j + 1 < len(simples) and ord(simples[j + 1]) == ord(simples[j]) + 1                 and simples[j + 1].isdigit() == simples[i].isdigit():
            j += 1
        if j - i >= 2:
            partes.append(f"{simples[i]}–{simples[j]}")
        else:
            partes.extend(simples[i:j + 1])
        i = j + 1
    partes.extend(mostrar(s) for s in otros if s != "")
    return ", ".join(partes)


def aristas(posiciones: dict[str, tuple[float, float]], grupos: dict[tuple[str, str], list[str]],
            mostrar=lambda s: s) -> list[Arista]:
    """Una :class:`Arista` por par (origen, destino) con todos sus símbolos."""
    res = []
    for (o, d), simbolos in grupos.items():
        if o not in posiciones or d not in posiciones:
            continue
        etiqueta = resumir_simbolos(simbolos, mostrar)
        curvar = o != d and (d, o) in grupos
        res.append(arista(o, d, etiqueta, posiciones[o], posiciones[d], curvar))
    return res


def estado_en(posiciones: dict[str, tuple[float, float]], x: float, y: float, radio: float = RADIO) -> str | None:
    """Estado cuyo círculo contiene el punto (el último dibujado gana)."""
    for q in reversed(list(posiciones)):
        px, py = posiciones[q]
        if math.hypot(x - px, y - py) <= radio + 3:
            return q
    return None


def caja(posiciones: dict[str, tuple[float, float]], margen: float = 70.0) -> tuple[float, float, float, float]:
    if not posiciones:
        return (0.0, 0.0, 400.0, 300.0)
    xs = [x for x, _ in posiciones.values()]
    ys = [y for _, y in posiciones.values()]
    return (min(xs) - margen, min(ys) - margen - 40, max(xs) + margen, max(ys) + margen)
