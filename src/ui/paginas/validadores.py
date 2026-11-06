"""Validadores construidos con expresiones regulares y autómatas (Práctica 4)."""

from __future__ import annotations

import re

import flet as ft

from core.simulacion import simular
from algoritmos import validadores as V
from algoritmos.minimizacion import estados_muertos
from ui.componentes.automatas import acciones_resultado
from ui.componentes.comunes import aviso, campo, chip, pestanas, refrescar, tarjeta, texto, titulo_pagina
from ui.componentes.lienzo import Lienzo
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO_CHICO, T, alfa

ICONOS = {"correo": ft.Icons.ALTERNATE_EMAIL, "telefono": ft.Icons.PHONE_OUTLINED,
          "fecha": ft.Icons.CALENDAR_MONTH_OUTLINED, "url": ft.Icons.LINK}


def bloque_codigo(etiqueta: str, valor: str, color: str) -> ft.Control:
    return ft.Column([
        texto(etiqueta, 11.5, T.texto_3, peso=ft.FontWeight.W_700),
        ft.Container(ft.Text(valor, font_family=FUENTE_MONO, size=12.5, color=color, selectable=True),
                     padding=12, border_radius=RADIO_CHICO, bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde)),
    ], spacing=6)


class PaginaValidadores:
    def __init__(self, estado: Estado):
        self.estado = estado
        self.clave = estado.recuperar("val.clave", "correo")
        self.selector = ft.Container()
        self.cuerpo = ft.Column(spacing=16)
        self.resultado = ft.Container()
        self.entrada = campo("Texto a validar", "", al_cambiar=lambda e: self.validar())
        self._construir()

    def _cambiar(self, clave: str) -> None:
        self.clave = clave
        self.estado.recordar("val.clave", clave)
        self._construir()
        refrescar(self.selector, self.cuerpo)

    def _construir(self) -> None:
        self.selector.content = pestanas([(k, v.nombre) for k, v in V.VALIDADORES.items()], self.clave, self._cambiar)
        v = V.VALIDADORES[self.clave]
        res = V.construir(self.clave)
        self.entrada.value = self.estado.recuperar(f"val.texto.{self.clave}", v.validos[0])
        self.entrada.prefix_icon = ICONOS[self.clave]
        etapas = ft.Row([chip(f"{e.titulo}: {len(e.automata.estados)} estados",
                              T.exito if i == 3 else (T.primario if i == 2 else T.texto_2))
                         for i, e in enumerate(res.etapas)], spacing=8, wrap=True)
        # Para que el diagrama se lea, se omite el estado de error (no acepta nada y recibe
        # todas las transiciones inválidas); el autómata que valida sí lo conserva.
        dibujo = res.minimo.copia()
        muertos = [q for q in estados_muertos(dibujo) if q != dibujo.inicial]
        for q in muertos:
            dibujo.eliminar_estado(q)
        lienzo = Lienzo(dibujo, alto=360)
        self.cuerpo.controls = [
            tarjeta(ft.Column([
                texto(v.descripcion, 13, T.texto_2),
                ft.Row([ft.Container(self.entrada, expand=True)]),
                self.resultado,
                texto("Pruebe: " + "  ·  ".join(v.validos[:3]) + "   (inválidos: " + "  ·  ".join(v.invalidos[:3]) + ")",
                      12, T.texto_3, selectable=True),
            ], spacing=12), v.nombre, ICONOS[self.clave]),
            ft.ResponsiveRow([
                ft.Container(tarjeta(ft.Column([
                    bloque_codigo("CLASES DECLARADAS", v.clases, T.texto),
                    bloque_codigo("EXPRESIÓN EN LA NOTACIÓN DEL CURSO", v.expresion, T.primario),
                    bloque_codigo("TRADUCCIÓN A re (escrita a mano)", v.python, T.acento),
                    bloque_codigo("TRADUCCIÓN AUTOMÁTICA DEL ÁRBOL", v.python_automatico(), T.texto_2),
                ], spacing=12), "Expresión regular", ft.Icons.FUNCTIONS), col={"xs": 12, "xl": 6}),
                ft.Container(tarjeta(ft.Column([
                    etapas,
                    texto(f"AFD antes de minimizar: {len(res.afd.estados)} estados · después: "
                          f"{len(res.minimo.estados)} estados · |Σ| = {len(res.minimo.alfabeto)}", 13, T.texto,
                          peso=ft.FontWeight.W_600),
                    lienzo.control,
                    texto("En el diagrama se omite el estado de error; las transiciones que faltan van a él.",
                          11.5, T.texto_3) if muertos else ft.Container(),
                    acciones_resultado(self.estado, lambda: res.minimo, f"Validador {v.nombre} (AFD mínimo)"),
                ], spacing=12), "AFD equivalente (mínimo)", ft.Icons.ACCOUNT_TREE_OUTLINED), col={"xs": 12, "xl": 6}),
            ], spacing=16, run_spacing=16),
            tarjeta(ft.Column([
                texto("Norma consultada: " + v.norma, 12.5, T.texto_2, selectable=True),
                texto("Casos que quedan fuera de la expresión:", 12.5, T.texto_3, peso=ft.FontWeight.W_700),
                *[texto(f"• {l}", 12.5, T.texto_2) for l in v.limites],
            ], spacing=8), "Alcance y límites", ft.Icons.POLICY_OUTLINED),
        ]
        self.validar(actualizar=False)

    def validar(self, actualizar: bool = True) -> None:
        v = V.VALIDADORES[self.clave]
        valor = self.entrada.value or ""
        self.estado.recordar(f"val.texto.{self.clave}", valor)
        r = simular(V.automata_minimo(self.clave), list(valor))
        coincide = bool(re.fullmatch(v.python, valor)) == r.aceptada
        color = T.exito if r.aceptada else T.error
        detalle = r.error or (f"El AFD mínimo termina en {', '.join(sorted(r.finales)) or '∅'}"
                              + (" (estado de aceptación)." if r.aceptada else "."))
        self.resultado.content = ft.Container(ft.Row([
            ft.Icon(ft.Icons.VERIFIED if r.aceptada else ft.Icons.GPP_BAD_OUTLINED, color=color, size=28),
            ft.Column([texto("VÁLIDO" if r.aceptada else "NO VÁLIDO", 15, color, peso=ft.FontWeight.W_800),
                       texto(detalle, 12, T.texto_2),
                       texto("re.fullmatch coincide con el autómata." if coincide else
                             "¡re.fullmatch no coincide con el autómata!", 11.5,
                             T.texto_3 if coincide else T.error)], spacing=2, expand=True),
        ], spacing=12), padding=14, border_radius=12, bgcolor=alfa(color, 0.1), border=ft.Border.all(1, alfa(color, 0.4)))
        if actualizar:
            refrescar(self.resultado)

    def vista(self) -> ft.Control:
        return ft.Column([
            titulo_pagina("Validadores",
                          "Correo, teléfono, fecha y URL: de la expresión regular al AFD mínimo que valida el texto.",
                          ft.Icons.VERIFIED_OUTLINED, "Práctica 4"),
            self.selector,
            self.cuerpo,
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def construir(estado: Estado) -> ft.Control:
    return PaginaValidadores(estado).vista()
