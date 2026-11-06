"""Simulación de autómatas finitos sin convertirlos.

Decisión de diseño (Práctica 2, 3.3)
------------------------------------
El no determinismo se simula **directamente**, siguiendo todos los caminos a la
vez: en cada paso se mantiene el *conjunto* de estados activos. Es la misma
idea de la construcción de subconjuntos, pero calculando sólo los conjuntos que
la cadena concreta visita.

* Coste de la simulación directa: por cada uno de los |w| símbolos se recorren
  a lo sumo |Q| estados activos y sus destinos, más la λ-clausura: O(|w|·|Q|²)
  en el peor caso, con memoria O(|Q|). No hay preprocesamiento.
* Coste de convertir a AFD y simular: la construcción de subconjuntos puede
  generar hasta 2^|Q| estados (tiempo y memoria exponenciales en |Q|), pero
  después cada cadena se valida en O(|w|). Conviene sólo si el mismo autómata
  valida muchísimas cadenas y el AFD resultante es pequeño.

Para mostrar *los caminos* (las bifurcaciones), :func:`arbol_computacion`
construye además el árbol de todas las computaciones, acotado en tamaño.

Un AFD es un caso particular: el conjunto activo tiene siempre un elemento
(o ninguno, si δ es parcial y la computación muere).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.automata import LAMBDA, Automata


def cerradura_lambda(a: Automata, estados) -> frozenset[str]:
    """λ-clausura de un conjunto: estados alcanzables sólo con transiciones λ."""
    resultado = set(estados)
    pila = list(estados)
    while pila:
        q = pila.pop()
        for d in a.destinos(q, LAMBDA):
            if d not in resultado:
                resultado.add(d)
                pila.append(d)
    return frozenset(resultado)


def _cerradura_con_aristas(a: Automata, estados) -> tuple[frozenset[str], list[tuple[str, str, str]]]:
    resultado = set(estados)
    pila = sorted(estados, key=a._orden)
    aristas = []
    while pila:
        q = pila.pop(0)
        for d in sorted(a.destinos(q, LAMBDA), key=a._orden):
            aristas.append((q, LAMBDA, d))
            if d not in resultado:
                resultado.add(d)
                pila.append(d)
    return frozenset(resultado), aristas


def mover(a: Automata, estados, simbolo: str) -> frozenset[str]:
    """δ̂ sin clausura: ∪ δ(q, a) para q en ``estados``."""
    res: set[str] = set()
    for q in estados:
        res |= a.destinos(q, simbolo)
    return frozenset(res)


@dataclass
class Paso:
    """Un paso de la simulación: leer ``simbolo`` desde ``antes``."""
    numero: int
    simbolo: str
    antes: frozenset[str]
    movimiento: frozenset[str]
    despues: frozenset[str]
    transiciones: list[tuple[str, str, str]] = field(default_factory=list)
    transiciones_lambda: list[tuple[str, str, str]] = field(default_factory=list)


@dataclass
class Resultado:
    cadena: str
    simbolos: list[str]
    aceptada: bool
    inicio: frozenset[str]
    inicio_sin_cerradura: frozenset[str]
    lambda_inicio: list[tuple[str, str, str]]
    pasos: list[Paso]
    finales: frozenset[str]
    error: Optional[str] = None
    posicion_error: Optional[int] = None

    @property
    def murio(self) -> bool:
        """``True`` si el conjunto activo quedó vacío antes de terminar."""
        return any(not p.despues for p in self.pasos)

    def explicacion(self, a: Automata) -> str:
        if self.error:
            return self.error
        if self.aceptada:
            acept = sorted(self.finales & a.aceptacion, key=a._orden)
            return f"Aceptada: al terminar, los estados activos incluyen {', '.join(acept)} ∈ F."
        if not self.finales:
            n = next((p.numero for p in self.pasos if not p.despues), len(self.pasos))
            return f"Rechazada: no hay transición disponible en el paso {n}; el conjunto activo quedó vacío."
        return ("Rechazada: al terminar, ningún estado activo {" + ", ".join(sorted(self.finales, key=a._orden))
                + "} es de aceptación.")


def simular(a: Automata, cadena: str | list[str]) -> Resultado:
    """Simula ``a`` sobre ``cadena`` y registra cada paso."""
    simbolos = a.tokenizar(cadena) if isinstance(cadena, str) else list(cadena)
    texto = cadena if isinstance(cadena, str) else "".join(cadena)
    if a.inicial is None:
        return Resultado(texto, simbolos, False, frozenset(), frozenset(), [], [], frozenset(),
                         "El autómata no tiene estado inicial.")
    inicio_crudo = frozenset({a.inicial})
    actual, aristas0 = _cerradura_con_aristas(a, inicio_crudo)
    inicio = actual
    pasos: list[Paso] = []
    for i, s in enumerate(simbolos, start=1):
        if s not in a.alfabeto:
            return Resultado(texto, simbolos, False, inicio, inicio_crudo, aristas0, pasos, actual,
                             f"El símbolo «{s}» (posición {i}) no pertenece al alfabeto Σ = "
                             f"{{{', '.join(a.alfabeto)}}}.", i)
        usadas = [(q, s, d) for q in sorted(actual, key=a._orden) for d in sorted(a.destinos(q, s), key=a._orden)]
        mov = frozenset(d for _, _, d in usadas)
        despues, aristas = _cerradura_con_aristas(a, mov)
        pasos.append(Paso(i, s, actual, mov, despues, usadas, aristas))
        actual = despues
    return Resultado(texto, simbolos, bool(actual & a.aceptacion), inicio, inicio_crudo, aristas0, pasos, actual)


def acepta(a: Automata, cadena: str | list[str]) -> bool:
    return simular(a, cadena).aceptada


# ---------------------------------------------------------------------------
# Árbol de computación: todos los caminos, con sus bifurcaciones
# ---------------------------------------------------------------------------

@dataclass
class Nodo:
    estado: str
    leidos: int                  # símbolos consumidos al llegar a este nodo
    via: Optional[str] = None    # símbolo con el que se llegó (λ = "")
    hijos: list["Nodo"] = field(default_factory=list)
    aceptacion: bool = False     # terminó la cadena en un estado de F
    muerto: bool = False         # no quedan transiciones y no terminó la cadena
    ciclo: bool = False          # ciclo λ cortado para no repetir indefinidamente


@dataclass
class Arbol:
    raiz: Nodo
    nodos: int
    truncado: bool
    caminos_aceptacion: int


def arbol_computacion(a: Automata, cadena: str | list[str], max_nodos: int = 400) -> Arbol:
    """Explora todas las computaciones posibles de ``a`` sobre la cadena.

    Cada camino de la raíz a una hoja es una computación. Las hojas indican si
    la computación acepta, rechaza al terminar la cadena o muere antes. Las
    transiciones λ se siguen sin consumir símbolos; un ciclo λ (volver a un
    estado ya visitado sin leer nada) se corta y se marca.
    """
    simbolos = a.tokenizar(cadena) if isinstance(cadena, str) else list(cadena)
    raiz = Nodo(a.inicial or "?", 0)
    contador = [1]
    truncado = [False]
    aceptados = [0]

    def expandir(nodo: Nodo, visitados_lambda: frozenset[str]) -> None:
        if contador[0] >= max_nodos:
            truncado[0] = True
            return
        i = nodo.leidos
        hijos: list[tuple[str, str, int, frozenset[str]]] = []
        for d in sorted(a.destinos(nodo.estado, LAMBDA), key=a._orden):
            hijos.append((d, LAMBDA, i, visitados_lambda | {nodo.estado}))
        if i < len(simbolos):
            for d in sorted(a.destinos(nodo.estado, simbolos[i]), key=a._orden):
                hijos.append((d, simbolos[i], i + 1, frozenset()))
        fin = i == len(simbolos)
        if fin and nodo.estado in a.aceptacion:
            nodo.aceptacion = True
            aceptados[0] += 1
        if not hijos and not fin:
            nodo.muerto = True
        for d, via, leidos, vis in hijos:
            if contador[0] >= max_nodos:
                truncado[0] = True
                return
            hijo = Nodo(d, leidos, via)
            contador[0] += 1
            nodo.hijos.append(hijo)
            if via == LAMBDA and d in vis | {nodo.estado}:
                hijo.ciclo = True
                continue
            expandir(hijo, vis)

    if a.inicial is not None:
        expandir(raiz, frozenset())
    return Arbol(raiz, contador[0], truncado[0], aceptados[0])


def caminos(arbol: Arbol) -> list[tuple[list[tuple[Optional[str], str]], str]]:
    """Aplana el árbol: cada camino como ``[(vía, estado), …]`` y su desenlace."""
    salida = []

    def recorrer(n: Nodo, acumulado):
        actual = acumulado + [(n.via, n.estado)]
        if n.aceptacion:
            salida.append((actual, "acepta"))
        if not n.hijos:
            if n.ciclo:
                salida.append((actual, "ciclo λ"))
            elif n.muerto:
                salida.append((actual, "sin transición"))
            elif not n.aceptacion:
                salida.append((actual, "rechaza"))
        for h in n.hijos:
            recorrer(h, actual)

    recorrer(arbol.raiz, [])
    return salida


# ---------------------------------------------------------------------------
# Validación de varias cadenas (una por línea)
# ---------------------------------------------------------------------------

def leer_lineas(texto: str) -> list[str]:
    """Una cadena por línea; ``λ``, ``lambda`` o ``ε`` en una línea es la vacía.

    Las líneas en blanco se ignoran y se recortan los espacios de los extremos.
    """
    cadenas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        cadenas.append("" if linea in ("λ", "lambda", "ε") else linea)
    return cadenas


def validar_lote(a: Automata, cadenas: list[str]) -> list[Resultado]:
    return [simular(a, w) for w in cadenas]


def informe_lote(a: Automata, resultados: list[Resultado], origen: str = "") -> str:
    """Informe de texto con el resultado de cada cadena."""
    aceptadas = sum(r.aceptada for r in resultados)
    lineas = [f"Informe de validación - {a.nombre} ({a.tipo})"]
    if origen:
        lineas.append(f"Archivo: {origen}")
    lineas += [f"Cadenas: {len(resultados)} · aceptadas: {aceptadas} · rechazadas: {len(resultados) - aceptadas}",
               "", f"{'#':>4}  {'resultado':<10} {'cadena':<30} detalle", "-" * 78]
    for i, r in enumerate(resultados, 1):
        estado = "ACEPTADA" if r.aceptada else "RECHAZADA"
        detalle = r.error or ("finales: {" + ", ".join(sorted(r.finales, key=a._orden)) + "}")
        lineas.append(f"{i:>4}  {estado:<10} {(r.cadena or 'λ'):<30} {detalle}")
    return "\n".join(lineas) + "\n"
