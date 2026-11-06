"""Pruebas de importación y exportación en .jff, .json y .xml (Práctica 2)."""

import json

import pytest

from core import ejemplos
from core.automata import LAMBDA
from core.lenguajes import cerradura_kleene
from core.simulacion import acepta
from formatos import ErrorFormato, cargar, exportar, leer_jff, leer_json, leer_xml

ANEXO_JFF = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<structure>
  <type>fa</type>
  <automaton>
    <state id="0" name="q0"><x>80.0</x><y>120.0</y><initial/></state>
    <state id="1" name="q1"><x>240.0</x><y>120.0</y><final/></state>
    <transition><from>0</from><to>1</to><read>a</read></transition>
    <transition><from>0</from><to>0</to><read>b</read></transition>
    <transition><from>0</from><to>1</to><read/></transition>
  </automaton>
</structure>"""

ANEXO_JSON = """{
  "tipo": "AFND-lambda", "alfabeto": ["a", "b"], "estados": ["q0", "q1"],
  "inicial": "q0", "aceptacion": ["q1"],
  "transiciones": [
    { "desde": "q0", "lee": "a", "hacia": ["q1"] },
    { "desde": "q0", "lee": "b", "hacia": ["q0"] },
    { "desde": "q0", "lee": "",  "hacia": ["q1"] } ] }"""

ANEXO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<automata tipo="AFND-lambda">
  <alfabeto><simbolo>a</simbolo><simbolo>b</simbolo></alfabeto>
  <estados>
    <estado nombre="q0" inicial="true"/>
    <estado nombre="q1" aceptacion="true"/>
  </estados>
  <transiciones>
    <transicion desde="q0" lee="a" hacia="q1"/>
    <transicion desde="q0" lee="b" hacia="q0"/>
    <transicion desde="q0" lee="" hacia="q1"/>
  </transiciones>
</automata>"""


# --- Los tres ejemplos del Anexo 3 describen el mismo autómata ----------------

def test_los_tres_archivos_del_anexo_dan_la_misma_quintupla():
    a, b, c = leer_jff(ANEXO_JFF), leer_json(ANEXO_JSON), leer_xml(ANEXO_XML)
    assert a.misma_definicion(b) and b.misma_definicion(c)
    assert a.estados == ["q0", "q1"]
    assert a.alfabeto == ["a", "b"]
    assert a.inicial == "q0"
    assert a.aceptacion == {"q1"}
    assert a.destinos("q0", LAMBDA) == {"q1"}
    assert a.posiciones["q1"] == (240.0, 120.0)


# --- Exportar e importar son operaciones inversas ------------------------------

@pytest.mark.parametrize("formato", ["jff", "json", "xml"])
@pytest.mark.parametrize("fabrica", list(ejemplos.EJEMPLOS.values()), ids=list(ejemplos.EJEMPLOS))
def test_ida_y_vuelta(formato, fabrica):
    original = fabrica()
    texto = exportar(original, formato)
    leido = cargar(f"x.{formato}", texto.encode("utf-8"))
    assert leido.misma_definicion(original)
    # Exportar de nuevo lo leído produce exactamente el mismo archivo.
    assert exportar(leido, formato) == texto


@pytest.mark.parametrize("formato", ["jff", "json", "xml"])
def test_ida_y_vuelta_conserva_el_lenguaje(formato):
    original = ejemplos.numeros_decimales()
    leido = cargar(f"x.{formato}", exportar(original, formato))
    for w in ["-1.5", "+.25", "9.", ".", "1", "--1.0", "12.34"]:
        assert acepta(leido, w) == acepta(original, w)


def test_json_conserva_nombre_y_posiciones():
    a = ejemplos.conexion_tcp()
    datos = json.loads(exportar(a, "json"))
    assert datos["tipo"] == "AFD" and datos["nombre"] == a.nombre
    assert datos["posiciones"]["CLOSED"] == [420.0, 60.0]


