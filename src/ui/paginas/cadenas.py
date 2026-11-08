"""Operación 1 de la Práctica 1: subcadenas, prefijos y sufijos."""

from __future__ import annotations

import flet as ft

from core import lenguajes as L
from ui.componentes.comunes import (aviso, boton, campo, chip, metrica, panel_cadenas, refrescar, tarjeta,
                                    texto, titulo_pagina)
from ui.estado import Estado
from ui.tema import FUENTE_MONO, T, alfa

MAX_LONGITUD = 400


def _escalera(w: str, modo: str) -> ft.Control:
    """Dibuja cada prefijo (o sufijo) resaltado dentro de la cadena completa."""
    filas = []
    n = len(w)
    rango = range(n + 1) if modo == "prefijos" else range(n, -1, -1)
    for i in rango:
        if modo == "prefijos":
            parte, resto_izq, resto_der = w[:i], "", w[i:]
        else:
            parte, resto_izq, resto_der = w[i:], w[:i], ""
        etiqueta = L.mostrar(parte)
        filas.append(
            ft.Row(
                [
                    ft.Container(ft.Text(f"{len(parte)}", size=11, color=T.texto_3, font_family=FUENTE_MONO),
                                 width=28),
                    ft.Text(
                        spans=[
                            ft.TextSpan(resto_izq, ft.TextStyle(color=T.texto_3, font_family=FUENTE_MONO)),
                            ft.TextSpan(etiqueta, ft.TextStyle(
                                color=T.lambda_ if parte == "" else T.primario, font_family=FUENTE_MONO,
                                weight=ft.FontWeight.W_700)),
                            ft.TextSpan(resto_der, ft.TextStyle(color=T.texto_3, font_family=FUENTE_MONO)),
                        ],
                        size=14, selectable=True,
                    ),
                ],
                spacing=6,
            )
        )
        if len(filas) >= 300:
            filas.append(texto(f"… {n + 1 - 300} más (exporte para verlos todos)", 12, T.texto_3))
            break
    return ft.Column(filas, spacing=4)


