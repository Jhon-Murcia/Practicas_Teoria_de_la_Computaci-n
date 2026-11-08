"""Autómatas de ejemplo integrados en el software.

Son ejemplos propios, construidos para mostrar cada clase de autómata y para
probar los algoritmos.
"""

from __future__ import annotations

from typing import Callable

from core.automata import LAMBDA, Automata
from core.disposicion import disponer


def _con_posiciones(a: Automata) -> Automata:
    if not a.posiciones:
        a.posiciones = disponer(a)
    return a


def multiplos_de_tres() -> Automata:
    """AFD: números binarios cuyo valor es múltiplo de 3. El estado es el residuo."""
    a = Automata.desde_tabla(
        ["r0", "r1", "r2"], ["0", "1"], "r0", ["r0"],
        {("r0", "0"): "r0", ("r0", "1"): "r1", ("r1", "0"): "r2", ("r1", "1"): "r0",
         ("r2", "0"): "r1", ("r2", "1"): "r2"},
        "Binarios múltiplos de 3")
    a.descripcion = "El estado r_i indica que el prefijo leído, como número binario, deja residuo i al dividir entre 3."
    a.posiciones = {"r0": (110, 200), "r1": (330, 200), "r2": (550, 200)}
    return a


def a_par() -> Automata:
    """AFD: cadenas sobre {a, b} con un número par de aes."""
    a = Automata.desde_tabla(
        ["par", "impar"], ["a", "b"], "par", ["par"],
        {("par", "a"): "impar", ("par", "b"): "par", ("impar", "a"): "par", ("impar", "b"): "impar"},
        "Número par de aes")
    a.descripcion = "El estado recuerda la paridad del número de aes leídas."
    a.posiciones = {"par": (140, 200), "impar": (400, 200)}
    return a


def termina_en_ab() -> Automata:
    """AFND: cadenas sobre {a, b} que terminan en ab."""
    a = Automata.desde_tabla(
        ["q0", "q1", "q2"], ["a", "b"], "q0", ["q2"],
        {("q0", "a"): {"q0", "q1"}, ("q0", "b"): "q0", ("q1", "b"): "q2"},
        "Termina en ab")
    a.descripcion = "En q0 el autómata «adivina» cuándo empieza el sufijo ab."
    a.posiciones = {"q0": (110, 200), "q1": (330, 200), "q2": (550, 200)}
    return a


def tercero_desde_el_final() -> Automata:
    """AFND: el tercer símbolo desde el final es 1 (su AFD necesita 2³ = 8 estados)."""
    a = Automata.desde_tabla(
        ["q0", "q1", "q2", "q3"], ["0", "1"], "q0", ["q3"],
        {("q0", "0"): "q0", ("q0", "1"): {"q0", "q1"}, ("q1", "0"): "q2", ("q1", "1"): "q2",
         ("q2", "0"): "q3", ("q2", "1"): "q3"},
        "Tercero desde el final es 1")
    a.descripcion = "Familia L_n = {w : el n-ésimo símbolo desde el final es 1}: el AFD mínimo tiene 2^n estados."
    a.posiciones = {"q0": (100, 200), "q1": (280, 200), "q2": (460, 200), "q3": (640, 200)}
    return a


def anexo_lambda() -> Automata:
    """AFND-λ del Anexo 3 de la Práctica 2: dos estados sobre {a, b}."""
    a = Automata.desde_tabla(
        ["q0", "q1"], ["a", "b"], "q0", ["q1"],
        {("q0", "a"): "q1", ("q0", "b"): "q0", ("q0", LAMBDA): "q1"},
        "AFND-λ del Anexo 3")
    a.posiciones = {"q0": (80, 120), "q1": (240, 120)}
    return a


def a_estrella_b_estrella_c_estrella() -> Automata:
    """AFND-λ: a*b*c*, con transiciones λ entre los tres bloques."""
    a = Automata.desde_tabla(
        ["p", "q", "r"], ["a", "b", "c"], "p", ["r"],
        {("p", "a"): "p", ("p", LAMBDA): "q", ("q", "b"): "q", ("q", LAMBDA): "r", ("r", "c"): "r"},
        "a*b*c*")
    a.descripcion = "Cada transición λ permite pasar al bloque siguiente sin leer nada."
    a.posiciones = {"p": (120, 200), "q": (340, 200), "r": (560, 200)}
    return a


