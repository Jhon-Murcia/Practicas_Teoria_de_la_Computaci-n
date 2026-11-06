"""Importación y exportación (.jff, .json, .xml) y proyectos de la sesión."""

from __future__ import annotations

import flet as ft

from core import ejemplos
from core.automata import ErrorAutomata
from core.proyecto import abrir_proyecto, guardar_proyecto
from formatos import EXTENSIONES, ErrorFormato, cargar, exportar
from ui.componentes.comunes import aviso, boton, boton_icono, chip, pestanas, refrescar, tarjeta, texto, titulo_pagina
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO_CHICO, T


class PaginaArchivos:
    def __init__(self, estado: Estado):
        self.estado = estado
        self.formato = estado.recuperar("archivos.formato", "jff")
        self.verificacion = ft.Column(spacing=10)
        self.vista_previa = ft.Container()
        self.biblioteca = ft.Column(spacing=8)
        self.selector_formato = ft.Container()
        self._construir_biblioteca()
        self._construir_previa()

    # ------------------------------------------------------------------
    async def importar(self, e=None) -> None:
        archivo = await self.estado.abrir(list(EXTENSIONES))
        if archivo is None:
            return
        nombre, datos = archivo
        avisos: list[str] = []
        try:
            a = cargar(nombre, datos, avisos)
        except (ErrorFormato, ErrorAutomata) as exc:
            self.verificacion.controls = [aviso(f"No se pudo leer {nombre}: {exc}", "error")]
            self.estado.notificar(f"Archivo inválido: {exc}", "error")
            refrescar(self.verificacion)
            return
        self.estado.agregar_automata(a)
        self.estado.notificar(f"Importado {nombre} ({a.tipo}, {len(a.estados)} estados)", "exito")
        q = a.quintupla()
        self.verificacion.controls = [
            ft.Row([ft.Icon(ft.Icons.TASK_ALT, color=T.exito), texto(f"{nombre} interpretado correctamente", 15,
                                                                      peso=ft.FontWeight.W_700),
                    chip(a.tipo, T.primario)], spacing=10),
            *[aviso(m, "aviso") for m in avisos],
            texto("Verifique los cinco componentes de la quíntupla:", 12.5, T.texto_3),
            *[ft.Row([texto(k, 13, T.primario, mono=True, peso=ft.FontWeight.W_700, width=30),
                      texto(v, 12.5, T.texto_2, mono=True, expand=True, selectable=True)],
                     vertical_alignment=ft.CrossAxisAlignment.START) for k, v in q.items()],
            ft.Row([boton("Abrir en el editor", lambda e: self.estado.navegar("editor"), ft.Icons.EDIT_OUTLINED),
                    boton("Simular", lambda e: self.estado.navegar("simulacion"), ft.Icons.PLAY_ARROW_ROUNDED,
                          "secundario")], spacing=10),
        ]
        self._construir_biblioteca()
        self._construir_previa()
        refrescar(self.verificacion, self.biblioteca, self.vista_previa)

    async def exportar_actual(self, formato: str) -> None:
        a = self.estado.actual
        if a is None:
            self.estado.notificar("No hay un autómata seleccionado.", "aviso")
            return
        try:
            contenido = exportar(a, formato)
        except ErrorAutomata as exc:
            self.estado.notificar(f"No se puede exportar: {exc}", "error")
            return
        base = "".join(c if c.isalnum() or c in "-_" else "_" for c in a.nombre).strip("_") or "automata"
        await self.estado.guardar(f"{base}.{formato}", contenido, [formato])

    async def guardar_proyecto(self, e=None) -> None:
        if not self.estado.automatas:
            self.estado.notificar("La sesión no tiene autómatas.", "aviso")
            return
        await self.estado.guardar("proyecto.alab.json", guardar_proyecto(self.estado.automatas, self.estado.indice),
                                  ["json"])

    async def abrir_proyecto(self, e=None) -> None:
        archivo = await self.estado.abrir(["json"])
        if archivo is None:
            return
        try:
            automatas, indice = abrir_proyecto(archivo[1])
        except ErrorAutomata as exc:
            self.estado.notificar(str(exc), "error")
            return
        self.estado.automatas = automatas
        self.estado.indice = indice
        self.estado.registrar(f"Proyecto abierto: {archivo[0]} ({len(automatas)} autómatas)", ft.Icons.FOLDER_OPEN)
        self.estado.notificar(f"Proyecto con {len(automatas)} autómatas abierto.", "exito")
        self._construir_biblioteca()
        self._construir_previa()
        refrescar(self.biblioteca, self.vista_previa)

    def cargar_ejemplos(self, e=None) -> None:
        for a in ejemplos.todos():
            self.estado.agregar_automata(a, seleccionar=False)
        if self.estado.indice < 0:
            self.estado.indice = 0
        self.estado.notificar(f"{len(ejemplos.EJEMPLOS)} ejemplos agregados a la sesión.", "exito")
        self._construir_biblioteca()
        self._construir_previa()
        refrescar(self.biblioteca, self.vista_previa)

    # ------------------------------------------------------------------
    def _seleccionar(self, i: int) -> None:
        self.estado.seleccionar(i)
        self._construir_biblioteca()
        self._construir_previa()
        refrescar(self.biblioteca, self.vista_previa)

    def _quitar(self, i: int) -> None:
        nombre = self.estado.automatas[i].nombre

        def borrar():
            self.estado.eliminar_automata(i)
            self._construir_biblioteca()
            self._construir_previa()
            refrescar(self.biblioteca, self.vista_previa)

        self.estado.confirmar("Quitar autómata", f"Se quitará «{nombre}» de la sesión.", borrar, "Quitar")

    def _construir_biblioteca(self) -> None:
        filas = []
        for i, a in enumerate(self.estado.automatas):
            activo = i == self.estado.indice
            filas.append(ft.Container(
                ft.Row([
                    ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED if activo else ft.Icons.RADIO_BUTTON_UNCHECKED,
                            color=T.primario if activo else T.texto_3, size=18),
                    texto(a.nombre, 13.5, peso=ft.FontWeight.W_600 if activo else None, expand=True),
                    chip(a.tipo, T.primario if a.tipo != "AFD" else T.acento),
                    texto(f"{len(a.estados)} estados", 12, T.texto_3, width=80),
                    boton_icono(ft.Icons.CLOSE, lambda e, i=i: self._quitar(i), "Quitar de la sesión"),
                ], spacing=10),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6), border_radius=RADIO_CHICO,
                bgcolor=T.primario_suave if activo else T.superficie_2,
                on_click=lambda e, i=i: self._seleccionar(i),
            ))
        if not filas:
            filas = [texto("La sesión no tiene autómatas. Importe uno o cargue los ejemplos.", 13, T.texto_3)]
        self.biblioteca.controls = filas

    def _cambiar_formato(self, f: str) -> None:
        self.formato = f
        self.estado.recordar("archivos.formato", f)
        self._construir_previa()
        refrescar(self.vista_previa)

    def _construir_previa(self) -> None:
        a = self.estado.actual
        if a is None:
            self.vista_previa.content = texto("Seleccione un autómata para ver su exportación.", 13, T.texto_3)
            return
        try:
            contenido = exportar(a, self.formato)
        except ErrorAutomata as exc:
            contenido = f"No se puede exportar: {exc}"
        self.vista_previa.content = ft.Column([
            ft.Row([pestanas([(f, f".{f}") for f in EXTENSIONES], self.formato, self._cambiar_formato),
                    ft.Container(expand=True),
                    boton("Descargar", lambda e: self.estado.page.run_task(self.exportar_actual, self.formato),
                          ft.Icons.DOWNLOAD_ROUNDED)], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            texto(f"Vista previa de «{a.nombre}»", 12.5, T.texto_3),
            ft.Container(
                ft.Column([ft.Text(contenido, font_family=FUENTE_MONO, size=12, color=T.texto_2, selectable=True)],
                          scroll=ft.ScrollMode.AUTO),
                height=360, padding=14, border_radius=10, bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde),
            ),
        ], spacing=10)

    # ------------------------------------------------------------------
    def vista(self) -> ft.Control:
        importar = tarjeta(ft.Column([
            texto("Abra un autómata en formato JFLAP (.jff) o en los formatos propios .json y .xml. "
                  "Las transiciones λ se reconocen por el símbolo vacío (<read/> en JFLAP).", 13, T.texto_2),
            ft.Row([boton("Importar archivo", self.importar, ft.Icons.UPLOAD_FILE),
                    boton("Cargar ejemplos", self.cargar_ejemplos, ft.Icons.AUTO_STORIES_OUTLINED, "secundario")],
                   spacing=10),
            self.verificacion,
        ], spacing=14), "Importar", ft.Icons.FILE_UPLOAD_OUTLINED)
        proyecto = tarjeta(ft.Column([
            texto("Guarde todos los autómatas de la sesión en un solo archivo y ábralo después.", 13, T.texto_2),
            ft.Row([boton("Guardar proyecto", self.guardar_proyecto, ft.Icons.SAVE_OUTLINED, "secundario"),
                    boton("Abrir proyecto", self.abrir_proyecto, ft.Icons.FOLDER_OPEN_OUTLINED, "secundario")],
                   spacing=10),
        ], spacing=14), "Proyecto", ft.Icons.WORK_OUTLINE)
        return ft.Column([
            titulo_pagina("Importación y exportación",
                          "Formatos .jff (JFLAP), .json y .xml, y proyectos con varios autómatas.",
                          ft.Icons.FOLDER_OPEN_ROUNDED, "Práctica 2"),
            ft.ResponsiveRow([
                ft.Container(ft.Column([importar, proyecto,
                                        tarjeta(self.biblioteca, "Autómatas de la sesión", ft.Icons.LIST)],
                                       spacing=16), col={"xs": 12, "lg": 6}),
                ft.Container(tarjeta(self.vista_previa, "Exportar el autómata seleccionado", ft.Icons.FILE_DOWNLOAD_OUTLINED),
                             col={"xs": 12, "lg": 6}),
            ], spacing=16, run_spacing=16),
        ], spacing=20)


def construir(estado: Estado) -> ft.Control:
    return PaginaArchivos(estado).vista()