class PaginaCadenas:
    def __init__(self, estado: Estado):
        self.estado = estado
        estado.contexto_ia = self._contexto_ia
        self.entrada = campo("Cadena w", estado.recuperar("cadenas.w", "abba"),
                             "Escriba λ o deje vacío para la cadena vacía", al_cambiar=self._al_cambiar,
                             al_enviar=lambda e: self.calcular(registrar=True), expand=True,
                             max_length=MAX_LONGITUD)
        self.vista_resultados = ft.Column(spacing=18)
        self.calcular(registrar=False)

    # ------------------------------------------------------------------
    def _cadena(self) -> str:
        return L.normalizar(self.entrada.value or "")

    def _al_cambiar(self, e) -> None:
        self.estado.recordar("cadenas.w", self.entrada.value)
        self.calcular(registrar=False)
        refrescar(self.vista_resultados)

    def _usar(self, w: str) -> None:
        self.entrada.value = w
        self.estado.recordar("cadenas.w", w)
        refrescar(self.entrada)
        self.calcular(registrar=True)

    def calcular(self, registrar: bool = True) -> None:
        w = self._cadena()
        pre, suf, sub = L.prefijos(w), L.sufijos(w), L.subcadenas(w)
        n = len(w)
        cota = L.max_subcadenas_distintas(n)
        self.resultado = (w, pre, suf, sub)
        metricas = ft.ResponsiveRow(
            [
                ft.Container(metrica("Longitud |w|", f"{n}", ft.Icons.STRAIGHTEN, T.primario),
                             col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(metrica("Prefijos", f"{len(pre)}", ft.Icons.FIRST_PAGE, T.acento, "n + 1"),
                             col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(metrica("Sufijos", f"{len(suf)}", ft.Icons.LAST_PAGE, T.acento, "n + 1"),
                             col={"xs": 12, "sm": 6, "lg": 3}),
                ft.Container(metrica("Subcadenas distintas", f"{len(sub)} / {cota}", ft.Icons.DATA_ARRAY,
                                     T.aviso, "máximo n(n+1)/2 + 1"),
                             col={"xs": 12, "sm": 6, "lg": 3}),
            ],
            spacing=16, run_spacing=16,
        )
        resultados = ft.ResponsiveRow(
            [
                ft.Container(tarjeta(_escalera(w, "prefijos"), "Prefijos", ft.Icons.FIRST_PAGE,
                                     subtitulo="De λ a w; el resaltado es el prefijo"),
                             col={"xs": 12, "lg": 6}),
                ft.Container(tarjeta(_escalera(w, "sufijos"), "Sufijos", ft.Icons.LAST_PAGE,
                                     subtitulo="De λ a w; el resaltado es el sufijo"),
                             col={"xs": 12, "lg": 6}),
            ],
            spacing=16, run_spacing=16,
        )
        self.vista_resultados.controls = [
            metricas,
            resultados,
            tarjeta(panel_cadenas(sub), "Subcadenas", ft.Icons.DATA_ARRAY,
                    subtitulo="Agrupadas por longitud, sin repeticiones"),
        ]
        if registrar:
            self.estado.registrar(f"Prefijos, sufijos y subcadenas de {L.mostrar(w)}", ft.Icons.TEXT_FIELDS)
            refrescar(self.vista_resultados)

    async def exportar(self, e) -> None:
        w, pre, suf, sub = self.resultado
        contenido = "\n".join([
            L.reporte_texto("Prefijos", pre, {"Cadena": L.mostrar(w), "Longitud": len(w)}),
            L.reporte_texto("Sufijos", suf, {"Cadena": L.mostrar(w)}),
            L.reporte_texto("Subcadenas", sub, {"Cadena": L.mostrar(w),
                                                "Cota n(n+1)/2 + 1": L.max_subcadenas_distintas(len(w))}),
        ])
        nombre = f"cadenas_{w or 'lambda'}.txt"[:60]
        await self.estado.guardar(nombre, contenido, ["txt"])

    # ------------------------------------------------------------------
    def _contexto_ia(self) -> str:
        w, pre, suf, sub = self.resultado
        return (f"Cadena w = {L.mostrar(w)} (longitud {len(w)}). Prefijos: {len(pre)}; sufijos: {len(suf)}; "
                f"subcadenas distintas: {len(sub)} de un máximo de {L.max_subcadenas_distintas(len(w))}.")

    def vista(self) -> ft.Control:
        ejemplos = ft.Row(
            [texto("Ejemplos:", 12.5, T.texto_3)]
            + [ft.Container(chip(L.mostrar(w), T.acento, mono=True), on_click=lambda e, w=w: self._usar(w))
               for w in ("", "a", "abba", "aab", "01101", "abcde")],
            spacing=8, wrap=True,
        )
        convencion = aviso(
            "Convención: λ es prefijo y sufijo de toda cadena (w = λw = wλ), y w es prefijo y sufijo de sí "
            "misma. Una cadena de longitud n tiene n + 1 prefijos, n + 1 sufijos y a lo sumo n(n+1)/2 + 1 "
            "subcadenas distintas (contando λ).", "info")
        entrada = tarjeta(
            ft.Column(
                [
                    ft.Row(
                        [self.entrada,
                         boton("Calcular", lambda e: self.calcular(True), ft.Icons.PLAY_ARROW_ROUNDED),
                         boton("Exportar .txt", self.exportar, ft.Icons.DOWNLOAD_ROUNDED, "secundario")],
                        spacing=12, vertical_alignment=ft.CrossAxisAlignment.START, wrap=False,
                    ),
                    ejemplos,
                    convencion,
                ],
                spacing=14,
            ),
            "Cadena de entrada", ft.Icons.KEYBOARD_OUTLINED,
        )
        return ft.Column(
            [
                titulo_pagina("Operaciones sobre cadenas",
                              "Calcule todos los prefijos, sufijos y subcadenas de una cadena.",
                              ft.Icons.TEXT_FIELDS_ROUNDED, "Práctica 1"),
                entrada,
                self.vista_resultados,
            ],
            spacing=22,
        )


def construir(estado: Estado) -> ft.Control:
    return PaginaCadenas(estado).vista()
