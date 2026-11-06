"""Pruebas de los proyectos con varios autómatas (Práctica 2)."""

import pytest

from core import ejemplos
from core.automata import ErrorAutomata
from core.proyecto import abrir_proyecto, guardar_proyecto


def test_proyecto_conserva_todos_los_automatas_y_el_actual():
    originales = ejemplos.todos()
    texto = guardar_proyecto(originales, 3)
    leidos, indice = abrir_proyecto(texto)
    assert indice == 3
    assert [a.nombre for a in leidos] == [a.nombre for a in originales]
    assert all(a.misma_definicion(b) for a, b in zip(leidos, originales))
    assert all(a.posiciones == b.posiciones for a, b in zip(leidos, originales))


@pytest.mark.parametrize("texto", ["{", "[]", '{"formato": "otro"}'])
def test_proyecto_invalido(texto):
    with pytest.raises(ErrorAutomata):
        abrir_proyecto(texto)
