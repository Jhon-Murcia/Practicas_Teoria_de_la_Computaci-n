"""Piezas visuales reutilizables: tarjetas, encabezados, botones y chips."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Optional, Sequence

import flet as ft

from core.lenguajes import mostrar
from ui.tema import FUENTE_MONO, RADIO, RADIO_CHICO, T, alfa


def refrescar(*controles: ft.Control) -> None:
    """Actualiza los controles que ya están en la página e ignora los demás."""
    for c in controles:
        try:
            c.update()
        except RuntimeError:
            pass


def texto(valor: str, tam: float = 14, color: Optional[str] = None, peso=None, mono: bool = False,
          **kw) -> ft.Text:
    return ft.Text(valor, size=tam, color=color or T.texto, weight=peso,
                   font_family=FUENTE_MONO if mono else None, **kw)


def titulo_pagina(titulo: str, subtitulo: str, icono: Any, practica: str = "") -> ft.Control:
    """Encabezado de cada pantalla con icono, título, descripción y etiqueta."""
    etiqueta = []
    if practica:
        etiqueta.append(chip(practica, T.primario))
    return ft.Row(
        [
            ft.Container(
                ft.Icon(icono, color=T.primario, size=26),
                width=52, height=52, border_radius=16, alignment=ft.Alignment.CENTER,
                bgcolor=T.primario_suave,
                border=ft.Border.all(1, alfa(T.primario, 0.35)),
            ),
            ft.Column(
                [
                    ft.Row([texto(titulo, 24, peso=ft.FontWeight.W_700), *etiqueta], spacing=12,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    texto(subtitulo, 13.5, T.texto_2),
                ],
                spacing=2, expand=True,
            ),
        ],
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def tarjeta(contenido: ft.Control, titulo: str = "", icono: Any = None, acciones: Sequence[ft.Control] = (),
            padding: int = 20, expand: Any = None, subtitulo: str = "", **kw) -> ft.Container:
    """Panel con borde suave, encabezado opcional y acciones a la derecha."""
    partes: list[ft.Control] = []
    if titulo:
        cabecera: list[ft.Control] = []
        if icono:
            cabecera.append(ft.Icon(icono, size=18, color=T.primario))
        cabecera.append(
            ft.Column([texto(titulo, 15, peso=ft.FontWeight.W_600),
                       *( [texto(subtitulo, 12, T.texto_3)] if subtitulo else [])],
                      spacing=0, expand=True)
        )
        cabecera.extend(acciones)
        partes.append(ft.Row(cabecera, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER))
    partes.append(contenido)
    return ft.Container(
        ft.Column(partes, spacing=14, expand=True if expand else False),
        padding=padding,
        bgcolor=T.superficie,
        border_radius=RADIO,
        border=ft.Border.all(1, T.borde),
        expand=expand,
        **kw,
    )


def boton(etiqueta: str, al_pulsar: Callable | None = None, icono: Any = None, tipo: str = "primario",
          tooltip: str | None = None, disabled: bool = False, **kw) -> ft.Control:
    """Botones con los tres estilos del sistema: primario, secundario y fantasma."""
    forma = ft.RoundedRectangleBorder(radius=RADIO_CHICO)
    relleno = ft.Padding.symmetric(horizontal=18, vertical=14)
    if tipo == "primario":
        estilo = ft.ButtonStyle(bgcolor=T.primario, color="#FFFFFF", shape=forma, padding=relleno,
                                elevation=0, icon_color="#FFFFFF")
        return ft.FilledButton(etiqueta, icon=icono, on_click=al_pulsar, style=estilo, tooltip=tooltip,
                               disabled=disabled, **kw)
    if tipo == "secundario":
        estilo = ft.ButtonStyle(color=T.texto, shape=forma, padding=relleno, icon_color=T.primario,
                                side=ft.BorderSide(1, T.borde), bgcolor=T.superficie_2)
        return ft.OutlinedButton(etiqueta, icon=icono, on_click=al_pulsar, style=estilo, tooltip=tooltip,
                                 disabled=disabled, **kw)
    estilo = ft.ButtonStyle(color=T.texto_2, shape=forma, padding=relleno, icon_color=T.texto_2)
    return ft.TextButton(etiqueta, icon=icono, on_click=al_pulsar, style=estilo, tooltip=tooltip,
                         disabled=disabled, **kw)


def boton_icono(icono: Any, al_pulsar: Callable | None = None, tooltip: str = "", color: str | None = None,
                **kw) -> ft.IconButton:
    return ft.IconButton(icono, on_click=al_pulsar, tooltip=tooltip, icon_color=color or T.texto_2,
                         icon_size=20, hover_color=T.superficie_3, **kw)


def chip(etiqueta: str, color: str | None = None, icono: Any = None, mono: bool = False) -> ft.Container:
    color = color or T.texto_2
    contenido: list[ft.Control] = []
    if icono:
        contenido.append(ft.Icon(icono, size=13, color=color))
    contenido.append(ft.Text(etiqueta, size=11.5, color=color, weight=ft.FontWeight.W_600,
                             font_family=FUENTE_MONO if mono else None))
    return ft.Container(
        ft.Row(contenido, spacing=5, tight=True),
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=20,
        bgcolor=alfa(color, 0.12),
        border=ft.Border.all(1, alfa(color, 0.3)),
    )


def campo(etiqueta: str, valor: str = "", ayuda: str = "", al_cambiar: Callable | None = None,
          al_enviar: Callable | None = None, mono: bool = True, **kw) -> ft.TextField:
    return ft.TextField(
        label=etiqueta,
        value=valor,
        helper=ayuda or None,
        on_change=al_cambiar,
        on_submit=al_enviar,
        border_radius=RADIO_CHICO,
        border_color=T.borde,
        focused_border_color=T.primario,
        bgcolor=T.superficie_2,
        filled=True,
        fill_color=T.superficie_2,
        text_style=ft.TextStyle(font_family=FUENTE_MONO if mono else None, size=15, color=T.texto),
        label_style=ft.TextStyle(color=T.texto_2),
        helper_style=ft.TextStyle(color=T.texto_3, size=11.5),
        cursor_color=T.primario,
        **kw,
    )


def metrica(etiqueta: str, valor: str, icono: Any, color: str | None = None, detalle: str = "",
            expand: Any = 1) -> ft.Container:
    """Tarjeta de indicador numérico para los paneles."""
    color = color or T.primario
    return ft.Container(
        ft.Row(
            [
                ft.Container(ft.Icon(icono, color=color, size=20), width=42, height=42, border_radius=12,
                             bgcolor=alfa(color, 0.14), alignment=ft.Alignment.CENTER),
                ft.Column(
                    [texto(etiqueta, 12, T.texto_3),
                     texto(valor, 20, peso=ft.FontWeight.W_700, mono=True),
                     *([texto(detalle, 11, T.texto_3)] if detalle else [])],
                    spacing=0, expand=True,
                ),
            ],
            spacing=14,
        ),
        padding=16,
        bgcolor=T.superficie,
        border_radius=RADIO,
        border=ft.Border.all(1, T.borde),
        expand=expand,
    )


def aviso(mensaje: str, tipo: str = "info", icono: Any = None) -> ft.Container:
    color = {"info": T.acento, "exito": T.exito, "error": T.error, "aviso": T.aviso}.get(tipo, T.acento)
    icono = icono or {"info": ft.Icons.INFO_OUTLINE, "exito": ft.Icons.CHECK_CIRCLE_OUTLINE,
                      "error": ft.Icons.ERROR_OUTLINE, "aviso": ft.Icons.WARNING_AMBER_ROUNDED}[tipo]
    return ft.Container(
        ft.Row([ft.Icon(icono, color=color, size=18), ft.Text(mensaje, color=T.texto, size=13, expand=True)],
               spacing=10, vertical_alignment=ft.CrossAxisAlignment.START),
        padding=ft.Padding.symmetric(horizontal=14, vertical=12),
        border_radius=RADIO_CHICO,
        bgcolor=alfa(color, 0.1),
        border=ft.Border.all(1, alfa(color, 0.35)),
    )


def chip_cadena(w: str, resaltar: bool = False) -> ft.Container:
    """Chip monoespaciado para una cadena; ``λ`` se distingue en color."""
    vacia = w == ""
    color = T.lambda_ if vacia else (T.primario if resaltar else T.texto)
    return ft.Container(
        ft.Text(mostrar(w), font_family=FUENTE_MONO, size=13, color=color, selectable=True,
                weight=ft.FontWeight.W_600 if vacia else None),
        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        border_radius=8,
        bgcolor=alfa(T.lambda_, 0.12) if vacia else T.superficie_3,
        border=ft.Border.all(1, alfa(T.lambda_, 0.4) if vacia else T.borde),
    )


MAX_CHIPS = 1500


def panel_cadenas(cadenas: Sequence[str], agrupar: bool = True, vacio: str = "Sin resultados") -> ft.Control:
    """Muestra un conjunto de cadenas agrupado por longitud.

    Para no saturar la interfaz se dibujan como máximo :data:`MAX_CHIPS`
    chips; el resto se obtiene completo con la exportación.
    """
    if not cadenas:
        return ft.Container(texto(vacio, 13, T.texto_3, italic=True), padding=10)
    visibles = list(cadenas[:MAX_CHIPS])
    bloques: list[ft.Control] = []
    if len(cadenas) > MAX_CHIPS:
        bloques.append(aviso(f"Se muestran {MAX_CHIPS:,} de {len(cadenas):,} cadenas. "
                             "Exporte el resultado para obtener la lista completa.", "aviso"))
    if agrupar:
        grupos: dict[int, list[str]] = {}
        for w in visibles:
            grupos.setdefault(len(w), []).append(w)
        for n, ws in sorted(grupos.items()):
            bloques.append(
                ft.Column(
                    [
                        ft.Row([chip(f"|w| = {n}", T.acento, mono=True),
                                texto(f"{len(ws):,} cadena{'s' if len(ws) != 1 else ''}", 12, T.texto_3)],
                               spacing=10),
                        ft.Row([chip_cadena(w) for w in ws], wrap=True, spacing=6, run_spacing=6),
                    ],
                    spacing=8,
                )
            )
    else:
        bloques.append(ft.Row([chip_cadena(w) for w in visibles], wrap=True, spacing=6, run_spacing=6))
    return ft.Column(bloques, spacing=16)


def separador() -> ft.Divider:
    return ft.Divider(height=1, thickness=1, color=T.borde)


def pestanas(opciones: Iterable[tuple[str, str]], seleccion: str, al_cambiar: Callable[[str], None]) -> ft.Container:
    """Selector segmentado propio con el estilo del sistema."""
    items = []
    for clave, etiqueta in opciones:
        activa = clave == seleccion
        items.append(
            ft.Container(
                ft.Text(etiqueta, size=13, weight=ft.FontWeight.W_600,
                        color="#FFFFFF" if activa else T.texto_2),
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                border_radius=8,
                bgcolor=T.primario if activa else None,
                on_click=lambda e, c=clave: al_cambiar(c),
                animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            )
        )
    return ft.Container(ft.Row(items, spacing=4, tight=True, wrap=True), padding=4, border_radius=12,
                        bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde))
