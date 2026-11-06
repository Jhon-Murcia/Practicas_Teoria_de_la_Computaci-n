"""Controles compartidos por las pantallas que trabajan sobre autómatas."""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from core.automata import Automata
from formatos import exportar
from ui.componentes.comunes import boton, chip, texto
from ui.estado import Estado
from ui.tema import RADIO_CHICO, T


def selector_automata(estado: Estado, indice: int, al_cambiar: Callable[[int], None], etiqueta: str = "Autómata",
                      ancho: int = 340) -> ft.Dropdown:
    return ft.Dropdown(
        value=str(indice) if 0 <= indice < len(estado.automatas) else None,
        options=[ft.DropdownOption(key=str(i), text=f"{a.nombre}  ·  {a.tipo}") for i, a in enumerate(estado.automatas)],
        label=etiqueta, width=ancho, dense=True, border_radius=RADIO_CHICO, border_color=T.borde,
        on_select=lambda e: al_cambiar(int(e.control.value)),
    )


def resumen_automata(a: Automata, etiqueta: str = "") -> ft.Control:
    return ft.Row([
        *( [texto(etiqueta, 13, T.texto_2, peso=ft.FontWeight.W_600)] if etiqueta else []),
        chip(a.tipo, T.acento if a.tipo == "AFD" else (T.lambda_ if a.tipo == "AFND-λ" else T.primario)),
        chip(f"|Q| = {len(a.estados)}", T.texto_2, mono=True),
        chip(f"|F| = {len(a.aceptacion)}", T.texto_2, mono=True),
        chip(f"|δ| = {len(a.lista_transiciones())}", T.texto_2, mono=True),
    ], spacing=8, wrap=True)


def acciones_resultado(estado: Estado, obtener: Callable[[], Optional[Automata]], nombre: str = "") -> ft.Control:
    """Botones para llevar un autómata resultante a la sesión, al editor o a un archivo."""

    def agregar(e=None, abrir: bool = False):
        a = obtener()
        if a is None:
            estado.notificar("Primero ejecute el algoritmo.", "aviso")
            return
        copia = a.copia(nombre or a.nombre)
        estado.agregar_automata(copia)
        estado.notificar(f"«{copia.nombre}» agregado a la sesión.", "exito")
        if abrir:
            estado.navegar("editor")

    async def descargar(e=None):
        a = obtener()
        if a is None:
            estado.notificar("Primero ejecute el algoritmo.", "aviso")
            return
        base = "".join(c if c.isalnum() or c in "-_" else "_" for c in (nombre or a.nombre)).strip("_") or "automata"
        await estado.guardar(f"{base}.jff", exportar(a, "jff"), ["jff"])

    return ft.Row([
        boton("Agregar a la sesión", agregar, ft.Icons.LIBRARY_ADD_OUTLINED, "secundario"),
        boton("Abrir en el editor", lambda e: agregar(abrir=True), ft.Icons.EDIT_OUTLINED, "secundario"),
        boton("Exportar .jff", descargar, ft.Icons.DOWNLOAD_ROUNDED, "fantasma"),
    ], spacing=8, wrap=True)
