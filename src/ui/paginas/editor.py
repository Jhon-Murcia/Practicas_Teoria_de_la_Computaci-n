"""Editor de autómatas: lienzo visual, definición formal y tabla de transiciones."""

from __future__ import annotations

from typing import Optional

import flet as ft

from core import ejemplos
from core.automata import LAMBDA, Automata, ErrorAutomata, leer_simbolo, mostrar_simbolo
from core.disposicion import disponer
from ui.componentes.comunes import (aviso, boton, boton_icono, campo, chip, pestanas, refrescar, texto)
from ui.componentes.lienzo import Lienzo, Seleccion
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO, RADIO_CHICO, T, alfa

HERRAMIENTAS = [
    ("mover", ft.Icons.NEAR_ME_OUTLINED, "Seleccionar y mover"),
    ("estado", ft.Icons.ADD_CIRCLE_OUTLINE, "Agregar estado: clic en el lienzo"),
    ("transicion", ft.Icons.ARROW_RIGHT_ALT, "Agregar transición: origen y luego destino"),
    ("eliminar", ft.Icons.DELETE_OUTLINE, "Eliminar estado o transición"),
]

AYUDA_MODO = {
    "mover": "Arrastre los estados para moverlos y el fondo para desplazar la vista. Rueda: zoom.",
    "estado": "Haga clic en un espacio vacío para crear un estado.",
    "transicion": "Haga clic en el estado de origen y después en el de destino.",
    "eliminar": "Haga clic en un estado o en la etiqueta de una transición para eliminarlo.",
}

COLOR_TIPO = {"AFD": "acento", "AFND": "primario", "AFND-λ": "lambda_"}


def color_tipo(tipo: str) -> str:
    return getattr(T, COLOR_TIPO.get(tipo, "primario"))


def parsear_simbolos(texto: str) -> list[str]:
    """``"a, b, λ"`` → ``["a", "b", ""]``."""
    piezas = [p for p in texto.replace(";", ",").split(",")]
    simbolos = []
    for p in piezas:
        if not p.strip() and len(piezas) > 1:
            continue
        s = leer_simbolo(p)
        if s not in simbolos:
            simbolos.append(s)
    return simbolos


