"""Panel lateral del asistente de IA, disponible en todas las secciones."""

from __future__ import annotations

import time

import flet as ft

from ia import cliente
from ia.contexto import SUGERENCIAS
from ui.componentes.comunes import refrescar, texto
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO, RADIO_CHICO, T, alfa

ANCHO = 390


class PanelAsistente:
    def __init__(self, estado: Estado):
        self.estado = estado
        self.abierto = False
        self.enviando = False
        self.lista = ft.ListView(expand=True, spacing=12, auto_scroll=True, padding=ft.Padding.only(right=6))
        self.entrada = ft.TextField(
            hint_text="Pregunta sobre autómatas, lenguajes o lo que ves en pantalla…",
            multiline=True, min_lines=1, max_lines=4, shift_enter=True, expand=True,
            border_radius=RADIO_CHICO, border_color=T.borde, focused_border_color=T.primario,
            on_submit=lambda e: self._enviar_desde_campo(),
        )
        self.sugerencias = ft.Row(wrap=True, spacing=6, run_spacing=6)
        self.estado_texto = ft.Text("", size=11, color=T.texto_3)
        self.control = ft.Container(width=ANCHO, visible=False, bgcolor=T.superficie,
                                    border=ft.Border.only(left=ft.BorderSide(1, T.borde)))
        self.construir()

    # ------------------------------------------------------------------
    def construir(self) -> None:
        """Rehace los controles (al iniciar y al cambiar de tema), conservando la conversación."""
        self.control.bgcolor = T.superficie
        self.control.border = ft.Border.only(left=ft.BorderSide(1, T.borde))
        self.entrada.border_color = T.borde
        self.entrada.focused_border_color = T.primario
        self._pintar_mensajes()
        self.actualizar_sugerencias()
        disponible = cliente.disponible()
        self.entrada.disabled = not disponible
        aviso = [] if disponible else [ft.Container(ft.Column([
            texto("El asistente no está configurado.", 13, T.aviso, peso=ft.FontWeight.W_700),
            texto("Defina la variable de entorno IA_API_KEY en el servidor (en Render: Environment) y "
                  "reinicie la aplicación. La clave gratuita se obtiene en console.groq.com. El resto del "
                  "sistema funciona sin IA.", 12, T.texto_2),
        ], spacing=4), padding=12, border_radius=RADIO_CHICO, bgcolor=alfa(T.aviso, 0.1),
            border=ft.Border.all(1, alfa(T.aviso, 0.35)))]
        self._actualizar_estado()
        self.control.content = ft.Column([
            ft.Row([
                ft.Container(ft.Icon(ft.Icons.AUTO_AWESOME, color="#FFFFFF", size=18), width=34, height=34,
                             border_radius=10, alignment=ft.Alignment.CENTER,
                             gradient=ft.LinearGradient(colors=[T.primario, T.acento])),
                ft.Column([texto("Asistente IA", 15, peso=ft.FontWeight.W_700), self.estado_texto],
                          spacing=0, expand=True),
                ft.IconButton(ft.Icons.DELETE_SWEEP_OUTLINED, icon_color=T.texto_2, tooltip="Borrar la conversación",
                              on_click=lambda e: self.limpiar()),
                ft.IconButton(ft.Icons.CLOSE, icon_color=T.texto_2, tooltip="Cerrar",
                              on_click=lambda e: self.alternar(False)),
            ], spacing=10),
            texto("Explica conceptos y lo que ves en pantalla. No resuelve ejercicios y puede equivocarse: "
                  "verifica con las herramientas del sistema.", 11.5, T.texto_3),
            *aviso,
            ft.Container(self.lista, expand=True),
            self.sugerencias,
            ft.Row([self.entrada,
                    ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="#FFFFFF", bgcolor=T.primario,
                                  tooltip="Enviar (Enter). Shift+Enter: nueva línea", disabled=not disponible,
                                  on_click=lambda e: self._enviar_desde_campo())],
                   spacing=8, vertical_alignment=ft.CrossAxisAlignment.END),
        ], spacing=12, expand=True)
        self.control.padding = 16

    def _actualizar_estado(self) -> None:
        if cliente.disponible():
            self.estado_texto.value = (f"{cliente.modelo()} · {self.estado.conversacion.restantes} consultas "
                                       "disponibles")
        else:
            self.estado_texto.value = "sin configurar"

    def actualizar_sugerencias(self) -> None:
        self.sugerencias.controls = [
            ft.Container(texto(s, 11.5, T.acento), padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                         border_radius=14, bgcolor=alfa(T.acento, 0.1), border=ft.Border.all(1, alfa(T.acento, 0.3)),
                         on_click=lambda e, s=s: self.preguntar(s), tooltip="Preguntar esto")
            for s in SUGERENCIAS.get(self.estado.modulo_actual, [])[:3]
        ] if cliente.disponible() else []
        refrescar(self.sugerencias)

    # ------------------------------------------------------------------
    def _burbuja(self, rol: str, contenido: str) -> ft.Control:
        if rol == "usuario":
            return ft.Row([ft.Container(
                ft.Text(contenido, size=13, color=T.texto, selectable=True),
                padding=12, border_radius=ft.BorderRadius.only(top_left=14, top_right=14, bottom_left=14, bottom_right=4),
                bgcolor=T.primario_suave, border=ft.Border.all(1, alfa(T.primario, 0.35)), width=ANCHO - 90,
            )], alignment=ft.MainAxisAlignment.END)
        if rol == "error":
            return ft.Container(ft.Row([ft.Icon(ft.Icons.ERROR_OUTLINE, color=T.error, size=16),
                                        ft.Text(contenido, size=12.5, color=T.texto, expand=True)], spacing=8),
                                padding=12, border_radius=RADIO_CHICO, bgcolor=alfa(T.error, 0.1),
                                border=ft.Border.all(1, alfa(T.error, 0.35)))
        return ft.Container(self._markdown(contenido), padding=12,
                            border_radius=ft.BorderRadius.only(top_left=14, top_right=14, bottom_right=14,
                                                               bottom_left=4),
                            bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde))

    def _markdown(self, contenido: str) -> ft.Markdown:
        return ft.Markdown(contenido or "…", selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                           md_style_sheet=ft.MarkdownStyleSheet(
                               p_text_style=ft.TextStyle(size=13, color=T.texto),
                               code_text_style=ft.TextStyle(font_family=FUENTE_MONO, size=12.5)))

    def _pintar_mensajes(self) -> None:
        mensajes = self.estado.conversacion.mensajes
        if not mensajes:
            self.lista.controls = [ft.Container(ft.Column([
                ft.Icon(ft.Icons.FORUM_OUTLINED, color=T.texto_3, size=34),
                texto("Pregúntame sobre lo que estás viendo. Por ejemplo: «¿por qué se rechazó esta cadena?»",
                      12.5, T.texto_3, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), padding=ft.Padding.only(top=40))]
        else:
            self.lista.controls = [self._burbuja(m.rol, m.texto) for m in mensajes]

    # ------------------------------------------------------------------
    def alternar(self, abrir: bool | None = None) -> None:
        self.abierto = (not self.abierto) if abrir is None else abrir
        self.control.visible = self.abierto
        if self.abierto:
            self.actualizar_sugerencias()
        refrescar(self.control)

    def limpiar(self) -> None:
        self.estado.conversacion.limpiar()
        self._pintar_mensajes()
        refrescar(self.lista)

    def _enviar_desde_campo(self) -> None:
        pregunta = (self.entrada.value or "").strip()
        if pregunta:
            self.entrada.value = ""
            refrescar(self.entrada)
            self.preguntar(pregunta)

    def preguntar(self, pregunta: str) -> None:
        """Abre el panel y envía la pregunta (la usan también otras pantallas)."""
        if not self.abierto:
            self.alternar(True)
        if self.enviando or not cliente.disponible():
            if not cliente.disponible():
                self.estado.notificar("El asistente no está configurado (falta IA_API_KEY).", "aviso")
            return
        self.estado.page.run_task(self._enviar, pregunta)

    async def _enviar(self, pregunta: str) -> None:
        self.enviando = True
        if not self.estado.conversacion.mensajes:
            self.lista.controls = []
        self.lista.controls.append(self._burbuja("usuario", pregunta))
        respuesta_md = self._markdown("")
        cargando = ft.Row([ft.ProgressRing(width=14, height=14, stroke_width=2, color=T.primario),
                           texto("Pensando…", 12, T.texto_3)], spacing=8)
        burbuja = ft.Container(ft.Column([cargando, respuesta_md], spacing=6), padding=12,
                               border_radius=ft.BorderRadius.only(top_left=14, top_right=14, bottom_right=14,
                                                                  bottom_left=4),
                               bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde))
        self.lista.controls.append(burbuja)
        refrescar(self.lista)
        ultimo = [0.0]

        def al_texto(acumulado: str) -> None:
            # Se actualiza a lo sumo unas 8 veces por segundo para no saturar la conexión.
            ahora = time.monotonic()
            if ahora - ultimo[0] > 0.12:
                ultimo[0] = ahora
                cargando.visible = False
                respuesta_md.value = acumulado
                refrescar(burbuja)

        try:
            final = await self.estado.conversacion.preguntar(pregunta, self.estado.describir_pantalla(), al_texto)
            cargando.visible = False
            respuesta_md.value = final
            self.estado.registrar("Consulta al asistente de IA", ft.Icons.AUTO_AWESOME)
        except cliente.ErrorIA as exc:
            self.lista.controls[-1] = self._burbuja("error", str(exc))
        finally:
            self.enviando = False
            self._actualizar_estado()
            refrescar(self.lista, self.estado_texto)
