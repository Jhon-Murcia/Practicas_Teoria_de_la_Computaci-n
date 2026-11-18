"""Pruebas de la visualización (Práctica 5, ejercicio 3.3).

El dibujo sólo pinta lo que calculan :mod:`core.disposicion` (posiciones) y
:mod:`core.animacion` (lo que se resalta en cada paso). Aquí se comprueba:

1. Que la posición asignada a cada estado es única y que dos estados nunca se
   encimen, para los ejemplos, los archivos del repositorio y los autómatas que
   producen las conversiones de las Prácticas 3 y 4.
2. Que la secuencia de estados resaltados coincide con el recorrido que calcula
   un simulador de referencia escrito aparte (sin usar :mod:`core.simulacion`),
   y que cada transición resaltada existe en δ y sale de un estado activo.
3. Que el resultado final de la animación coincide con el de las prácticas
   anteriores: la simulación, el autómata convertido y la expresión regular.
"""

import itertools
import math
import random
from pathlib import Path

import pytest

from core import ejemplos
from core.animacion import cuadros, recorrido
from core.automata import LAMBDA, Automata
from core.disposicion import SEP_X, SEP_Y, asegurar_posiciones, disponer
from core.expresion_regular import analizar, pertenece
from core.lenguajes import cerradura_kleene
from core.simulacion import acepta, simular
from formatos import leer_archivo
from algoritmos.eliminacion_lambda import eliminar_lambda
from algoritmos.minimizacion import minimizar
from algoritmos.subconjuntos import construir_afd
from algoritmos.tuberia import desde_texto
from ui.geometria import RADIO

RAIZ = Path(__file__).resolve().parents[1] / "automatas"
ARCHIVOS = sorted(p for p in RAIZ.rglob("*") if p.suffix in (".jff", ".json", ".xml"))
EXPRESIONES = ["(a+b)*bb", "a*b*", "(ab+ba)*", "a(a+b)*a+b", "(a+λ)(b+λ)", "((a+b)(a+b))*", "∅", "λ"]


def automata_aleatorio(rnd: random.Random, n: int, alfabeto=("a", "b"), con_lambda: bool = True) -> Automata:
    estados = [f"q{i}" for i in range(n)]
    delta: dict = {}
    for q in estados:
        for s in alfabeto + (("",) if con_lambda else ()):
            prob = 0.25 if s == "" else 0.7
            destinos = {d for d in estados if rnd.random() < prob / max(1, n / 2)}
            if destinos:
                delta[(q, s)] = destinos
    finales = [q for q in estados if rnd.random() < 0.35] or [estados[-1]]
    return Automata.desde_tabla(estados, list(alfabeto), "q0", finales, delta, f"aleatorio {n}")


def aleatorios(cantidad: int = 40, semilla: int = 5) -> list[Automata]:
    rnd = random.Random(semilla)
    return [automata_aleatorio(rnd, rnd.randint(1, 6), con_lambda=i % 2 == 0) for i in range(cantidad)]


def con_conversiones(a: Automata) -> list[Automata]:
    sin_lambda = eliminar_lambda(a)[0]
    afd = construir_afd(sin_lambda)[0]
    return [a, sin_lambda, afd, minimizar(afd)[0]]


def todos_los_dibujables() -> list[Automata]:
    lista = []
    for a in ejemplos.todos():
        lista += con_conversiones(a)
    for ruta in ARCHIVOS:
        lista.append(leer_archivo(str(ruta)))
    for texto in EXPRESIONES:
        lista += [e.automata for e in desde_texto(texto).etapas]
    return lista + aleatorios(15)


# ---------------------------------------------------------------------------
# 1. Posiciones
# ---------------------------------------------------------------------------

def assert_posiciones_validas(a: Automata, posiciones: dict) -> None:
    assert set(posiciones) == set(a.estados), a.nombre
    puntos = list(posiciones.values())
    assert len(set(puntos)) == len(puntos), f"{a.nombre}: dos estados comparten posición"
    for (q, p), (r, s) in itertools.combinations(posiciones.items(), 2):
        assert math.dist(p, s) >= 2 * RADIO, f"{a.nombre}: {q} y {r} se enciman"


@pytest.mark.parametrize("a", todos_los_dibujables(), ids=lambda a: a.nombre)
def test_disposicion_automatica_da_posiciones_unicas(a):
    assert_posiciones_validas(a, disponer(a))


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: p.name)
def test_archivos_con_coordenadas_propias_no_se_enciman(ruta):
    a = leer_archivo(str(ruta))
    asegurar_posiciones(a)
    assert_posiciones_validas(a, a.posiciones)


def test_completar_posiciones_no_mueve_las_existentes_ni_encima():
    a = ejemplos.termina_en_ab()
    asegurar_posiciones(a)
    antes = dict(a.posiciones)
    for i in range(9):            # varios estados nuevos, algunos en la misma capa
        a.agregar_estado(f"n{i}")
        a.agregar_transicion(a.inicial, "a", f"n{i}")
    asegurar_posiciones(a)
    assert all(a.posiciones[q] == p for q, p in antes.items())
    assert_posiciones_validas(a, a.posiciones)


def test_la_disposicion_por_capas_sigue_el_recorrido_en_anchura():
    a = ejemplos.tercero_desde_el_final()
    pos = disponer(a)
    x0 = pos[a.inicial][0]
    for q, s, d in a.lista_transiciones():
        # Un sucesor nunca queda más de una columna a la derecha de su origen.
        assert pos[d][0] - pos[q][0] <= SEP_X + 1e-9
    assert min(x for x, _ in pos.values()) == x0
    assert SEP_X > 2 * RADIO and SEP_Y > 2 * RADIO