class PaginaEditor:
    def __init__(self, estado: Estado):
        self.estado = estado
        if estado.actual is None:
            estado.agregar_automata(ejemplos.termina_en_ab())
        self.pestana = estado.recuperar("editor.pestana", "propiedades")
        self.deshacer: list[Automata] = []
        self.rehacer: list[Automata] = []
        self.lienzo = Lienzo(estado.actual, editable=True, al_cambiar=self._al_cambiar,
                             al_seleccionar=self._al_seleccionar, al_nueva_transicion=self._nueva_transicion,
                             al_eliminar=self._eliminar, al_antes_de_cambiar=self._guardar_historial)
        self.cabecera = ft.Container()
        self.barra = ft.Container()
        self.panel = ft.Column(spacing=14, scroll=ft.ScrollMode.AUTO, expand=True,
                               horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        self.selector_pestana = ft.Container()
        estado.teclado = self._teclado
        self._construir_todo()

    @property
    def a(self) -> Automata:
        return self.estado.actual

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------
    def _guardar_historial(self) -> None:
        self.deshacer.append(self.a.copia())
        del self.deshacer[:-60]
        self.rehacer.clear()

    def _restaurar(self, desde: list[Automata], hacia: list[Automata]) -> None:
        if not desde:
            return
        hacia.append(self.a.copia())
        previo = desde.pop()
        self.estado.automatas[self.estado.indice] = previo
        self.lienzo.usar(previo, ajustar=False)
        self._al_cambiar()

    def deshacer_cambio(self, e=None) -> None:
        self._restaurar(self.deshacer, self.rehacer)

    def rehacer_cambio(self, e=None) -> None:
        self._restaurar(self.rehacer, self.deshacer)

    def _teclado(self, e) -> None:
        # Sólo combinaciones con Ctrl: las teclas sueltas llegan aquí aunque el
        # foco esté en un campo de texto, y borrarían o cambiarían de herramienta.
        tecla = (e.key or "").lower()
        if e.ctrl and tecla == "z":
            self.deshacer_cambio()
        elif e.ctrl and tecla == "y":
            self.rehacer_cambio()

    # ------------------------------------------------------------------
    # Acciones sobre el modelo
    # ------------------------------------------------------------------
    def _al_cambiar(self) -> None:
        self._construir_cabecera()
        self._construir_panel()
        refrescar(self.cabecera, self.panel)

    def _al_seleccionar(self, sel: Seleccion) -> None:
        if sel is not None and self.pestana != "propiedades":
            self.pestana = "propiedades"
            self._construir_pestanas()
            refrescar(self.selector_pestana)
        self._construir_panel()
        refrescar(self.panel)

    def _modificar(self, accion, exito: str = "") -> bool:
        self._guardar_historial()
        try:
            accion()
        except ErrorAutomata as exc:
            self.deshacer.pop()
            self.estado.notificar(str(exc), "error")
            return False
        self.lienzo.dibujar()
        self._al_cambiar()
        if exito:
            self.estado.notificar(exito, "exito")
        return True

    def _nueva_transicion(self, origen: str, destino: str) -> None:
        def aplicar(texto_simbolos: str) -> Optional[str]:
            simbolos = parsear_simbolos(texto_simbolos)
            if not simbolos:
                return "Escriba al menos un símbolo (λ para la transición vacía)."
            ok = self._modificar(lambda: [self.a.agregar_transicion(origen, s, destino) for s in simbolos])
            if ok:
                self.lienzo.seleccionar(("arista", (origen, destino)))
            return None if ok else "No se pudo agregar la transición."

        self.estado.pedir_texto(f"Transición {origen} → {destino}", "Símbolos", aplicar,
                                ayuda="Separe varios símbolos con comas. λ (o «lambda») es la transición vacía.",
                                insertar=("λ",))

    def _eliminar(self, sel: Seleccion) -> None:
        if sel is None:
            return
        tipo, valor = sel
        if tipo == "estado":
            q = str(valor)
            n = sum(1 for o, _, d in self.a.lista_transiciones() if q in (o, d))
            def borrar():
                if self._modificar(lambda: self.a.eliminar_estado(q)):
                    self.lienzo.seleccionar(None)
            self.estado.confirmar("Eliminar estado", f"Se eliminará el estado {q} y sus {n} transiciones.", borrar)
        else:
            o, d = valor  # type: ignore[misc]
            simbolos = self.a.agrupar_aristas().get((o, d), [])
            if self._modificar(lambda: [self.a.eliminar_transicion(o, s, d) for s in simbolos]):
                self.lienzo.seleccionar(None)

    def cambiar_modo(self, modo: str) -> None:
        self.lienzo.cambiar_modo(modo)
        self._construir_barra()
        refrescar(self.barra)

    def ordenar(self, e=None) -> None:
        self._guardar_historial()
        self.a.posiciones = disponer(self.a)
        self.lienzo.ajustar()

    def seleccionar_automata(self, indice: int) -> None:
        self.estado.seleccionar(indice)
        self.deshacer.clear()
        self.rehacer.clear()
        self.lienzo.usar(self.estado.actual)
        self._al_cambiar()

    def nuevo(self, e=None) -> None:
        def crear(nombre: str) -> Optional[str]:
            if not nombre.strip():
                return "Escriba un nombre."
            a = Automata(nombre=nombre.strip())
            self.estado.agregar_automata(a)
            self.seleccionar_automata(self.estado.indice)
            self.cambiar_modo("estado")
            return None
        self.estado.pedir_texto("Nuevo autómata", "Nombre", crear, f"Autómata {len(self.estado.automatas) + 1}")

    def cargar_ejemplo(self, titulo: str) -> None:
        self.estado.agregar_automata(ejemplos.EJEMPLOS[titulo]())
        self.seleccionar_automata(self.estado.indice)
        self.estado.notificar(f"Ejemplo cargado: {titulo}", "exito")

    def duplicar(self, e=None) -> None:
        self.estado.agregar_automata(self.a.copia(f"{self.a.nombre} (copia)"))
        self.seleccionar_automata(self.estado.indice)

    def eliminar_automata(self, e=None) -> None:
        def borrar():
            self.estado.eliminar_automata(self.estado.indice)
            if self.estado.actual is None:
                self.estado.agregar_automata(Automata(nombre="Autómata 1"))
            self.seleccionar_automata(self.estado.indice)
        self.estado.confirmar("Eliminar autómata", f"Se quitará «{self.a.nombre}» de la sesión.", borrar)

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def _construir_todo(self) -> None:
        self._construir_cabecera()
        self._construir_barra()
        self._construir_pestanas()
        self._construir_panel()

    def _construir_cabecera(self) -> None:
        a = self.a
        opciones = [ft.DropdownOption(key=str(i), text=x.nombre) for i, x in enumerate(self.estado.automatas)]
        selector = ft.Dropdown(
            value=str(self.estado.indice), options=opciones, width=290, dense=True,
            on_select=lambda e: self.seleccionar_automata(int(e.control.value)),
            border_radius=RADIO_CHICO, border_color=T.borde, focused_border_color=T.primario,
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_600, color=T.texto),
            leading_icon=ft.Icons.ACCOUNT_TREE_OUTLINED,
        )
        menu_ejemplos = ft.PopupMenuButton(
            content=ft.Container(ft.Row([ft.Icon(ft.Icons.AUTO_STORIES_OUTLINED, size=18, color=T.primario),
                                         texto("Ejemplos", 13.5, peso=ft.FontWeight.W_600),
                                         ft.Icon(ft.Icons.EXPAND_MORE, size=18, color=T.texto_2)],
                                        spacing=6, tight=True),
                                 padding=ft.Padding.symmetric(horizontal=14, vertical=11),
                                 border_radius=RADIO_CHICO, border=ft.Border.all(1, T.borde), bgcolor=T.superficie_2),
            items=[ft.PopupMenuItem(content=ft.Text(t), on_click=lambda e, t=t: self.cargar_ejemplo(t))
                   for t in ejemplos.EJEMPLOS],
            tooltip="Cargar un autómata de ejemplo",
        )
        tipo = a.tipo
        self.cabecera.content = ft.Row(
            [
                selector,
                chip(tipo, color_tipo(tipo)),
                chip(f"|Q| = {len(a.estados)}", T.texto_2, mono=True),
                chip(f"|Σ| = {len(a.alfabeto)}", T.texto_2, mono=True),
                chip(f"|δ| = {len(a.lista_transiciones())}", T.texto_2, mono=True),
                ft.Container(expand=True),
                boton("Nuevo", self.nuevo, ft.Icons.ADD, "secundario"),
                menu_ejemplos,
                boton_icono(ft.Icons.CONTENT_COPY, self.duplicar, "Duplicar autómata"),
                boton_icono(ft.Icons.FOLDER_OPEN_OUTLINED, lambda e: self.estado.navegar("archivos"),
                            "Importar y exportar (.jff, .json, .xml)"),
                boton_icono(ft.Icons.DELETE_FOREVER_OUTLINED, self.eliminar_automata, "Quitar autómata de la sesión",
                            T.error),
            ],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _construir_barra(self) -> None:
        botones = []
        for modo, icono, ayuda in HERRAMIENTAS:
            activo = self.lienzo.modo == modo
            botones.append(ft.Container(
                ft.Icon(icono, size=20, color="#FFFFFF" if activo else T.texto_2),
                width=40, height=36, border_radius=8, alignment=ft.Alignment.CENTER,
                bgcolor=T.primario if activo else None, tooltip=ayuda,
                on_click=lambda e, m=modo: self.cambiar_modo(m),
            ))
        self.barra.content = ft.Row(
            [
                ft.Container(ft.Row(botones, spacing=2, tight=True), padding=3, border_radius=11,
                             bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde)),
                ft.Container(ft.Row([boton_icono(ft.Icons.UNDO, self.deshacer_cambio, "Deshacer (Ctrl+Z)"),
                                     boton_icono(ft.Icons.REDO, self.rehacer_cambio, "Rehacer (Ctrl+Y)")],
                                    spacing=0, tight=True),
                             border_radius=11, bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde)),
                ft.Container(ft.Row([boton_icono(ft.Icons.ZOOM_OUT, lambda e: self.lienzo.acercar(1 / 1.2), "Alejar"),
                                     boton_icono(ft.Icons.ZOOM_IN, lambda e: self.lienzo.acercar(1.2), "Acercar"),
                                     boton_icono(ft.Icons.FIT_SCREEN, lambda e: self.lienzo.ajustar(), "Ajustar a la vista"),
                                     boton_icono(ft.Icons.AUTO_FIX_HIGH, self.ordenar, "Ordenar automáticamente")],
                                    spacing=0, tight=True),
                             border_radius=11, bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde)),
                ft.Row([ft.Icon(ft.Icons.TIPS_AND_UPDATES_OUTLINED, size=16, color=T.texto_3),
                        texto(AYUDA_MODO[self.lienzo.modo], 12.5, T.texto_3, expand=True)],
                       spacing=6, expand=True),
            ],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _cambiar_pestana(self, clave: str) -> None:
        self.pestana = clave
        self.estado.recordar("editor.pestana", clave)
        self._construir_pestanas()
        self._construir_panel()
        refrescar(self.selector_pestana, self.panel)

    def _construir_pestanas(self) -> None:
        self.selector_pestana.content = pestanas(
            [("propiedades", "Propiedades"), ("definicion", "Definición"), ("tabla", "Tabla δ")],
            self.pestana, self._cambiar_pestana)

    def _construir_panel(self) -> None:
        if self.pestana == "definicion":
            self.panel.controls = self._panel_definicion()
        elif self.pestana == "tabla":
            self.panel.controls = self._panel_tabla()
        else:
            self.panel.controls = self._panel_propiedades()

    # ------------------------------------------------------------------
    # Panel: propiedades
    # ------------------------------------------------------------------
    def _seccion(self, titulo: str, *controles: ft.Control) -> ft.Control:
        return ft.Column([texto(titulo.upper(), 10.5, T.texto_3, peso=ft.FontWeight.W_700), *controles], spacing=8)

    def _panel_propiedades(self) -> list[ft.Control]:
        sel = self.lienzo.seleccion
        if sel and sel[0] == "estado" and sel[1] in self.a.estados:
            return self._propiedades_estado(str(sel[1]))
        if sel and sel[0] == "arista":
            o, d = sel[1]  # type: ignore[misc]
            if (o, d) in self.a.agrupar_aristas():
                return self._propiedades_arista(o, d)
        return self._propiedades_automata()

    def _propiedades_estado(self, q: str) -> list[ft.Control]:
        nombre = campo("Nombre del estado", q, mono=True)

        def renombrar(e=None):
            nuevo = (nombre.value or "").strip()
            if nuevo and nuevo != q and self._modificar(lambda: self.a.renombrar_estado(q, nuevo)):
                self.lienzo.seleccion = ("estado", nuevo)
                self.lienzo.dibujar()
                self._construir_panel()
                refrescar(self.panel)

        nombre.on_submit = renombrar
        nombre.on_blur = renombrar

        def marcar_inicial(e):
            self._modificar(lambda: setattr(self.a, "inicial", q))

        def marcar_aceptacion(e):
            self._modificar(lambda: self.a.alternar_aceptacion(q))

        salientes = [(s, d) for o, s, d in self.a.lista_transiciones() if o == q]
        entrantes = [(o, s) for o, s, d in self.a.lista_transiciones() if d == q]
        filas = [ft.Row([chip(mostrar_simbolo(s), T.lambda_ if s == LAMBDA else T.acento, mono=True),
                         ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=T.texto_3), texto(d, 13, mono=True)],
                        spacing=8) for s, d in salientes] or [texto("Sin transiciones salientes.", 12.5, T.texto_3)]
        return [
            ft.Row([ft.Icon(ft.Icons.CIRCLE_OUTLINED, color=T.primario, size=18),
                    texto(f"Estado {q}", 16, peso=ft.FontWeight.W_700)], spacing=8),
            nombre,
            ft.Switch(label="Estado inicial", value=self.a.inicial == q, on_change=marcar_inicial,
                      active_color=T.primario, disabled=self.a.inicial == q),
            ft.Switch(label="Estado de aceptación", value=q in self.a.aceptacion, on_change=marcar_aceptacion,
                      active_color=T.primario),
            self._seccion(f"Transiciones salientes ({len(salientes)})", *filas),
            self._seccion("Entrantes", texto(", ".join(f"{o} --{mostrar_simbolo(s)}→" for o, s in entrantes) or "—",
                                             12.5, T.texto_2, mono=True)),
            boton("Eliminar estado", lambda e: self._eliminar(("estado", q)), ft.Icons.DELETE_OUTLINE, "secundario"),
        ]

    def _propiedades_arista(self, o: str, d: str) -> list[ft.Control]:
        simbolos = self.a.agrupar_aristas()[(o, d)]
        entrada = campo("Símbolos", ", ".join(mostrar_simbolo(s) for s in simbolos),
                        "Separados por comas; λ para la transición vacía")

        def aplicar(e=None):
            nuevos = parsear_simbolos(entrada.value or "")
            if not nuevos:
                self.estado.notificar("Para quitar la transición use «Eliminar».", "aviso")
                return
            def cambiar():
                for s in simbolos:
                    self.a.eliminar_transicion(o, s, d)
                for s in nuevos:
                    self.a.agregar_transicion(o, s, d)
            self._modificar(cambiar, "Transición actualizada")

        entrada.on_submit = aplicar
        return [
            ft.Row([ft.Icon(ft.Icons.ARROW_RIGHT_ALT, color=T.primario, size=20),
                    texto(f"{o}  →  {d}", 16, peso=ft.FontWeight.W_700, mono=True)], spacing=8),
            entrada,
            ft.Row([boton("Aplicar", aplicar, ft.Icons.CHECK), boton("Eliminar", lambda e: self._eliminar(("arista", (o, d))),
                                                                    ft.Icons.DELETE_OUTLINE, "secundario")], spacing=10),
            self._seccion("Función de transición",
                          *[texto(f"δ({o}, {mostrar_simbolo(s)}) ∋ {d}", 13, T.texto_2, mono=True) for s in simbolos]),
        ]

    def _propiedades_automata(self) -> list[ft.Control]:
        a = self.a
        nombre = campo("Nombre del autómata", a.nombre, mono=False)

        def renombrar(e=None):
            if (nombre.value or "").strip() and nombre.value.strip() != a.nombre:
                a.nombre = nombre.value.strip()
                self._construir_cabecera()
                refrescar(self.cabecera)

        nombre.on_submit = renombrar
        nombre.on_blur = renombrar
        descripcion = campo("Descripción", a.descripcion, mono=False, multiline=True, min_lines=2, max_lines=4)

        def describir(e=None):
            a.descripcion = descripcion.value or ""

        descripcion.on_blur = describir
        conflictos = a.conflictos_determinismo()
        diagnostico: list[ft.Control] = []
        if conflictos:
            diagnostico.append(aviso(f"No es determinista ({len(conflictos)} conflicto"
                                     f"{'s' if len(conflictos) != 1 else ''}):", "info", ft.Icons.CALL_SPLIT))
            diagnostico += [texto(f"• {m}", 12.5, T.texto_2, mono=True) for _, _, m in conflictos[:8]]
        else:
            diagnostico.append(aviso("Es determinista: ningún par (q, a) tiene más de un destino ni hay λ.", "exito"))
        if a.estados and a.alfabeto and not a.es_completo():
            diagnostico.append(aviso(f"δ es parcial: faltan {len(a.faltantes())} pares (q, a). La ausencia de "
                                     "transición equivale a rechazar.", "aviso"))
        inacc = a.inaccesibles()
        if inacc:
            diagnostico.append(aviso(f"Estados inaccesibles desde {a.inicial}: {', '.join(inacc)}", "aviso"))
        for err in a.validar():
            diagnostico.append(aviso(err, "error"))
        return [
            nombre,
            descripcion,
            self._seccion("Diagnóstico", *diagnostico),
            self._seccion("Ayuda",
                          texto("Seleccione un estado o una transición en el lienzo para editar sus propiedades. "
                                "Ctrl+Z deshace y Ctrl+Y rehace.",
                                12.5, T.texto_3)),
        ]

    # ------------------------------------------------------------------
    # Panel: definición formal
    # ------------------------------------------------------------------
    def _panel_definicion(self) -> list[ft.Control]:
        a = self.a
        sigma = campo("Σ — alfabeto", ", ".join(a.alfabeto), "Símbolos separados por comas")

        def aplicar_sigma(e=None):
            nuevos = [s for s in parsear_simbolos(sigma.value or "") if s != LAMBDA]
            usados = {s for (_, s) in a.transiciones if s != LAMBDA}
            faltan = sorted(usados - set(nuevos))
            if faltan:
                self.estado.notificar(f"No se puede quitar {', '.join(faltan)}: hay transiciones que lo usan.", "error")
                return
            self._modificar(lambda: setattr(a, "alfabeto", nuevos), "Alfabeto actualizado")

        sigma.on_submit = aplicar_sigma
        nuevo_estado = campo("Agregar estado a Q", "", "Escriba el nombre y pulse Enter")

        def agregar(e=None):
            n = (nuevo_estado.value or "").strip()
            if n and self._modificar(lambda: self.a.agregar_estado(n)):
                self.lienzo.ajustar()

        nuevo_estado.on_submit = agregar
        inicial = ft.Dropdown(
            label="q0 — estado inicial", value=a.inicial,
            options=[ft.DropdownOption(key=q, text=q) for q in a.estados], dense=True,
            on_select=lambda e: self._modificar(lambda: setattr(a, "inicial", e.control.value)),
            border_radius=RADIO_CHICO, border_color=T.borde, expand=True,
        )
        finales = ft.Row(
            [ft.Container(chip(q, T.exito if q in a.aceptacion else T.texto_3, mono=True,
                               icono=ft.Icons.CHECK if q in a.aceptacion else None),
                          on_click=lambda e, q=q: self._modificar(lambda: a.alternar_aceptacion(q)),
                          tooltip="Clic para marcar o desmarcar")
             for q in a.estados], wrap=True, spacing=6, run_spacing=6)
        estados = ft.Row([chip(q, T.primario, mono=True) for q in a.estados], wrap=True, spacing=6, run_spacing=6)
        quint = a.quintupla()
        return [
            texto("M = (Q, Σ, δ, q0, F)", 16, peso=ft.FontWeight.W_700, mono=True),
            self._seccion("Q — estados", estados, nuevo_estado),
            self._seccion("Σ — alfabeto", sigma, boton("Aplicar Σ", aplicar_sigma, ft.Icons.CHECK, "secundario")),
            self._seccion("q0 — estado inicial", ft.Row([inicial])),
            self._seccion("F — estados de aceptación", finales),
            self._seccion("Quíntupla", *[ft.Row([texto(k, 13, T.primario, mono=True, peso=ft.FontWeight.W_700, width=26),
                                                  texto(v, 12.5, T.texto_2, mono=True, selectable=True, expand=True)],
                                                 vertical_alignment=ft.CrossAxisAlignment.START)
                                          for k, v in quint.items()]),
        ]

    # ------------------------------------------------------------------
    # Panel: tabla de transiciones editable
    # ------------------------------------------------------------------
    def _panel_tabla(self) -> list[ft.Control]:
        a = self.a
        if not a.estados:
            return [aviso("Agregue estados para definir la función de transición.", "info")]
        columnas = list(a.alfabeto) + [LAMBDA]
        ancho_estado, ancho_celda = 78, 84

        def encabezado(t: str, ancho: int, color=None) -> ft.Control:
            return ft.Container(texto(t, 12.5, color or T.texto_2, mono=True, peso=ft.FontWeight.W_700),
                                width=ancho, padding=ft.Padding.symmetric(horizontal=6, vertical=8))

        filas: list[ft.Control] = [ft.Row(
            [encabezado("δ", ancho_estado)] + [encabezado(mostrar_simbolo(s), ancho_celda,
                                                          T.lambda_ if s == LAMBDA else T.primario)
                                               for s in columnas], spacing=4)]
        for q in a.estados:
            marca = ("→" if q == a.inicial else "") + ("*" if q in a.aceptacion else "")
            celdas: list[ft.Control] = [ft.Container(
                texto(f"{marca}{q}", 13, T.texto, mono=True, peso=ft.FontWeight.W_600, no_wrap=True),
                width=ancho_estado, padding=ft.Padding.symmetric(horizontal=6))]
            for s in columnas:
                valor = ", ".join(sorted(a.destinos(q, s), key=a._orden))
                celda = ft.TextField(
                    value=valor, width=ancho_celda, dense=True, text_size=12.5,
                    text_style=ft.TextStyle(font_family=FUENTE_MONO, color=T.texto),
                    border_radius=8, border_color=T.borde, focused_border_color=T.primario,
                    content_padding=ft.Padding.symmetric(horizontal=8, vertical=8),
                    hint_text="∅", data=(q, s),
                )

                def aplicar(e, q=q, s=s):
                    destinos = [x.strip() for x in (e.control.value or "").split(",") if x.strip()]
                    if set(destinos) == a.destinos(q, s):
                        return
                    if not self._modificar(lambda: a.definir_transiciones(q, s, destinos)):
                        e.control.value = ", ".join(sorted(a.destinos(q, s)))
                        refrescar(e.control)

                celda.on_blur = aplicar
                celda.on_submit = aplicar
                celdas.append(celda)
            filas.append(ft.Row(celdas, spacing=4))
        return [
            texto("Escriba en cada celda los destinos separados por comas y pulse Enter. "
                  "→ marca el estado inicial y * los de aceptación.", 12.5, T.texto_3),
            ft.Row([ft.Column(filas, spacing=4)], scroll=ft.ScrollMode.AUTO),
        ]

    # ------------------------------------------------------------------
    def vista(self) -> ft.Control:
        estrecho = self.estado.ancho < 1100
        panel_derecho = ft.Container(
            ft.Column([self.selector_pestana, self.panel], spacing=14, expand=True),
            width=None if estrecho else (310 if self.estado.ancho < 1380 else 380),
            height=420 if estrecho else None,
            padding=18, bgcolor=T.superficie, border_radius=RADIO, border=ft.Border.all(1, T.borde),
        )
        if estrecho:
            # En pantallas estrechas el panel va debajo del lienzo.
            cuerpo = ft.Column([ft.Container(self.lienzo.control, height=460), panel_derecho], spacing=16,
                               scroll=ft.ScrollMode.AUTO, expand=True)
        else:
            cuerpo = ft.Row([ft.Container(self.lienzo.control, expand=True), panel_derecho], spacing=16,
                            expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        return ft.Column([self.cabecera, self.barra, cuerpo], spacing=14, expand=True)


def construir(estado: Estado) -> ft.Control:
    return PaginaEditor(estado).vista()
