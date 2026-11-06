"""Minimización de AFD y prueba de equivalencia entre dos autómatas."""

from __future__ import annotations

from typing import Optional

import flet as ft

from core import ejemplos
from core.automata import Automata
from algoritmos.equivalencia import comparar
from algoritmos.minimizacion import minimizar, renombrar_canonico, tabla_distinguibles
from algoritmos.subconjuntos import construir_afd
from ui.componentes.automatas import acciones_resultado, resumen_automata, selector_automata
from ui.componentes.comunes import aviso, boton, chip, pestanas, refrescar, tarjeta, texto, titulo_pagina
from ui.componentes.lienzo import Lienzo
from ui.componentes.reproductor import Reproductor, tabla_control
from ui.estado import Estado
from ui.tema import FUENTE_MONO, T, alfa


class PaginaMinimizacion:
    def __init__(self, estado: Estado):
        self.estado = estado
        if estado.actual is None:
            estado.agregar_automata(ejemplos.multiplos_de_tres())
        self.modo = estado.recuperar("min.modo", "minimizar")
        self.indice_b = estado.recuperar("min.b", 0)
        self.reproductor = Reproductor(estado)
        self.cabecera = ft.Container()
        self.cuerpo = ft.Column(spacing=16)
        self.minimo: Optional[Automata] = None
        self.ronda_tabla = 0
        self._construir()

    @property
    def a(self) -> Automata:
        return self.estado.actual

    def _cambiar_modo(self, modo: str) -> None:
        self.modo = modo
        self.estado.recordar("min.modo", modo)
        self._construir()
        refrescar(self.cabecera, self.cuerpo)

    def _cambiar_a(self, i: int) -> None:
        self.estado.seleccionar(i)
        self._construir()
        refrescar(self.cabecera, self.cuerpo)

    def _cambiar_b(self, i: int) -> None:
        self.indice_b = i
        self.estado.recordar("min.b", i)
        self._construir()
        refrescar(self.cabecera, self.cuerpo)

    # ------------------------------------------------------------------
    def _construir(self) -> None:
        selectores = [selector_automata(self.estado, self.estado.indice, self._cambiar_a,
                                        "Autómata" if self.modo == "minimizar" else "Autómata 1")]
        if self.modo == "equivalencia":
            if not 0 <= self.indice_b < len(self.estado.automatas):
                self.indice_b = 0
            selectores.append(selector_automata(self.estado, self.indice_b, self._cambiar_b, "Autómata 2"))
        self.cabecera.content = ft.Column([
            pestanas([("minimizar", "Minimizar AFD"), ("equivalencia", "Equivalencia de autómatas")], self.modo,
                     self._cambiar_modo),
            ft.Row(selectores, spacing=14, wrap=True),
        ], spacing=14)
        if self.modo == "minimizar":
            self._minimizar()
        else:
            self._equivalencia()

    # ------------------------------------------------------------------
    def _minimizar(self, convertir: bool = False) -> None:
        a = self.a
        if not a.es_determinista():
            if not convertir:
                q, s, motivo = a.conflictos_determinismo()[0]
                self.reproductor.cargar([])
                self.cuerpo.controls = [aviso(
                    f"«{a.nombre}» no es un AFD ({motivo}). La minimización se aplica a autómatas deterministas.",
                    "aviso"),
                    boton("Convertir a AFD por subconjuntos y minimizar", lambda e: self._convertir_y_minimizar(),
                          ft.Icons.TRANSFORM)]
                return
            a = construir_afd(a)[0]
        try:
            self.minimo, pasos, info = minimizar(a)
        except ValueError as exc:
            self.cuerpo.controls = [aviso(str(exc), "error")]
            return
        self.reproductor.cargar(pasos)
        self.estado.registrar(f"Minimizado «{a.nombre}»: {len(a.estados)} → {len(self.minimo.estados)} estados",
                              ft.Icons.COMPRESS)
        rondas, estados = tabla_distinguibles(a)
        self.ronda_tabla = len(rondas) - 1
        self._tabla_pares = (rondas, estados)
        self.panel_pares = ft.Container(self._pares())
        metricas = ft.Row([
            chip(f"{len(a.estados)} estados originales", T.texto_2),
            chip(f"{len(info['inaccesibles'])} inaccesibles", T.aviso),
            chip(f"{len(info['rondas'])} particiones", T.acento),
            chip(f"{len(self.minimo.estados)} en el AFD mínimo", T.exito),
        ], spacing=8, wrap=True)
        self.cuerpo.controls = [
            tarjeta(self.reproductor.vista(), "Refinamiento de particiones paso a paso", ft.Icons.TIMELINE),
            ft.ResponsiveRow([
                ft.Container(tarjeta(ft.Column([
                    metricas,
                    resumen_automata(self.minimo, "AFD mínimo:"),
                    ft.Row([boton("Renombrar como q0, q1, …", self._renombrar, ft.Icons.SORT_BY_ALPHA, "fantasma")]),
                    acciones_resultado(self.estado, lambda: self.minimo, f"{a.nombre} (mínimo)"),
                ], spacing=12), "Resultado", ft.Icons.CHECK_CIRCLE_OUTLINE), col={"xs": 12, "lg": 5}),
                ft.Container(tarjeta(self.panel_pares, "Método de la tabla de pares distinguibles",
                                     ft.Icons.GRID_4X4), col={"xs": 12, "lg": 7}),
            ], spacing=16, run_spacing=16),
        ]

    def _convertir_y_minimizar(self) -> None:
        self._minimizar(convertir=True)
        refrescar(self.cuerpo)

    def _renombrar(self, e=None) -> None:
        if self.minimo is not None:
            self.minimo = renombrar_canonico(self.minimo)
            self.estado.notificar("Estados renombrados en orden de recorrido en anchura.", "exito")

    def _pares(self) -> ft.Control:
        rondas, estados = self._tabla_pares
        marcados = rondas[self.ronda_tabla]
        filas = []
        for i, p in enumerate(estados[1:], start=1):
            celdas = [ft.Container(texto(p, 12, T.texto_2, mono=True, no_wrap=True), width=86)]
            for q in estados[:i]:
                ronda = marcados.get((q, p), marcados.get((p, q)))
                if ronda is None:
                    contenido, fondo = "", T.superficie_2
                else:
                    contenido, fondo = ("×" if ronda == 0 else f"×{ronda}"), alfa(T.error if ronda == 0 else T.aviso, 0.25)
                celdas.append(ft.Container(texto(contenido, 12, T.texto, mono=True), width=44, height=30,
                                           alignment=ft.Alignment.CENTER, bgcolor=fondo, border_radius=4,
                                           tooltip=f"{{{q}, {p}}}"))
            filas.append(ft.Row(celdas, spacing=3))
        filas.append(ft.Row([ft.Container(width=86)] + [
            ft.Container(texto(q, 11, T.texto_3, mono=True, no_wrap=True), width=44) for q in estados[:-1]], spacing=3))
        sin_marcar = [f"{{{p},{q}}}" for i, p in enumerate(estados) for q in estados[i + 1:]
                      if (p, q) not in rondas[-1] and (q, p) not in rondas[-1]]

        def mover(d):
            self.ronda_tabla = max(0, min(self.ronda_tabla + d, len(rondas) - 1))
            self.panel_pares.content = self._pares()
            refrescar(self.panel_pares)

        return ft.Column([
            ft.Row([ft.IconButton(ft.Icons.CHEVRON_LEFT, on_click=lambda e: mover(-1)),
                    chip(f"ronda {self.ronda_tabla} de {len(rondas) - 1}", T.primario, mono=True),
                    ft.IconButton(ft.Icons.CHEVRON_RIGHT, on_click=lambda e: mover(1))], spacing=6),
            texto("× : distinguidos por F (ronda 0). ×n : marcados en la ronda n porque con algún símbolo van a un "
                  "par ya marcado. Los pares sin marcar al final son equivalentes.", 12, T.texto_3),
            ft.Row([ft.Column(filas, spacing=3)], scroll=ft.ScrollMode.AUTO),
            texto("Pares equivalentes: " + (", ".join(sin_marcar) if sin_marcar else "ninguno (ya era mínimo)"),
                  12.5, T.texto_2, mono=True),
        ], spacing=10)

    # ------------------------------------------------------------------
    def _equivalencia(self) -> None:
        a1 = self.a
        a2 = self.estado.automatas[self.indice_b]
        comp = comparar(a1, a2)
        self.estado.registrar(f"Equivalencia «{a1.nombre}» vs «{a2.nombre}»: "
                              f"{'equivalentes' if comp.equivalentes else 'distintos'}", ft.Icons.COMPARE_ARROWS)
        color = T.exito if comp.equivalentes else T.error
        veredicto = ft.Container(ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE if comp.equivalentes else ft.Icons.CANCEL, color=color, size=30),
            ft.Column([texto("EQUIVALENTES" if comp.equivalentes else "NO EQUIVALENTES", 16, color,
                             peso=ft.FontWeight.W_800),
                       texto(comp.motivo, 12.5, T.texto_2)], spacing=2, expand=True)], spacing=12),
            padding=16, border_radius=12, bgcolor=alfa(color, 0.1), border=ft.Border.all(1, alfa(color, 0.4)))
        detalle: list[ft.Control] = []
        if comp.equivalentes:
            filas = [["Mínimo 1", "Mínimo 2"]] + [[p, q] for p, q in comp.correspondencia.items()]
            detalle.append(tarjeta(tabla_control(filas), "Correspondencia de estados (isomorfismo)",
                                   ft.Icons.COMPARE_ARROWS))
        elif comp.contraejemplo is not None:
            w = comp.contraejemplo or "λ"
            quien = a1.nombre if comp.acepta1 else a2.nombre
            detalle.append(aviso(f"Contraejemplo más corto: «{w}». Lo acepta «{quien}» y el otro no.", "error",
                                 ft.Icons.REPORT_GMAILERRORRED))
        l1 = Lienzo(comp.minimo1, alto=320)
        l2 = Lienzo(comp.minimo2, alto=320)
        self.cuerpo.controls = [
            veredicto,
            texto("Método: ambos se convierten en AFD completos, se minimizan y se comparan los mínimos salvo el nombre "
                  "de los estados.", 12.5, T.texto_3),
            ft.ResponsiveRow([
                ft.Container(tarjeta(ft.Column([resumen_automata(comp.minimo1), l1.control], spacing=10),
                                     f"Mínimo de «{a1.nombre}»", ft.Icons.ACCOUNT_TREE_OUTLINED), col={"xs": 12, "lg": 6}),
                ft.Container(tarjeta(ft.Column([resumen_automata(comp.minimo2), l2.control], spacing=10),
                                     f"Mínimo de «{a2.nombre}»", ft.Icons.ACCOUNT_TREE_OUTLINED), col={"xs": 12, "lg": 6}),
            ], spacing=16, run_spacing=16),
            *detalle,
        ]

    # ------------------------------------------------------------------
    def vista(self) -> ft.Control:
        return ft.Column([
            titulo_pagina("Minimización y equivalencia",
                          "AFD mínimo por refinamiento de particiones y prueba de equivalencia de autómatas.",
                          ft.Icons.COMPRESS_ROUNDED, "Práctica 3"),
            tarjeta(self.cabecera),
            self.cuerpo,
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def construir(estado: Estado) -> ft.Control:
    return PaginaMinimizacion(estado).vista()
