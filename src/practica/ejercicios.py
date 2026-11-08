"""Ejercicios de práctica y su evaluación automática.

La evaluación no usa IA: la respuesta del estudiante (un autómata o una
expresión regular) se compara con una expresión de referencia oculta mediante
la prueba de equivalencia de AFD mínimos. Si no son equivalentes se muestra la
cadena más corta en la que difieren. La IA sólo genera enunciados nuevos y da
pistas; un ejercicio generado se valida antes de aceptarse.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from core import ejemplos
from core.automata import Automata
from core.expresion_regular import ErrorSintaxis, analizar, muestra, simbolos
from core.simulacion import acepta
from algoritmos.equivalencia import comparar
from algoritmos.tuberia import desde_expresion

TIPOS = {"automata": "Construir un autómata", "expresion": "Escribir una expresión regular"}


@dataclass(frozen=True)
class Ejercicio:
    clave: str
    titulo: str
    enunciado: str
    tipo: str                       # "automata" | "expresion"
    alfabeto: tuple
    referencia: str                 # expresión oculta en la notación del curso
    dificultad: str = "básico"
    exigir_afd: bool = False
    generado_por_ia: bool = False


@dataclass
class Evaluacion:
    correcto: bool
    mensaje: str
    contraejemplo: Optional[str] = None
    deberia_aceptar: Optional[bool] = None
    avisos: list[str] = field(default_factory=list)


BANCO: list[Ejercicio] = [
    Ejercicio("empieza-a", "Empieza con a", "Diseña un AFD que acepte las cadenas sobre {a, b} que empiezan con a.",
              "automata", ("a", "b"), "a(a+b)*", exigir_afd=True),
    Ejercicio("termina-bb", "Termina en bb", "Diseña un AFD que acepte las cadenas sobre {a, b} que terminan en bb.",
              "automata", ("a", "b"), "(a+b)*bb", exigir_afd=True),
    Ejercicio("contiene-aba", "Contiene aba", "Diseña un autómata (AFD o AFND) que acepte las cadenas sobre {a, b} "
              "que contienen la subcadena aba.", "automata", ("a", "b"), "(a+b)*aba(a+b)*", "intermedio"),
    Ejercicio("b-impar", "Número impar de bes", "Diseña un AFD que acepte las cadenas sobre {a, b} con un número "
              "impar de bes.", "automata", ("a", "b"), "a*ba*(ba*ba*)*", exigir_afd=True),
    Ejercicio("longitud-par", "Longitud par", "Diseña un AFD que acepte las cadenas binarias de longitud par "
              "(incluida la vacía).", "automata", ("0", "1"), "((0+1)(0+1))*", exigir_afd=True),
    Ejercicio("sin-11", "Sin dos unos seguidos", "Diseña un AFD que acepte las cadenas binarias que no contienen la "
              "subcadena 11.", "automata", ("0", "1"), "(0+10)*(λ+1)", "intermedio", exigir_afd=True),
    Ejercicio("a-multiplo-3", "Aes múltiplo de 3", "Diseña un AFD que acepte las cadenas sobre {a, b} cuyo número "
              "de aes es múltiplo de 3.", "automata", ("a", "b"), "b*(ab*ab*ab*)*", "intermedio", exigir_afd=True),
    Ejercicio("tercero-final", "Tercero desde el final", "Diseña un AFND que acepte las cadenas sobre {a, b} cuyo "
              "tercer símbolo desde el final es a.", "automata", ("a", "b"), "(a+b)*a(a+b)(a+b)", "avanzado"),
    Ejercicio("lambda-ab", "a* seguido de b*", "Diseña un AFND-λ que acepte el lenguaje {aⁿbᵐ : n, m ≥ 0}.",
              "automata", ("a", "b"), "a*b*"),
    Ejercicio("dos-a", "Exactamente dos aes", "Escribe una expresión regular para las cadenas sobre {a, b} con "
              "exactamente dos aes.", "expresion", ("a", "b"), "b*ab*ab*"),
    Ejercicio("mismo-extremo", "Mismo símbolo en los extremos", "Escribe una expresión regular para las cadenas "
              "binarias no vacías que empiezan y terminan con el mismo símbolo.", "expresion", ("0", "1"),
              "0+1+0(0+1)*0+1(0+1)*1", "intermedio"),
    Ejercicio("identificador", "Identificadores", "Sea l una letra y d un dígito. Escribe una expresión regular para "
              "los identificadores: una letra seguida de cualquier cantidad de letras o dígitos.", "expresion",
              ("l", "d"), "l(l+d)*"),
    Ejercicio("sin-bb", "Sin bb", "Escribe una expresión regular para las cadenas sobre {a, b} que no contienen la "
              "subcadena bb.", "expresion", ("a", "b"), "(a+ba)*(λ+b)", "avanzado"),
]


def buscar(clave: str) -> Optional[Ejercicio]:
    return next((e for e in BANCO if e.clave == clave), None)


def automata_referencia(e: Ejercicio) -> Automata:
    return desde_expresion(analizar(e.referencia)).minimo


def _comparar_con_referencia(e: Ejercicio, candidato: Automata) -> Evaluacion:
    referencia = automata_referencia(e)
    comp = comparar(candidato, referencia)
    if comp.equivalentes:
        return Evaluacion(True, "¡Correcto! Tu respuesta reconoce exactamente el lenguaje pedido.")
    w = comp.contraejemplo
    if w is None:
        return Evaluacion(False, "Tu respuesta no reconoce el lenguaje pedido.")
    debe = acepta(referencia, list(w))
    texto = w or "λ"
    return Evaluacion(False, f"Todavía no. Prueba con la cadena «{texto}»: "
                             + ("pertenece al lenguaje, pero tu respuesta la rechaza."
                                if debe else "no pertenece al lenguaje, pero tu respuesta la acepta."),
                      w, debe)


def evaluar_automata(e: Ejercicio, a: Automata) -> Evaluacion:
    errores = a.validar()
    if errores:
        return Evaluacion(False, "El autómata está incompleto: " + errores[0])
    fuera = sorted(set(a.alfabeto) - set(e.alfabeto))
    if fuera:
        return Evaluacion(False, f"El autómata usa símbolos que no están en Σ = {{{', '.join(e.alfabeto)}}}: "
                                 f"{', '.join(fuera)}.")
    resultado = _comparar_con_referencia(e, a)
    if e.exigir_afd and not a.es_determinista():
        q, s, motivo = a.conflictos_determinismo()[0]
        aviso = f"El ejercicio pide un AFD y tu autómata no es determinista ({motivo})."
        if resultado.correcto:
            return Evaluacion(False, "El lenguaje es el correcto, pero " + aviso[0].lower() + aviso[1:])
        resultado.avisos.append(aviso)
    return resultado


def evaluar_expresion(e: Ejercicio, texto: str) -> Evaluacion:
    try:
        r = analizar(texto)
    except ErrorSintaxis as exc:
        return Evaluacion(False, f"La expresión está mal formada en la posición {exc.posicion}: {exc.mensaje}")
    fuera = sorted(simbolos(r) - set(e.alfabeto))
    if fuera:
        return Evaluacion(False, f"La expresión usa símbolos fuera de Σ = {{{', '.join(e.alfabeto)}}}: "
                                 f"{', '.join(fuera)}.")
    return _comparar_con_referencia(e, desde_expresion(r).minimo)


# ---------------------------------------------------------------------------
# Ejercicios generados por la IA
# ---------------------------------------------------------------------------

def validar_generado(datos: dict) -> Ejercicio:
    """Convierte la respuesta de la IA en un ejercicio, o lanza ``ValueError``."""
    alfabeto = tuple(dict.fromkeys(str(s) for s in datos.get("alfabeto", [])))
    if not 1 <= len(alfabeto) <= 4 or any(len(s) != 1 or s in "+*()λ∅\\{} " for s in alfabeto):
        raise ValueError("El alfabeto propuesto no es válido.")
    tipo = datos.get("tipo")
    if tipo not in TIPOS:
        raise ValueError("Tipo de ejercicio desconocido.")
    try:
        r = analizar(str(datos.get("expresion_referencia", "")))
    except ErrorSintaxis as exc:
        raise ValueError(f"La expresión de referencia no es válida: {exc}") from exc
    if not simbolos(r) <= set(alfabeto):
        raise ValueError("La expresión de referencia usa símbolos fuera del alfabeto.")
    if muestra(r, random.Random(0)) is None:
        raise ValueError("La expresión de referencia describe el lenguaje vacío.")
    titulo = str(datos.get("titulo", "")).strip()[:80] or "Ejercicio generado"
    enunciado = str(datos.get("enunciado", "")).strip()
    if not enunciado:
        raise ValueError("El ejercicio no tiene enunciado.")
    return Ejercicio(f"ia-{abs(hash((titulo, enunciado))) % 10**8}", titulo, enunciado, tipo, alfabeto,
                     str(datos["expresion_referencia"]), str(datos.get("dificultad", "intermedio")),
                     generado_por_ia=True)


# ---------------------------------------------------------------------------
# Preguntas rápidas: ¿el autómata acepta la cadena?
# ---------------------------------------------------------------------------

@dataclass
class Pregunta:
    automata: Automata
    cadena: str
    respuesta: bool


def pregunta_aleatoria(rnd: random.Random) -> Pregunta:
    fabrica = rnd.choice([f for n, f in ejemplos.EJEMPLOS.items() if "TCP" not in n and "decimales" not in n])
    a = fabrica()
    longitud = rnd.randint(0, 6)
    cadena = "".join(rnd.choice(a.alfabeto) for _ in range(longitud))
    return Pregunta(a, cadena, acepta(a, cadena))
