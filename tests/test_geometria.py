"""Pruebas de la geometría del diagrama (sin interfaz)."""

import math

from ui.geometria import RADIO, arista, aristas, caja, estado_en


def test_recta_empieza_y_termina_en_los_bordes():
    a = arista("p", "q", "a", (0, 0), (200, 0), curvar=False)
    assert a.tipo == "recta"
    assert a.inicio == (RADIO, 0) and a.fin == (200 - RADIO, 0)
    assert a.punta[0] == a.fin


def test_aristas_opuestas_se_curvan_hacia_lados_distintos():
    grupos = {("p", "q"): ["a"], ("q", "p"): ["b"]}
    ida, vuelta = aristas({"p": (0, 0), "q": (200, 0)}, grupos)
    assert ida.tipo == vuelta.tipo == "curva"
    assert ida.control1[1] * vuelta.control1[1] < 0


def test_bucle_queda_encima_del_estado():
    b = arista("q", "q", "a, b", (100, 100), (100, 100), curvar=False)
    assert b.tipo == "bucle" and b.pos_etiqueta[1] < 100 - RADIO


def test_etiqueta_y_distancia():
    a = arista("p", "q", "a", (0, 0), (200, 0), curvar=False)
    assert a.contiene_etiqueta(*a.pos_etiqueta)
    assert a.distancia(100, 0) < 1e-6


def test_estado_en_y_caja():
    pos = {"p": (0, 0), "q": (100, 0)}
    assert estado_en(pos, 5, 5) == "p" and estado_en(pos, 50, 50) is None
    x0, y0, x1, y1 = caja(pos)
    assert x0 < 0 < 100 < x1 and y0 < 0 < y1
    assert math.isclose(x1 - x0, 240)


def test_resumen_de_simbolos_en_rangos():
    from ui.geometria import resumir_simbolos
    assert resumir_simbolos([str(i) for i in range(10)]) == "0–9"
    assert resumir_simbolos(["a", "b"]) == "a, b"
    assert resumir_simbolos(["", "+", "-"], lambda s: s or "λ") == "λ, +, -"
    assert resumir_simbolos(["a", "b", "c", "x", "1", "2", "3"]) == "1–3, a–c, x"
