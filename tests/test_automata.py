"""Pruebas del modelo de autómata y de la simulación (Práctica 2)."""

import pytest

from core import ejemplos
from core.automata import AFD, AFND, AFND_LAMBDA, LAMBDA, Automata, ErrorAutomata
from core.lenguajes import cerradura_kleene
from core.simulacion import acepta, arbol_computacion, caminos, cerradura_lambda, simular


# --- Clasificación ---------------------------------------------------------

def test_clasificacion_de_los_ejemplos():
    assert ejemplos.multiplos_de_tres().tipo == AFD
    assert ejemplos.termina_en_ab().tipo == AFND
    assert ejemplos.anexo_lambda().tipo == AFND_LAMBDA
    assert ejemplos.conexion_tcp().tipo == AFD


def test_conflictos_de_determinismo_indican_estado_y_simbolo():
    conflictos = ejemplos.termina_en_ab().conflictos_determinismo()
    assert [(q, s) for q, s, _ in conflictos] == [("q0", "a")]
    conflictos = ejemplos.anexo_lambda().conflictos_determinismo()
    assert ("q0", "λ") in [(q, s) for q, s, _ in conflictos]


def test_completitud():
    assert ejemplos.multiplos_de_tres().es_completo()
    a = ejemplos.termina_en_ab()
    assert not a.es_completo()
    assert ("q2", "a") in a.faltantes()


# --- Edición ---------------------------------------------------------------

def test_agregar_y_eliminar_estados_y_transiciones():
    a = Automata()
    q0 = a.agregar_estado()
    q1 = a.agregar_estado()
    assert (q0, q1, a.inicial) == ("q0", "q1", "q0")
    a.agregar_transicion("q0", "a", "q1")
    a.agregar_transicion("q1", LAMBDA, "q0")
    assert a.alfabeto == ["a"]
    assert a.tipo == AFND_LAMBDA
    a.eliminar_transicion("q1", LAMBDA, "q0")
    assert a.tipo == AFD
    a.eliminar_estado("q1")
    assert a.transiciones == {} and a.estados == ["q0"]


def test_renombrar_actualiza_toda_la_quintupla():
    a = ejemplos.termina_en_ab()
    a.renombrar_estado("q0", "inicio")
    a.renombrar_estado("q2", "fin")
    assert a.inicial == "inicio" and a.aceptacion == {"fin"}
    assert a.destinos("inicio", "a") == {"inicio", "q1"}
    assert a.destinos("q1", "b") == {"fin"}


def test_errores_de_edicion():
    a = Automata()
    a.agregar_estado("q0")
    with pytest.raises(ErrorAutomata):
        a.agregar_estado("q0")
    with pytest.raises(ErrorAutomata):
        a.agregar_transicion("q0", "a", "q9")
    with pytest.raises(ErrorAutomata):
        a.agregar_simbolo(LAMBDA)


def test_validacion_detecta_inconsistencias():
    a = Automata(estados=["q0"], alfabeto=["a"], inicial="q5", aceptacion={"q7"})
    errores = a.validar()
    assert any("inicial" in e for e in errores)
    assert any("q7" in e for e in errores)


def test_alcanzables_e_inaccesibles():
    a = ejemplos.multiplos_de_tres()
    a.agregar_estado("aislado")
    assert a.inaccesibles() == ["aislado"]


def test_tokenizar_simbolos_de_varios_caracteres():
    a = Automata.desde_tabla(["q0"], ["ab", "c"], "q0", ["q0"], {("q0", "ab"): "q0", ("q0", "c"): "q0"})
    assert a.tokenizar("abcab") == ["ab", "c", "ab"]
    assert a.tokenizar("ab c ab") == ["ab", "c", "ab"]


# --- Simulación de AFD -----------------------------------------------------

@pytest.mark.parametrize("w", ["", "0", "11", "110", "1001", "1111", "10010"])
def test_afd_acepta_multiplos_de_tres(w):
    assert acepta(ejemplos.multiplos_de_tres(), w)


@pytest.mark.parametrize("w", ["1", "10", "100", "101", "111", "1000"])
def test_afd_rechaza_no_multiplos(w):
    assert not acepta(ejemplos.multiplos_de_tres(), w)


def test_afd_coincide_con_la_aritmetica_en_todas_las_cadenas():
    a = ejemplos.multiplos_de_tres()
    for w in cerradura_kleene(["0", "1"], 10):
        assert acepta(a, w) == (int(w or "0", 2) % 3 == 0)


def test_traza_del_afd_tiene_un_estado_por_paso():
    r = simular(ejemplos.multiplos_de_tres(), "110")
    assert [sorted(p.despues) for p in r.pasos] == [["r1"], ["r0"], ["r0"]]
    assert [p.transiciones for p in r.pasos][0] == [("r0", "1", "r1")]
    assert r.aceptada


def test_simbolo_fuera_del_alfabeto_se_informa_con_su_posicion():
    r = simular(ejemplos.multiplos_de_tres(), "1021")
    assert not r.aceptada and r.posicion_error == 3 and "«2»" in r.error


