"""Lectura y escritura del formato nativo de JFLAP (``.jff``).

Estructura (JFLAP 7)::

    <structure>
      <type>fa</type>
      <automaton>
        <state id="0" name="q0"><x>80.0</x><y>120.0</y><initial/></state>
        <state id="1" name="q1"><x>240.0</x><y>120.0</y><final/></state>
        <transition><from>0</from><to>1</to><read>a</read></transition>
        <transition><from>0</from><to>1</to><read/></transition>   ← λ
      </automaton>
    </structure>

* Las transiciones se refieren a los estados por ``id``; el nombre visible es el
  atributo ``name`` (si falta se usa ``q<id>``).
* ``<read/>`` vacío (o ausente) es una transición λ.
* JFLAP no guarda el alfabeto: se deduce de los símbolos leídos.
* Las coordenadas sólo sirven para dibujar; se toleran y se conservan.
* Versiones antiguas de JFLAP colocan los estados directamente en
  ``<structure>`` sin ``<automaton>``; también se aceptan.
* JFLAP permite que una transición lea varios caracteres (``<read>ab</read>``),
  lo que equivale a una cadena de transiciones. Se expande con estados
  intermedios y se informa con un aviso.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

from core.automata import LAMBDA, Automata, ErrorAutomata
from core.disposicion import disponer


class ErrorFormato(ErrorAutomata):
    """El archivo no tiene la estructura esperada."""


def leer_jff(texto: str | bytes, nombre: str = "Autómata", avisos: Optional[list[str]] = None) -> Automata:
    avisos = avisos if avisos is not None else []
    try:
        raiz = ET.fromstring(texto)
    except ET.ParseError as exc:
        raise ErrorFormato(f"El archivo .jff no es un XML válido: {exc}") from exc
    if raiz.tag != "structure":
        raise ErrorFormato(f"Se esperaba el elemento raíz <structure> y se encontró <{raiz.tag}>.")
    tipo = (raiz.findtext("type") or "").strip()
    if tipo != "fa":
        raise ErrorFormato(f"El archivo es de tipo «{tipo or 'desconocido'}»; sólo se admiten autómatas "
                           "finitos (<type>fa</type>).")
    cuerpo = raiz.find("automaton")
    if cuerpo is None:
        cuerpo = raiz

    a = Automata(nombre=nombre)
    por_id: dict[str, str] = {}
    for e in cuerpo.findall("state"):
        ident = e.get("id")
        if ident is None:
            raise ErrorFormato("Un <state> no tiene atributo id.")
        if ident in por_id:
            raise ErrorFormato(f"El id de estado {ident} está repetido.")
        visible = (e.get("name") or f"q{ident}").strip() or f"q{ident}"
        base, k = visible, 1
        while visible in a.estados:          # nombres repetidos: JFLAP lo permite
            visible = f"{base}_{k}"
            k += 1
        if visible != base:
            avisos.append(f"El nombre {base} estaba repetido; el estado id={ident} se renombró a {visible}.")
        a.estados.append(visible)
        por_id[ident] = visible
        try:
            x, y = float(e.findtext("x", "nan")), float(e.findtext("y", "nan"))
            if x == x and y == y:  # descarta NaN
                a.posiciones[visible] = (x, y)
        except ValueError:
            avisos.append(f"Coordenadas inválidas en el estado {visible}; se ignoran.")
        if e.find("initial") is not None:
            if a.inicial is not None:
                avisos.append(f"Hay varios estados iniciales; se conserva {a.inicial}.")
            else:
                a.inicial = visible
        if e.find("final") is not None:
            a.aceptacion.add(visible)

    if not a.estados:
        raise ErrorFormato("El autómata no tiene estados.")
    if a.inicial is None:
        raise ErrorFormato("Ningún estado está marcado como inicial (<initial/>).")

    contador = 0
    for t in cuerpo.findall("transition"):
        origen, destino = t.findtext("from"), t.findtext("to")
        if origen is None or destino is None:
            raise ErrorFormato("Una <transition> no tiene <from> o <to>.")
        origen, destino = origen.strip(), destino.strip()
        if origen not in por_id or destino not in por_id:
            raise ErrorFormato(f"Una transición usa un id de estado inexistente ({origen} → {destino}).")
        lee = t.findtext("read") or ""
        lee = lee.strip() if lee.strip() else ""
        q, d = por_id[origen], por_id[destino]
        if len(lee) <= 1:
            a.agregar_transicion(q, lee, d)
            continue
        # Transición multicarácter: q --c1--> i1 --c2--> … --cn--> d
        avisos.append(f"La transición {q} → {d} lee «{lee}»; se expandió con estados intermedios.")
        actual = q
        for c in lee[:-1]:
            intermedio = f"{q}_{lee}_{contador}"
            contador += 1
            a.estados.append(intermedio)
            a.agregar_transicion(actual, c, intermedio)
            actual = intermedio
        a.agregar_transicion(actual, lee[-1], d)
    a.alfabeto.sort()
    a.validar(estricto=True)
    return a


def escribir_jff(a: Automata) -> str:
    """Genera un ``.jff`` que JFLAP 7 abre directamente."""
    a.validar(estricto=True)
    posiciones = a.posiciones if all(q in a.posiciones for q in a.estados) else disponer(a)
    ids = {q: str(i) for i, q in enumerate(a.estados)}
    raiz = ET.Element("structure")
    ET.SubElement(raiz, "type").text = "fa"
    cuerpo = ET.SubElement(raiz, "automaton")
    cuerpo.append(ET.Comment("Lista de estados."))
    for q in a.estados:
        e = ET.SubElement(cuerpo, "state", id=ids[q], name=q)
        x, y = posiciones.get(q, (0.0, 0.0))
        ET.SubElement(e, "x").text = f"{float(x):.1f}"
        ET.SubElement(e, "y").text = f"{float(y):.1f}"
        if q == a.inicial:
            ET.SubElement(e, "initial")
        if q in a.aceptacion:
            ET.SubElement(e, "final")
    cuerpo.append(ET.Comment("Lista de transiciones."))
    for q, s, d in a.lista_transiciones():
        t = ET.SubElement(cuerpo, "transition")
        ET.SubElement(t, "from").text = ids[q]
        ET.SubElement(t, "to").text = ids[d]
        r = ET.SubElement(t, "read")
        if s != LAMBDA:
            r.text = s
    ET.indent(raiz, space="\t")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="no"?><!--Created with AutómataLab.-->\n'
            + ET.tostring(raiz, encoding="unicode") + "\n")
