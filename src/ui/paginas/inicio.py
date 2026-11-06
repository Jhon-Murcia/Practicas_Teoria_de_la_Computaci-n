"""Panel principal: presentación, indicadores, accesos rápidos y actividad."""

from __future__ import annotations

import flet as ft

from ui.componentes.comunes import metrica, tarjeta, texto
from ui.estado import Estado
from ui.tema import RADIO, T, alfa


def _hero() -> ft.Control:
    return ft.Container(
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Container(
                            ft.Text("IPN · ESCOM · Teoría de la Computación", size=11.5,
                                    color="#FFFFFF", weight=ft.FontWeight.W_600),
                            padding=ft.Padding.symmetric(horizontal=12, vertical=5), border_radius=20,
                            bgcolor="#FFFFFF,0.16",
                        ),
                        ft.Text("AutómataLab", size=34, weight=ft.FontWeight.W_800, color="#FFFFFF"),
                        ft.Text(
                            "Software interactivo para estudiar cadenas, lenguajes y autómatas finitos: "
                            "crear, visualizar, simular y transformar, paso a paso.",
                            size=14.5, color="#FFFFFF,0.88",
                        ),
                    ],
                    spacing=10, expand=True,
                ),
                ft.Container(
                    ft.Text("Σ*", size=72, weight=ft.FontWeight.W_800, color="#FFFFFF,0.22"),
                    padding=ft.Padding.only(right=12),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding.symmetric(horizontal=32, vertical=28),
        border_radius=RADIO + 4,
        gradient=ft.LinearGradient(begin=ft.Alignment.TOP_LEFT, end=ft.Alignment.BOTTOM_RIGHT,
                                   colors=[T.primario, "#5B6CFF", T.acento]),
    )


def _acceso(estado: Estado, modulo) -> ft.Control:
    def al_pasar(e):
        e.control.border = ft.Border.all(1, T.primario if e.data in (True, "true") else T.borde)
        e.control.update()

    return ft.Container(
        ft.Column(
            [
                ft.Container(ft.Icon(modulo.icono_activo, color=T.primario, size=22), width=44, height=44,
                             border_radius=12, bgcolor=T.primario_suave, alignment=ft.Alignment.CENTER),
                texto(modulo.etiqueta, 15, peso=ft.FontWeight.W_600),
                texto(modulo.descripcion, 12.5, T.texto_3),
            ],
            spacing=10,
        ),
        padding=18,
        border_radius=RADIO,
        bgcolor=T.superficie,
        border=ft.Border.all(1, T.borde),
        on_click=lambda e: estado.navegar(modulo.clave),
        on_hover=al_pasar,
        col={"xs": 12, "sm": 6, "md": 4, "xl": 3},
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
    )


def metricas_extra(estado: Estado) -> list[ft.Control]:
    """Indicadores que dependen de los módulos de cada práctica."""
    a = estado.actual
    return [metrica("Autómatas en la sesión", f"{len(estado.automatas)}", ft.Icons.ACCOUNT_TREE_OUTLINED, T.exito,
                    f"actual: {a.nombre[:24]} ({a.tipo})" if a else "ninguno seleccionado")]


def construir(estado: Estado) -> ft.Control:
    modulos = [m for m in estado.modulos if m.clave != "inicio"]
    extras = metricas_extra(estado)

    metricas = ft.ResponsiveRow(
        [
            ft.Container(metrica("Operaciones en la sesión", f"{estado.operaciones}", ft.Icons.BOLT,
                                 T.primario), col={"xs": 12, "sm": 6, "lg": 3}),
            *[ft.Container(m, col={"xs": 12, "sm": 6, "lg": 3}) for m in extras],
            ft.Container(metrica("Módulos disponibles", f"{len(modulos)}", ft.Icons.WIDGETS_OUTLINED,
                                 T.acento), col={"xs": 12, "sm": 6, "lg": 3}),
            ft.Container(metrica("Último archivo", estado.ultimo_archivo.split("/")[-1].split("\\")[-1][:22],
                                 ft.Icons.DESCRIPTION_OUTLINED, T.aviso), col={"xs": 12, "sm": 6, "lg": 3}),
        ],
        spacing=16, run_spacing=16,
    )

    if estado.actividad:
        filas = [
            ft.Row(
                [
                    ft.Container(ft.Icon(a.icono, size=16, color=a.color or T.primario), width=32, height=32,
                                 border_radius=10, bgcolor=alfa(a.color or T.primario, 0.12),
                                 alignment=ft.Alignment.CENTER),
                    texto(a.texto, 13, expand=True),
                    texto(a.hora, 11.5, T.texto_3, mono=True),
                ],
                spacing=12,
            )
            for a in estado.actividad[:8]
        ]
        actividad = ft.Column(filas, spacing=10)
    else:
        actividad = texto("Aún no hay actividad en esta sesión.", 13, T.texto_3)

    return ft.Column(
        [
            _hero(),
            metricas,
            texto("Accesos rápidos", 16, peso=ft.FontWeight.W_700),
            ft.ResponsiveRow([_acceso(estado, m) for m in modulos], spacing=16, run_spacing=16),
            tarjeta(actividad, "Actividad reciente", ft.Icons.HISTORY),
        ],
        spacing=22,
    )
