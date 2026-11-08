"""Expresiones regulares: ER → autómata, autómata → ER y comparación de expresiones."""

from __future__ import annotations

from typing import Optional

import flet as ft

from core import ejemplos
from core.automata import ErrorAutomata
from core.expresion_regular import ErrorSintaxis, a_python, a_texto, analizar, analizar_clases, arbol_texto, tamano
from core.simulacion import simular
from algoritmos.eliminacion_estados import eliminar_estados
from algoritmos.equivalencia import comparar
from algoritmos.tuberia import Resultado, desde_expresion, desde_texto
from formatos import EXTENSIONES, ErrorFormato, cargar, exportar
from ui.componentes.automatas import acciones_resultado, resumen_automata, selector_automata
from ui.componentes.comunes import (aviso, boton, campo, chip, pestanas, refrescar, tarjeta, texto, titulo_pagina)
from ui.componentes.reproductor import Reproductor
from ia.contexto import describir_automata
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO_CHICO, T, alfa

NOTACION = ("Notación: + unión · yuxtaposición = concatenación · * cerradura · λ palabra vacía · ∅ vacío · "
            "( ) agrupan · \\c usa c como símbolo (\\+ \\* \\( \\) \\␣) · {D} clase declarada.")


def caja_error(exc: ErrorSintaxis) -> ft.Control:
    return ft.Container(ft.Column([
        ft.Row([ft.Icon(ft.Icons.ERROR_OUTLINE, color=T.error, size=18),
                texto(f"Expresión mal formada en la posición {exc.posicion}: {exc.mensaje}", 13, T.texto,
                      expand=True)], spacing=8),
        ft.Text(exc.marca(), font_family=FUENTE_MONO, size=14, color=T.error, selectable=True),
    ], spacing=8), padding=14, border_radius=RADIO_CHICO, bgcolor=alfa(T.error, 0.08),
        border=ft.Border.all(1, alfa(T.error, 0.4)))


def expresion_destacada(valor: str, color: Optional[str] = None) -> ft.Control:
    color = color or T.primario
    return ft.Container(ft.Text(valor, size=18, font_family=FUENTE_MONO, color=color, selectable=True,
                                weight=ft.FontWeight.W_700),
                        padding=14, border_radius=RADIO_CHICO, bgcolor=alfa(color, 0.08),
                        border=ft.Border.all(1, alfa(color, 0.3)))


