"""Operación 2 de la Práctica 1: Σ*, Σ⁺, Σⁿ y operaciones entre lenguajes."""

from __future__ import annotations

import flet as ft

from core import lenguajes as L
from ui.componentes.comunes import (aviso, boton, campo, chip, metrica, panel_cadenas, pestanas, refrescar,
                                    tarjeta, texto, titulo_pagina)
from ui.estado import Estado
from ui.tema import FUENTE_MONO, T

OPERACIONES = [("kleene", "Σ*  Kleene"), ("positiva", "Σ⁺  positiva"), ("potencia", "Σⁿ  potencia")]
OPS_LENGUAJES = [
    ("concatenacion", "L₁·L₂"), ("union", "L₁ ∪ L₂"), ("interseccion", "L₁ ∩ L₂"),
    ("diferencia", "L₁ − L₂"), ("potencia", "L₁ⁿ"), ("reflexion", "L₁ᴿ"),
]


class PaginaLenguajes:
    def __init__(self, estado: Estado):
        self.estado = estado
        estado.contexto_ia = self._contexto_ia
        r = estado.recuperar
        self.op = r("leng.op", "kleene")
        self.alfabeto = campo("Alfabeto Σ", r("leng.alfabeto", "a, b"), "Símbolos separados por comas o espacios",
                              al_cambiar=self._al_cambiar_parametros, expand=True)
        self.longitud = ft.Slider(min=0, max=20, divisions=20, value=r("leng.n", 3), label="{value}",
                                  on_change=self._al_cambiar_parametros, active_color=T.primario, expand=True)
        self.etiqueta_n = texto("", 15, mono=True, peso=ft.FontWeight.W_700)
        self.selector = ft.Container()
        self.prevision = ft.Column(spacing=8)
        self.resultado = ft.Column([texto("Pulse «Generar» para ver el conjunto.", 13, T.texto_3)], spacing=14)
        self.cadenas: list[str] = []
        self.descripcion = ""

        self.l1 = campo("L₁", r("leng.l1", "a, ab, λ"), "Cadenas separadas por comas; λ es la vacía",
                        al_cambiar=lambda e: self.estado.recordar("leng.l1", e.control.value), expand=True)
        self.l2 = campo("L₂", r("leng.l2", "b, ab"), "Cadenas separadas por comas",
                        al_cambiar=lambda e: self.estado.recordar("leng.l2", e.control.value), expand=True)
        self.exp = campo("n", r("leng.exp", "2"), "Exponente para L₁ⁿ", width=110,
                         al_cambiar=lambda e: self.estado.recordar("leng.exp", e.control.value))
        self.resultado_ops = ft.Column(spacing=12)
        self.cadenas_ops: list[str] = []
        self.titulo_ops = ""
        self._actualizar_prevision()

    # ------------------------------------------------------------------
    # Cerraduras
    # ------------------------------------------------------------------
    def _n(self) -> int:
        return int(self.longitud.value or 0)

    def _al_cambiar_parametros(self, e=None) -> None:
        self.estado.recordar("leng.alfabeto", self.alfabeto.value)
        self.estado.recordar("leng.n", self._n())
        self._actualizar_prevision()
        refrescar(self.prevision, self.etiqueta_n)

    def _cambiar_op(self, op: str) -> None:
        self.op = op
        self.estado.recordar("leng.op", op)
        self._actualizar_prevision()
        refrescar(self.selector, self.prevision)

    def _total(self, k: int, n: int) -> int:
        if self.op == "potencia":
            return L.contar_potencia(k, n)
        return L.contar_cerradura(k, n, positiva=self.op == "positiva")

    def _actualizar_prevision(self) -> None:
        n = self._n()
        self.etiqueta_n.value = f"n = {n}"
        self.selector.content = pestanas(OPERACIONES, self.op, self._cambiar_op)
        try:
            sigma = L.parsear_alfabeto(self.alfabeto.value or "")
        except ValueError as exc:
            self.prevision.controls = [aviso(str(exc), "error")]
            return
        k = len(sigma)
        total = self._total(k, n)
        formula = {
            "kleene": f"Σ_(i=0..{n}) {k}^i",
            "positiva": f"Σ_(i=1..{n}) {k}^i",
            "potencia": f"{k}^{n}",
        }[self.op]
        excede = total > L.LIMITE_CADENAS
        color = T.error if excede else (T.aviso if total > L.LIMITE_CADENAS * 0.5 else T.exito)
        self.prevision.controls = [
            ft.Row(
                [texto(f"|Σ| = {k}", 13, T.texto_2, mono=True),
                 texto("·", 13, T.texto_3),
                 texto(f"{formula} = {total:,} cadenas", 13, T.texto, mono=True),
                 chip("excede el límite" if excede else "dentro del límite", color)],
                spacing=10, wrap=True,
            ),
            ft.ProgressBar(value=min(total / L.LIMITE_CADENAS, 1.0), color=color, bgcolor=T.superficie_3,
                           bar_height=6, border_radius=3),
            texto(f"Límite: {L.LIMITE_CADENAS:,} cadenas. El número crece como |Σ|ⁿ.", 11.5, T.texto_3),
        ]

    def generar(self, e=None) -> None:
        n = self._n()
        try:
            sigma = L.parsear_alfabeto(self.alfabeto.value or "")
            if self.op == "kleene":
                self.cadenas = L.cerradura_kleene(sigma, n)
                nombre = "Σ*"
            elif self.op == "positiva":
                self.cadenas = L.cerradura_positiva(sigma, n)
                nombre = "Σ⁺"
            else:
                self.cadenas = L.potencia_alfabeto(sigma, n)
                nombre = f"Σ^{n}"
        except L.LimiteExcedido as exc:
            self.cadenas = []
            self.resultado.controls = [aviso(str(exc), "error", ft.Icons.BLOCK)]
            self.estado.notificar("Operación rechazada: supera las 200 000 cadenas.", "error")
            refrescar(self.resultado)
            return
        except ValueError as exc:
            self.estado.notificar(str(exc), "error")
            return
        self.descripcion = f"{nombre} con Σ = {{{', '.join(sigma)}}} y longitud ≤ {n}"
        self.estado.registrar(f"Generado {nombre} (n = {n}): {len(self.cadenas):,} cadenas", ft.Icons.ALL_INCLUSIVE)
        tiene_lambda = "" in self.cadenas
        self.resultado.controls = [
            ft.Row(
                [texto(self.descripcion, 14, peso=ft.FontWeight.W_600),
                 chip(f"{len(self.cadenas):,} cadenas", T.primario),
                 chip("contiene λ" if tiene_lambda else "sin λ", T.lambda_ if tiene_lambda else T.texto_3)],
                spacing=10, wrap=True,
            ),
            panel_cadenas(self.cadenas, vacio="El conjunto es vacío (Σ⁺ no contiene cadenas de longitud 0)."),
        ]
        refrescar(self.resultado)

    async def exportar(self, e=None) -> None:
        if not self.descripcion:
            self.estado.notificar("Primero genere un conjunto de cadenas.", "aviso")
            return
        contenido = L.reporte_texto(self.descripcion, self.cadenas)
        await self.estado.guardar(f"lenguaje_{self.op}_n{self._n()}.txt", contenido, ["txt"])

    # ------------------------------------------------------------------
    # Operaciones entre lenguajes
    # ------------------------------------------------------------------
    def operar(self, op: str) -> None:
        l1 = L.parsear_lenguaje(self.l1.value or "")
        l2 = L.parsear_lenguaje(self.l2.value or "")
        try:
            if op == "concatenacion":
                res = L.concatenacion(l1, l2)
            elif op == "union":
                res = L.union(l1, l2)
            elif op == "interseccion":
                res = L.interseccion(l1, l2)
            elif op == "diferencia":
                res = L.diferencia(l1, l2)
            elif op == "potencia":
                res = L.potencia_lenguaje(l1, int(self.exp.value or "0"))
            else:
                res = L.reflexion_lenguaje(l1)
        except (ValueError, L.LimiteExcedido) as exc:
            self.estado.notificar(str(exc), "error")
            return
        etiqueta = dict(OPS_LENGUAJES)[op].replace("ⁿ", f"^{self.exp.value}")
        self.cadenas_ops = res
        self.titulo_ops = etiqueta
        self.estado.registrar(f"Operación {etiqueta}: {len(res)} cadenas", ft.Icons.MERGE_TYPE)
        self.resultado_ops.controls = [
            ft.Row([texto(etiqueta, 15, mono=True, peso=ft.FontWeight.W_700),
                    chip(f"{len(res)} cadena{'s' if len(res) != 1 else ''}", T.primario)], spacing=10),
            panel_cadenas(res, agrupar=False, vacio="∅ — el lenguaje resultante es vacío."),
        ]
        refrescar(self.resultado_ops)

    async def exportar_ops(self, e=None) -> None:
        if not self.titulo_ops:
            self.estado.notificar("Primero realice una operación.", "aviso")
            return
        contenido = L.reporte_texto(self.titulo_ops, self.cadenas_ops,
                                    {"L1": self.l1.value, "L2": self.l2.value})
        await self.estado.guardar("operacion_lenguajes.txt", contenido, ["txt"])

    # ------------------------------------------------------------------
    def _contexto_ia(self) -> str:
        partes = [f"Operación elegida: {self.op}; alfabeto «{self.alfabeto.value}»; longitud máxima {self._n()}."]
        if self.descripcion:
            partes.append(f"Último resultado: {self.descripcion}, {len(self.cadenas)} cadenas.")
        if self.titulo_ops:
            partes.append(f"Operación entre lenguajes: {self.titulo_ops} con L1 = {{{self.l1.value}}} y "
                          f"L2 = {{{self.l2.value}}}: {len(self.cadenas_ops)} cadenas.")
        return "\n".join(partes)

    def vista(self) -> ft.Control:
        cerraduras = tarjeta(
            ft.Column(
                [
                    self.selector,
                    ft.Row([self.alfabeto], spacing=12),
                    ft.Row([texto("Longitud máxima", 13, T.texto_2), self.longitud, self.etiqueta_n],
                           spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self.prevision,
                    ft.Row([boton("Generar", self.generar, ft.Icons.AUTO_AWESOME),
                            boton("Exportar .txt", self.exportar, ft.Icons.DOWNLOAD_ROUNDED, "secundario")],
                           spacing=12),
                ],
                spacing=16,
            ),
            "Cerraduras del alfabeto", ft.Icons.ALL_INCLUSIVE,
            subtitulo="Σ* = Σ⁰ ∪ Σ¹ ∪ … y Σ⁺ = Σ¹ ∪ Σ² ∪ …, truncadas a la longitud elegida",
        )
        operaciones = tarjeta(
            ft.Column(
                [
                    ft.Row([self.l1, self.l2, self.exp], spacing=12, wrap=False),
                    ft.Row([boton(et, lambda e, o=o: self.operar(o), tipo="secundario")
                            for o, et in OPS_LENGUAJES]
                           + [boton("Exportar", self.exportar_ops, ft.Icons.DOWNLOAD_ROUNDED, "fantasma")],
                           spacing=8, wrap=True),
                    self.resultado_ops,
                ],
                spacing=14,
            ),
            "Operaciones entre lenguajes finitos", ft.Icons.MERGE_TYPE,
            subtitulo="Concatenación, unión, intersección, diferencia, potencia y reflexión",
        )
        teoria = ft.ResponsiveRow(
            [
                ft.Container(metrica("Σ⁰", "{λ}", ft.Icons.EXPOSURE_ZERO, T.lambda_,
                                     "la única cadena de longitud 0"), col={"xs": 12, "md": 4}),
                ft.Container(metrica("Σ* − Σ⁺", "{λ}", ft.Icons.REMOVE_CIRCLE_OUTLINE, T.acento,
                                     "Σ⁺ = Σ* − {λ}"), col={"xs": 12, "md": 4}),
                ft.Container(metrica("|Σⁿ|", "|Σ|ⁿ", ft.Icons.TRENDING_UP, T.aviso,
                                     "crecimiento exponencial"), col={"xs": 12, "md": 4}),
            ],
            spacing=16, run_spacing=16,
        )
        return ft.Column(
            [
                titulo_pagina("Operaciones sobre lenguajes",
                              "Genere Σ*, Σ⁺ y Σⁿ, y combine lenguajes finitos.",
                              ft.Icons.ALL_INCLUSIVE_ROUNDED, "Práctica 1"),
                teoria,
                cerraduras,
                tarjeta(self.resultado, "Resultado", ft.Icons.LIST_ALT),
                operaciones,
            ],
            spacing=22,
        )


def construir(estado: Estado) -> ft.Control:
    return PaginaLenguajes(estado).vista()
