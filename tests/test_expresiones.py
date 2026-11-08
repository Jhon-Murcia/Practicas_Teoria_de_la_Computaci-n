"""Pruebas de la Práctica 4: analizador, Thompson, cadena completa y validadores."""

import random
import re

import pytest

from core.expresion_regular import (Clase, Concat, ErrorSintaxis, Estrella, Simbolo, Union, a_python, a_texto,
                                    analizar, analizar_clases, muestra, pertenece, simbolos)
from core.lenguajes import cerradura_kleene
from core.simulacion import acepta
from algoritmos import validadores as V
from algoritmos.eliminacion_estados import eliminar_estados
from algoritmos.equivalencia import comparar
from algoritmos.thompson import thompson
from algoritmos.tuberia import desde_texto

# Expresiones propias de prueba.
EXPRESIONES = [
    "a", "λ", "∅", "ab", "a+b", "a*", "(a+b)*", "(a+b)*abb", "a*b*c*", "(ab+ba)*", "a(a+b)*b+b(a+b)*a",
    "(a+λ)(b+λ)", "((a*)*)*", "(a+b)*a(a+b)(a+b)", "(aa)*+(bbb)*", "∅*", "a∅+b", "(0+1(01*0)*1)*",
    "(λ+a)b*(a+λ)",
]


# --- Analizador ------------------------------------------------------------

def test_precedencia_estrella_concatenacion_union():
    r = analizar("a+bc*")
    assert r == Union((Simbolo("a"), Concat((Simbolo("b"), Estrella(Simbolo("c"))))))


def test_parentesis_cambian_la_precedencia():
    assert analizar("(a+b)c") == Concat((Union((Simbolo("a"), Simbolo("b"))), Simbolo("c")))
    assert analizar("(ab)*") == Estrella(Concat((Simbolo("a"), Simbolo("b"))))


def test_espacios_y_escapes():
    assert analizar("a + b") == analizar("a+b")
    assert analizar("\\+5\\ ") == Concat((Simbolo("+"), Simbolo("5"), Simbolo(" ")))


@pytest.mark.parametrize("texto,posicion,fragmento", [
    ("", 1, "vacía"),
    ("a+", 2, "derecho"),
    ("+a", 1, "izquierdo"),
    ("a++b", 2, "derecho"),
    ("*a", 1, "cerradura"),
    ("(a+b", 1, "cerrar el paréntesis"),
    ("a+b)", 4, "sin su apertura"),
    ("()", 1, "vacíos"),
    ("a(+b)", 3, "izquierdo"),
    ("ab\\", 3, "barra"),
    ("{X}a", 1, "no está declarada"),
    ("a{", 2, "cerrar"),
])
def test_errores_indican_la_posicion(texto, posicion, fragmento):
    with pytest.raises(ErrorSintaxis) as info:
        analizar(texto)
    assert info.value.posicion == posicion
    assert fragmento in info.value.mensaje
    assert info.value.marca().splitlines()[-1] == " " * (posicion - 1) + "^"


@pytest.mark.parametrize("texto", EXPRESIONES)
def test_escribir_y_volver_a_analizar(texto):
    r = analizar(texto)
    assert analizar(a_texto(r)) == r


def test_clases_declaradas():
    clases = analizar_clases("D = [0-9]\nS = \\+ + -\nL = [a-cx]\nA = {L}+{D}")
    assert clases["S"].simbolos == ("+", "-")
    assert clases["D"].simbolos == tuple("0123456789")
    assert clases["L"].simbolos == ("a", "b", "c", "x")
    assert set(clases["A"].simbolos) == set("abcx0123456789")
    r = analizar("{D}{D}*", clases)
    assert isinstance(r.partes[0], Clase)
    assert pertenece(r, "2026") and not pertenece(r, "")


@pytest.mark.parametrize("decl", ["D [0-9]", "D = ab", "D = [9-0]", "= [0-9]"])
def test_clases_invalidas(decl):
    with pytest.raises(ValueError):
        analizar_clases(decl)


