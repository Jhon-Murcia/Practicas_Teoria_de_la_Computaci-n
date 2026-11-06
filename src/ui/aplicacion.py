"""Estructura principal: menú lateral, barra superior y área de contenido.

Cada módulo del software se registra en :data:`MODULOS` con la función que
construye su pantalla. Las prácticas posteriores sólo añaden entradas a esta
lista, sin modificar el resto de la estructura.
"""

from __future__ import annotations

import platform
from dataclasses import dataclass
from typing import Any, Callable

import flet as ft

from ui.estado import Estado
from ui.tema import CLARO, FUENTES, OSCURO, RADIO_CHICO, T, alfa, tema_flet
from ui.paginas import (archivos, ayuda, cadenas, conversiones, editor, inicio, lenguajes, minimizacion,
                        simulacion)

NOMBRE_APP = "AutómataLab"
VERSION = "3.0 · Práctica 3"


@dataclass(frozen=True)
class Modulo:
    clave: str
    etiqueta: str
    icono: Any
    icono_activo: Any
    grupo: str
    construir: Callable[[Estado], ft.Control]
    descripcion: str = ""
    desplazable: bool = True


MODULOS: list[Modulo] = [
    Modulo("inicio", "Inicio", ft.Icons.SPACE_DASHBOARD_OUTLINED, ft.Icons.SPACE_DASHBOARD_ROUNDED,
           "General", inicio.construir, "Panel principal"),
    Modulo("cadenas", "Cadenas", ft.Icons.TEXT_FIELDS_OUTLINED, ft.Icons.TEXT_FIELDS_ROUNDED,
           "Lenguajes", cadenas.construir, "Prefijos, sufijos y subcadenas"),
    Modulo("lenguajes", "Lenguajes", ft.Icons.ALL_INCLUSIVE_OUTLINED, ft.Icons.ALL_INCLUSIVE_ROUNDED,
           "Lenguajes", lenguajes.construir, "Σ*, Σ⁺ y operaciones entre lenguajes"),
    Modulo("editor", "Editor", ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Icons.ACCOUNT_TREE_ROUNDED,
           "Autómatas", editor.construir, "Crear y editar AFD, AFND y AFND-λ", desplazable=False),
    Modulo("simulacion", "Simulación", ft.Icons.PLAY_CIRCLE_OUTLINE, ft.Icons.PLAY_CIRCLE_ROUNDED,
           "Autómatas", simulacion.construir, "Validar cadenas paso a paso"),
    Modulo("archivos", "Archivos", ft.Icons.FOLDER_OPEN_OUTLINED, ft.Icons.FOLDER_OPEN_ROUNDED,
           "Autómatas", archivos.construir, "Importar y exportar .jff, .json y .xml"),
    Modulo("conversiones", "Conversiones", ft.Icons.TRANSFORM_OUTLINED, ft.Icons.TRANSFORM_ROUNDED,
           "Algoritmos", conversiones.construir, "λ-clausura, eliminación de λ, subconjuntos y AFD → ER"),
    Modulo("minimizacion", "Minimización", ft.Icons.COMPRESS_OUTLINED, ft.Icons.COMPRESS_ROUNDED,
           "Algoritmos", minimizacion.construir, "AFD mínimo y equivalencia de autómatas"),
    Modulo("ayuda", "Ayuda", ft.Icons.HELP_OUTLINE_ROUNDED, ft.Icons.HELP_ROUNDED,
           "Soporte", ayuda.construir, "Guía y convenciones"),
]