def test_afd_parcial_rechaza_cuando_no_hay_transicion():
    r = simular(ejemplos.termina_en_ab(), "abba")
    assert not r.aceptada


# --- Simulación de AFND ----------------------------------------------------

def test_afnd_sigue_todos_los_caminos():
    a = ejemplos.termina_en_ab()
    r = simular(a, "aab")
    assert [sorted(p.despues) for p in r.pasos] == [["q0", "q1"], ["q0", "q1"], ["q0", "q2"]]
    assert r.aceptada


def test_afnd_coincide_con_la_definicion_del_lenguaje():
    a = ejemplos.termina_en_ab()
    for w in cerradura_kleene(["a", "b"], 9):
        assert acepta(a, w) == w.endswith("ab")


def test_tercero_desde_el_final():
    a = ejemplos.tercero_desde_el_final()
    for w in cerradura_kleene(["0", "1"], 8):
        assert acepta(a, w) == (len(w) >= 3 and w[-3] == "1")


# --- AFND-λ: aceptación que requiere la λ-clausura ---------------------------

def test_lambda_clausura():
    a = ejemplos.a_estrella_b_estrella_c_estrella()
    assert cerradura_lambda(a, {"p"}) == {"p", "q", "r"}
    assert cerradura_lambda(a, {"q"}) == {"q", "r"}
    assert cerradura_lambda(a, {"r"}) == {"r"}


def test_afnd_lambda_acepta_la_vacia_solo_por_la_clausura():
    # q0 no es de aceptación; λ se acepta porque q1 ∈ λ-clausura(q0).
    a = ejemplos.anexo_lambda()
    r = simular(a, "")
    assert r.inicio_sin_cerradura == {"q0"} and r.inicio == {"q0", "q1"}
    assert r.aceptada


def test_afnd_lambda_acepta_b_gracias_a_la_clausura():
    a = ejemplos.anexo_lambda()
    assert acepta(a, "bbb") and acepta(a, "a") and not acepta(a, "ab")


def test_afnd_lambda_a_estrella_b_estrella_c_estrella():
    a = ejemplos.a_estrella_b_estrella_c_estrella()
    import re
    for w in cerradura_kleene(["a", "b", "c"], 6):
        assert acepta(a, w) == bool(re.fullmatch("a*b*c*", w))


@pytest.mark.parametrize("w,esperado", [("-12.5", True), ("+.5", True), ("7.", True), ("3.14", True),
                                        (".", False), ("12", False), ("+-1.0", False), ("", False)])
def test_numeros_decimales(w, esperado):
    assert acepta(ejemplos.numeros_decimales(), w) == esperado


def test_paso_registra_transiciones_lambda_usadas():
    a = ejemplos.a_estrella_b_estrella_c_estrella()
    r = simular(a, "b")
    assert ("p", LAMBDA, "q") in r.lambda_inicio
    paso = r.pasos[0]
    assert paso.movimiento == {"q"} and paso.despues == {"q", "r"}
    assert ("q", LAMBDA, "r") in paso.transiciones_lambda


# --- Árbol de computación (caminos múltiples) ------------------------------------

def test_arbol_muestra_bifurcaciones():
    arbol = arbol_computacion(ejemplos.termina_en_ab(), "ab")
    assert arbol.caminos_aceptacion == 1
    desenlaces = sorted(d for _, d in caminos(arbol))
    assert desenlaces == ["acepta", "rechaza"]


def test_arbol_corta_ciclos_lambda():
    a = Automata.desde_tabla(["p", "q"], ["a"], "p", ["q"], {("p", LAMBDA): "q", ("q", LAMBDA): "p"})
    arbol = arbol_computacion(a, "")
    assert arbol.caminos_aceptacion >= 1
    assert any(d == "ciclo λ" for _, d in caminos(arbol))


def test_arbol_respeta_el_limite_de_nodos():
    arbol = arbol_computacion(ejemplos.tercero_desde_el_final(), "1" * 30, max_nodos=50)
    assert arbol.truncado and arbol.nodos <= 50


# --- Autómata de aplicación: conexión TCP ------------------------------------------

@pytest.mark.parametrize("w,esperado", [
    ("", True),            # sin eventos: la conexión sigue cerrada
    ("PC", True),          # escuchar y cerrar
    ("PSKFCK", True),      # cierre pasivo completo
    ("AYCKFT", True),      # cierre activo con TIME_WAIT
    ("AYCXT", True),       # FIN+ACK simultáneo
    ("AYCFKT", True),      # cierre simultáneo (CLOSING)
    ("PSRSKCKFT", True),   # RST vuelve a LISTEN y luego se completa
    ("PSK", False),        # queda ESTABLISHED
    ("AYCKF", False),      # queda en TIME_WAIT esperando el temporizador
    ("K", False),          # ACK sin conexión: no hay transición
    ("PZ", False),         # Z no es un evento
])
def test_conexion_tcp(w, esperado):
    assert acepta(ejemplos.conexion_tcp(), w) == esperado


def test_todos_los_ejemplos_son_validos():
    for a in ejemplos.todos():
        assert a.validar() == []
        assert set(a.posiciones) == set(a.estados)
