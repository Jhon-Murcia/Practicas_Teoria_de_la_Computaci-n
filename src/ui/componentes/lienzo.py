"""Lienzo interactivo para dibujar y editar autómatas.

El dibujo se rehace con formas de ``flet.canvas`` a partir del modelo cada vez
que algo cambia; la geometría sale de :mod:`ui.geometria`. El mismo componente
sirve como editor (``editable=True``) y como vista de sólo lectura para la
simulación y los algoritmos (resaltando estados y aristas).

Interacción
-----------
* Rueda del ratón: acercar o alejar alrededor del puntero.
* Arrastrar un estado: moverlo. Arrastrar el fondo: desplazar la vista.
* Herramientas del editor: ``mover`` (seleccionar), ``estado`` (clic en el
  fondo crea un estado), ``transicion`` (clic en origen y luego en destino) y
  ``eliminar`` (clic en un estado o en la etiqueta de una transición).
"""

from __future__ import annotations

import math
from typing import Callable, Iterable, Optional

import flet as ft
import flet.canvas as cv

from core.automata import LAMBDA, Automata, mostrar_simbolo
from core.disposicion import asegurar_posiciones
from ui.componentes.comunes import refrescar
from ui.geometria import RADIO, Arista, aristas, caja, estado_en
from ui.tema import FUENTE, FUENTE_MONO, RADIO as RADIO_UI, T, alfa

Seleccion = Optional[tuple[str, object]]   # ("estado", q) | ("arista", (o, d))


