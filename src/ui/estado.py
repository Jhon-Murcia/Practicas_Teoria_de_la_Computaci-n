"""Estado compartido por todas las pantallas de la aplicación.

Guarda el historial de actividad, los valores que el usuario escribió en cada
pantalla (para conservarlos al navegar o cambiar de tema) y concentra las
operaciones que dependen de la plataforma: notificar, guardar y abrir archivos.
``FilePicker`` funciona igual en escritorio y en el navegador, por lo que la
aplicación servida desde el contenedor también puede exportar e importar.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import flet as ft

from core.automata import Automata
from ia.contexto import describir_automata
from ia.conversacion import Conversacion
from ui.tema import T


@dataclass
class Actividad:
    hora: str
    icono: Any
    texto: str
    color: str = ""


@dataclass
class Estado:
    page: ft.Page
    actividad: list[Actividad] = field(default_factory=list)
    memoria: dict[str, Any] = field(default_factory=dict)
    operaciones: int = 0
    ultimo_archivo: str = "—"
    navegar: Callable[[str], None] = lambda clave: None
    picker: Optional[ft.FilePicker] = None
    modulos: list[Any] = field(default_factory=list)
    automatas: list[Automata] = field(default_factory=list)
    indice: int = -1
    teclado: Optional[Callable[[Any], None]] = None
    ancho: float = 1440.0
    # Asistente de IA: la conversación sobrevive a la navegación; cada pantalla
    # registra en ``contexto_ia`` una función que describe lo que se ve.
    conversacion: Conversacion = field(default_factory=Conversacion)
    contexto_ia: Optional[Callable[[], str]] = None
    preguntar_ia: Callable[[str], None] = lambda pregunta: None
    modulo_actual: str = "inicio"

    def describir_pantalla(self) -> str:
        """Texto que se envía al asistente junto con cada pregunta."""
        partes = [f"Sección abierta: {self.modulo_actual}."]
        try:
            extra = self.contexto_ia() if self.contexto_ia else ""
        except Exception:
            extra = ""
        if extra:
            partes.append(extra)
        elif self.actual is not None:
            partes.append(describir_automata(self.actual))
        return "\n".join(partes)

    # ------------------------------------------------------------------
    # Biblioteca de autómatas de la sesión
    # ------------------------------------------------------------------
    @property
    def actual(self) -> Optional[Automata]:
        if 0 <= self.indice < len(self.automatas):
            return self.automatas[self.indice]
        return None

    def agregar_automata(self, a: Automata, seleccionar: bool = True) -> Automata:
        """Añade un autómata; si el nombre ya existe se numera para distinguirlo."""
        nombres = {x.nombre for x in self.automatas}
        base, k = a.nombre or "Autómata", 2
        while a.nombre in nombres:
            a.nombre = f"{base} ({k})"
            k += 1
        self.automatas.append(a)
        if seleccionar:
            self.indice = len(self.automatas) - 1
        self.registrar(f"Autómata «{a.nombre}» agregado ({a.tipo})", ft.Icons.ACCOUNT_TREE_OUTLINED)
        return a

    def seleccionar(self, indice: int) -> None:
        if 0 <= indice < len(self.automatas):
            self.indice = indice

    def eliminar_automata(self, indice: int) -> None:
        if 0 <= indice < len(self.automatas):
            quitado = self.automatas.pop(indice)
            self.registrar(f"Autómata «{quitado.nombre}» eliminado", ft.Icons.DELETE_OUTLINE)
            if self.indice >= len(self.automatas):
                self.indice = len(self.automatas) - 1

    # ------------------------------------------------------------------
    # Memoria por pantalla
    # ------------------------------------------------------------------
    def recordar(self, clave: str, valor: Any) -> None:
        self.memoria[clave] = valor

    def recuperar(self, clave: str, defecto: Any = None) -> Any:
        return self.memoria.get(clave, defecto)

    # ------------------------------------------------------------------
    # Actividad y notificaciones
    # ------------------------------------------------------------------
    def registrar(self, texto: str, icono: Any = ft.Icons.BOLT, color: str = "") -> None:
        self.operaciones += 1
        hora = _dt.datetime.now().strftime("%H:%M:%S")
        self.actividad.insert(0, Actividad(hora, icono, texto, color))
        del self.actividad[40:]

    def confirmar(self, titulo: str, mensaje: str, accion: Callable[[], None], etiqueta: str = "Eliminar") -> None:
        """Diálogo de confirmación antes de una acción destructiva."""
        def aceptar(e):
            self.page.pop_dialog()
            accion()

        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo, size=18, weight=ft.FontWeight.W_700),
            content=ft.Text(mensaje, color=T.texto_2),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.FilledButton(etiqueta, on_click=aceptar,
                                     style=ft.ButtonStyle(bgcolor=T.error, color="#FFFFFF"))],
            bgcolor=T.superficie,
            shape=ft.RoundedRectangleBorder(radius=16),
        ))

    def pedir_texto(self, titulo: str, etiqueta: str, accion: Callable[[str], Optional[str]], valor: str = "",
                    ayuda: str = "", insertar: tuple[str, ...] = ()) -> None:
        """Pide un texto; ``accion`` devuelve un mensaje de error o ``None``.

        ``insertar`` añade botones que escriben símbolos difíciles de teclear (λ).
        """
        campo = ft.TextField(label=etiqueta, value=valor, autofocus=True, helper=ayuda or None,
                             helper_max_lines=2, border_radius=10, focused_border_color=T.primario)

        def agregar(simbolo: str):
            actual = (campo.value or "").rstrip()
            campo.value = f"{actual}, {simbolo}" if actual else simbolo
            campo.update()

        botones = [ft.OutlinedButton(f"Insertar {s}", on_click=lambda e, s=s: agregar(s)) for s in insertar]

        def aceptar(e=None):
            error = accion(campo.value or "")
            if error:
                campo.error = error
                campo.update()
            else:
                self.page.pop_dialog()

        campo.on_submit = aceptar
        self.page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo, size=18, weight=ft.FontWeight.W_700),
            content=ft.Container(ft.Column([campo, ft.Row(botones, spacing=8)], tight=True, spacing=10),
                                 width=400),
            actions=[ft.TextButton("Cancelar", on_click=lambda e: self.page.pop_dialog()),
                     ft.FilledButton("Aceptar", on_click=aceptar,
                                     style=ft.ButtonStyle(bgcolor=T.primario, color="#FFFFFF"))],
            bgcolor=T.superficie,
            shape=ft.RoundedRectangleBorder(radius=16),
        ))

    def notificar(self, mensaje: str, tipo: str = "info") -> None:
        colores = {
            "info": (T.superficie_3, T.texto, ft.Icons.INFO_OUTLINE, T.acento),
            "exito": (T.superficie_3, T.texto, ft.Icons.CHECK_CIRCLE_OUTLINE, T.exito),
            "error": (T.superficie_3, T.texto, ft.Icons.ERROR_OUTLINE, T.error),
            "aviso": (T.superficie_3, T.texto, ft.Icons.WARNING_AMBER_ROUNDED, T.aviso),
        }
        fondo, texto, icono, acento = colores.get(tipo, colores["info"])
        barra = ft.SnackBar(
            content=ft.Row(
                [ft.Icon(icono, color=acento, size=20),
                 ft.Text(mensaje, color=texto, expand=True)],
                spacing=12,
            ),
            bgcolor=fondo,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=12),
            width=520,
            duration=ft.Duration(milliseconds=4200),
        )
        self.page.show_dialog(barra)

    # ------------------------------------------------------------------
    # Archivos
    # ------------------------------------------------------------------
    def _selector(self) -> ft.FilePicker:
        if self.picker is None:
            self.picker = ft.FilePicker()
        return self.picker

    async def guardar(self, nombre: str, contenido: str | bytes, extensiones: list[str] | None = None) -> bool:
        """Abre el diálogo de guardado (o descarga el archivo en el navegador)."""
        datos = contenido.encode("utf-8") if isinstance(contenido, str) else contenido
        try:
            ruta = await self._selector().save_file(
                dialog_title="Guardar archivo",
                file_name=nombre,
                file_type=ft.FilePickerFileType.CUSTOM if extensiones else ft.FilePickerFileType.ANY,
                allowed_extensions=extensiones,
                src_bytes=datos,
            )
        except Exception as exc:  # el diálogo puede no estar disponible
            self.notificar(f"No se pudo guardar el archivo: {exc}", "error")
            return False
        if self.page.web:
            # En el navegador el archivo se descarga directamente.
            self.ultimo_archivo = nombre
            self.registrar(f"Descargado {nombre}", ft.Icons.DOWNLOAD)
            self.notificar(f"Descarga iniciada: {nombre}", "exito")
            return True
        if not ruta:
            return False
        # En escritorio, FilePicker escribe src_bytes; si la plataforma no lo
        # hiciera, se escribe aquí para no depender de ese detalle.
        try:
            with open(ruta, "wb") as f:
                f.write(datos)
        except OSError as exc:
            self.notificar(f"No se pudo escribir {ruta}: {exc}", "error")
            return False
        self.ultimo_archivo = ruta
        self.registrar(f"Guardado {ruta}", ft.Icons.SAVE_ALT)
        self.notificar(f"Archivo guardado en {ruta}", "exito")
        return True

    async def abrir(self, extensiones: list[str] | None = None) -> tuple[str, bytes] | None:
        """Pide un archivo al usuario y devuelve ``(nombre, contenido)``."""
        try:
            archivos = await self._selector().pick_files(
                dialog_title="Abrir archivo",
                file_type=ft.FilePickerFileType.CUSTOM if extensiones else ft.FilePickerFileType.ANY,
                allowed_extensions=extensiones,
                with_data=True,
            )
        except Exception as exc:
            self.notificar(f"No se pudo abrir el selector de archivos: {exc}", "error")
            return None
        if not archivos:
            return None
        archivo = archivos[0]
        datos = archivo.bytes
        if datos is None and archivo.path:
            with open(archivo.path, "rb") as f:
                datos = f.read()
        if datos is None:
            self.notificar("El archivo seleccionado no tiene contenido legible.", "error")
            return None
        self.ultimo_archivo = archivo.name
        return archivo.name, datos