def test_tipo_afnd_lambda_se_escribe_con_la_palabra_lambda():
    assert json.loads(exportar(ejemplos.anexo_lambda(), "json"))["tipo"] == "AFND-lambda"
    assert 'tipo="AFND-lambda"' in exportar(ejemplos.anexo_lambda(), "xml")


def test_jff_escribe_lambda_como_read_vacio():
    texto = exportar(ejemplos.anexo_lambda(), "jff")
    assert "<read />" in texto or "<read/>" in texto


def test_jff_sin_coordenadas_recibe_disposicion_automatica():
    a = ejemplos.termina_en_ab()
    a.posiciones = {}
    leido = leer_jff(exportar(a, "jff"))
    assert set(leido.posiciones) == set(a.estados)


# --- Tolerancia y validación ----------------------------------------------------

def test_jff_antiguo_sin_elemento_automaton():
    texto = """<structure><type>fa</type>
      <state id="0"><x>0</x><y>0</y><initial/><final/></state>
      <transition><from>0</from><to>0</to><read>a</read></transition></structure>"""
    a = leer_jff(texto)
    assert a.estados == ["q0"] and acepta(a, "aaa")


def test_jff_transicion_multicaracter_se_expande():
    texto = """<structure><type>fa</type><automaton>
      <state id="0" name="q0"><initial/></state><state id="1" name="q1"><final/></state>
      <transition><from>0</from><to>1</to><read>ab</read></transition></automaton></structure>"""
    avisos = []
    a = leer_jff(texto, avisos=avisos)
    assert avisos and acepta(a, "ab") and not acepta(a, "a")
    assert a.alfabeto == ["a", "b"]


@pytest.mark.parametrize("texto,mensaje", [
    ("<structure><type>pda</type></structure>", "pda"),
    ("<structure><type>fa</type><automaton/></structure>", "no tiene estados"),
    ("<structure><type>fa</type><automaton><state id='0'/></automaton></structure>", "inicial"),
    ("no es xml", "XML"),
    ("<structure><type>fa</type><automaton><state id='0'><initial/></state>"
     "<transition><from>0</from><to>7</to><read>a</read></transition></automaton></structure>", "inexistente"),
])
def test_jff_invalidos(texto, mensaje):
    with pytest.raises(ErrorFormato, match=mensaje):
        leer_jff(texto)


@pytest.mark.parametrize("texto", [
    "{",
    "[]",
    '{"estados": ["q0"]}',
    '{"estados": ["q0"], "inicial": "q9", "aceptacion": [], "transiciones": []}',
    '{"estados": ["q0"], "inicial": "q0", "aceptacion": [], "transiciones": [{"desde": "q0"}]}',
])
def test_json_invalidos(texto):
    with pytest.raises(Exception):
        leer_json(texto)


def test_xml_rechaza_un_jff():
    with pytest.raises(ErrorFormato, match="JFLAP"):
        leer_xml(ANEXO_JFF)


def test_extension_no_admitida():
    with pytest.raises(ErrorFormato):
        cargar("automata.txt", "x")


def test_json_acepta_lambda_escrita_como_simbolo():
    texto = ANEXO_JSON.replace('"lee": "",', '"lee": "λ",')
    assert leer_json(texto).destinos("q0", LAMBDA) == {"q1"}


def test_archivos_de_ejemplo_del_repositorio_se_leen(tmp_path):
    from pathlib import Path
    carpeta = Path(__file__).resolve().parents[1] / "automatas" / "ejemplos"
    archivos = sorted(carpeta.glob("*.*"))
    assert archivos, "La carpeta automatas/ejemplos debe contener los ejemplos exportados"
    for ruta in archivos:
        a = cargar(ruta.name, ruta.read_bytes())
        assert a.validar() == []


def test_exportacion_completa_de_lenguaje_por_formato():
    a = ejemplos.tercero_desde_el_final()
    for formato in ("jff", "json", "xml"):
        b = cargar(f"x.{formato}", exportar(a, formato))
        assert all(acepta(a, w) == acepta(b, w) for w in cerradura_kleene(["0", "1"], 7))
