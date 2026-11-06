"""Pruebas de los algoritmos de la Práctica 3.

Para cada caso se comprueba que el autómata original, el AFN sin λ, el AFD de
subconjuntos y el AFD mínimo aceptan exactamente las mismas cadenas, y que el
AFD mínimo no tiene más estados que el AFD del que procede.

Longitud de comparación: todas las cadenas de Σ* de longitud ≤ 8 (511 cadenas
sobre {a, b}). Los autómatas de prueba tienen a lo sumo 6 estados, así que esa
longitud alcanza todos los estados y recorre cada ciclo más de una vez. Para
alfabetos de 4 a 6 símbolos se usa longitud 4 y para alfabetos mayores
(TCP: 11 eventos; decimales: 13 símbolos) longitud 3, porque |Σ|ⁿ crece
demasiado (13⁴ = 28 561 cadenas por autómata). Como una exploración finita no es una demostración, cada caso se
verifica además con la prueba de equivalencia exacta (isomorfismo de los AFD
mínimos), que no depende de ninguna longitud.

Además de los ejemplos integrados y de autómatas aleatorios (semilla fija),
se prueban todos los ``.jff`` de ``automatas/practica3/casos-de-prueba/``.
"""

import random
from pathlib import Path

import pytest

from core import ejemplos
from core.automata import LAMBDA, Automata
from core.lenguajes import cerradura_kleene
from core.simulacion import acepta, informe_lote, leer_lineas, validar_lote
from formatos import leer_archivo
from algoritmos.cerradura import cerradura, cerradura_con_pasos, tabla_cerraduras
from algoritmos.eliminacion_lambda import eliminar_lambda
from algoritmos.equivalencia import comparar, equivalentes
from algoritmos.minimizacion import completar, minimizar, refinar, renombrar_canonico, tabla_distinguibles
from algoritmos.subconjuntos import construir_afd

LONGITUD = 8
CARPETA = Path(__file__).resolve().parents[1] / "automatas" / "practica3" / "casos-de-prueba"


def aleatorio(semilla: int, n: int = 4, lambda_: bool = True) -> Automata:
    rnd = random.Random(semilla)
    a = Automata(nombre=f"aleatorio-{semilla}")
    for i in range(n):
        a.agregar_estado(f"q{i}")
    a.alfabeto = ["a", "b"]
    for q in a.estados:
        for s in ["a", "b"] + ([LAMBDA] if lambda_ else []):
            for d in a.estados:
                if rnd.random() < (0.12 if s == LAMBDA else 0.3):
                    a.agregar_transicion(q, s, d)
    a.aceptacion = {q for q in a.estados if rnd.random() < 0.35} or {a.estados[-1]}
    return a


def casos():
    lista = [(f(), n) for n, f in ejemplos.EJEMPLOS.items()]
    lista += [(aleatorio(s), f"aleatorio-{s}") for s in range(12)]
    lista += [(leer_archivo(str(r)), r.name) for r in sorted(CARPETA.glob("*.jff"))]
    return lista


CASOS = casos()


def mismo_lenguaje(a: Automata, b: Automata, n: int = LONGITUD) -> bool:
    alfabeto = sorted(set(a.alfabeto) | set(b.alfabeto))
    if len(alfabeto) > 6:
        n = 3
    elif len(alfabeto) > 3:
        n = 4
    return all(acepta(a, w) == acepta(b, w) for w in cerradura_kleene(alfabeto, n))


@pytest.mark.parametrize("a,nombre", CASOS, ids=[n for _, n in CASOS])
def test_la_cadena_de_conversiones_preserva_el_lenguaje(a, nombre):
    sin_lambda, _, _ = eliminar_lambda(a)
    assert not sin_lambda.tiene_lambda()
    afd, _, _ = construir_afd(sin_lambda)
    assert afd.es_determinista() and afd.es_completo()
    minimo, _, _ = minimizar(afd)
    for b in (sin_lambda, afd, minimo):
        assert mismo_lenguaje(a, b)
    assert len(minimo.estados) <= len(afd.estados)
    assert equivalentes(a, minimo) and equivalentes(afd, minimo)


@pytest.mark.parametrize("a,nombre", CASOS, ids=[n for _, n in CASOS])
def test_subconjuntos_directo_sobre_afnd_lambda(a, nombre):
    afd, _, _ = construir_afd(a)
    assert mismo_lenguaje(a, afd)


# --- λ-clausura ------------------------------------------------------------

def test_cerradura_y_sus_pasos():
    a = ejemplos.a_estrella_b_estrella_c_estrella()
    assert tabla_cerraduras(a) == {"p": {"p", "q", "r"}, "q": {"q", "r"}, "r": {"r"}}
    final, pasos = cerradura_con_pasos(a, "p")
    assert final == {"p", "q", "r"} and pasos[-1].tipo == "exito"


def test_cerradura_con_ciclo_lambda():
    a = Automata.desde_tabla(["x", "y", "z"], ["a"], "x", ["z"],
                             {("x", LAMBDA): "y", ("y", LAMBDA): {"x", "z"}})
    assert cerradura(a, {"x"}) == {"x", "y", "z"}
    assert cerradura(a, {"z"}) == {"z"}


# --- Eliminación de λ --------------------------------------------------------

