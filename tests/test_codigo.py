"""El código fuente compila sin advertencias de sintaxis.

Se compila desde el texto (no desde los .pyc en caché), porque una secuencia
de escape inválida sólo avisa la primera vez que se compila el archivo.
"""

import warnings
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
ARCHIVOS = sorted(SRC.rglob("*.py"))


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=[str(p.relative_to(SRC)) for p in ARCHIVOS])
def test_compila_sin_advertencias(ruta):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(ruta.read_text(encoding="utf-8"), str(ruta), "exec")


def test_ninguna_fila_con_wrap_tiene_hijos_expandidos():
    """En Flet, ``Row(wrap=True)`` con un hijo ``expand`` no se dibuja (queda un bloque gris)."""
    import ast
    errores = []
    for ruta in ARCHIVOS:
        for n in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "Row":
                wrap = any(k.arg == "wrap" and getattr(k.value, "value", False) is True for k in n.keywords)
                if wrap and n.args and isinstance(n.args[0], ast.List):
                    for h in n.args[0].elts:
                        if isinstance(h, ast.Call) and any(k.arg == "expand" for k in h.keywords):
                            errores.append(f"{ruta.name}:{n.lineno}")
    assert not errores, errores
