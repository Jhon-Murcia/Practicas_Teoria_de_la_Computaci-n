"""Punto de entrada del software interactivo.

Ejecución local:      python src/app.py
En el contenedor:     docker compose up py312  →  http://localhost:8550
En Render:            el servicio define PORT; la aplicación escucha en ese puerto.

La interfaz vive en ``ui/`` y sólo invoca a las funciones puras de ``core/``,
``formatos/``, ``algoritmos/``, ``practica/`` e ``ia/``.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Render (y otros servicios en la nube) indican el puerto en la variable PORT;
# en ese caso la aplicación se sirve como página web en todas las interfaces.
if os.getenv("PORT"):
    os.environ["FLET_SERVER_PORT"] = os.environ["PORT"]
    os.environ.setdefault("FLET_FORCE_WEB_SERVER", "true")
    os.environ.setdefault("FLET_SERVER_IP", "0.0.0.0")

import flet as ft  # noqa: E402

from ui.aplicacion import main  # noqa: E402

if __name__ == "__main__":
    ft.run(main)
