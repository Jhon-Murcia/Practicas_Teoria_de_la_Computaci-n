"""Proyectos: varios autómatas guardados en un solo archivo ``.alab.json``."""

from __future__ import annotations

import json

from core.automata import Automata, ErrorAutomata

FORMATO = "automatalab-proyecto"
VERSION = 1


def guardar_proyecto(automatas: list[Automata], indice: int = 0) -> str:
    datos = {
        "formato": FORMATO,
        "version": VERSION,
        "actual": indice,
        "automatas": [a.a_dict() for a in automatas],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def abrir_proyecto(texto: str | bytes) -> tuple[list[Automata], int]:
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ErrorAutomata(f"El proyecto no es un JSON válido: {exc.msg}.") from exc
    if not isinstance(datos, dict) or datos.get("formato") != FORMATO:
        raise ErrorAutomata("El archivo no es un proyecto de AutómataLab.")
    automatas = [Automata.de_dict(d) for d in datos.get("automatas", [])]
    indice = int(datos.get("actual", 0))
    return automatas, max(0, min(indice, len(automatas) - 1))