class Lienzo:
    def __init__(self, automata: Optional[Automata], editable: bool = False,
                 al_cambiar: Optional[Callable[[], None]] = None,
                 al_seleccionar: Optional[Callable[[Seleccion], None]] = None,
                 al_nueva_transicion: Optional[Callable[[str, str], None]] = None,
                 al_eliminar: Optional[Callable[[Seleccion], None]] = None,
                 al_antes_de_cambiar: Optional[Callable[[], None]] = None,
                 alto: Optional[float] = None, rejilla: bool = True):
        self.a = automata
        self.editable = editable
        self.al_cambiar = al_cambiar
        self.al_seleccionar = al_seleccionar
        self.al_nueva_transicion = al_nueva_transicion
        self.al_eliminar = al_eliminar
        self.al_antes_de_cambiar = al_antes_de_cambiar
        self.mostrar_rejilla = rejilla

        self.zoom, self.ox, self.oy = 1.0, 0.0, 0.0
        self.ancho, self.alto = 800.0, alto or 520.0
        self.modo = "mover"
        self.seleccion: Seleccion = None
        self.origen_transicion: Optional[str] = None
        self.resaltados: set[str] = set()
        self.resaltadas: set[tuple[str, str]] = set()
        self.color_resaltado = T.acento
        self.atenuados: set[str] = set()
        self.etiquetas_extra: dict[str, str] = {}

        self._arrastrando: Optional[str] = None
        self._ultimo: Optional[tuple[float, float]] = None
        self._ajustado = False
        self._movido = False
        self._aristas: list[Arista] = []

        self.canvas = cv.Canvas(shapes=[], expand=True, on_resize=self._al_redimensionar, resize_interval=60)
        self.detector = ft.GestureDetector(
            content=self.canvas,
            expand=True,
            drag_interval=16,
            on_tap_down=self._al_tocar,
            on_pan_start=self._al_iniciar_arrastre,
            on_pan_update=self._al_arrastrar,
            on_pan_end=self._al_terminar_arrastre,
            on_scroll=self._al_desplazar_rueda,
            mouse_cursor=ft.MouseCursor.BASIC,
        )
        self.control = ft.Container(
            self.detector,
            bgcolor=T.lienzo,
            border_radius=RADIO_UI,
            border=ft.Border.all(1, T.borde),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            expand=alto is None,
            height=alto,
        )
        if self.a is not None:
            asegurar_posiciones(self.a)
        self.dibujar(actualizar=False)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def usar(self, automata: Optional[Automata], ajustar: bool = True) -> None:
        self.a = automata
        self.seleccion = None
        self.origen_transicion = None
        self.resaltados, self.resaltadas = set(), set()
        if self.a is not None:
            asegurar_posiciones(self.a)
        if ajustar:
            self.ajustar(actualizar=False)
        self.dibujar()

    def cambiar_modo(self, modo: str) -> None:
        self.modo = modo
        self.origen_transicion = None
        self.detector.mouse_cursor = {
            "mover": ft.MouseCursor.BASIC, "estado": ft.MouseCursor.PRECISE,
            "transicion": ft.MouseCursor.CLICK, "eliminar": ft.MouseCursor.FORBIDDEN,
        }.get(modo, ft.MouseCursor.BASIC)
        refrescar(self.detector)
        self.dibujar()

    def resaltar(self, estados: Iterable[str] = (), aristas_: Iterable[tuple[str, str]] = (),
                 color: Optional[str] = None, atenuados: Iterable[str] = ()) -> None:
        self.resaltados = set(estados)
        self.resaltadas = set(aristas_)
        self.color_resaltado = color or T.acento
        self.atenuados = set(atenuados)
        self.dibujar()

    def seleccionar(self, sel: Seleccion) -> None:
        self.seleccion = sel
        self.dibujar()
        if self.al_seleccionar:
            self.al_seleccionar(sel)

    def ajustar(self, actualizar: bool = True) -> None:
        """Encuadra todo el autómata en el área visible."""
        if self.a is None or not self.a.posiciones:
            self.zoom, self.ox, self.oy = 1.0, 40.0, 40.0
        else:
            x0, y0, x1, y1 = caja(self.a.posiciones)
            z = min(self.ancho / max(x1 - x0, 1), self.alto / max(y1 - y0, 1))
            self.zoom = max(0.35, min(z, 1.6))
            self.ox = (self.ancho - (x1 - x0) * self.zoom) / 2 - x0 * self.zoom
            self.oy = (self.alto - (y1 - y0) * self.zoom) / 2 - y0 * self.zoom
        if actualizar:
            self.dibujar()

    def acercar(self, factor: float) -> None:
        self._zoom_en(self.ancho / 2, self.alto / 2, factor)

    # ------------------------------------------------------------------
    # Coordenadas
    # ------------------------------------------------------------------
    def _pantalla(self, p: tuple[float, float]) -> tuple[float, float]:
        return p[0] * self.zoom + self.ox, p[1] * self.zoom + self.oy

    def _mundo(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.ox) / self.zoom, (y - self.oy) / self.zoom

    def _zoom_en(self, sx: float, sy: float, factor: float) -> None:
        nuevo = max(0.25, min(self.zoom * factor, 3.5))
        wx, wy = self._mundo(sx, sy)
        self.zoom = nuevo
        self.ox, self.oy = sx - wx * nuevo, sy - wy * nuevo
        self.dibujar()

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _al_redimensionar(self, e: cv.CanvasResizeEvent) -> None:
        self.ancho, self.alto = float(e.width), float(e.height)
        if not self._ajustado:
            self._ajustado = True
            self.ajustar()
        else:
            self.dibujar()

    def _pos(self, e) -> tuple[float, float]:
        p = e.local_position
        return (p.x, p.y) if p is not None else (0.0, 0.0)

    def _arista_en(self, wx: float, wy: float) -> Optional[Arista]:
        for ar in reversed(self._aristas):
            if ar.contiene_etiqueta(wx, wy):
                return ar
        cercana = min(self._aristas, key=lambda ar: ar.distancia(wx, wy), default=None)
        if cercana is not None and cercana.distancia(wx, wy) <= 7:
            return cercana
        return None

    def _al_tocar(self, e: ft.TapEvent) -> None:
        if self.a is None:
            return
        wx, wy = self._mundo(*self._pos(e))
        q = estado_en(self.a.posiciones, wx, wy)
        ar = None if q else self._arista_en(wx, wy)
        objetivo: Seleccion = ("estado", q) if q else (("arista", (ar.origen, ar.destino)) if ar else None)

        if not self.editable or self.modo == "mover":
            self.seleccionar(objetivo)
            return
        if self.modo == "estado":
            if q:
                self.seleccionar(objetivo)
                return
            self._antes()
            nuevo = self.a.agregar_estado(posicion=(round(wx), round(wy)))
            self.seleccion = ("estado", nuevo)
            self._cambio()
            if self.al_seleccionar:
                self.al_seleccionar(self.seleccion)
            return
        if self.modo == "transicion":
            if not q:
                self.origen_transicion = None
                self.dibujar()
                return
            if self.origen_transicion is None:
                self.origen_transicion = q
                self.dibujar()
                return
            origen, self.origen_transicion = self.origen_transicion, None
            self.dibujar()
            if self.al_nueva_transicion:
                self.al_nueva_transicion(origen, q)
            return
        if self.modo == "eliminar" and objetivo and self.al_eliminar:
            self.al_eliminar(objetivo)

    def _al_iniciar_arrastre(self, e: ft.DragStartEvent) -> None:
        self._ultimo = self._pos(e)
        self._movido = False
        self._arrastrando = None
        if self.a is not None and self.modo in ("mover", "estado"):
            self._arrastrando = estado_en(self.a.posiciones, *self._mundo(*self._ultimo))

    def _al_arrastrar(self, e: ft.DragUpdateEvent) -> None:
        x, y = self._pos(e)
        if self._ultimo is None:
            self._ultimo = (x, y)
            return
        dx, dy = x - self._ultimo[0], y - self._ultimo[1]
        self._ultimo = (x, y)
        if self._arrastrando and self.a is not None:
            if not self._movido and self.al_antes_de_cambiar:
                self.al_antes_de_cambiar()
            self._movido = True
            px, py = self.a.posiciones[self._arrastrando]
            self.a.posiciones[self._arrastrando] = (px + dx / self.zoom, py + dy / self.zoom)
        else:
            self.ox += dx
            self.oy += dy
        self.dibujar()

    def _al_terminar_arrastre(self, e) -> None:
        if self._arrastrando and self.a is not None:
            px, py = self.a.posiciones[self._arrastrando]
            self.a.posiciones[self._arrastrando] = (round(px), round(py))
            if self._movido and self.al_cambiar:
                self.al_cambiar()
        self._arrastrando = None
        self._ultimo = None

    def _al_desplazar_rueda(self, e: ft.ScrollEvent) -> None:
        dy = e.scroll_delta.y if e.scroll_delta is not None else 0
        if dy:
            self._zoom_en(*self._pos(e), math.pow(1.0015, -dy))

    def _antes(self) -> None:
        if self.al_antes_de_cambiar:
            self.al_antes_de_cambiar()

    def _cambio(self) -> None:
        self.dibujar()
        if self.al_cambiar:
            self.al_cambiar()

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def dibujar(self, actualizar: bool = True) -> None:
        formas: list[cv.Shape] = []
        if self.mostrar_rejilla:
            formas.extend(self._rejilla())
        if self.a is None:
            formas.append(cv.Text(self.ancho / 2, self.alto / 2, "No hay un autómata seleccionado",
                                  style=ft.TextStyle(size=14, color=T.texto_3, font_family=FUENTE),
                                  alignment=ft.Alignment.CENTER))
        else:
            asegurar_posiciones(self.a)
            self._aristas = aristas(self.a.posiciones, self.a.agrupar_aristas(), mostrar_simbolo)
            for ar in self._aristas:
                formas.extend(self._forma_arista(ar))
            if self.a.inicial in self.a.posiciones:
                formas.extend(self._flecha_inicial(self.a.posiciones[self.a.inicial]))
            for q in self.a.estados:
                formas.extend(self._forma_estado(q))
            if not self.a.estados and self.editable:
                formas.append(cv.Text(self.ancho / 2, self.alto / 2,
                                      "Elija la herramienta «Estado» y haga clic en el lienzo",
                                      style=ft.TextStyle(size=14, color=T.texto_3, font_family=FUENTE),
                                      alignment=ft.Alignment.CENTER))
        self.canvas.shapes = formas
        if actualizar:
            refrescar(self.canvas)

    def _rejilla(self) -> list[cv.Shape]:
        paso = 40 * self.zoom
        while paso < 18:
            paso *= 2
        pintura = ft.Paint(color=T.rejilla, stroke_width=1)
        formas: list[cv.Shape] = []
        x = self.ox % paso
        while x < self.ancho:
            formas.append(cv.Line(x, 0, x, self.alto, paint=pintura))
            x += paso
        y = self.oy % paso
        while y < self.alto:
            formas.append(cv.Line(0, y, self.ancho, y, paint=pintura))
            y += paso
        return formas

    def _pintura_linea(self, color: str, ancho: float, discontinua: bool = False) -> ft.Paint:
        return ft.Paint(color=color, stroke_width=ancho * max(self.zoom, 0.6), style=ft.PaintingStyle.STROKE,
                        stroke_cap=ft.StrokeCap.ROUND,
                        stroke_dash_pattern=[6 * self.zoom, 5 * self.zoom] if discontinua else None)

    def _forma_arista(self, ar: Arista) -> list[cv.Shape]:
        clave = (ar.origen, ar.destino)
        simbolos = self.a.agrupar_aristas().get(clave, []) if self.a else []
        solo_lambda = bool(simbolos) and all(s == LAMBDA for s in simbolos)
        seleccionada = self.seleccion == ("arista", clave)
        if clave in self.resaltadas:
            color, ancho = self.color_resaltado, 3.0
        elif seleccionada:
            color, ancho = T.primario, 2.6
        elif solo_lambda:
            color, ancho = T.lambda_, 1.8
        else:
            color, ancho = T.transicion, 1.7
        if self.atenuados and (ar.origen in self.atenuados or ar.destino in self.atenuados):
            color = alfa(color, 0.3)
        P = self._pantalla
        ini, fin = P(ar.inicio), P(ar.fin)
        elementos: list = [cv.Path.MoveTo(*ini)]
        if ar.tipo == "recta":
            elementos.append(cv.Path.LineTo(*fin))
        elif ar.tipo == "curva":
            c = P(ar.control1)
            elementos.append(cv.Path.QuadraticTo(c[0], c[1], fin[0], fin[1]))
        else:
            c1, c2 = P(ar.control1), P(ar.control2)
            elementos.append(cv.Path.CubicTo(c1[0], c1[1], c2[0], c2[1], fin[0], fin[1]))
        formas: list[cv.Shape] = [cv.Path(elementos, paint=self._pintura_linea(color, ancho, solo_lambda))]
        punta = [P(p) for p in ar.punta]
        formas.append(cv.Path([cv.Path.MoveTo(*punta[0]), cv.Path.LineTo(*punta[1]), cv.Path.LineTo(*punta[2]),
                               cv.Path.Close()], paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL)))
        # Etiqueta con fondo para que se lea sobre las líneas.
        ex, ey = P(ar.pos_etiqueta)
        tam = 12.5 * max(self.zoom, 0.7)
        ancho_txt = max(14.0, 7.6 * len(ar.etiqueta)) * max(self.zoom, 0.7)
        fondo = T.primario_suave if seleccionada else T.lienzo
        formas.append(cv.Rect(ex - ancho_txt / 2 - 5, ey - tam * 0.85, ancho_txt + 10, tam * 1.7,
                              border_radius=6 * self.zoom, paint=ft.Paint(color=fondo, style=ft.PaintingStyle.FILL)))
        formas.append(cv.Text(ex, ey, ar.etiqueta, alignment=ft.Alignment.CENTER,
                              style=ft.TextStyle(size=tam, color=color if color != T.transicion else T.texto,
                                                 font_family=FUENTE_MONO, weight=ft.FontWeight.W_600)))
        return formas

    def _flecha_inicial(self, p: tuple[float, float]) -> list[cv.Shape]:
        x, y = self._pantalla(p)
        r = RADIO * self.zoom
        largo = 36 * self.zoom
        punta = 10 * self.zoom
        color = T.texto_2
        return [
            cv.Line(x - r - largo, y, x - r - 2, y, paint=self._pintura_linea(color, 2)),
            cv.Path([cv.Path.MoveTo(x - r, y), cv.Path.LineTo(x - r - punta, y - punta * 0.55),
                     cv.Path.LineTo(x - r - punta, y + punta * 0.55), cv.Path.Close()],
                    paint=ft.Paint(color=color, style=ft.PaintingStyle.FILL)),
        ]

    def _forma_estado(self, q: str) -> list[cv.Shape]:
        x, y = self._pantalla(self.a.posiciones[q])
        r = RADIO * self.zoom
        seleccionado = self.seleccion == ("estado", q) or self.origen_transicion == q
        resaltado = q in self.resaltados
        atenuado = q in self.atenuados and not resaltado
        borde = self.color_resaltado if resaltado else (T.primario if seleccionado else T.estado_borde)
        relleno = alfa(self.color_resaltado, 0.22) if resaltado else T.estado
        if atenuado:
            borde, relleno = alfa(borde, 0.35), alfa(T.estado, 0.5)
        formas: list[cv.Shape] = []
        if seleccionado or resaltado:
            formas.append(cv.Circle(x, y, r + 8 * self.zoom,
                                    paint=ft.Paint(color=alfa(borde, 0.18), style=ft.PaintingStyle.FILL)))
        formas.append(cv.Circle(x, y, r, paint=ft.Paint(color=T.lienzo, style=ft.PaintingStyle.FILL)))
        formas.append(cv.Circle(x, y, r, paint=ft.Paint(color=relleno, style=ft.PaintingStyle.FILL)))
        formas.append(cv.Circle(x, y, r, paint=ft.Paint(color=borde, style=ft.PaintingStyle.STROKE,
                                                       stroke_width=(3 if resaltado else 2) * max(self.zoom, 0.6))))
        if q in self.a.aceptacion:
            formas.append(cv.Circle(x, y, r - 5 * self.zoom,
                                    paint=ft.Paint(color=borde, style=ft.PaintingStyle.STROKE,
                                                   stroke_width=1.6 * max(self.zoom, 0.6))))
        etiqueta = q if len(q) <= 12 else q[:11] + "…"
        n = len(etiqueta)
        tam = (13 if n <= 4 else 11 if n <= 6 else 9 if n <= 8 else 7.4) * self.zoom
        formas.append(cv.Text(x, y, etiqueta, alignment=ft.Alignment.CENTER,
                              style=ft.TextStyle(size=tam, color=T.estado_texto if not atenuado else T.texto_3,
                                                 font_family=FUENTE_MONO, weight=ft.FontWeight.W_700)))
        extra = self.etiquetas_extra.get(q)
        if extra:
            formas.append(cv.Text(x, y + r + 12 * self.zoom, extra, alignment=ft.Alignment.CENTER,
                                  style=ft.TextStyle(size=10.5 * max(self.zoom, 0.8), color=T.texto_2,
                                                     font_family=FUENTE_MONO)))
        return formas
