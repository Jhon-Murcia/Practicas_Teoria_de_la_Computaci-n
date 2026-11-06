"""Formato ``.json`` propio (esquema del Anexo 3 de la Práctica 2).

::

    {
      "tipo": "AFND-lambda",
      "nombre": "Ejemplo",
      "alfabeto": ["a", "b"],
      "estados": ["q0", "q1"],
      "inicial": "q0",
      "aceptacion": ["q1"],
      "transiciones": [
        { "desde": "q0", "lee": "a", "hacia": ["q1"] },
        { "desde": "q0", "lee": "",  "hacia": ["q1"] }      ← λ: "lee" vacío
      ],
      "posiciones": { "q0": [80, 120], "q1": [240, 120] }   ← opcional
    }

``tipo`` es informativo: al leer se recalcula a partir de δ. ``hacia`` es una
lista porque un AFND puede tener varios destinos; también se acepta una cadena.
"""

from __future__ import annotations

import json

from core.automata import AFND_LAMBDA, Automata
from formatos.jff import ErrorFormato

TIPOS_ARCHIVO = {"AFD": "AFD", "AFND": "AFND", AFND_LAMBDA: "AFND-lambda"}


def escribir_json(a: Automata) -> str:
    a.validar(estricto=True)
    datos = a.a_dict()
    datos["tipo"] = TIPOS_ARCHIVO[a.tipo]
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def leer_json(texto: str | bytes, nombre: str = "Autómata") -> Automata:
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ErrorFormato(f"El archivo .json no es válido (línea {exc.lineno}, columna {exc.colno}): "
                           f"{exc.msg}.") from exc
    if not isinstance(datos, dict):
        raise ErrorFormato("El archivo .json debe contener un objeto con la definición del autómata.")
    datos.setdefault("nombre", nombre)
    try:
        return Automata.de_dict(datos)
    except ErrorFormato:
        raise
    except (ValueError, TypeError) as exc:
        raise ErrorFormato(f"Definición inválida en el .json: {exc}") from exc
