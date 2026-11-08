"""Descripción en texto de lo que el usuario tiene en pantalla, para el asistente."""

from __future__ import annotations

from core.automata import Automata

MAX_TRANSICIONES = 80


def describir_automata(a: Automata | None) -> str:
    if a is None:
        return "No hay un autómata seleccionado."
    q = a.quintupla()
    lineas = [
        f"Autómata «{a.nombre}» de tipo {a.tipo}.",
        f"Q = {q['Q']}",
        f"Σ = {q['Σ']}",
        f"q0 = {q['q0']}",
        f"F = {q['F']}",
    ]
    trans = a.lista_transiciones()
    if trans:
        mostradas = trans[:MAX_TRANSICIONES]
        lineas.append("δ: " + "; ".join(f"δ({o}, {s or 'λ'}) ∋ {d}" for o, s, d in mostradas)
                      + (f" (y {len(trans) - MAX_TRANSICIONES} más)" if len(trans) > MAX_TRANSICIONES else ""))
    else:
        lineas.append("δ no tiene transiciones.")
    conflictos = a.conflictos_determinismo()
    if conflictos:
        lineas.append("No es determinista: " + "; ".join(m for _, _, m in conflictos[:5]))
    if a.descripcion:
        lineas.append(f"Descripción: {a.descripcion}")
    return "\n".join(lineas)


# Sugerencias que el asistente ofrece en cada sección del menú.
SUGERENCIAS: dict[str, list[str]] = {
    "inicio": ["¿Qué puedo hacer con AutómataLab?", "¿Qué diferencia hay entre un AFD y un AFND?",
               "Explícame la jerarquía de Chomsky en pocas palabras"],
    "cadenas": ["¿Por qué λ es prefijo de toda cadena?", "¿Cuántas subcadenas distintas puede tener una cadena?",
                "¿Qué diferencia hay entre prefijo y prefijo propio?"],
    "lenguajes": ["¿Qué diferencia hay entre Σ* y Σ⁺?", "¿Por qué Σ⁰ = {λ}?",
                  "¿Por qué crece tan rápido el número de cadenas?"],
    "editor": ["Explícame el autómata que tengo abierto", "¿Qué representa cada estado de este autómata?",
               "¿Por qué este autómata no es determinista?"],
    "simulacion": ["¿Por qué la cadena se aceptó o se rechazó?", "Explícame el paso actual de la simulación",
                   "¿Cómo se simula un AFND sin convertirlo?"],
    "archivos": ["¿Qué es un archivo .jff?", "¿Cómo se representa λ en JFLAP?"],
    "conversiones": ["Explícame el paso actual del algoritmo", "¿Para qué sirve la λ-clausura?",
                     "¿Por qué el AFD puede tener hasta 2ⁿ estados?"],
    "minimizacion": ["Explícame la ronda actual de la partición", "¿Qué significa que dos estados sean equivalentes?",
                     "¿Cómo sé si dos autómatas aceptan el mismo lenguaje?"],
    "expresiones": ["Explícame la expresión regular que escribí", "¿Cómo funciona la construcción de Thompson?",
                    "¿Qué diferencia hay entre + en la teoría y + en Python?"],
    "validadores": ["¿Por qué este texto no es válido?", "¿Qué casos deja fuera este validador?",
                    "¿Por qué una expresión regular no puede validar todo el estándar?"],
    "practica": ["Dame una pista para el ejercicio actual", "¿Cómo empiezo a pensar los estados?",
                 "¿Qué cadenas debería probar antes de evaluar?"],
    "ayuda": ["¿Cómo agrego una transición λ en el editor?", "¿Cómo exporto un autómata a JFLAP?"],
}
