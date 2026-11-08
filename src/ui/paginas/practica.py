"""Práctica: ejercicios evaluados por el sistema, pistas y ejercicios generados por la IA."""

from __future__ import annotations

import random
from typing import Optional

import flet as ft

from core.automata import Automata
from ia import cliente
from ia.contexto import describir_automata
from ia.prompts import ESQUEMA_EJERCICIO, SISTEMA_GENERADOR, pedido_ejercicio, pedido_pista
from practica.ejercicios import (BANCO, TIPOS, Ejercicio, Evaluacion, Pregunta, evaluar_automata, evaluar_expresion,
                                 pregunta_aleatoria, validar_generado)
from ui.componentes.automatas import selector_automata
from ui.componentes.comunes import (aviso, boton, campo, chip, pestanas, refrescar, tarjeta, texto, titulo_pagina)
from ui.componentes.lienzo import Lienzo
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO, RADIO_CHICO, T, alfa

COLOR_DIFICULTAD = {"básico": "exito", "intermedio": "aviso", "avanzado": "error"}


class PaginaPractica:
    def __init__(self, estado: Estado):
        self.estado = estado
        estado.contexto_ia = self._contexto_ia
        r = estado.recuperar
        self.modo = r("practica.modo", "ejercicios")
        self.generados: list[Ejercicio] = r("practica.generados", [])
        estado.recordar("practica.generados", self.generados)
        self.resueltos: set[str] = r("practica.resueltos", set())
        estado.recordar("practica.resueltos", self.resueltos)
        self.clave = r("practica.sel", BANCO[0].clave)
        self.evaluacion: Optional[Evaluacion] = None
        self.ultimo_intento = ""
        self.selector = ft.Container()
        self.cuerpo = ft.Column(spacing=16)
        self.resultado = ft.Container()
        self.respuesta_er = campo("Tu expresión regular", "", "Notación del curso: + unión, * cerradura, λ vacía",
                                  al_enviar=lambda e: self.evaluar())
        self.indice_automata = estado.indice
        # Generador
        self.gen_tipo = r("practica.gen_tipo", "automata")
        self.gen_dificultad = r("practica.gen_dif", "intermedio")
        self.gen_alfabeto = campo("Alfabeto", r("practica.gen_alf", "a, b"), "Uno a cuatro símbolos de un carácter")
        self.gen_tema = campo("Idea o tema (opcional)", r("practica.gen_tema", ""), "p. ej. «subcadenas», «paridad»",
                              mono=False)
        self.generando = False
        self.salida_generador = ft.Container()
        # Preguntas rápidas
        self.rnd = random.Random()
        self.pregunta: Optional[Pregunta] = None
        self.respondida: Optional[bool] = None
        self.puntos = r("practica.puntos", [0, 0])
        estado.recordar("practica.puntos", self.puntos)
        self.lienzo_pregunta = Lienzo(None, alto=300)
        self.panel_pregunta = ft.Column(spacing=12)
        self._construir()

    # ------------------------------------------------------------------
    @property
    def ejercicios(self) -> list[Ejercicio]:
        return BANCO + self.generados

    @property
    def actual(self) -> Ejercicio:
        return next((e for e in self.ejercicios if e.clave == self.clave), BANCO[0])

    def _cambiar_modo(self, modo: str) -> None:
        self.modo = modo
        self.estado.recordar("practica.modo", modo)
        self._construir()
        refrescar(self.selector, self.cuerpo)

    def _construir(self) -> None:
        self.selector.content = pestanas([("ejercicios", "Ejercicios"), ("preguntas", "Preguntas rápidas")],
                                         self.modo, self._cambiar_modo)
        if self.modo == "preguntas":
            if self.pregunta is None:
                self._nueva_pregunta(actualizar=False)
            self._pintar_pregunta()
            self.cuerpo.controls = [tarjeta(ft.Column([
                texto("¿El autómata acepta la cadena? Responde y el sistema te dice si acertaste.", 13, T.texto_2),
                ft.ResponsiveRow([ft.Container(self.lienzo_pregunta.control, col={"xs": 12, "lg": 7}),
                                  ft.Container(self.panel_pregunta, col={"xs": 12, "lg": 5})],
                                 spacing=16, run_spacing=16),
            ], spacing=12), "Preguntas rápidas", ft.Icons.QUIZ_OUTLINED)]
        else:
            self.cuerpo.controls = [ft.ResponsiveRow([
                ft.Container(self._lista(), col={"xs": 12, "lg": 4}),
                ft.Container(ft.Column([self._detalle(), self._generador()], spacing=16), col={"xs": 12, "lg": 8}),
            ], spacing=16, run_spacing=16)]

    # ------------------------------------------------------------------
    # Lista de ejercicios
    # ------------------------------------------------------------------
    def _lista(self) -> ft.Control:
        filas = []
        for e in self.ejercicios:
            activo = e.clave == self.clave
            hecho = e.clave in self.resueltos
            filas.append(ft.Container(ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE if hecho else ft.Icons.RADIO_BUTTON_UNCHECKED,
                        color=T.exito if hecho else T.texto_3, size=18),
                ft.Column([texto(e.titulo, 13.5, peso=ft.FontWeight.W_600 if activo else None),
                           ft.Row([chip(e.dificultad, getattr(T, COLOR_DIFICULTAD.get(e.dificultad, "acento"))),
                                   chip("ER" if e.tipo == "expresion" else "autómata", T.texto_2),
                                   *([chip("IA", T.primario, icono=ft.Icons.AUTO_AWESOME)] if e.generado_por_ia
                                     else [])], spacing=4, wrap=True)], spacing=4, expand=True),
            ], spacing=10), padding=10, border_radius=RADIO_CHICO,
                bgcolor=T.primario_suave if activo else None,
                border=ft.Border.all(1, alfa(T.primario, 0.35) if activo else T.borde),
                on_click=lambda ev, c=e.clave: self._seleccionar(c)))
        total = len(self.ejercicios)
        return tarjeta(ft.Column([
            ft.Row([chip(f"{len(self.resueltos & {e.clave for e in self.ejercicios})} de {total} resueltos", T.exito)]),
            ft.Column(filas, spacing=6),
        ], spacing=12), "Ejercicios", ft.Icons.LIST_ALT)

    def _seleccionar(self, clave: str) -> None:
        self.clave = clave
        self.estado.recordar("practica.sel", clave)
        self.evaluacion = None
        self.respuesta_er.value = ""
        self._construir()
        refrescar(self.cuerpo)

    # ------------------------------------------------------------------
    # Ejercicio seleccionado
    # ------------------------------------------------------------------
    def _detalle(self) -> ft.Control:
        e = self.actual
        self._pintar_resultado()
        if e.tipo == "expresion":
            respuesta = ft.Row([ft.Container(self.respuesta_er, expand=True),
                                boton("Evaluar", lambda ev: self.evaluar(), ft.Icons.FACT_CHECK)],
                               spacing=12, vertical_alignment=ft.CrossAxisAlignment.START)
        else:
            respuesta = ft.Column([
                texto("Construye tu autómata en el Editor y elígelo aquí para evaluarlo.", 12.5, T.texto_3),
                ft.Row([
                    selector_automata(self.estado, self.indice_automata, self._elegir_automata, "Tu autómata")
                    if self.estado.automatas else texto("Aún no tienes autómatas en la sesión.", 12.5, T.texto_3),
                    boton("Evaluar", lambda ev: self.evaluar(), ft.Icons.FACT_CHECK,
                          disabled=not self.estado.automatas),
                    boton("Crear autómata para este ejercicio", lambda ev: self.crear_automata(),
                          ft.Icons.ADD_CIRCLE_OUTLINE, "secundario"),
                ], spacing=12, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=8)
        return tarjeta(ft.Column([
            ft.Row([texto(e.titulo, 17, peso=ft.FontWeight.W_700, expand=True),
                    chip(TIPOS[e.tipo], T.acento),
                    chip(e.dificultad, getattr(T, COLOR_DIFICULTAD.get(e.dificultad, "acento")))],
                   spacing=8),
            texto(e.enunciado, 14, T.texto),
            ft.Row([texto("Σ =", 13, T.texto_3), texto("{" + ", ".join(e.alfabeto) + "}", 13, mono=True)], spacing=6),
            *([aviso("Ejercicio generado por la IA: el sistema validó que la respuesta de referencia es una "
                     "expresión correcta, pero el enunciado podría no describirla con total exactitud.", "aviso")]
              if e.generado_por_ia else []),
            respuesta,
            self.resultado,
        ], spacing=12), "Ejercicio", ft.Icons.EDIT_NOTE)

    def _elegir_automata(self, i: int) -> None:
        self.indice_automata = i

    def crear_automata(self) -> None:
        e = self.actual
        a = Automata(nombre=f"Práctica: {e.titulo}", alfabeto=list(e.alfabeto))
        self.estado.agregar_automata(a)
        self.estado.notificar("Autómata creado. Dibújalo en el Editor y vuelve a Práctica para evaluarlo.", "exito")
        self.estado.navegar("editor")

    def evaluar(self) -> None:
        e = self.actual
        if e.tipo == "expresion":
            self.ultimo_intento = self.respuesta_er.value or ""
            self.evaluacion = evaluar_expresion(e, self.ultimo_intento)
        else:
            if not 0 <= self.indice_automata < len(self.estado.automatas):
                self.estado.notificar("Elige un autómata de la sesión.", "aviso")
                return
            a = self.estado.automatas[self.indice_automata]
            self.ultimo_intento = describir_automata(a)
            self.evaluacion = evaluar_automata(e, a)
        if self.evaluacion.correcto:
            self.resueltos.add(e.clave)
        self.estado.registrar(f"Práctica «{e.titulo}»: {'correcto' if self.evaluacion.correcto else 'por corregir'}",
                              ft.Icons.FACT_CHECK, T.exito if self.evaluacion.correcto else T.aviso)
        self._construir()
        refrescar(self.cuerpo)

    def _pintar_resultado(self) -> None:
        ev = self.evaluacion
        if ev is None:
            self.resultado.content = None
            return
        color = T.exito if ev.correcto else T.error
        botones = [] if ev.correcto else [ft.TextButton(
            "Pedir una pista a la IA", icon=ft.Icons.AUTO_AWESOME, disabled=not cliente.disponible(),
            on_click=lambda e: self.estado.preguntar_ia(
                pedido_pista(self.actual.enunciado, self.ultimo_intento, ev.contraejemplo, ev.deberia_aceptar)))]
        self.resultado.content = ft.Container(ft.Column([
            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE if ev.correcto else ft.Icons.CANCEL, color=color),
                    texto(ev.mensaje, 13.5, T.texto, expand=True)], spacing=10),
            *[texto(f"• {a}", 12.5, T.texto_2) for a in ev.avisos],
            *botones,
        ], spacing=8), padding=14, border_radius=RADIO_CHICO, bgcolor=alfa(color, 0.08),
            border=ft.Border.all(1, alfa(color, 0.35)))

    # ------------------------------------------------------------------
    # Generador de ejercicios con IA
    # ------------------------------------------------------------------
    def _generador(self) -> ft.Control:
        disponible = cliente.disponible()
        controles = ft.Column([
            texto("La IA propone un enunciado y una respuesta de referencia; el sistema la valida y es el que evalúa "
                  "tu respuesta. La referencia nunca se muestra.", 12.5, T.texto_3),
            ft.Row([pestanas(list(TIPOS.items()), self.gen_tipo, self._cambiar_gen_tipo),
                    pestanas([(d, d) for d in COLOR_DIFICULTAD], self.gen_dificultad, self._cambiar_gen_dif)],
                   spacing=12, wrap=True),
            ft.Row([ft.Container(self.gen_alfabeto, width=200), ft.Container(self.gen_tema, expand=True)], spacing=12),
            ft.Row([boton("Generar ejercicio", self.generar, ft.Icons.AUTO_AWESOME,
                          disabled=not disponible or self.generando)]),
            self.salida_generador,
            *([] if disponible else [aviso("La IA no está configurada (falta ANTHROPIC_API_KEY). Los ejercicios del "
                                           "banco funcionan igual.", "aviso")]),
        ], spacing=12)
        return tarjeta(controles, "Nuevo ejercicio con IA", ft.Icons.AUTO_AWESOME)

    def _cambiar_gen_tipo(self, t: str) -> None:
        self.gen_tipo = t
        self.estado.recordar("practica.gen_tipo", t)
        self._construir()
        refrescar(self.cuerpo)

    def _cambiar_gen_dif(self, d: str) -> None:
        self.gen_dificultad = d
        self.estado.recordar("practica.gen_dif", d)
        self._construir()
        refrescar(self.cuerpo)

    async def generar(self, e=None) -> None:
        alfabeto = [s.strip() for s in (self.gen_alfabeto.value or "").replace(",", " ").split() if s.strip()]
        self.estado.recordar("practica.gen_alf", self.gen_alfabeto.value)
        self.estado.recordar("practica.gen_tema", self.gen_tema.value)
        if not 1 <= len(alfabeto) <= 4 or any(len(s) != 1 for s in alfabeto):
            self.estado.notificar("Use de 1 a 4 símbolos de un carácter, separados por comas.", "aviso")
            return
        self.generando = True
        self.salida_generador.content = ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2),
                                                texto("Generando y validando el ejercicio…", 12.5, T.texto_3)],
                                               spacing=8)
        refrescar(self.salida_generador)
        try:
            for intento in range(2):   # un reintento si la propuesta no pasa la validación
                datos = await cliente.generar_json(
                    SISTEMA_GENERADOR, pedido_ejercicio(self.gen_tipo, self.gen_dificultad, alfabeto,
                                                        self.gen_tema.value or ""), ESQUEMA_EJERCICIO)
                datos["tipo"] = self.gen_tipo
                datos["alfabeto"] = alfabeto
                try:
                    ejercicio = validar_generado(datos)
                    break
                except ValueError as exc:
                    if intento == 1:
                        raise cliente.ErrorIA(f"La propuesta de la IA no pasó la validación: {exc}") from exc
            self.generados.append(ejercicio)
            self.estado.registrar(f"Ejercicio generado por IA: {ejercicio.titulo}", ft.Icons.AUTO_AWESOME)
            self.generando = False
            self.salida_generador.content = None
            self._seleccionar(ejercicio.clave)
        except cliente.ErrorIA as exc:
            self.generando = False
            self.salida_generador.content = aviso(str(exc), "error")
            refrescar(self.salida_generador)

    # ------------------------------------------------------------------
    # Preguntas rápidas
    # ------------------------------------------------------------------
    def _nueva_pregunta(self, actualizar: bool = True) -> None:
        self.pregunta = pregunta_aleatoria(self.rnd)
        self.respondida = None
        self.lienzo_pregunta.usar(self.pregunta.automata)
        if actualizar:
            self._pintar_pregunta()
            refrescar(self.panel_pregunta)

    def _responder(self, dice_que_acepta: bool) -> None:
        if self.pregunta is None or self.respondida is not None:
            return
        self.respondida = dice_que_acepta
        self.puntos[1] += 1
        if dice_que_acepta == self.pregunta.respuesta:
            self.puntos[0] += 1
        self._pintar_pregunta()
        refrescar(self.panel_pregunta)

    def _pintar_pregunta(self) -> None:
        p = self.pregunta
        if p is None:
            return
        controles: list[ft.Control] = [
            texto(f"Autómata: {p.automata.nombre} ({p.automata.tipo})", 13, T.texto_2),
            ft.Row([texto("Cadena:", 14, T.texto_2),
                    ft.Container(ft.Text(p.cadena or "λ", font_family=FUENTE_MONO, size=20, color=T.primario,
                                         weight=ft.FontWeight.W_700, selectable=True),
                                 padding=ft.Padding.symmetric(horizontal=14, vertical=8), border_radius=10,
                                 bgcolor=T.primario_suave)], spacing=10),
        ]
        if self.respondida is None:
            controles.append(ft.Row([boton("Acepta", lambda e: self._responder(True), ft.Icons.CHECK),
                                     boton("Rechaza", lambda e: self._responder(False), ft.Icons.CLOSE, "secundario")],
                                    spacing=10))
        else:
            acierto = self.respondida == p.respuesta
            controles.append(aviso(("¡Correcto! " if acierto else "No. ") + "El autómata "
                                   + ("acepta" if p.respuesta else "rechaza") + f" «{p.cadena or 'λ'}». "
                                   "Compruébalo en Simulación si quieres ver el recorrido.",
                                   "exito" if acierto else "error"))
            controles.append(ft.Row([
                boton("Siguiente", lambda e: self._nueva_pregunta(), ft.Icons.ARROW_FORWARD),
                ft.TextButton("Explicar con IA", icon=ft.Icons.AUTO_AWESOME, disabled=not cliente.disponible(),
                              on_click=lambda e: self.estado.preguntar_ia(
                                  f"Explícame por qué el autómata {'acepta' if p.respuesta else 'rechaza'} "
                                  f"la cadena «{p.cadena or 'λ'}».")),
            ], spacing=10))
        controles.append(chip(f"aciertos: {self.puntos[0]} de {self.puntos[1]}", T.acento))
        self.panel_pregunta.controls = controles

    # ------------------------------------------------------------------
    def _contexto_ia(self) -> str:
        if self.modo == "preguntas" and self.pregunta is not None:
            p = self.pregunta
            texto_ctx = (f"Pregunta rápida: ¿el autómata acepta «{p.cadena or 'λ'}»?\n"
                         + describir_automata(p.automata))
            if self.respondida is None:
                texto_ctx += "\nEl estudiante aún no responde: no le digas la respuesta, ayúdale a razonarla."
            return texto_ctx
        e = self.actual
        partes = [f"Ejercicio de práctica: {e.titulo}. {e.enunciado} Σ = {{{', '.join(e.alfabeto)}}}.",
                  "No reveles la solución: sólo pistas."]
        if self.evaluacion is not None:
            partes.append(f"Última evaluación del sistema: {self.evaluacion.mensaje}")
            if self.ultimo_intento:
                partes.append(f"Intento del estudiante:\n{self.ultimo_intento}")
        return "\n".join(partes)

    def vista(self) -> ft.Control:
        return ft.Column([
            titulo_pagina("Práctica", "Resuelve ejercicios: el sistema evalúa tu respuesta y la IA te da pistas.",
                          ft.Icons.FITNESS_CENTER_ROUNDED),
            self.selector,
            self.cuerpo,
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def construir(estado: Estado) -> ft.Control:
    return PaginaPractica(estado).vista()
