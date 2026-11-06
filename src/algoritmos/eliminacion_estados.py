"""De un autómata a una expresión regular por eliminación de estados.

Método (Hopcroft, Motwani y Ullman, 2007, sec. 3.2.2; Brzozowski y McCluskey,
1963), sobre un **autómata generalizado** cuyas aristas llevan expresiones:

1. Se agrega un estado inicial nuevo *I* con una arista λ al inicial original
   y un estado final nuevo *F* con aristas λ desde cada estado de aceptación.
   Las aristas paralelas p → q se unen en una sola: R(p, q) = a + b + …
2. Se elimina un estado intermedio q a la vez. Para cada par de vecinos p → q
   → r se actualiza
           R(p, r) := R(p, r) + R(p, q) · R(q, q)* · R(q, r)
3. Cuando sólo quedan *I* y *F*, la expresión es R(I, F) (∅ si no existe).

Por omisión se elimina primero el estado con menos combinaciones
(entradas × salidas), lo que suele producir expresiones más cortas; también se
puede fijar el orden.

Coste: eliminar un estado con e entradas y s salidas crea e·s expresiones; en
total O(|Q|³) operaciones sobre expresiones, cuyo tamaño puede crecer
exponencialmente en el peor caso.
"""

from __future__ import annotations

from typing import Optional

from core.automata import LAMBDA as SIM_LAMBDA, Automata
from core.disposicion import disponer
from core.expresion_regular import ER, LAMBDA, VACIO, a_texto, concat, estrella, sim, union
from algoritmos.pasos import Paso

class Generalizado:
    """Autómata generalizado: un diccionario (p, q) → expresión."""

    def __init__(self, estados: list[str], aristas: dict[tuple[str, str], ER], inicio: str, fin: str):
        self.estados = estados
        self.aristas = aristas
        self.inicio, self.fin = inicio, fin

    def r(self, p: str, q: str) -> ER:
        return self.aristas.get((p, q), VACIO)

    def foto(self, posiciones: dict[str, tuple[float, float]]) -> Automata:
        """Autómata para dibujar: las etiquetas de las aristas son expresiones."""
        a = Automata(nombre="Autómata generalizado")
        for q in self.estados:
            a.estados.append(q)
        a.inicial = self.inicio
        a.aceptacion = {self.fin}
        for (p, q), e in self.aristas.items():
            texto = a_texto(e)
            a.transiciones.setdefault((p, "" if texto == "λ" else texto), set()).add(q)
        a.posiciones = {q: posiciones[q] for q in self.estados if q in posiciones}
        return a


def _nombres_libres(a: Automata) -> tuple[str, str]:
    i, f = "I", "F"
    while i in a.estados:
        i += "'"
    while f in a.estados:
        f += "'"
    return i, f


def eliminar_estados(a: Automata, orden: Optional[list[str]] = None) -> tuple[ER, list[Paso], list[str]]:
    if a.inicial is None:
        raise ValueError("El autómata no tiene estado inicial.")
    INICIO, FIN = _nombres_libres(a)
    estados = [INICIO, *a.estados, FIN]
    aristas: dict[tuple[str, str], ER] = {(INICIO, a.inicial): LAMBDA}
    for q in a.aceptacion:
        aristas[(q, FIN)] = union(aristas.get((q, FIN), VACIO), LAMBDA)
    for q, s, d in a.lista_transiciones():
        aristas[(q, d)] = union(aristas.get((q, d), VACIO), sim(s if s != SIM_LAMBDA else ""))
    g = Generalizado(estados, aristas, INICIO, FIN)

    posiciones = dict(a.posiciones) if all(q in a.posiciones for q in a.estados) else disponer(a)
    xs = [x for x, _ in posiciones.values()] or [0.0]
    ys = [y for _, y in posiciones.values()] or [0.0]
    py_ini = posiciones.get(a.inicial, (min(xs), sum(ys) / len(ys)))[1]
    posiciones[INICIO] = (min(xs) - 150, py_ini)
    posiciones[FIN] = (max(xs) + 150, sum(ys) / len(ys))

    pasos = [Paso("1. Autómata generalizado",
                  f"Se agregan {INICIO} (con λ hacia {a.inicial}) y {FIN} (con λ desde cada estado de "
                  "aceptación). Las aristas paralelas se unen con +.",
                  g.foto(posiciones), {INICIO, FIN}, set(), tabla=_tabla(g))]
    pendientes = [q for q in a.estados]
    usado: list[str] = []
    if orden:
        faltan = [q for q in orden if q not in pendientes]
        if faltan:
            raise ValueError(f"El orden menciona estados inexistentes: {', '.join(faltan)}.")
        pendientes = [q for q in orden] + [q for q in pendientes if q not in orden]

    while pendientes:
        if orden:
            q = pendientes.pop(0)
        else:
            q = min(pendientes, key=lambda x: (_costo(g, x), a._orden(x)))
            pendientes.remove(q)
        usado.append(q)
        entradas = [p for p in g.estados if p != q and (p, q) in g.aristas]
        salidas = [r for r in g.estados if r != q and (q, r) in g.aristas]
        bucle = estrella(g.r(q, q))
        cambios = []
        nuevas = set()
        for p in entradas:
            for r in salidas:
                atajo = concat(g.r(p, q), bucle, g.r(q, r))
                anterior = g.r(p, r)
                g.aristas[(p, r)] = union(anterior, atajo)
                nuevas.add((p, r))
                cambios.append(f"R({p},{r}) = {a_texto(anterior)} + ({a_texto(g.r(p, q))})"
                               f"({a_texto(g.r(q, q))})*({a_texto(g.r(q, r))}) = {a_texto(g.aristas[(p, r)])}")
        g.estados.remove(q)
        g.aristas = {k: v for k, v in g.aristas.items() if q not in k}
        pasos.append(Paso(
            f"Se elimina {q}",
            (f"Entradas: {', '.join(entradas) or '—'}; salidas: {', '.join(salidas) or '—'}; "
             + (f"bucle R({q},{q}) = {a_texto(g.r(q, q))}.\n" if (q, q) in g.aristas
                else f"sin bucle (R({q},{q}) = ∅ y ∅* = λ).\n"))
            + ("\n".join(cambios) if cambios else "No conecta ningún par de estados: se quita sin agregar aristas."),
            g.foto(posiciones), set(), nuevas, tabla=_tabla(g), tipo="nuevo"))
    resultado = g.r(INICIO, FIN)
    pasos.append(Paso("Expresión regular resultante",
                      f"Sólo quedan {INICIO} y {FIN}: la expresión es R({INICIO},{FIN}) = {a_texto(resultado)}",
                      g.foto(posiciones), {INICIO, FIN}, {(INICIO, FIN)}, tabla=_tabla(g), tipo="exito"))
    return resultado, pasos, usado


def _costo(g: Generalizado, q: str) -> int:
    e = sum(1 for p in g.estados if p != q and (p, q) in g.aristas)
    s = sum(1 for r in g.estados if r != q and (q, r) in g.aristas)
    return e * s


def _tabla(g: Generalizado) -> list[list[str]]:
    filas = [["Desde", "Hacia", "Expresión"]]
    for (p, q), e in sorted(g.aristas.items(), key=lambda kv: (g.estados.index(kv[0][0]), g.estados.index(kv[0][1]))):
        filas.append([p, q, a_texto(e)])
    return filas


def afd_a_er(a: Automata, orden: Optional[list[str]] = None) -> ER:
    return eliminar_estados(a, orden)[0]
