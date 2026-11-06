"""Modelo de autómata finito: la quíntupla M = (Q, Σ, δ, q0, F).

Una sola clase representa AFD, AFND y AFND-λ. La función de transición se
guarda como un diccionario ``(estado, símbolo) → conjunto de destinos``; la
transición λ usa el símbolo :data:`LAMBDA` (la cadena vacía), que es también la
convención de los formatos ``.jff``, ``.json`` y ``.xml``.

El tipo del autómata no se declara: se deduce de δ.

* **AFD**: no hay transiciones λ y cada par (q, a) tiene a lo sumo un destino.
  (Se admite que δ sea parcial; la ausencia de transición equivale a un estado
  de error implícito. :meth:`Automata.es_completo` indica si δ es total.)
* **AFND**: algún par (q, a) tiene dos o más destinos, sin transiciones λ.
* **AFND-λ**: existe al menos una transición λ.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

LAMBDA = ""
"""Símbolo interno de la transición λ."""

SIMBOLO_LAMBDA = "λ"
"""Cómo se muestra la transición λ."""

AFD, AFND, AFND_LAMBDA = "AFD", "AFND", "AFND-λ"


class ErrorAutomata(ValueError):
    """Definición inválida o inconsistente de un autómata."""


def mostrar_simbolo(s: str) -> str:
    return SIMBOLO_LAMBDA if s == LAMBDA else s


def leer_simbolo(texto: str) -> str:
    """Interpreta lo que escribe el usuario: ``λ``, ``lambda`` o ``ε`` son λ."""
    texto = texto.strip()
    return LAMBDA if texto in (SIMBOLO_LAMBDA, "lambda", "ε", "epsilon") else texto


@dataclass
class Automata:
    estados: list[str] = field(default_factory=list)
    alfabeto: list[str] = field(default_factory=list)
    inicial: Optional[str] = None
    aceptacion: set[str] = field(default_factory=set)
    transiciones: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    nombre: str = "Autómata"
    descripcion: str = ""
    posiciones: dict[str, tuple[float, float]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    @classmethod
    def desde_tabla(cls, estados: Iterable[str], alfabeto: Iterable[str], inicial: str,
                    aceptacion: Iterable[str], delta: dict, nombre: str = "Autómata") -> "Automata":
        """Construye desde ``delta = {(q, a): "p" | {"p", "r"}}``. Usar ``""`` para λ."""
        a = cls(list(estados), list(alfabeto), inicial, set(aceptacion), {}, nombre)
        for (q, s), destinos in delta.items():
            for d in ([destinos] if isinstance(destinos, str) else destinos):
                a.agregar_transicion(q, s, d)
        a.validar(estricto=True)
        return a

    def copia(self, nombre: Optional[str] = None) -> "Automata":
        c = copy.deepcopy(self)
        if nombre is not None:
            c.nombre = nombre
        return c

    def nuevo_nombre_estado(self, prefijo: str = "q") -> str:
        i = 0
        while f"{prefijo}{i}" in self.estados:
            i += 1
        return f"{prefijo}{i}"

    def agregar_estado(self, nombre: Optional[str] = None, posicion: Optional[tuple[float, float]] = None) -> str:
        nombre = (nombre or self.nuevo_nombre_estado()).strip()
        if not nombre:
            raise ErrorAutomata("El nombre del estado no puede ser vacío.")
        if nombre in self.estados:
            raise ErrorAutomata(f"Ya existe un estado llamado {nombre}.")
        self.estados.append(nombre)
        if posicion is not None:
            self.posiciones[nombre] = posicion
        if self.inicial is None:
            self.inicial = nombre
        return nombre

    def eliminar_estado(self, nombre: str) -> None:
        if nombre not in self.estados:
            raise ErrorAutomata(f"No existe el estado {nombre}.")
        self.estados.remove(nombre)
        self.aceptacion.discard(nombre)
        self.posiciones.pop(nombre, None)
        if self.inicial == nombre:
            self.inicial = self.estados[0] if self.estados else None
        nuevas: dict[tuple[str, str], set[str]] = {}
        for (q, s), ds in self.transiciones.items():
            if q == nombre:
                continue
            ds = {d for d in ds if d != nombre}
            if ds:
                nuevas[(q, s)] = ds
        self.transiciones = nuevas

    def renombrar_estado(self, viejo: str, nuevo: str) -> None:
        nuevo = nuevo.strip()
        if viejo not in self.estados:
            raise ErrorAutomata(f"No existe el estado {viejo}.")
        if not nuevo:
            raise ErrorAutomata("El nombre del estado no puede ser vacío.")
        if nuevo == viejo:
            return
        if nuevo in self.estados:
            raise ErrorAutomata(f"Ya existe un estado llamado {nuevo}.")
        self.estados[self.estados.index(viejo)] = nuevo
        if viejo in self.aceptacion:
            self.aceptacion.discard(viejo)
            self.aceptacion.add(nuevo)
        if self.inicial == viejo:
            self.inicial = nuevo
        if viejo in self.posiciones:
            self.posiciones[nuevo] = self.posiciones.pop(viejo)
        self.transiciones = {
            (nuevo if q == viejo else q, s): {nuevo if d == viejo else d for d in ds}
            for (q, s), ds in self.transiciones.items()
        }

    def agregar_simbolo(self, simbolo: str) -> None:
        if simbolo == LAMBDA:
            raise ErrorAutomata("λ no puede pertenecer al alfabeto: representa la cadena vacía.")
        if simbolo not in self.alfabeto:
            self.alfabeto.append(simbolo)

    def agregar_transicion(self, origen: str, simbolo: str, destino: str) -> None:
        for q in (origen, destino):
            if q not in self.estados:
                raise ErrorAutomata(f"No existe el estado {q}.")
        if simbolo != LAMBDA:
            self.agregar_simbolo(simbolo)
        self.transiciones.setdefault((origen, simbolo), set()).add(destino)

    def eliminar_transicion(self, origen: str, simbolo: str, destino: str) -> None:
        ds = self.transiciones.get((origen, simbolo))
        if not ds or destino not in ds:
            raise ErrorAutomata(f"No existe la transición δ({origen}, {mostrar_simbolo(simbolo)}) → {destino}.")
        ds.discard(destino)
        if not ds:
            del self.transiciones[(origen, simbolo)]

    def definir_transiciones(self, origen: str, simbolo: str, destinos: Iterable[str]) -> None:
        """Sustituye δ(origen, símbolo) por ``destinos`` (vacío la elimina)."""
        destinos = set(destinos)
        for d in destinos:
            if d not in self.estados:
                raise ErrorAutomata(f"No existe el estado {d}.")
        if destinos:
            if simbolo != LAMBDA:
                self.agregar_simbolo(simbolo)
            self.transiciones[(origen, simbolo)] = destinos
        else:
            self.transiciones.pop((origen, simbolo), None)

    def alternar_aceptacion(self, estado: str) -> None:
        if estado in self.aceptacion:
            self.aceptacion.discard(estado)
        else:
            self.aceptacion.add(estado)

    def eliminar_simbolos_sin_uso(self) -> None:
        usados = {s for (_, s) in self.transiciones}
        self.alfabeto = [s for s in self.alfabeto if s in usados]

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def destinos(self, origen: str, simbolo: str) -> set[str]:
        return self.transiciones.get((origen, simbolo), set())

    def lista_transiciones(self) -> list[tuple[str, str, str]]:
        """Ternas (origen, símbolo, destino) en orden estable."""
        # Se ordena por estado (orden de Q) y por símbolo (λ primero, luego en
        # orden lexicográfico). No se usa el orden de Σ porque .jff no lo guarda,
        # y así exportar lo importado produce exactamente el mismo archivo.
        orden_q = {q: i for i, q in enumerate(self.estados)}
        ternas = [(q, s, d) for (q, s), ds in self.transiciones.items() for d in ds]
        return sorted(ternas, key=lambda t: (orden_q.get(t[0], 1 << 30), t[1], orden_q.get(t[2], 1 << 30), t))

    def iter_transiciones(self) -> Iterator[tuple[str, str, str]]:
        yield from self.lista_transiciones()

    def agrupar_aristas(self) -> dict[tuple[str, str], list[str]]:
        """``(origen, destino) → [símbolos]`` para dibujar una flecha por par."""
        grupos: dict[tuple[str, str], list[str]] = {}
        for q, s, d in self.lista_transiciones():
            grupos.setdefault((q, d), []).append(s)
        return grupos

    def tiene_lambda(self) -> bool:
        return any(s == LAMBDA and ds for (_, s), ds in self.transiciones.items())

    def conflictos_determinismo(self) -> list[tuple[str, str, str]]:
        """Motivos por los que el autómata no es un AFD: ``(estado, símbolo, explicación)``."""
        conflictos = []
        for (q, s), ds in sorted(self.transiciones.items(), key=lambda kv: (self._orden(kv[0][0]), kv[0][1])):
            if not ds:
                continue
            if s == LAMBDA:
                conflictos.append((q, SIMBOLO_LAMBDA,
                                   f"δ({q}, λ) = {{{', '.join(sorted(ds))}}}: un AFD no admite transiciones λ"))
            elif len(ds) > 1:
                conflictos.append((q, s, f"δ({q}, {s}) tiene {len(ds)} destinos: {{{', '.join(sorted(ds))}}}"))
        return conflictos

    def _orden(self, q: str) -> int:
        try:
            return self.estados.index(q)
        except ValueError:
            return 1 << 30

    def es_determinista(self) -> bool:
        return not self.conflictos_determinismo()

    def es_completo(self) -> bool:
        """``True`` si δ(q, a) está definida para todo q ∈ Q y a ∈ Σ."""
        return all(self.destinos(q, a) for q in self.estados for a in self.alfabeto)

    def faltantes(self) -> list[tuple[str, str]]:
        return [(q, a) for q in self.estados for a in self.alfabeto if not self.destinos(q, a)]

    @property
    def tipo(self) -> str:
        if self.tiene_lambda():
            return AFND_LAMBDA
        if any(len(ds) > 1 for ds in self.transiciones.values()):
            return AFND
        return AFD

    def alcanzables(self) -> list[str]:
        """Estados alcanzables desde el inicial (con cualquier símbolo, incluido λ)."""
        if self.inicial is None:
            return []
        vistos = [self.inicial]
        pila = [self.inicial]
        sucesores: dict[str, set[str]] = {}
        for (q, _), ds in self.transiciones.items():
            sucesores.setdefault(q, set()).update(ds)
        while pila:
            q = pila.pop()
            for d in sorted(sucesores.get(q, ()), key=self._orden):
                if d not in vistos:
                    vistos.append(d)
                    pila.append(d)
        return sorted(vistos, key=self._orden)

    def inaccesibles(self) -> list[str]:
        alc = set(self.alcanzables())
        return [q for q in self.estados if q not in alc]

    def validar(self, estricto: bool = False) -> list[str]:
        """Lista de problemas de la definición. Con ``estricto`` lanza el primero."""
        errores: list[str] = []
        if not self.estados:
            errores.append("El autómata no tiene estados.")
        if len(set(self.estados)) != len(self.estados):
            errores.append("Hay estados repetidos.")
        if self.inicial is None:
            errores.append("No se ha definido el estado inicial.")
        elif self.inicial not in self.estados:
            errores.append(f"El estado inicial {self.inicial} no pertenece a Q.")
        for f in sorted(self.aceptacion - set(self.estados)):
            errores.append(f"El estado de aceptación {f} no pertenece a Q.")
        if LAMBDA in self.alfabeto:
            errores.append("λ no puede pertenecer al alfabeto.")
        for (q, s), ds in self.transiciones.items():
            if q not in self.estados:
                errores.append(f"δ usa el estado {q}, que no pertenece a Q.")
            if s != LAMBDA and s not in self.alfabeto:
                errores.append(f"δ usa el símbolo {s}, que no pertenece a Σ.")
            for d in ds:
                if d not in self.estados:
                    errores.append(f"δ({q}, {mostrar_simbolo(s)}) lleva a {d}, que no pertenece a Q.")
        if estricto and errores:
            raise ErrorAutomata(errores[0])
        return errores

    # ------------------------------------------------------------------
    # Cadenas de entrada
    # ------------------------------------------------------------------
    def tokenizar(self, cadena: str) -> list[str]:
        """Divide la entrada en símbolos de Σ.

        Si todos los símbolos tienen un carácter, cada carácter es un símbolo.
        Si hay símbolos de varios caracteres, la entrada puede separarse con
        espacios o comas; sin separadores se usa la coincidencia más larga.
        Un fragmento que no pertenece a Σ se conserva para que la simulación
        informe el error en la posición exacta.
        """
        if cadena in ("", SIMBOLO_LAMBDA):
            return []
        if all(len(s) == 1 for s in self.alfabeto):
            return [c for c in cadena if not c.isspace()] if " " in cadena else list(cadena)
        if any(sep in cadena for sep in (" ", ",")):
            return [p for p in cadena.replace(",", " ").split() if p]
        simbolos = sorted(self.alfabeto, key=len, reverse=True)
        res, i = [], 0
        while i < len(cadena):
            for s in simbolos:
                if cadena.startswith(s, i):
                    res.append(s)
                    i += len(s)
                    break
            else:
                res.append(cadena[i])
                i += 1
        return res

    # ------------------------------------------------------------------
    # Serialización neutral (la usan los formatos y los proyectos)
    # ------------------------------------------------------------------
    def a_dict(self) -> dict:
        trans = []
        for (q, s), ds in sorted(self.transiciones.items(), key=lambda kv: (self._orden(kv[0][0]), kv[0][1])):
            trans.append({"desde": q, "lee": s, "hacia": sorted(ds, key=self._orden)})
        datos = {
            "tipo": self.tipo,
            "nombre": self.nombre,
            "alfabeto": list(self.alfabeto),
            "estados": list(self.estados),
            "inicial": self.inicial,
            "aceptacion": sorted(self.aceptacion, key=self._orden),
            "transiciones": trans,
        }
        if self.descripcion:
            datos["descripcion"] = self.descripcion
        if self.posiciones:
            datos["posiciones"] = {q: [round(float(x), 1), round(float(y), 1)] for q, (x, y) in self.posiciones.items()
                                   if q in self.estados}
        return datos

    @classmethod
    def de_dict(cls, datos: dict) -> "Automata":
        if not isinstance(datos, dict):
            raise ErrorAutomata("Se esperaba un objeto con la definición del autómata.")
        faltan = [k for k in ("estados", "inicial", "aceptacion", "transiciones") if k not in datos]
        if faltan:
            raise ErrorAutomata(f"Faltan los campos: {', '.join(faltan)}.")
        a = cls(nombre=str(datos.get("nombre") or "Autómata"), descripcion=str(datos.get("descripcion") or ""))
        estados = datos["estados"]
        if not isinstance(estados, list) or not all(isinstance(q, str) for q in estados):
            raise ErrorAutomata("«estados» debe ser una lista de nombres.")
        for q in estados:
            a.agregar_estado(q)
        for s in datos.get("alfabeto") or []:
            a.agregar_simbolo(str(s))
        a.inicial = datos["inicial"]
        a.aceptacion = set(datos["aceptacion"] or [])
        for t in datos["transiciones"]:
            if not isinstance(t, dict) or not {"desde", "lee", "hacia"} <= set(t):
                raise ErrorAutomata("Cada transición necesita «desde», «lee» y «hacia».")
            hacia = t["hacia"] if isinstance(t["hacia"], list) else [t["hacia"]]
            for d in hacia:
                a.agregar_transicion(str(t["desde"]), leer_simbolo(str(t["lee"] or "")), str(d))
        for q, xy in (datos.get("posiciones") or {}).items():
            if q in a.estados and isinstance(xy, (list, tuple)) and len(xy) == 2:
                a.posiciones[q] = (float(xy[0]), float(xy[1]))
        a.validar(estricto=True)
        return a

    def misma_definicion(self, otro: "Automata") -> bool:
        """Compara las cinco componentes de la quíntupla (ignora nombre y posiciones)."""
        return (set(self.estados) == set(otro.estados)
                and set(self.alfabeto) == set(otro.alfabeto)
                and self.inicial == otro.inicial
                and self.aceptacion == otro.aceptacion
                and {k: v for k, v in self.transiciones.items() if v} == {k: v for k, v in otro.transiciones.items() if v})

    def quintupla(self) -> dict[str, str]:
        """Las cinco componentes como texto, para mostrarlas o documentarlas."""
        delta = [f"δ({q}, {mostrar_simbolo(s)}) = {d}" for q, s, d in self.lista_transiciones()]
        return {
            "Q": "{" + ", ".join(self.estados) + "}",
            "Σ": "{" + ", ".join(self.alfabeto) + "}",
            "q0": self.inicial or "—",
            "F": "{" + ", ".join(sorted(self.aceptacion, key=self._orden)) + "}",
            "δ": "; ".join(delta) if delta else "∅",
        }