class PaginaExpresiones:
    def __init__(self, estado: Estado):
        self.estado = estado
        estado.contexto_ia = self._contexto_ia
        r = estado.recuperar
        self.modo = r("er.modo", "er_a_automata")
        self.reproductor = Reproductor(estado, vacio="Escriba una expresión y pulse «Construir».")
        self.cuerpo = ft.Column(spacing=16)
        self.selector = ft.Container()
        self.resultado: Optional[Resultado] = None
        self.etapa = 0
        # ER → autómata
        self.expresion = campo("Expresión regular", r("er.texto", "(a+b)*abb"), al_enviar=lambda e: self.construir())
        self.clases = campo("Clases (opcional, una por línea)", r("er.clases", ""),
                            "Ejemplo: D = [0-9]   o   V = a+e+i+o+u", multiline=True, min_lines=2, max_lines=5)
        self.cadena = campo("Cadena a validar", r("er.cadena", "aabb"), "λ o vacío para la cadena vacía",
                            al_enviar=lambda e: self.validar_cadena())
        self.salida_er = ft.Column(spacing=14)
        self.salida_cadena = ft.Container()
        # Autómata → ER
        self.jflap = campo("Expresión obtenida con JFLAP", r("er.jflap", ""),
                           "Escríbala en la notación del curso para comprobar que es equivalente",
                           al_enviar=lambda e: self.comparar_jflap())
        self.salida_jflap = ft.Container()
        self.expr_automata = None
        # Comparar
        self.e1 = campo("Expresión 1", r("er.e1", "(a+b)*ab"))
        self.e2 = campo("Expresión 2", r("er.e2", "(a*b*)*ab"))
        self.salida_comparar = ft.Container()
        self._construir()

    # ------------------------------------------------------------------
    def _cambiar_modo(self, modo: str) -> None:
        self.modo = modo
        self.estado.recordar("er.modo", modo)
        self._construir()
        refrescar(self.cuerpo, self.selector)

    def _construir(self) -> None:
        self.selector.content = pestanas([("er_a_automata", "ER → Autómata"), ("automata_a_er", "Autómata → ER"),
                                          ("comparar", "Comparar expresiones")], self.modo, self._cambiar_modo)
        if self.modo == "er_a_automata":
            self._vista_er_a_automata()
        elif self.modo == "automata_a_er":
            self._vista_automata_a_er()
        else:
            self._vista_comparar()

    # ------------------------------------------------------------------
    # ER → autómata
    # ------------------------------------------------------------------
    def _vista_er_a_automata(self) -> None:
        ejemplos_er = ft.Row([texto("Ejemplos:", 12.5, T.texto_3)] + [
            ft.Container(chip(e, T.acento, mono=True), on_click=lambda ev, e=e, c=c: self._usar(e, c))
            for e, c in [("(a+b)*abb", ""), ("a*b*c*", ""), ("(0+1(01*0)*1)*", ""), ("(ab+ba)*", ""),
                         ("{D}{D}*(.{D}{D}*+λ)", "D = [0-9]")]], spacing=8, wrap=True)
        self.cuerpo.controls = [
            tarjeta(ft.Column([
                ft.Row([ft.Container(self.expresion, expand=True),
                        boton("Construir", lambda e: self.construir(), ft.Icons.PLAY_ARROW_ROUNDED)],
                       spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Row([ft.Container(self.clases, expand=True)]),
                ejemplos_er,
                texto(NOTACION, 12, T.texto_3),
            ], spacing=12), "Expresión", ft.Icons.FUNCTIONS),
            self.salida_er,
        ]
        if self.resultado is None:
            self.construir(registrar=False)

    def _usar(self, expr: str, clases: str) -> None:
        self.expresion.value = expr
        self.clases.value = clases
        refrescar(self.expresion, self.clases)
        self.construir()

    def construir(self, registrar: bool = True) -> None:
        texto_er = self.expresion.value or ""
        self.estado.recordar("er.texto", texto_er)
        self.estado.recordar("er.clases", self.clases.value)
        try:
            clases = analizar_clases(self.clases.value or "")
        except ValueError as exc:
            self.resultado = None
            self.salida_er.controls = [aviso(f"Clases: {exc}", "error")]
            refrescar(self.salida_er)
            return
        try:
            arbol = analizar(texto_er, clases)
        except ErrorSintaxis as exc:
            self.resultado = None
            self.reproductor.cargar([])
            self.salida_er.controls = [caja_error(exc)]
            refrescar(self.salida_er)
            return
        self.resultado = desde_expresion(arbol, texto_er.strip())
        if registrar:
            self.estado.registrar(f"ER {texto_er} → AFD mínimo de {len(self.resultado.minimo.estados)} estados",
                                  ft.Icons.FUNCTIONS)
        self.etapa = 0
        self.reproductor.cargar(self.resultado.etapas[0].pasos)
        self._pintar_salida_er()
        self.validar_cadena(actualizar=False)
        refrescar(self.salida_er)

    def _elegir_etapa(self, i: int) -> None:
        self.etapa = i
        self.reproductor.cargar(self.resultado.etapas[i].pasos)
        self._pintar_salida_er()
        refrescar(self.salida_er)

    def _pintar_salida_er(self) -> None:
        res = self.resultado
        arbol = res.expresion
        tarjetas = []
        for i, et in enumerate(res.etapas):
            activo = i == self.etapa
            tarjetas.append(ft.Container(ft.Column([
                texto(f"{i + 1} · {et.titulo}", 13.5, peso=ft.FontWeight.W_700),
                ft.Row([texto(f"{len(et.automata.estados)}", 28, T.primario, mono=True, peso=ft.FontWeight.W_800),
                        texto("estados", 12, T.texto_3)], spacing=6, vertical_alignment=ft.CrossAxisAlignment.END),
                resumen_automata(et.automata),
                ft.Row([ft.TextButton("Ver pasos", on_click=lambda e, i=i: self._elegir_etapa(i)),
                        ft.TextButton(".jff", icon=ft.Icons.DOWNLOAD_ROUNDED,
                                      on_click=lambda e, a=et.automata: self.estado.page.run_task(
                                          self._descargar, a))], spacing=0),
            ], spacing=6), padding=14, border_radius=14,
                bgcolor=T.primario_suave if activo else T.superficie,
                border=ft.Border.all(1, T.primario if activo else T.borde), col={"xs": 12, "md": 6, "xl": 3}))
        self.salida_er.controls = [
            ft.ResponsiveRow([
                ft.Container(tarjeta(ft.Column([
                    texto("Expresión analizada (paréntesis mínimos):", 12.5, T.texto_3),
                    expresion_destacada(a_texto(arbol)),
                    ft.Row([chip(f"tamaño {tamano(arbol)}", T.texto_2), chip(f"Σ = {{{', '.join(res.afd.alfabeto)}}}"
                                                                           if len(res.afd.alfabeto) <= 12 else
                                                                           f"|Σ| = {len(res.afd.alfabeto)}", T.texto_2,
                                                                           mono=True)], spacing=8, wrap=True),
                    ft.Row([texto("re de Python:", 12.5, T.texto_3),
                            ft.Text(a_python(arbol), font_family=FUENTE_MONO, size=12.5, color=T.acento,
                                    selectable=True, expand=True)], spacing=8),
                ], spacing=10), "Análisis", ft.Icons.CHECK_CIRCLE_OUTLINE), col={"xs": 12, "lg": 6}),
                ft.Container(tarjeta(ft.Container(
                    ft.Text("\n".join(arbol_texto(arbol)), font_family=FUENTE_MONO, size=12.5, color=T.texto_2,
                            selectable=True), padding=12, border_radius=RADIO_CHICO, bgcolor=T.superficie_2),
                    "Árbol sintáctico", ft.Icons.ACCOUNT_TREE_OUTLINED), col={"xs": 12, "lg": 6}),
            ], spacing=16, run_spacing=16),
            ft.ResponsiveRow(tarjetas, spacing=12, run_spacing=12),
            tarjeta(self.reproductor.vista(), f"Paso a paso: {res.etapas[self.etapa].titulo}", ft.Icons.TIMELINE),
            tarjeta(ft.Column([
                ft.Row([ft.Container(self.cadena, expand=True),
                        boton("Validar", lambda e: self.validar_cadena(), ft.Icons.RULE)], spacing=12,
                       vertical_alignment=ft.CrossAxisAlignment.START),
                self.salida_cadena,
                acciones_resultado(self.estado, lambda: self.resultado.minimo if self.resultado else None,
                                   f"AFD mínimo de {a_texto(arbol)}"),
            ], spacing=12), "Validar cadenas con el autómata obtenido", ft.Icons.RULE),
        ]

    async def _descargar(self, a) -> None:
        base = "".join(c if c.isalnum() or c in "-_" else "_" for c in a.nombre).strip("_")[:50] or "automata"
        await self.estado.guardar(f"{base}.jff", exportar(a, "jff"), ["jff"])

    def validar_cadena(self, actualizar: bool = True) -> None:
        if self.resultado is None:
            return
        valor = self.cadena.value or ""
        self.estado.recordar("er.cadena", valor)
        w = "" if valor.strip() in ("λ", "lambda") else valor
        r_min = simular(self.resultado.minimo, list(w))
        r_afn = simular(self.resultado.afn_lambda, list(w))
        ok = r_min.aceptada
        color = T.exito if ok else T.error
        self.salida_cadena.content = ft.Container(ft.Column([
            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE if ok else ft.Icons.CANCEL, color=color),
                    texto(f"«{w or 'λ'}» {'pertenece' if ok else 'no pertenece'} a L({a_texto(self.resultado.expresion)})",
                          14, color, peso=ft.FontWeight.W_700, expand=True)], spacing=10),
            texto(r_min.error or ("Recorrido en el AFD mínimo: " + " → ".join(
                [next(iter(r_min.inicio))] + [next(iter(p.despues)) if p.despues else "∅" for p in r_min.pasos])),
                12.5, T.texto_2, mono=True, selectable=True),
            texto(f"El AFN-λ de Thompson da el mismo resultado ({'acepta' if r_afn.aceptada else 'rechaza'}).",
                  12, T.texto_3),
        ], spacing=6), padding=14, border_radius=RADIO_CHICO, bgcolor=alfa(color, 0.08),
            border=ft.Border.all(1, alfa(color, 0.35)))
        if actualizar:
            refrescar(self.salida_cadena)

    # ------------------------------------------------------------------
    # Autómata → ER
    # ------------------------------------------------------------------
    def _vista_automata_a_er(self) -> None:
        if self.estado.actual is None:
            self.estado.agregar_automata(ejemplos.multiplos_de_tres())
        a = self.estado.actual
        conflictos = a.conflictos_determinismo()
        if conflictos:
            verificacion = ft.Column([
                aviso(f"«{a.nombre}» no es determinista; lo impiden:", "error", ft.Icons.CALL_SPLIT),
                *[texto(f"• estado {q}, símbolo {s}: {m}", 12.5, T.texto_2, mono=True) for q, s, m in conflictos],
                texto("Convierta el autómata a AFD (Conversiones → Subconjuntos) o elija otro.", 12.5, T.texto_3),
            ], spacing=6)
            self.reproductor.cargar([])
            resultado: list[ft.Control] = []
        else:
            verificacion = aviso(f"«{a.nombre}» es determinista: ningún par (estado, símbolo) tiene más de un destino "
                                 "ni hay transiciones λ.", "exito")
            self.expr_automata, pasos, orden = eliminar_estados(a)
            self.reproductor.cargar(pasos)
            resultado = [
                tarjeta(self.reproductor.vista(), "Eliminación de estados paso a paso", ft.Icons.TIMELINE),
                tarjeta(ft.Column([
                    expresion_destacada(a_texto(self.expr_automata)),
                    ft.Row([chip(f"tamaño {tamano(self.expr_automata)}", T.texto_2),
                            chip("orden: " + ", ".join(orden), T.texto_2, mono=True)], spacing=8, wrap=True),
                    ft.Row([ft.Container(self.jflap, expand=True),
                            boton("Comparar", lambda e: self.comparar_jflap(), ft.Icons.COMPARE_ARROWS)],
                           spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                    self.salida_jflap,
                ], spacing=12), "Expresión regular obtenida", ft.Icons.FUNCTIONS),
            ]
        self.cuerpo.controls = [
            tarjeta(ft.Column([
                ft.Row([selector_automata(self.estado, self.estado.indice, self._cambiar_automata),
                        boton("Importar .jff", self.importar, ft.Icons.UPLOAD_FILE, "secundario"),
                        resumen_automata(a)], spacing=12, wrap=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                verificacion,
            ], spacing=12), "Autómata de entrada", ft.Icons.ACCOUNT_TREE_OUTLINED),
            *resultado,
        ]

    def _cambiar_automata(self, i: int) -> None:
        self.estado.seleccionar(i)
        self._construir()
        refrescar(self.cuerpo)

    async def importar(self, e=None) -> None:
        archivo = await self.estado.abrir(list(EXTENSIONES))
        if archivo is None:
            return
        try:
            a = cargar(*archivo)
        except (ErrorFormato, ErrorAutomata) as exc:
            self.estado.notificar(f"No se pudo leer {archivo[0]}: {exc}", "error")
            return
        self.estado.agregar_automata(a)
        self.estado.notificar(f"Importado {archivo[0]} ({a.tipo}).", "exito")
        self._construir()
        refrescar(self.cuerpo)

    def comparar_jflap(self) -> None:
        if self.expr_automata is None:
            return
        self.estado.recordar("er.jflap", self.jflap.value)
        try:
            otra = desde_texto(self.jflap.value or "")
        except ErrorSintaxis as exc:
            self.salida_jflap.content = caja_error(exc)
            refrescar(self.salida_jflap)
            return
        propia = desde_expresion(self.expr_automata)
        comp = comparar(propia.minimo, otra.minimo)
        self.salida_jflap.content = self._veredicto(comp, "la expresión del software", "la de JFLAP",
                                                    a_texto(self.expr_automata), self.jflap.value or "")
        refrescar(self.salida_jflap)

    # ------------------------------------------------------------------
    # Comparar dos expresiones
    # ------------------------------------------------------------------
    def _vista_comparar(self) -> None:
        self.cuerpo.controls = [
            tarjeta(ft.Column([
                self.e1, self.e2,
                ft.Row([boton("Comparar", lambda e: self.comparar_expresiones(), ft.Icons.COMPARE_ARROWS)]),
                texto("Ambas expresiones se convierten en AFD mínimos (Thompson → subconjuntos → minimización) y se "
                      "comparan salvo el nombre de los estados.", 12.5, T.texto_3),
                self.salida_comparar,
            ], spacing=12), "Equivalencia de expresiones regulares", ft.Icons.COMPARE_ARROWS),
        ]

    def comparar_expresiones(self) -> None:
        self.estado.recordar("er.e1", self.e1.value)
        self.estado.recordar("er.e2", self.e2.value)
        try:
            r1 = desde_texto(self.e1.value or "")
            r2 = desde_texto(self.e2.value or "")
        except ErrorSintaxis as exc:
            self.salida_comparar.content = caja_error(exc)
            refrescar(self.salida_comparar)
            return
        comp = comparar(r1.minimo, r2.minimo)
        self.estado.registrar(f"Comparación {self.e1.value} vs {self.e2.value}: "
                              f"{'equivalentes' if comp.equivalentes else 'distintas'}", ft.Icons.COMPARE_ARROWS)
        self.salida_comparar.content = self._veredicto(comp, "la expresión 1", "la expresión 2", self.e1.value,
                                                       self.e2.value)
        refrescar(self.salida_comparar)

    def _veredicto(self, comp, n1: str, n2: str, t1: str, t2: str) -> ft.Control:
        color = T.exito if comp.equivalentes else T.error
        lineas = [texto("EQUIVALENTES" if comp.equivalentes else "NO EQUIVALENTES", 16, color,
                        peso=ft.FontWeight.W_800),
                  texto(f"AFD mínimos de {len(comp.minimo1.estados)} y {len(comp.minimo2.estados)} estados. "
                        + comp.motivo, 12.5, T.texto_2)]
        if not comp.equivalentes and comp.contraejemplo is not None:
            w = comp.contraejemplo or "λ"
            quien = n1 if comp.acepta1 else n2
            lineas.append(texto(f"Contraejemplo más corto: «{w}», que sólo acepta {quien}.", 13, T.texto,
                                peso=ft.FontWeight.W_600))
        return ft.Container(ft.Column(lineas, spacing=6), padding=16, border_radius=12, bgcolor=alfa(color, 0.1),
                            border=ft.Border.all(1, alfa(color, 0.4)))

    # ------------------------------------------------------------------
    def _contexto_ia(self) -> str:
        if self.modo == "er_a_automata":
            texto = f"Expresión escrita: {self.expresion.value}"
            if (self.clases.value or "").strip():
                texto += f"\nClases declaradas:\n{self.clases.value}"
            if self.resultado is not None:
                texto += (f"\nEtapa mostrada: {self.resultado.etapas[self.etapa].titulo}. Estados por etapa: "
                          + ", ".join(f"{e.titulo} {len(e.automata.estados)}" for e in self.resultado.etapas))
                texto += "\n" + self.reproductor.descripcion()
            return texto
        if self.modo == "automata_a_er":
            texto = describir_automata(self.estado.actual)
            if self.expr_automata is not None:
                texto += f"\nExpresión obtenida por eliminación de estados: {a_texto(self.expr_automata)}"
            return texto + "\n" + self.reproductor.descripcion()
        return f"Comparando las expresiones «{self.e1.value}» y «{self.e2.value}»."

    def vista(self) -> ft.Control:
        return ft.Column([
            titulo_pagina("Expresiones regulares",
                          "Las dos direcciones del teorema de Kleene, paso a paso, en la notación del curso.",
                          ft.Icons.FUNCTIONS, "Práctica 4"),
            self.selector,
            self.cuerpo,
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def construir(estado: Estado) -> ft.Control:
    return PaginaExpresiones(estado).vista()
