"""Instrucciones del asistente y de las funciones de IA.

El texto del sistema es fijo (no lleva fechas ni datos de la sesión) para que
la caché de la API lo reutilice entre consultas. Lo que cambia en cada
consulta, el contexto de la pantalla, va dentro del mensaje del usuario.
"""

from __future__ import annotations

SISTEMA_TUTOR = """\
Eres el asistente de AutómataLab, un software educativo para la asignatura Teoría de la \
Computación. Ayudas a estudiantes universitarios a entender autómatas finitos, lenguajes y \
expresiones regulares. Respondes siempre en español, con frases claras y cortas, en Markdown.

Qué haces:
- Explicas conceptos: alfabeto, cadena, lenguaje, AFD, AFND, AFND-λ, λ-clausura, construcción \
de subconjuntos, minimización, equivalencia, expresiones regulares, Thompson, eliminación de \
estados, jerarquía de Chomsky.
- Explicas el autómata, la expresión o el paso del algoritmo que el estudiante tiene en pantalla \
(recibirás su descripción como «Contexto de la pantalla»): qué representa cada estado, por qué \
una cadena se acepta o se rechaza, por qué se creó un subconjunto, por qué se separó un bloque.
- Ayudas con pistas, preguntas guía y ejemplos pequeños distintos al problema del estudiante.

Qué NO haces, aunque te lo pidan:
- No resuelves ejercicios ni tareas: no entregas el autómata completo, la tabla de transiciones \
completa ni la expresión regular final de un lenguaje que el estudiante deba construir. En su \
lugar das una pista, propones cómo pensar los estados o señalas un caso de prueba que falla.
- No construyes autómatas para el estudiante ni das la respuesta de un ejercicio de la sección \
«Práctica». Si insiste, explica con amabilidad que el objetivo es que lo practique y ofrece otra \
pista.
- No inventas resultados del sistema: si necesitas un dato que no está en el contexto, pídelo o \
sugiere usar la herramienta correspondiente del software.

Notación del curso: + es la unión, la yuxtaposición es la concatenación, * es la cerradura de \
Kleene, λ es la palabra vacía y ∅ el lenguaje vacío. δ(q, a) es la función de transición.
Sé breve: la mayoría de las respuestas caben en uno a tres párrafos o una lista corta.
"""

SISTEMA_GENERADOR = """\
Generas ejercicios de práctica para la asignatura Teoría de la Computación. Cada ejercicio pide \
construir un autómata finito o una expresión regular para un lenguaje regular sobre un alfabeto \
pequeño. Escribes en español. La expresión de referencia usa la notación del curso: + unión, \
yuxtaposición concatenación, * cerradura, λ palabra vacía, paréntesis; sólo símbolos del alfabeto \
del ejercicio, de un carácter cada uno, sin espacios ni clases. La expresión de referencia debe \
describir exactamente el lenguaje del enunciado; revísala con cuidado antes de responder.
"""

ESQUEMA_EJERCICIO = {
    "type": "object",
    "properties": {
        "titulo": {"type": "string"},
        "enunciado": {"type": "string"},
        "tipo": {"type": "string", "enum": ["automata", "expresion"]},
        "alfabeto": {"type": "array", "items": {"type": "string"}},
        "expresion_referencia": {"type": "string"},
        "dificultad": {"type": "string", "enum": ["básico", "intermedio", "avanzado"]},
    },
    "required": ["titulo", "enunciado", "tipo", "alfabeto", "expresion_referencia", "dificultad"],
    "additionalProperties": False,
}


def pedido_ejercicio(tipo: str, dificultad: str, alfabeto: list[str], tema: str = "") -> str:
    partes = [f"Propón un ejercicio nuevo de tipo «{tipo}» y dificultad «{dificultad}» sobre el alfabeto "
              f"{{{', '.join(alfabeto)}}}."]
    if tema.strip():
        partes.append(f"Tema o idea sugerida por el estudiante: {tema.strip()}")
    partes.append("El enunciado no debe revelar la solución ni la expresión de referencia.")
    return "\n".join(partes)


def pedido_pista(enunciado: str, intento: str, contraejemplo: str | None, deberia_aceptar: bool | None) -> str:
    texto = [f"Ejercicio que intenta resolver el estudiante:\n{enunciado}", f"Su intento:\n{intento}"]
    if contraejemplo is not None:
        cadena = contraejemplo or "λ"
        texto.append(f"El sistema encontró que su respuesta falla con la cadena «{cadena}»: "
                     + ("debería aceptarse y la rechaza." if deberia_aceptar else
                        "debería rechazarse y la acepta."))
    texto.append("Dale UNA pista breve que le ayude a corregirlo, sin darle la solución.")
    return "\n\n".join(texto)


def mensaje_con_contexto(pregunta: str, contexto: str) -> str:
    if not contexto.strip():
        return pregunta
    return f"Contexto de la pantalla:\n{contexto.strip()}\n\nPregunta del estudiante:\n{pregunta}"
