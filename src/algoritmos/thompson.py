"""De una expresión regular a un AFN-λ (primera parte del teorema de Kleene).

Construcción por casos básicos y por inducción sobre el árbol sintáctico
(Thompson, 1968; Hopcroft, Motwani y Ullman, 2007, sec. 3.2.3). Cada fragmento
tiene un único estado inicial y un único estado final, sin transiciones que
salgan del final:

* ∅: inicio y fin sin transiciones.        * λ: inicio –λ→ fin.
* a: inicio –a→ fin.                        * {C}: inicio –c→ fin para cada c ∈ C
  (es la unión de los casos básicos de C con un solo par de estados).
* r1 + … + rk: nuevo inicio –λ→ inicio de cada ri; fin de cada ri –λ→ nuevo fin.
* r1 r2 … rk: fin de ri –λ→ inicio de r(i+1).
* r*: nuevo inicio –λ→ inicio de r y –λ→ nuevo fin; fin de r –λ→ inicio de r
  y –λ→ nuevo fin.

El AFN-λ resultante tiene a lo sumo 2·|r| estados y cada estado a lo sumo dos
transiciones salientes (salvo las clases), así que la construcción es lineal
en el tamaño de la expresión.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.automata import LAMBDA as SIM_LAMBDA, Automata
from core.disposicion import disponer
from core.expresion_regular import (ER, Clase, Concat, Estrella, Lambda, Simbolo, Union, Vacio, a_texto,
                                    arbol_texto, simbolos)
from algoritmos.pasos import Paso


@dataclass
class Fragmento:
    inicio: str
    fin: str
    estados: list[str]


class _Constructor:
    def __init__(self, nombre: str):
        self.a = Automata(nombre=nombre)
        self.contador = 0
        self.pasos: list[Paso] = []

    def nuevo(self) -> str:
        q = f"s{self.contador}"
        self.contador += 1
        self.a.agregar_estado(q)
        return q

    def arista(self, p: str, s: str, q: str) -> None:
        self.a.agregar_transicion(p, s, q)

    def foto(self, f: Fragmento) -> Automata:
        b = Automata(nombre="fragmento", alfabeto=[])
        for q in f.estados:
            b.estados.append(q)
        b.inicial = f.inicio
        b.aceptacion = {f.fin}
        conjunto = set(f.estados)
        for (q, s), ds in self.a.transiciones.items():
            if q in conjunto:
                for d in ds:
                    if d in conjunto:
                        b.transiciones.setdefault((q, s), set()).add(d)
                        if s != SIM_LAMBDA and s not in b.alfabeto:
                            b.alfabeto.append(s)
        b.posiciones = disponer(b)
        return b

    def registrar(self, titulo: str, detalle: str, f: Fragmento, nuevos: set[str],
                  aristas: set[tuple[str, str]]) -> None:
        self.pasos.append(Paso(titulo, detalle, self.foto(f), nuevos, aristas, tipo="nuevo"))

    def construir(self, r: ER) -> Fragmento:
        if isinstance(r, (Vacio, Lambda, Simbolo, Clase)):
            i, f = self.nuevo(), self.nuevo()
            if isinstance(r, Lambda):
                self.arista(i, SIM_LAMBDA, f)
                titulo, detalle = "Caso básico λ", f"{i} –λ→ {f}: acepta sólo la palabra vacía."
            elif isinstance(r, Simbolo):
                self.arista(i, r.s, f)
                titulo, detalle = f"Caso básico «{r.s}»", f"{i} –{r.s}→ {f}: acepta sólo «{r.s}»."
            elif isinstance(r, Clase):
                for c in r.simbolos:
                    self.arista(i, c, f)
                titulo = f"Clase {{{r.nombre}}}"
                detalle = (f"{i} → {f} con cada uno de sus {len(r.simbolos)} símbolos: es la unión de los casos "
                           "básicos de la clase con un solo par de estados.")
            else:
                titulo, detalle = "Caso básico ∅", f"{i} y {f} sin transiciones: no acepta ninguna cadena."
            frag = Fragmento(i, f, [i, f])
            self.registrar(titulo, detalle, frag, {i, f}, {(i, f)})
            return frag

        if isinstance(r, Union):
            hijos = [self.construir(p) for p in r.partes]
            i, f = self.nuevo(), self.nuevo()
            aristas = set()
            for h in hijos:
                self.arista(i, SIM_LAMBDA, h.inicio)
                self.arista(h.fin, SIM_LAMBDA, f)
                aristas |= {(i, h.inicio), (h.fin, f)}
            frag = Fragmento(i, f, [i] + [q for h in hijos for q in h.estados] + [f])
            self.registrar(f"Unión de {len(hijos)} expresiones: {a_texto(r)}",
                           f"Nuevo inicio {i} con λ hacia " + ", ".join(h.inicio for h in hijos)
                           + f"; λ desde " + ", ".join(h.fin for h in hijos) + f" hacia el nuevo final {f}.",
                           frag, {i, f}, aristas)
            return frag

        if isinstance(r, Concat):
            hijos = [self.construir(p) for p in r.partes]
            aristas = set()
            for h1, h2 in zip(hijos, hijos[1:]):
                self.arista(h1.fin, SIM_LAMBDA, h2.inicio)
                aristas.add((h1.fin, h2.inicio))
            frag = Fragmento(hijos[0].inicio, hijos[-1].fin, [q for h in hijos for q in h.estados])
            self.registrar(f"Concatenación: {a_texto(r)}",
                           "Se une el final de cada fragmento con el inicio del siguiente: "
                           + ", ".join(f"{p} –λ→ {q}" for p, q in sorted(aristas)) + ".",
                           frag, set(), aristas)
            return frag

        assert isinstance(r, Estrella)
        h = self.construir(r.r)
        i, f = self.nuevo(), self.nuevo()
        for p, q in ((i, h.inicio), (i, f), (h.fin, h.inicio), (h.fin, f)):
            self.arista(p, SIM_LAMBDA, q)
        frag = Fragmento(i, f, [i] + h.estados + [f])
        self.registrar(f"Cerradura de Kleene: {a_texto(r)}",
                       f"{i} –λ→ {h.inicio} (entrar), {i} –λ→ {f} (cero repeticiones), "
                       f"{h.fin} –λ→ {h.inicio} (repetir) y {h.fin} –λ→ {f} (salir).",
                       frag, {i, f}, {(i, h.inicio), (i, f), (h.fin, h.inicio), (h.fin, f)})
        return frag


def thompson(r: ER, nombre: str = "AFN-λ de Thompson") -> tuple[Automata, list[Paso]]:
    c = _Constructor(nombre)
    pasos_arbol = Paso("Árbol sintáctico", "\n".join(arbol_texto(r)) + "\n\nLa construcción recorre el árbol "
                       "de las hojas a la raíz: primero los casos básicos y después cada operación.")
    frag = c.construir(r)
    a = c.a
    a.inicial = frag.inicio
    a.aceptacion = {frag.fin}
    a.alfabeto = sorted(simbolos(r))
    a.posiciones = disponer(a)
    c.pasos.append(Paso("AFN-λ resultante",
                        f"{len(a.estados)} estados (inicio {frag.inicio}, final {frag.fin}) y "
                        f"{len(a.lista_transiciones())} transiciones, "
                        f"{sum(1 for _, s, _ in a.lista_transiciones() if s == SIM_LAMBDA)} de ellas λ.",
                        a, {frag.inicio, frag.fin}, set(), tipo="exito"))
    return a, [pasos_arbol] + c.pasos
