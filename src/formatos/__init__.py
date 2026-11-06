"""Importación y exportación de autómatas en ``.jff``, ``.json`` y ``.xml``.

Convención para λ en los tres formatos: el símbolo leído es la cadena vacía
(``<read/>`` en JFLAP, ``"lee": ""`` en JSON y ``lee=""`` en XML). Al leer
también se aceptan ``λ``, ``lambda`` y ``ε`` en JSON y XML.
"""

from __future__ import annotations

import os

from core.automata import Automata
from formatos.jff import ErrorFormato, escribir_jff, leer_jff
from formatos.json_fmt import escribir_json, leer_json
from formatos.xml_fmt import escribir_xml, leer_xml

EXTENSIONES = ("jff", "json", "xml")

__all__ = ["ErrorFormato", "cargar", "exportar", "leer_jff", "escribir_jff", "leer_json", "escribir_json",
           "leer_xml", "escribir_xml", "EXTENSIONES"]


def _decodificar(datos: str | bytes) -> str:
    if isinstance(datos, str):
        return datos
    for codificacion in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    raise ErrorFormato("No se pudo decodificar el archivo.")


def cargar(nombre_archivo: str, datos: str | bytes, avisos: list[str] | None = None) -> Automata:
    """Lee un autómata según la extensión del archivo."""
    base, ext = os.path.splitext(os.path.basename(nombre_archivo))
    ext = ext.lower().lstrip(".")
    # Los XML se leen desde bytes para respetar la codificación que declaren.
    crudo = datos if isinstance(datos, bytes) else datos.encode("utf-8")
    if ext == "jff":
        return leer_jff(crudo, base, avisos)
    if ext == "json":
        return leer_json(_decodificar(datos), base)
    if ext == "xml":
        return leer_xml(crudo, base)
    raise ErrorFormato(f"Extensión no admitida: .{ext}. Use .jff, .json o .xml.")


def exportar(a: Automata, formato: str) -> str:
    formato = formato.lower().lstrip(".")
    if formato == "jff":
        return escribir_jff(a)
    if formato == "json":
        return escribir_json(a)
    if formato == "xml":
        return escribir_xml(a)
    raise ErrorFormato(f"Formato no admitido: {formato}.")


def leer_archivo(ruta: str, avisos: list[str] | None = None) -> Automata:
    with open(ruta, "rb") as f:
        return cargar(ruta, f.read(), avisos)


def guardar_archivo(a: Automata, ruta: str) -> None:
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(exportar(a, os.path.splitext(ruta)[1]))