def test_eliminacion_lambda_marca_nuevos_estados_de_aceptacion():
    a = ejemplos.anexo_lambda()
    b, _, info = eliminar_lambda(a)
    assert info["nuevas_finales"] == ["q0"]       # λ-clausura(q0) contiene q1 ∈ F
    assert b.aceptacion == {"q0", "q1"}
    assert set(b.destinos("q0", "a")) == {"q1"}
    assert set(b.destinos("q0", "b")) == {"q0", "q1"}
    assert ("q0", "b", "q1") in info["agregadas"]


# --- Construcción de subconjuntos ----------------------------------------------

def test_subconjuntos_solo_alcanzables_y_cota_2_a_la_n():
    a = ejemplos.tercero_desde_el_final()
    afd, pasos, tabla = construir_afd(a)
    assert len(afd.estados) == 8 == 2 ** (len(a.estados) - 1)   # la familia alcanza la cota
    assert len(tabla) - 1 == len(afd.estados)
    assert all(nombre.startswith("{q0") for nombre in afd.estados)   # q0 en todos: sólo alcanzables


def test_subconjuntos_termina_en_ab():
    afd, _, _ = construir_afd(ejemplos.termina_en_ab())
    assert sorted(afd.estados) == ["{q0,q1}", "{q0,q2}", "{q0}"]
    assert afd.aceptacion == {"{q0,q2}"}


def test_subconjuntos_incluye_el_vacio_como_estado_de_error():
    afd, _, _ = construir_afd(ejemplos.anexo_lambda())
    assert "∅" in afd.estados
    assert all(afd.destinos("∅", s) == {"∅"} for s in afd.alfabeto)


# --- Minimización -------------------------------------------------------------

def test_minimizacion_fusiona_equivalentes_y_quita_inaccesibles():
    # Dos copias del AFD de paridad más un estado inaccesible.
    a = Automata.desde_tabla(
        ["p0", "i0", "p1", "i1", "x"], ["a", "b"], "p0", ["p0", "p1"],
        {("p0", "a"): "i0", ("p0", "b"): "p1", ("p1", "a"): "i1", ("p1", "b"): "p0",
         ("i0", "a"): "p1", ("i0", "b"): "i1", ("i1", "a"): "p0", ("i1", "b"): "i0",
         ("x", "a"): "x", ("x", "b"): "p0"})
    m, pasos, info = minimizar(a)
    assert info["inaccesibles"] == ["x"]
    assert len(m.estados) == 2
    assert sorted(map(sorted, info["equivalentes"])) == [["i0", "i1"], ["p0", "p1"]]
    assert mismo_lenguaje(a, m)


def test_minimo_de_afd_parcial_no_crece():
    a = ejemplos.conexion_tcp()
    m, _, info = minimizar(a)
    assert info["sumidero"] is not None
    assert len(m.estados) <= len(a.estados)
    assert mismo_lenguaje(a, m)


def test_rondas_de_refinamiento():
    a, _ = completar(ejemplos.multiplos_de_tres())
    rondas = refinar(a)
    assert len(rondas[0]) == 2 and len(rondas[-1]) == 3


def test_tabla_de_pares_coincide_con_particiones():
    a = ejemplos.multiplos_de_tres()
    rondas, estados = tabla_distinguibles(a)
    total = len(estados) * (len(estados) - 1) // 2
    assert len(rondas[-1]) == total   # el AFD ya es mínimo: todos los pares son distinguibles


def test_minimizar_rechaza_un_afnd():
    with pytest.raises(ValueError, match="determinista"):
        minimizar(ejemplos.termina_en_ab())


def test_renombrar_canonico():
    m, _, _ = minimizar(construir_afd(ejemplos.termina_en_ab())[0])
    r = renombrar_canonico(m)
    assert r.inicial == "q0" and set(r.estados) == {"q0", "q1", "q2"}
    assert mismo_lenguaje(m, r)


# --- Equivalencia ---------------------------------------------------------------

def test_equivalencia_entre_un_afnd_y_su_afd():
    comp = comparar(ejemplos.termina_en_ab(), construir_afd(ejemplos.termina_en_ab())[0])
    assert comp.equivalentes and len(comp.correspondencia) == 3


def test_no_equivalentes_con_contraejemplo_minimo():
    comp = comparar(ejemplos.a_par(), ejemplos.termina_en_ab())
    assert not comp.equivalentes
    w = comp.contraejemplo
    assert acepta(ejemplos.a_par(), w) != acepta(ejemplos.termina_en_ab(), w)
    assert w == ""   # λ tiene cero aes (par) y no termina en ab


def test_equivalencia_con_alfabetos_distintos():
    a = Automata.desde_tabla(["s"], ["a"], "s", ["s"], {("s", "a"): "s"})
    b = Automata.desde_tabla(["s"], ["a", "b"], "s", ["s"], {("s", "a"): "s", ("s", "b"): "s"})
    comp = comparar(a, b)
    assert not comp.equivalentes and comp.contraejemplo == "b"


# --- Validación de varias cadenas --------------------------------------------

def test_validacion_por_lotes_e_informe():
    a = ejemplos.termina_en_ab()
    cadenas = leer_lineas("ab\n\nba\nλ\n  aab  \n")
    assert cadenas == ["ab", "ba", "", "aab"]
    resultados = validar_lote(a, cadenas)
    assert [r.aceptada for r in resultados] == [True, False, False, True]
    informe = informe_lote(a, resultados, "pruebas.txt")
    assert "aceptadas: 2" in informe and "RECHAZADA" in informe and "pruebas.txt" in informe