# --- Thompson -----------------------------------------------------------------

@pytest.mark.parametrize("texto", EXPRESIONES)
def test_thompson_reconoce_el_lenguaje_de_la_expresion(texto):
    r = analizar(texto)
    afn, pasos = thompson(r)
    assert afn.tipo in ("AFND-λ", "AFND", "AFD")
    alfabeto = sorted(simbolos(r)) or ["a"]
    for w in cerradura_kleene(alfabeto, 6 if len(alfabeto) <= 2 else 5):
        assert acepta(afn, w) == pertenece(r, w), (texto, w)


@pytest.mark.parametrize("texto", EXPRESIONES)
def test_forma_del_afn_de_thompson(texto):
    r = analizar(texto)
    afn, pasos = thompson(r)
    (final,) = afn.aceptacion
    assert not any(q == final for q, _, _ in afn.lista_transiciones())    # el final no tiene salidas
    assert len(afn.estados) <= 2 * len(a_texto(r)) + 2
    assert pasos[0].titulo == "Árbol sintáctico" and pasos[-1].tipo == "exito"


def test_pasos_de_thompson_siguen_el_arbol():
    _, pasos = thompson(analizar("(a+b)*c"))
    titulos = [p.titulo for p in pasos]
    assert titulos[1:4] == ["Caso básico «a»", "Caso básico «b»", "Unión de 2 expresiones: a+b"]
    assert titulos[4].startswith("Cerradura") and titulos[5] == "Caso básico «c»"
    assert titulos[6].startswith("Concatenación")


# --- Cadena completa hasta el AFD mínimo -------------------------------------------

@pytest.mark.parametrize("texto", EXPRESIONES)
def test_cadena_completa(texto):
    res = desde_texto(texto)
    r = res.expresion
    alfabeto = sorted(simbolos(r)) or ["a"]
    for etapa in res.etapas:
        for w in cerradura_kleene(alfabeto, 5):
            assert acepta(etapa.automata, w) == pertenece(r, w), (texto, etapa.titulo, w)
    assert len(res.minimo.estados) <= len(res.afd.estados)
    assert res.afd.es_determinista()


def test_minimo_conocido():
    assert len(desde_texto("(a+b)*abb").minimo.estados) == 4
    assert len(desde_texto("(a+b)*a(a+b)(a+b)").minimo.estados) == 8   # cota 2^3


# --- De autómata a ER y comparación de expresiones --------------------------------------

@pytest.mark.parametrize("texto", EXPRESIONES)
def test_ida_y_vuelta_er_automata_er(texto):
    # ER → AFD mínimo → ER: la expresión obtenida describe el mismo lenguaje.
    # (Se verifica con derivadas: reconstruir con Thompson una expresión que puede
    # ser muy larga haría la prueba lenta sin aportar más.)
    res = desde_texto(texto)
    expr, _, _ = eliminar_estados(res.minimo)
    original = res.expresion
    alfabeto = sorted(simbolos(original)) or ["a"]
    for w in cerradura_kleene(alfabeto, 6):
        assert pertenece(expr, w) == pertenece(original, w) == acepta(res.minimo, w), (texto, w)


def test_ida_y_vuelta_completa_con_equivalencia():
    res = desde_texto("(a+b)*abb")
    expr, _, _ = eliminar_estados(res.minimo)
    assert comparar(desde_texto(a_texto(expr)).minimo, res.minimo).equivalentes


@pytest.mark.parametrize("e1,e2,iguales", [
    ("(a+b)*ab", "(a*b*)*ab", True),
    ("(a+b)*", "(a*b*)*", True),
    ("a(ba)*", "(ab)*a", True),
    ("(a+b)*ab", "(a+b)*ba", False),
    ("a*", "a*a", False),
])
def test_equivalencia_de_expresiones(e1, e2, iguales):
    comp = comparar(desde_texto(e1).minimo, desde_texto(e2).minimo)
    assert comp.equivalentes == iguales
    if not iguales:
        w = comp.contraejemplo
        assert pertenece(analizar(e1), w) != pertenece(analizar(e2), w)


