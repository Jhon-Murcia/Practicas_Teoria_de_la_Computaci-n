"""Pruebas de la conversión de autómatas a expresiones regulares (Práctica 3).

La expresión obtenida se verifica de dos formas independientes del autómata:
con derivadas de Brzozowski y con ``re.fullmatch`` sobre su traducción a la
sintaxis de Python.
"""

import re

import pytest

from core import ejemplos
from core.automata import Automata
from core.expresion_regular import (LAMBDA, VACIO, Concat, Estrella, a_python, a_texto, concat, estrella,
                                    pertenece, sim, union)
from core.lenguajes import cerradura_kleene
from core.simulacion import acepta
from algoritmos.eliminacion_estados import eliminar_estados
from algoritmos.minimizacion import minimizar
from algoritmos.subconjuntos import construir_afd

from test_algoritmos import CASOS

a, b = sim("a"), sim("b")


# --- Leyes algebraicas aplicadas por los constructores ----------------------------

@pytest.mark.parametrize("expr,texto", [
    (union(VACIO, a), "a"),                  # ∅ + r = r
    (union(a, a), "a"),                      # r + r = r
    (concat(VACIO, a), "∅"),                 # ∅r = ∅
    (concat(LAMBDA, a, LAMBDA), "a"),        # λr = rλ = r
    (estrella(VACIO), "λ"),                  # ∅* = λ
    (estrella(LAMBDA), "λ"),                 # λ* = λ
    (estrella(estrella(a)), "a*"),           # (r*)* = r*
    (estrella(union(LAMBDA, a)), "a*"),      # (λ + r)* = r*
    (union(LAMBDA, concat(a, estrella(a))), "a*"),   # λ + rr* = r*
    (union(LAMBDA, estrella(a)), "a*"),      # λ + r = r si λ ∈ L(r)
    (concat(estrella(a), estrella(a)), "a*"),        # r*r* = r*
])
def test_leyes_algebraicas(expr, texto):
    assert a_texto(expr) == texto


@pytest.mark.parametrize("expr,texto", [
    (concat(union(a, b), estrella(a)), "(a+b)a*"),
    (estrella(concat(a, b)), "(ab)*"),
    (union(concat(a, b), estrella(b)), "ab+b*"),
    (estrella(union(a, b)), "(a+b)*"),
])
def test_parentesis_minimos(expr, texto):
    assert a_texto(expr) == texto


def test_traduccion_a_python():
    expr = concat(estrella(union(a, b)), a, b)
    assert a_python(expr) == "[ab]*ab"
    for w in cerradura_kleene(["a", "b"], 6):
        assert bool(re.fullmatch(a_python(expr), w)) == pertenece(expr, w) == w.endswith("ab")


# --- Eliminación de estados ---------------------------------------------------------

@pytest.mark.parametrize("aut,nombre", CASOS, ids=[n for _, n in CASOS])
def test_la_expresion_describe_el_lenguaje_del_automata(aut, nombre):
    expr, pasos, orden = eliminar_estados(aut)
    assert sorted(orden) == sorted(aut.estados)
    n = 6 if len(aut.alfabeto) <= 3 else 3
    patron = re.compile(a_python(expr))
    for w in cerradura_kleene(aut.alfabeto, n):
        esperado = acepta(aut, w)
        assert pertenece(expr, w) == esperado, (a_texto(expr), w)
        assert bool(patron.fullmatch(w)) == esperado


def test_ejemplo_termina_en_ab():
    expr, pasos, _ = eliminar_estados(ejemplos.termina_en_ab())
    assert a_texto(expr) == "(a+b)*ab"
    assert pasos[0].titulo.startswith("1.") and pasos[-1].tipo == "exito"


def test_multiplos_de_tres():
    expr, _, _ = eliminar_estados(ejemplos.multiplos_de_tres())
    for w in cerradura_kleene(["0", "1"], 9):
        assert pertenece(expr, w) == (int(w or "0", 2) % 3 == 0)


def test_lenguaje_vacio():
    aut = Automata.desde_tabla(["p", "q"], ["a"], "p", ["q"], {("p", "a"): "p"})
    expr, _, _ = eliminar_estados(aut)
    assert expr == VACIO


def test_orden_de_eliminacion_fijado():
    aut = ejemplos.termina_en_ab()
    e1, _, orden1 = eliminar_estados(aut, ["q0", "q1", "q2"])
    e2, _, orden2 = eliminar_estados(aut, ["q2", "q1", "q0"])
    assert orden1 == ["q0", "q1", "q2"] and orden2 == ["q2", "q1", "q0"]
    for w in cerradura_kleene(["a", "b"], 7):
        assert pertenece(e1, w) == pertenece(e2, w) == w.endswith("ab")


def test_orden_invalido():
    with pytest.raises(ValueError):
        eliminar_estados(ejemplos.termina_en_ab(), ["zz"])


def test_ida_y_vuelta_con_el_afd_minimo():
    aut = minimizar(construir_afd(ejemplos.tercero_desde_el_final())[0])[0]
    expr, _, _ = eliminar_estados(aut)
    for w in cerradura_kleene(["0", "1"], 7):
        assert pertenece(expr, w) == (len(w) >= 3 and w[-3] == "1")