class Aplicacion:
    def __init__(self, page: ft.Page):
        self.page = page
        self.estado = Estado(page=page)
        self.estado.navegar = self.ir
        self.estado.modulos = MODULOS
        self.actual = "inicio"
        self.compacto = False
        self.contenido = ft.AnimatedSwitcher(
            content=ft.Container(),
            duration=ft.Duration(milliseconds=220),
            reverse_duration=ft.Duration(milliseconds=120),
            transition=ft.AnimatedSwitcherTransition.FADE,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            expand=True,
        )
        page.on_resize = self._al_redimensionar
        page.on_keyboard_event = self._al_teclear

    # ------------------------------------------------------------------
    def iniciar(self) -> None:
        p = self.page
        p.title = f"{NOMBRE_APP} · Teoría de la Computación"
        p.fonts = FUENTES
        p.padding = 0
        p.spacing = 0
        self.estado.ancho = float(p.width or 1440)
        self.compacto = self.estado.ancho < 1100
        self._aplicar_tema()
        self.estado.registrar("Sesión iniciada", ft.Icons.PLAY_CIRCLE_OUTLINE)
        self.reconstruir()

    def _aplicar_tema(self) -> None:
        p = self.page
        p.theme_mode = ft.ThemeMode.DARK if T.oscuro else ft.ThemeMode.LIGHT
        p.theme = tema_flet()
        p.dark_theme = tema_flet()
        p.bgcolor = T.fondo

    def alternar_tema(self, e=None) -> None:
        T.usar(CLARO if T.oscuro else OSCURO)
        self._aplicar_tema()
        self.reconstruir()

    @staticmethod
    def _clase(ancho: float) -> int:
        """Rangos de ancho en los que cambia la distribución de la interfaz."""
        return 0 if ancho < 1100 else (1 if ancho < 1380 else 2)

    def _al_redimensionar(self, e) -> None:
        ancho = float(getattr(e, "width", None) or self.page.width or 1440)
        anterior = self._clase(self.estado.ancho)
        self.estado.ancho = ancho
        self.compacto = ancho < 1100
        if self._clase(ancho) != anterior:
            self.reconstruir()

    def _al_teclear(self, e) -> None:
        if self.estado.teclado is not None:
            self.estado.teclado(e)

    # ------------------------------------------------------------------
    def ir(self, clave: str) -> None:
        if not any(m.clave == clave for m in MODULOS):
            return
        self.actual = clave
        self.reconstruir()

    def _modulo(self) -> Modulo:
        return next(m for m in MODULOS if m.clave == self.actual)

    def reconstruir(self) -> None:
        modulo = self._modulo()
        self.estado.teclado = None
        try:
            vista = modulo.construir(self.estado)
        except Exception as exc:  # una pantalla rota no debe tumbar la aplicación
            vista = ft.Text(f"No se pudo construir la pantalla: {exc}", color=T.error)
        if modulo.desplazable:
            cuerpo = ft.Column([vista], scroll=ft.ScrollMode.AUTO, expand=True)
        else:
            cuerpo = vista
        self.contenido.content = ft.Container(cuerpo, key=f"{modulo.clave}-{T.nombre}",
                                              padding=ft.Padding.only(left=32, right=32, top=24, bottom=24),
                                              expand=True)
        self.page.controls.clear()
        self.page.add(
            ft.Row(
                [
                    self._menu_lateral(),
                    ft.Container(width=1, bgcolor=T.borde),
                    ft.Column([self._barra_superior(modulo), self.contenido], spacing=0, expand=True),
                ],
                spacing=0,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
        self.page.update()

    # ------------------------------------------------------------------
    def _logo(self) -> ft.Control:
        insignia = ft.Container(
            ft.Text("Σ*", size=18, weight=ft.FontWeight.W_800, color="#FFFFFF"),
            width=40, height=40, border_radius=12, alignment=ft.Alignment.CENTER,
            gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                       colors=[T.primario, T.acento]),
        )
        if self.compacto:
            return ft.Container(insignia, padding=ft.Padding.only(top=20, bottom=16),
                                alignment=ft.Alignment.CENTER)
        return ft.Container(
            ft.Row(
                [insignia,
                 ft.Column([ft.Text(NOMBRE_APP, size=17, weight=ft.FontWeight.W_800, color=T.texto),
                            ft.Text("Teoría de la Computación", size=11, color=T.texto_3)], spacing=0)],
                spacing=12,
            ),
            padding=ft.Padding.only(left=20, right=20, top=22, bottom=18),
        )

    def _item_menu(self, m: Modulo) -> ft.Control:
        activo = m.clave == self.actual
        color = T.primario if activo else T.texto_2
        icono = ft.Icon(m.icono_activo if activo else m.icono, color=color, size=20)
        if self.compacto:
            contenido = ft.Container(icono, alignment=ft.Alignment.CENTER, height=44)
        else:
            contenido = ft.Row(
                [icono, ft.Text(m.etiqueta, size=13.5, color=T.texto if activo else T.texto_2,
                                weight=ft.FontWeight.W_600 if activo else ft.FontWeight.W_500)],
                spacing=12,
            )

        def al_pasar(e: ft.Event, c=None):
            if not activo:
                e.control.bgcolor = T.superficie_3 if e.data in (True, "true") else None
                e.control.update()

        return ft.Container(
            contenido,
            padding=ft.Padding.symmetric(horizontal=14, vertical=11) if not self.compacto else 0,
            margin=ft.Margin.symmetric(horizontal=12, vertical=1),
            border_radius=RADIO_CHICO,
            bgcolor=T.primario_suave if activo else None,
            border=ft.Border.all(1, alfa(T.primario, 0.35)) if activo else ft.Border.all(1, "transparent"),
            on_click=lambda e, c=m.clave: self.ir(c),
            on_hover=al_pasar,
            tooltip=m.etiqueta if self.compacto else (m.descripcion or None),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

    def _menu_lateral(self) -> ft.Control:
        items: list[ft.Control] = []
        grupo_actual = None
        for m in MODULOS:
            if m.grupo != grupo_actual:
                grupo_actual = m.grupo
                if not self.compacto:
                    items.append(ft.Container(
                        ft.Text(m.grupo.upper(), size=10.5, color=T.texto_3, weight=ft.FontWeight.W_700),
                        padding=ft.Padding.only(left=26, top=14, bottom=6)))
                else:
                    items.append(ft.Container(height=10))
            items.append(self._item_menu(m))

        pie = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [ft.IconButton(ft.Icons.LIGHT_MODE_OUTLINED if T.oscuro else ft.Icons.DARK_MODE_OUTLINED,
                                       icon_color=T.texto_2, on_click=self.alternar_tema,
                                       tooltip="Cambiar entre tema oscuro y claro"),
                         *([] if self.compacto else
                           [ft.Text("Tema oscuro" if T.oscuro else "Tema claro", size=12, color=T.texto_3)])],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER if self.compacto else ft.MainAxisAlignment.START,
                    ),
                    *([] if self.compacto else
                      [ft.Text(f"v{VERSION} · Python {platform.python_version()}", size=10.5, color=T.texto_3)]),
                ],
                spacing=4,
            ),
            padding=ft.Padding.only(left=14, right=14, bottom=16, top=8),
        )
        return ft.Container(
            ft.Column(
                [self._logo(), ft.Column(items, spacing=2, scroll=ft.ScrollMode.AUTO, expand=True), pie],
                spacing=0,
                expand=True,
            ),
            width=76 if self.compacto else 248,
            bgcolor=T.superficie,
        )

    def _barra_superior(self, m: Modulo) -> ft.Control:
        return ft.Container(
            ft.Row(
                [
                    ft.Row([ft.Text(m.grupo, size=12.5, color=T.texto_3),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=T.texto_3),
                            ft.Text(m.etiqueta, size=12.5, color=T.texto, weight=ft.FontWeight.W_600)],
                           spacing=4, expand=True),
                    ft.Container(
                        ft.Row([ft.Icon(ft.Icons.SCHOOL_OUTLINED, size=15, color=T.acento),
                                ft.Text("IPN · ESCOM", size=12, color=T.texto_2)], spacing=6, tight=True),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=6), border_radius=20,
                        bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=32, vertical=14),
            bgcolor=T.fondo,
            border=ft.Border.only(bottom=ft.BorderSide(1, T.borde)),
        )


def main(page: ft.Page) -> None:
    Aplicacion(page).iniciar()
