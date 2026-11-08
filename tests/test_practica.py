"""Pruebas de los ejercicios de práctica y de su evaluación automática."""

import random
import re

import pytest

from core import ejemplos
from core.automata import Automata
from core.expresion_regular import analizar, pertenece
from core.lenguajes import cerradura_kleene
from algoritmos.subconjuntos import construir_afd
from practica.ejercicios import (BANCO, buscar, evaluar_automata, evaluar_expresion, pregunta_aleatoria,
                                 validar_generado)

# Definición independiente de cada lenguaje del banco, para comprobar que la
# expresión de referencia oculta es la correcta.
DEFINICIONES = {
    "empieza-a": lambda w: w.startswith("a"),
    "termina-bb": lambda w: w.endswith("bb"),
    "contiene-aba": lambda w: "aba" in w,
    "b-impar": lambda w: w.count("b") % 2 == 1,
    "longitud-par": lambda w: len(w) % 2 == 0,
    "sin-11": lambda w: "11" not in w,
    "a-multiplo-3": lambda w: w.count("a") % 3 == 0,
    "tercero-final": lambda w: len(w) >= 3 and w[-3] == "a",
    "lambda-ab": lambda w: re.fullmatch("a*b*", w) is not None,
    "dos-a": lambda w: w.count("a") == 2,
    "mismo-extremo": lambda w: len(w) >= 1 and w[0] == w[-1],
    "identificador": lambda w: re.fullmatch("l[ld]*", w) is not None,
    "sin-bb": lambda w: "bb" not in w,
}


def test_todos_los_ejercicios_tienen_definicion():
    assert {e.clave for e in BANCO} == set(DEFINICIONES)


@pytest.mark.parametrize("ej", BANCO, ids=[e.clave for e in BANCO])
def test_la_referencia_describe_el_enunciado(ej):
    r = analizar(ej.referencia)
    for w in cerradura_kleene(list(ej.alfabeto), 8):
        assert pertenece(r, w) == DEFINICIONES[ej.clave](w), (ej.clave, w)


def test_afd_correcto_se_aprueba():
    a = Automata.desde_tabla(["q0", "q1", "x"], ["a", "b"], "q0", ["q1"],
                             {("q0", "a"): "q1", ("q0", "b"): "x", ("q1", "a"): "q1", ("q1", "b"): "q1",
                              ("x", "a"): "x", ("x", "b"): "x"})
    ev = evaluar_automata(buscar("empieza-a"), a)
    assert ev.correcto


def test_respuesta_incorrecta_da_contraejemplo():
    ev = evaluar_automata(buscar("empieza-a"), ejemplos.a_par())
    assert not ev.correcto and ev.contraejemplo is not None
    w = ev.contraejemplo
    assert ev.deberia_aceptar == w.startswith("a")
    assert f"«{w or 'λ'}»" in ev.mensaje


def test_afnd_correcto_no_cuenta_si_se_pide_afd():
    ev = evaluar_automata(buscar("termina-bb"), _afnd_termina_bb())
    assert not ev.correcto and "determinista" in ev.mensaje


def test_afnd_se_acepta_cuando_no_se_exige_afd():
    ej = buscar("tercero-final")
    a = Automata.desde_tabla(["p", "q", "r", "s"], ["a", "b"], "p", ["s"],
                             {("p", "a"): {"p", "q"}, ("p", "b"): "p", ("q", "a"): "r", ("q", "b"): "r",
                              ("r", "a"): "s", ("r", "b"): "s"})
    assert evaluar_automata(ej, a).correcto
    assert evaluar_automata(ej, construir_afd(a)[0]).correcto


def test_simbolos_fuera_del_alfabeto():
    ev = evaluar_automata(buscar("empieza-a"), ejemplos.multiplos_de_tres())
    assert not ev.correcto and "Σ" in ev.mensaje


@pytest.mark.parametrize("texto,correcto", [("b*ab*ab*", True), ("b*(ab*)(ab*)", True), ("(a+b)*", False),
                                            ("b*ab*a", False)])
def test_evaluar_expresion(texto, correcto):
    assert evaluar_expresion(buscar("dos-a"), texto).correcto == correcto


def test_expresion_mal_formada():
    ev = evaluar_expresion(buscar("dos-a"), "b*a(b*")
    assert not ev.correcto and "posición" in ev.mensaje


def test_validar_ejercicio_generado():
    ej = validar_generado({"titulo": "Pares de a", "enunciado": "Cadenas con un número par de aes.",
                           "tipo": "expresion", "alfabeto": ["a", "b"], "expresion_referencia": "(b*ab*a)*b*",
                           "dificultad": "intermedio"})
    assert ej.generado_por_ia and ej.alfabeto == ("a", "b")
    assert evaluar_expresion(ej, "b*(ab*ab*)*").correcto


@pytest.mark.parametrize("datos", [
    {"titulo": "x", "enunciado": "x", "tipo": "expresion", "alfabeto": ["a"], "expresion_referencia": "(a"},
    {"titulo": "x", "enunciado": "x", "tipo": "expresion", "alfabeto": ["a"], "expresion_referencia": "ab"},
    {"titulo": "x", "enunciado": "x", "tipo": "expresion", "alfabeto": ["a"], "expresion_referencia": "∅"},
    {"titulo": "x", "enunciado": "x", "tipo": "otro", "alfabeto": ["a"], "expresion_referencia": "a"},
    {"titulo": "x", "enunciado": "", "tipo": "expresion", "alfabeto": ["a"], "expresion_referencia": "a"},
    {"titulo": "x", "enunciado": "x", "tipo": "expresion", "alfabeto": ["ab"], "expresion_referencia": "a"},
])
def test_ejercicios_generados_invalidos(datos):
    with pytest.raises(ValueError):
        validar_generado(datos)


def test_preguntas_rapidas_tienen_respuesta_correcta():
    from core.simulacion import acepta
    rnd = random.Random(3)
    for _ in range(30):
        p = pregunta_aleatoria(rnd)
        assert acepta(p.automata, p.cadena) == p.respuesta


def _afnd_termina_bb():
    return Automata.desde_tabla(["p", "q", "r"], ["a", "b"], "p", ["r"],
                                {("p", "a"): "p", ("p", "b"): {"p", "q"}, ("q", "b"): "r"})
