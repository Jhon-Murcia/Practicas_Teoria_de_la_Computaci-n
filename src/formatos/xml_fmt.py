"""Formato ``.xml`` propio (esquema del Anexo 3 de la Práctica 2).

::

    <automata tipo="AFND-lambda" nombre="Ejemplo">
      <alfabeto><simbolo>a</simbolo><simbolo>b</simbolo></alfabeto>
      <estados>
        <estado nombre="q0" inicial="true" x="80" y="120"/>
        <estado nombre="q1" aceptacion="true"/>
      </estados>
      <transiciones>
        <transicion desde="q0" lee="a" hacia="q1"/>
        <transicion desde="q0" lee="" hacia="q1"/>        ← λ: lee vacío
      </transiciones>
    </automata>

Es el mismo contenido que el ``.json``: las cinco componentes de la quíntupla.
Si δ(q, a) tiene varios destinos se escribe un ``<transicion>`` por destino.
Las coordenadas ``x`` e ``y`` son opcionales.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from core.automata import Automata, leer_simbolo
from formatos.jff import ErrorFormato
from formatos.json_fmt import TIPOS_ARCHIVO


def escribir_xml(a: Automata) -> str:
    a.validar(estricto=True)
    raiz = ET.Element("automata", tipo=TIPOS_ARCHIVO[a.tipo], nombre=a.nombre)
    if a.descripcion:
        ET.SubElement(raiz, "descripcion").text = a.descripcion
    alfabeto = ET.SubElement(raiz, "alfabeto")
    for s in a.alfabeto:
        ET.SubElement(alfabeto, "simbolo").text = s
    estados = ET.SubElement(raiz, "estados")
    for q in a.estados:
        atributos = {"nombre": q}
        if q == a.inicial:
            atributos["inicial"] = "true"
        if q in a.aceptacion:
            atributos["aceptacion"] = "true"
        if q in a.posiciones:
            x, y = a.posiciones[q]
            atributos["x"], atributos["y"] = f"{x:.1f}", f"{y:.1f}"
        ET.SubElement(estados, "estado", atributos)
    transiciones = ET.SubElement(raiz, "transiciones")
    for q, s, d in a.lista_transiciones():
        ET.SubElement(transiciones, "transicion", desde=q, lee=s, hacia=d)
    ET.indent(raiz, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(raiz, encoding="unicode") + "\n"


def _verdadero(valor: str | None) -> bool:
    return (valor or "").strip().lower() in ("true", "1", "si", "sí", "yes")


def leer_xml(texto: str | bytes, nombre: str = "Autómata") -> Automata:
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError as exc:
        raise ErrorFormato(f"El archivo .xml no es válido: {exc}") from exc
    if raiz.tag == "structure":
        raise ErrorFormato("Este archivo tiene la estructura de JFLAP; ábralo con extensión .jff.")
    if raiz.tag != "automata":
        raise ErrorFormato(f"Se esperaba el elemento raíz <automata> y se encontró <{raiz.tag}>.")
    a = Automata(nombre=raiz.get("nombre") or nombre, descripcion=(raiz.findtext("descripcion") or "").strip())
    nodo_estados = raiz.find("estados")
    if nodo_estados is None:
        raise ErrorFormato("Falta el elemento <estados>.")
    for e in nodo_estados.findall("estado"):
        q = e.get("nombre")
        if not q:
            raise ErrorFormato("Un <estado> no tiene atributo nombre.")
        a.agregar_estado(q)
        if _verdadero(e.get("inicial")):
            a.inicial = q
        if _verdadero(e.get("aceptacion")):
            a.aceptacion.add(q)
        if e.get("x") is not None and e.get("y") is not None:
            try:
                a.posiciones[q] = (float(e.get("x")), float(e.get("y")))
            except ValueError:
                pass
    if not any(_verdadero(e.get("inicial")) for e in nodo_estados.findall("estado")):
        raise ErrorFormato("Ningún <estado> tiene inicial=\"true\".")
    nodo_alfabeto = raiz.find("alfabeto")
    if nodo_alfabeto is not None:
        for s in nodo_alfabeto.findall("simbolo"):
            if s.text and s.text.strip():
                a.agregar_simbolo(s.text.strip())
    nodo_trans = raiz.find("transiciones")
    for t in (nodo_trans.findall("transicion") if nodo_trans is not None else []):
        desde, hacia = t.get("desde"), t.get("hacia")
        if desde is None or hacia is None:
            raise ErrorFormato("Una <transicion> no tiene «desde» o «hacia».")
        for d in hacia.split(","):
            a.agregar_transicion(desde, leer_simbolo(t.get("lee") or ""), d.strip())
    a.validar(estricto=True)
    return a