def test_determinismo_indica_estado_y_simbolo():
    afn, _ = thompson(analizar("a*"))
    conflictos = afn.conflictos_determinismo()
    assert conflictos and all(s == "λ" for _, s, _ in conflictos)


# --- Validadores: congruencia entre el autómata y re.fullmatch -------------------

FUERA = [" ", "#", "ñ", "!", "é"]


def generar_casos(v: V.Validador, semilla: int = 2026, total: int = 600) -> list[str]:
    """Procedimiento de generación (descrito también en el README):

    1. 40 % cadenas válidas tomadas al azar del lenguaje de la expresión
       (``muestra`` recorre el árbol eligiendo ramas y repeticiones al azar).
    2. 40 % mutaciones de cadenas válidas: insertar, borrar, sustituir o
       duplicar un carácter, tomado de Σ o de caracteres fuera de Σ.
    3. 20 % cadenas aleatorias sobre Σ de longitud 0 a 25.
    Más los ejemplos válidos e inválidos escritos a mano.
    """
    rnd = random.Random(semilla)
    r = v.arbol()
    sigma = sorted(simbolos(r))
    validas = []
    while len(validas) < total * 0.4:
        w = muestra(r, rnd)
        if w is not None:
            validas.append(w)
    mutadas = []
    while len(mutadas) < total * 0.4:
        w = list(rnd.choice(validas))
        i = rnd.randint(0, len(w))
        c = rnd.choice(sigma + FUERA)
        op = rnd.choice(["insertar", "borrar", "sustituir", "duplicar"])
        if op == "insertar" or not w:
            w.insert(i, c)
        elif op == "borrar":
            del w[min(i, len(w) - 1)]
        elif op == "sustituir":
            w[min(i, len(w) - 1)] = c
        else:
            j = min(i, len(w) - 1)
            w.insert(j, w[j])
        mutadas.append("".join(w))
    aleatorias = ["".join(rnd.choice(sigma) for _ in range(rnd.randint(0, 25))) for _ in range(int(total * 0.2))]
    return validas + mutadas + aleatorias + list(v.validos) + list(v.invalidos)


@pytest.mark.parametrize("clave", list(V.VALIDADORES))
def test_validador_coincide_con_re_fullmatch(clave):
    v = V.VALIDADORES[clave]
    casos = generar_casos(v)
    assert len(casos) >= 500
    minimo = V.automata_minimo(clave)
    manual = re.compile(v.python)
    automatica = re.compile(v.python_automatico())
    aceptadas = 0
    for w in casos:
        esperado = bool(manual.fullmatch(w))
        aceptadas += esperado
        assert acepta(minimo, list(w)) == esperado, (clave, w)
        assert bool(automatica.fullmatch(w)) == esperado, (clave, w)
    # El conjunto mezcla de verdad válidas e inválidas.
    assert 0.3 * len(casos) < aceptadas < 0.8 * len(casos)


@pytest.mark.parametrize("clave", list(V.VALIDADORES))
def test_ejemplos_de_cada_validador(clave):
    v = V.VALIDADORES[clave]
    assert all(V.validar(clave, w) for w in v.validos)
    assert not any(V.validar(clave, w) for w in v.invalidos)


@pytest.mark.parametrize("clave", list(V.VALIDADORES))
def test_todas_las_etapas_del_validador_coinciden(clave):
    res = V.construir(clave)
    casos = generar_casos(V.VALIDADORES[clave], semilla=7, total=150)
    for w in casos:
        esperado = acepta(res.minimo, list(w))
        for etapa in res.etapas[:3]:
            assert acepta(etapa.automata, list(w)) == esperado, (clave, etapa.titulo, w)
    assert len(res.minimo.estados) <= len(res.afd.estados)
