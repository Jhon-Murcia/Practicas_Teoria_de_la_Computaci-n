"""Exporta los autómatas de ejemplo a automatas/ en .jff, .json y .xml.

Uso:  python herramientas/exportar_ejemplos.py
"""

import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from core import ejemplos  # noqa: E402
from formatos import guardar_archivo  # noqa: E402


def nombre_archivo(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.replace("λ", "lambda")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def main() -> None:
    for titulo, fabrica in ejemplos.EJEMPLOS.items():
        a = fabrica()
        carpeta = RAIZ / "automatas" / ("aplicacion" if fabrica is ejemplos.conexion_tcp else "ejemplos")
        carpeta.mkdir(parents=True, exist_ok=True)
        for ext in ("jff", "json", "xml"):
            ruta = carpeta / f"{nombre_archivo(titulo)}.{ext}"
            guardar_archivo(a, str(ruta))
            print(ruta.relative_to(RAIZ))


if __name__ == "__main__":
    main()
