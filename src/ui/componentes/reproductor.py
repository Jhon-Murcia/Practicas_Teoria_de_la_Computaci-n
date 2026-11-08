"""Reproductor de pasos de un algoritmo.

Muestra, para el paso actual, la foto del autómata con los estados y aristas
resaltados, el título, la explicación y la tabla que el algoritmo registró.
Permite avanzar, retroceder, ir al inicio o al final y reproducir.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from algoritmos.pasos import Paso
from ui.componentes.comunes import boton_icono, chip, refrescar, texto
from ui.componentes.lienzo import Lienzo
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO, T, alfa

COLOR_TIPO = {"info": "acento", "nuevo": "primario", "exito": "exito", "aviso": "aviso"}


def tabla_control(filas: list[list[str]], resaltar_ultima: bool = False, max_filas: int = 120) -> ft.Control:
    """Tabla compacta con encabezado; desplazable en horizontal."""
    if not filas:
        return ft.Container()
    columnas = len(filas[0])
    anchos = [max(54, min(260, 8 * max(len(str(f[c])) if c < len(f) else 0 for f in filas) + 18))
              for c in range(columnas)]
    controles = []
    for i, fila in enumerate(filas[:max_filas + 1]):
        cabecera = i == 0
        ultima = resaltar_ultima and i == len(filas) - 1 and i > 0
        controles.append(ft.Container(
            ft.Row([ft.Text(str(v), width=w, size=12, font_family=FUENTE_MONO, selectable=True,
                            color=T.texto_3 if cabecera else T.texto,
                            weight=ft.FontWeight.W_700 if cabecera else None)
                    for v, w in zip(fila, anchos)], spacing=6),
            padding=ft.Padding.symmetric(horizontal=8, vertical=5), border_radius=6,
            bgcolor=T.superficie_2 if cabecera else (T.primario_suave if ultima else None),
        ))
    if len(filas) > max_filas + 1:
        controles.append(texto(f"… {len(filas) - max_filas - 1} filas más", 12, T.texto_3))
    return ft.Row([ft.Column(controles, spacing=1)], scroll=ft.ScrollMode.AUTO)


class Reproductor:
    def __init__(self, estado: Estado, alto: float = 440, vacio: str = "Ejecute el algoritmo para ver sus pasos."):
        self.estado = estado
        self.pasos: list[Paso] = []
        self.i = 0
        self.reproduciendo = False
        self.vacio = vacio
        self._alto = alto
        self.lienzo = Lienzo(None, editable=False, alto=alto)
        self.cabecera = ft.Container()
        self.detalle = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
        self.controles = ft.Container()
        self._estados_previos: Optional[frozenset[str]] = None
        self._mostrar()

    def descripcion(self) -> str:
        """El paso actual en texto, para el asistente de IA."""
        if not self.pasos:
            return ""
        paso = self.pasos[self.i]
        texto = f"Paso {self.i + 1} de {len(self.pasos)}: {paso.titulo}"
        if paso.detalle:
            texto += f"\n{paso.detalle}"
        if paso.tabla:
            texto += "\nTabla: " + " | ".join("; ".join(map(str, f)) for f in paso.tabla[:15])
        return texto

    def cargar(self, pasos: list[Paso], ir_al_final: bool = False) -> None:
        self.pasos = pasos
        self.i = len(pasos) - 1 if ir_al_final else 0
        self._estados_previos = None
        self._mostrar()

    def ir(self, i: int) -> None:
        if not self.pasos:
            return
        self.i = max(0, min(i, len(self.pasos) - 1))
        self._mostrar()

    async def _reproducir(self) -> None:
        if self.i >= len(self.pasos) - 1:
            self.i = 0
        self.reproduciendo = True
        self._mostrar()
        while self.reproduciendo and self.i < len(self.pasos) - 1:
            await asyncio.sleep(1.3)
            if not self.reproduciendo:
                break
            self.i += 1
            self._mostrar()
        self.reproduciendo = False
        self._mostrar()

    def alternar(self, e=None) -> None:
        if self.reproduciendo:
            self.reproduciendo = False
            self._mostrar()
        elif self.pasos:
            self.estado.page.run_task(self._reproducir)

    def _mostrar(self) -> None:
        n = len(self.pasos)
        self.controles.content = ft.Row([
            ft.Container(ft.Row([
                boton_icono(ft.Icons.FIRST_PAGE, lambda e: self.ir(0), "Primer paso"),
                boton_icono(ft.Icons.CHEVRON_LEFT, lambda e: self.ir(self.i - 1), "Paso anterior"),
                boton_icono(ft.Icons.PAUSE if self.reproduciendo else ft.Icons.SLOW_MOTION_VIDEO, self.alternar,
                            "Reproducir los pasos", T.primario),
                boton_icono(ft.Icons.CHEVRON_RIGHT, lambda e: self.ir(self.i + 1), "Paso siguiente"),
                boton_icono(ft.Icons.LAST_PAGE, lambda e: self.ir(n - 1), "Último paso"),
            ], spacing=0, tight=True), border_radius=11, bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde)),
            chip(f"paso {self.i + 1 if n else 0} / {n}", T.primario, mono=True),
            ft.TextButton("Explicar este paso", icon=ft.Icons.AUTO_AWESOME, disabled=not n,
                          tooltip="Pedir al asistente de IA que explique el paso actual",
                          on_click=lambda e: self.estado.preguntar_ia(
                              "Explícame este paso del algoritmo y por qué ocurre.")),
            ft.Container(ft.ProgressBar(value=(self.i + 1) / n if n else 0, color=T.primario,
                                        bgcolor=T.superficie_3, bar_height=6, border_radius=3), expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        if not self.pasos:
            self.cabecera.content = texto(self.vacio, 13, T.texto_3)
            self.detalle.controls = []
            self.lienzo.mensaje_vacio = self.vacio
            self.lienzo.usar(None)
            refrescar(self.controles, self.cabecera, self.detalle)
            return
        paso = self.pasos[self.i]
        color = getattr(T, COLOR_TIPO.get(paso.tipo, "acento"))
        self.cabecera.content = ft.Row([
            ft.Container(width=4, height=40, border_radius=2, bgcolor=color),
            ft.Column([texto(f"PASO {self.i + 1}", 10.5, color, peso=ft.FontWeight.W_700),
                       texto(paso.titulo, 15, peso=ft.FontWeight.W_700, selectable=True)], spacing=2, expand=True),
        ], spacing=12)
        contenido: list[ft.Control] = []
        if paso.detalle:
            contenido.append(ft.Container(
                ft.Text(paso.detalle, size=12.5, font_family=FUENTE_MONO, color=T.texto_2, selectable=True),
                padding=12, border_radius=10, bgcolor=alfa(color, 0.07), border=ft.Border.all(1, alfa(color, 0.25))))
        if paso.tabla:
            contenido.append(tabla_control(paso.tabla, resaltar_ultima=paso.tipo == "nuevo"))
        self.detalle.controls = contenido
        if paso.automata is None:
            self.lienzo.mensaje_vacio = "Este paso no tiene diagrama: vea la explicación a la derecha."
            self._estados_previos = None
            self.lienzo.usar(None, ajustar=False)
        else:
            nuevos = frozenset(paso.automata.estados)
            cambia = nuevos != self._estados_previos
            self._estados_previos = nuevos
            self.lienzo.a = paso.automata
            self.lienzo.etiquetas_extra = dict(paso.etiquetas)
            if cambia:
                self.lienzo.ajustar(actualizar=False)
            self.lienzo.resaltar(paso.estados, paso.aristas, color)
        refrescar(self.controles, self.cabecera, self.detalle)

    def vista(self, ancho_panel: int = 430) -> ft.Control:
        panel = ft.Container(
            ft.Column([self.cabecera, self.detalle], spacing=12, expand=True),
            width=ancho_panel, height=self._alto, padding=16, bgcolor=T.superficie,
            border_radius=RADIO, border=ft.Border.all(1, T.borde),
        )
        return ft.Column([
            self.controles,
            ft.Row([ft.Container(self.lienzo.control, expand=True), panel], spacing=14,
                   vertical_alignment=ft.CrossAxisAlignment.START),
        ], spacing=12)
