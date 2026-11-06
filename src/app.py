"""Punto de entrada del software interactivo.

Ejecución local:      python src/app.py
En el contenedor:     docker compose up py312  →  http://localhost:8550

La interfaz vive en ``ui/`` y sólo invoca a las funciones puras de ``core/``
(y, en prácticas posteriores, de ``formatos/`` y ``algoritmos/``).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft  # noqa: E402

from ui.aplicacion import main  # noqa: E402

if __name__ == "__main__":
    ft.run(main)