def numeros_decimales() -> Automata:
    """AFND-λ: números con signo opcional, dígitos y punto decimal (p. ej. -12.5, +.5, 7.)."""
    d = [str(i) for i in range(10)]
    delta: dict = {("q0", LAMBDA): {"q1"}, ("q0", "+"): {"q1"}, ("q0", "-"): {"q1"},
                   ("q1", "."): {"q2"}, ("q4", "."): {"q3"}, ("q3", LAMBDA): {"q5"}}
    for c in d:
        delta[("q1", c)] = {"q1", "q4"}
        delta[("q2", c)] = {"q3"}
        delta[("q3", c)] = {"q3"}
    a = Automata.desde_tabla(["q0", "q1", "q2", "q3", "q4", "q5"], ["+", "-", "."] + d, "q0", ["q5"], delta,
                             "Números decimales")
    a.descripcion = "Signo opcional (λ, + o -), dígitos y un punto decimal con al menos un dígito a un lado."
    a.posiciones = {"q0": (90, 200), "q1": (260, 200), "q2": (430, 90), "q3": (600, 200), "q4": (430, 310),
                    "q5": (770, 200)}
    return a


# Glosario de eventos del autómata TCP (un carácter por evento).
EVENTOS_TCP = {
    "P": "abrir en modo pasivo (el servidor escucha)",
    "A": "abrir en modo activo (se envía SYN)",
    "E": "la aplicación envía datos desde LISTEN (se envía SYN)",
    "S": "se recibe SYN",
    "Y": "se recibe SYN+ACK",
    "K": "se recibe ACK",
    "F": "se recibe FIN",
    "X": "se recibe FIN+ACK",
    "R": "se recibe RST",
    "C": "la aplicación cierra (close)",
    "T": "vence el temporizador 2·MSL",
}


def conexion_tcp() -> Automata:
    """Autómata de aplicación: ciclo de vida de una conexión TCP.

    Modelo tomado del diagrama de estados de la especificación de TCP
    (Postel, 1981, RFC 793, fig. 6). Cada símbolo es un evento; una cadena es
    una secuencia de eventos y se acepta si la conexión termina de nuevo en
    CLOSED, es decir, si describe un ciclo de vida completo.
    """
    t = {
        ("CLOSED", "P"): "LISTEN", ("CLOSED", "A"): "SYN_SENT",
        ("LISTEN", "S"): "SYN_RCVD", ("LISTEN", "E"): "SYN_SENT", ("LISTEN", "C"): "CLOSED",
        ("SYN_SENT", "S"): "SYN_RCVD", ("SYN_SENT", "Y"): "ESTABLISHED", ("SYN_SENT", "C"): "CLOSED",
        ("SYN_RCVD", "K"): "ESTABLISHED", ("SYN_RCVD", "C"): "FIN_WAIT_1", ("SYN_RCVD", "R"): "LISTEN",
        ("ESTABLISHED", "C"): "FIN_WAIT_1", ("ESTABLISHED", "F"): "CLOSE_WAIT",
        ("FIN_WAIT_1", "K"): "FIN_WAIT_2", ("FIN_WAIT_1", "F"): "CLOSING", ("FIN_WAIT_1", "X"): "TIME_WAIT",
        ("FIN_WAIT_2", "F"): "TIME_WAIT",
        ("CLOSING", "K"): "TIME_WAIT",
        ("TIME_WAIT", "T"): "CLOSED",
        ("CLOSE_WAIT", "C"): "LAST_ACK",
        ("LAST_ACK", "K"): "CLOSED",
    }
    estados = ["CLOSED", "LISTEN", "SYN_SENT", "SYN_RCVD", "ESTABLISHED", "FIN_WAIT_1", "FIN_WAIT_2",
               "CLOSING", "TIME_WAIT", "CLOSE_WAIT", "LAST_ACK"]
    a = Automata.desde_tabla(estados, list(EVENTOS_TCP), "CLOSED", ["CLOSED"], t, "Conexión TCP (RFC 793)")
    a.descripcion = "Eventos: " + "; ".join(f"{k} = {v}" for k, v in EVENTOS_TCP.items())
    a.posiciones = {
        "CLOSED": (420, 60), "LISTEN": (250, 180), "SYN_SENT": (600, 180), "SYN_RCVD": (250, 320),
        "ESTABLISHED": (600, 320), "FIN_WAIT_1": (250, 470), "CLOSE_WAIT": (800, 470),
        "FIN_WAIT_2": (250, 620), "CLOSING": (480, 470), "TIME_WAIT": (480, 620), "LAST_ACK": (800, 620),
    }
    return a


EJEMPLOS: dict[str, Callable[[], Automata]] = {
    "Binarios múltiplos de 3 (AFD)": multiplos_de_tres,
    "Número par de aes (AFD)": a_par,
    "Termina en ab (AFND)": termina_en_ab,
    "Tercero desde el final es 1 (AFND)": tercero_desde_el_final,
    "AFND-λ del Anexo 3": anexo_lambda,
    "a*b*c* (AFND-λ)": a_estrella_b_estrella_c_estrella,
    "Números decimales (AFND-λ)": numeros_decimales,
    "Conexión TCP — aplicación (AFD)": conexion_tcp,
}


def todos() -> list[Automata]:
    return [_con_posiciones(f()) for f in EJEMPLOS.values()]