# ---------------------------------------------------------------------------
# 2. Lo que se resalta coincide con el recorrido
# ---------------------------------------------------------------------------

def clausura_referencia(a: Automata, conjunto) -> frozenset:
    """λ-clausura escrita de nuevo, sin usar el simulador del programa."""
    resultado, pila = set(conjunto), list(conjunto)
    while pila:
        q = pila.pop()
        for (origen, s), destinos in a.transiciones.items():
            if origen == q and s == LAMBDA:
                for d in destinos - resultado:
                    resultado.add(d)
                    pila.append(d)
    return frozenset(resultado)


def recorrido_referencia(a: Automata, cadena: str) -> list[frozenset]:
    actual = clausura_referencia(a, {a.inicial})
    lista = [actual]
    for s in cadena:
        siguiente = set()
        for q in actual:
            siguiente |= a.transiciones.get((q, s), set())
        actual = clausura_referencia(a, siguiente)
        lista.append(actual)
    return lista


def casos_de_simulacion():
    casos = []
    for a in ejemplos.todos()[:7] + aleatorios(25, semilla=11):
        sigma = a.alfabeto if len(a.alfabeto) <= 3 else a.alfabeto[:3]
        for w in cerradura_kleene(list(sigma), 4 if len(sigma) <= 2 else 3):
            casos.append((a, w))
    return casos


CASOS = casos_de_simulacion()


def test_hay_suficientes_casos():
    assert len(CASOS) > 1000


def test_estados_resaltados_coinciden_con_el_recorrido_del_simulador():
    for a, w in CASOS:
        r = simular(a, w)
        assert recorrido(r) == recorrido_referencia(a, w), (a.nombre, w)
        assert len(cuadros(r)) == len(w) + 1


def test_transiciones_resaltadas_existen_y_salen_de_estados_activos():
    for a, w in CASOS:
        lista = cuadros(simular(a, w))
        for anterior, c in zip(lista, lista[1:]):
            simbolicas = [t for t in c.transiciones if t[1] != LAMBDA]
            assert all(d in a.destinos(q, s) for q, s, d in c.transiciones), (a.nombre, w)
            assert all(q in anterior.activos and s == c.simbolo for q, s, _ in simbolicas), (a.nombre, w)
            assert {d for _, _, d in simbolicas} <= c.activos


def test_en_un_afd_se_resalta_un_solo_estado_y_una_transicion():
    a = ejemplos.multiplos_de_tres()
    for w in cerradura_kleene(a.alfabeto, 6):
        lista = cuadros(simular(a, w))
        estado = a.inicial
        assert lista[0].activos == {estado}
        for c, s in zip(lista[1:], w):
            siguiente = next(iter(a.destinos(estado, s)))
            assert c.activos == {siguiente}
            assert c.aristas == {(estado, siguiente)}
            estado = siguiente


def test_cinta_leida_y_pendiente():
    r = simular(ejemplos.termina_en_ab(), "abab")
    lista = cuadros(r)
    assert [("".join(c.leido), "".join(c.pendiente)) for c in lista] == [
        ("", "abab"), ("a", "bab"), ("ab", "ab"), ("aba", "b"), ("abab", "")]
    assert [c.simbolo for c in lista] == [None, "a", "b", "a", "b"]


def test_el_veredicto_aparece_solo_al_final():
    for a, w in CASOS[:400]:
        lista = cuadros(simular(a, w))
        assert all(c.veredicto is None for c in lista[:-1])
        assert lista[-1].terminado


def test_simbolo_fuera_del_alfabeto_termina_rechazada():
    r = simular(ejemplos.termina_en_ab(), "abx")
    lista = cuadros(r)
    assert lista[-1].veredicto is False and len(lista) == 3


# ---------------------------------------------------------------------------
# 3. El resultado final coincide con el de las prácticas anteriores
# ---------------------------------------------------------------------------

def test_veredicto_igual_a_la_simulacion_de_la_practica_2():
    for a, w in CASOS:
        assert cuadros(simular(a, w))[-1].veredicto == acepta(a, w), (a.nombre, w)


@pytest.mark.parametrize("a", ejemplos.todos() + aleatorios(10, semilla=21), ids=lambda a: a.nombre)
def test_veredicto_igual_en_el_original_y_en_cada_conversion_de_la_practica_3(a):
    etapas = con_conversiones(a)
    sigma = a.alfabeto if len(a.alfabeto) <= 3 else a.alfabeto[:3]
    for w in cerradura_kleene(list(sigma), 5 if len(sigma) <= 2 else 3):
        veredictos = {cuadros(simular(e, w))[-1].veredicto for e in etapas}
        assert len(veredictos) == 1, (a.nombre, w)


@pytest.mark.parametrize("texto", EXPRESIONES)
def test_veredicto_igual_a_la_expresion_regular_de_la_practica_4(texto):
    r = analizar(texto)
    res = desde_texto(texto)
    for w in cerradura_kleene(["a", "b"], 6):
        esperado = pertenece(r, w)
        for etapa in res.etapas:
            assert cuadros(simular(etapa.automata, w))[-1].veredicto == esperado, (texto, etapa.titulo, w)
