"""Pruebas del núcleo de operaciones sobre cadenas y lenguajes (Práctica 1)."""

import pytest

from core.lenguajes import (
    LIMITE_CADENAS,
    LimiteExcedido,
    agrupar_por_longitud,
    cerradura_kleene,
    cerradura_positiva,
    concatenacion,
    contar_cerradura,
    diferencia,
    interseccion,
    max_subcadenas_distintas,
    mostrar,
    parsear_alfabeto,
    parsear_lenguaje,
    potencia_alfabeto,
    potencia_cadena,
    potencia_lenguaje,
    prefijos,
    reflexion,
    reflexion_lenguaje,
    reporte_texto,
    subcadenas,
    sufijos,
    union,
)


# --- Cadena vacía -----------------------------------------------------------

def test_prefijos_de_la_cadena_vacia():
    assert prefijos("") == [""]


def test_sufijos_de_la_cadena_vacia():
    assert sufijos("") == [""]


def test_subcadenas_de_la_cadena_vacia():
    assert subcadenas("") == [""]


def test_la_vacia_se_muestra_como_lambda():
    assert mostrar("") == "λ"
    assert mostrar("ab") == "ab"


# --- Cadena de longitud 1 ---------------------------------------------------

def test_prefijos_y_sufijos_de_longitud_uno():
    assert prefijos("a") == ["", "a"]
    assert sufijos("a") == ["", "a"]


def test_subcadenas_de_longitud_uno():
    assert subcadenas("a") == ["", "a"]


# --- Casos generales --------------------------------------------------------

def test_prefijos_generales():
    assert prefijos("abc") == ["", "a", "ab", "abc"]


def test_sufijos_generales():
    assert sufijos("abc") == ["", "c", "bc", "abc"]


@pytest.mark.parametrize("w", ["", "a", "ab", "abba", "aaaa", "abcdef"])
def test_hay_n_mas_uno_prefijos_y_sufijos(w):
    assert len(prefijos(w)) == len(w) + 1
    assert len(sufijos(w)) == len(w) + 1


def test_subcadenas_sin_repeticiones():
    assert subcadenas("aab") == ["", "a", "b", "aa", "ab", "aab"]


@pytest.mark.parametrize("w", ["abc", "abcd", "xyzw1"])
def test_cota_de_subcadenas_se_alcanza_con_simbolos_distintos(w):
    assert len(subcadenas(w)) == max_subcadenas_distintas(len(w))


def test_cota_de_subcadenas_no_se_alcanza_con_repeticiones():
    assert len(subcadenas("aaaa")) == 5 < max_subcadenas_distintas(4)


def test_reflexion_y_potencia_de_cadena():
    assert reflexion("abc") == "cba"
    assert potencia_cadena("ab", 3) == "ababab"
    assert potencia_cadena("ab", 0) == ""


# --- Alfabeto de un solo símbolo --------------------------------------------

def test_kleene_de_alfabeto_unario():
    assert cerradura_kleene(["a"], 3) == ["", "a", "aa", "aaa"]


def test_positiva_de_alfabeto_unario():
    assert cerradura_positiva(["a"], 3) == ["a", "aa", "aaa"]


# --- Diferencia entre Σ* y Σ⁺ en longitud cero -------------------------------

def test_kleene_longitud_cero_es_lambda():
    assert cerradura_kleene(["a", "b"], 0) == [""]


def test_positiva_longitud_cero_es_vacia():
    assert cerradura_positiva(["a", "b"], 0) == []


def test_sigma_cero_es_lambda():
    assert potencia_alfabeto(["0", "1"], 0) == [""]


def test_kleene_menos_positiva_es_solo_lambda():
    estrella = set(cerradura_kleene(["a", "b"], 4))
    mas = set(cerradura_positiva(["a", "b"], 4))
    assert estrella - mas == {""}


# --- Cerraduras ---------------------------------------------------------------

def test_kleene_binaria_en_orden_canonico():
    assert cerradura_kleene(["a", "b"], 2) == ["", "a", "b", "aa", "ab", "ba", "bb"]


@pytest.mark.parametrize("k,n", [(1, 5), (2, 6), (3, 4), (5, 3)])
def test_cantidad_de_cadenas_generadas(k, n):
    alfabeto = [chr(ord("a") + i) for i in range(k)]
    assert len(cerradura_kleene(alfabeto, n)) == contar_cerradura(k, n)
    assert len(cerradura_positiva(alfabeto, n)) == contar_cerradura(k, n, positiva=True)


def test_se_rechaza_mas_de_doscientas_mil_cadenas():
    # 2^0 + ... + 2^17 = 262 143 > 200 000
    with pytest.raises(LimiteExcedido) as info:
        cerradura_kleene(["0", "1"], 17)
    assert info.value.cantidad == 2 ** 18 - 1
    assert "200,000" in str(info.value)


def test_limite_exacto_se_acepta():
    # 2^0 + ... + 2^16 = 131 071 <= 200 000
    assert len(cerradura_kleene(["0", "1"], 16)) == 131_071 <= LIMITE_CADENAS


def test_longitud_negativa_se_rechaza():
    with pytest.raises(ValueError):
        cerradura_kleene(["a"], -1)


def test_agrupar_por_longitud():
    grupos = agrupar_por_longitud(cerradura_kleene(["a", "b"], 2))
    assert grupos == {0: [""], 1: ["a", "b"], 2: ["aa", "ab", "ba", "bb"]}


# --- Entrada del usuario -----------------------------------------------------

def test_parsear_alfabeto():
    assert parsear_alfabeto("a, b,  c a") == ["a", "b", "c"]


@pytest.mark.parametrize("texto", ["", "  ,  ", "a, λ"])
def test_parsear_alfabeto_invalido(texto):
    with pytest.raises(ValueError):
        parsear_alfabeto(texto)


def test_parsear_lenguaje_con_lambda():
    assert parsear_lenguaje("ab, λ, ba, ab") == ["ab", "", "ba"]


# --- Operaciones sobre lenguajes ---------------------------------------------

def test_operaciones_de_conjuntos():
    l1, l2 = ["a", "ab"], ["ab", "b"]
    assert union(l1, l2) == ["a", "b", "ab"]
    assert interseccion(l1, l2) == ["ab"]
    assert diferencia(l1, l2) == ["a"]


def test_concatenacion_de_lenguajes():
    assert concatenacion(["a", ""], ["b"]) == ["b", "ab"]


def test_potencia_de_lenguaje():
    assert potencia_lenguaje(["a", "b"], 0) == [""]
    assert potencia_lenguaje(["a", "b"], 2) == ["aa", "ab", "ba", "bb"]


def test_reflexion_de_lenguaje():
    assert reflexion_lenguaje(["ab", "abc"]) == ["ba", "cba"]


def test_reporte_de_texto():
    texto = reporte_texto("Prefijos", prefijos("ab"), {"Cadena": "ab"})
    assert texto.splitlines()[-3:] == ["λ", "a", "ab"]
    assert "Total de cadenas: 3" in texto
