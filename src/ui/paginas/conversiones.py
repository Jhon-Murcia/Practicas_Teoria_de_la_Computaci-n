"""Conversiones: λ-clausura, eliminación de λ, subconjuntos, AFD → ER y la cadena completa."""

from __future__ import annotations

from typing import Optional

import flet as ft

from core import ejemplos
from core.automata import Automata
from core.expresion_regular import a_python, a_texto, tamano
from algoritmos.cerradura import cerradura_con_pasos, tabla_cerraduras
from algoritmos.eliminacion_estados import eliminar_estados
from algoritmos.eliminacion_lambda import eliminar_lambda
from algoritmos.minimizacion import minimizar
from algoritmos.pasos import conjunto
from algoritmos.subconjuntos import construir_afd
from ui.componentes.automatas import acciones_resultado, resumen_automata, selector_automata
from ui.componentes.comunes import aviso, boton, chip, pestanas, refrescar, tarjeta, texto, titulo_pagina
from ui.componentes.reproductor import Reproductor, tabla_control
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO_CHICO, T, alfa

ALGORITMOS = [
    ("cerradura", "λ-clausura"),
    ("lambda", "Eliminar λ"),
    ("subconjuntos", "Subconjuntos"),
    ("er", "Autómata → ER"),
    ("cadena", "Cadena completa"),
]

EXPLICACION = {
    "cerradura": "λ-clausura(q): estados alcanzables desde q usando sólo transiciones λ (incluye a q).",
    "lambda": "δ'(q, a) = λ-clausura(δ(λ-clausura(q), a)) y F' = {q : λ-clausura(q) ∩ F ≠ ∅}.",
    "subconjuntos": "Cada estado del AFD es un subconjunto de estados del AFN; sólo se generan los alcanzables.",
    "er": "Se agrega un inicio I y un final F, y se elimina un estado a la vez: R(p,r) += R(p,q)R(q,q)*R(q,r).",
    "cadena": "AFN-λ → AFN sin λ → AFD (subconjuntos) → AFD mínimo, verificando el número de estados.",
}


class PaginaConversiones:
    def __init__(self, estado: Estado):
        self.estado = estado
        if estado.actual is None:
            estado.agregar_automata(ejemplos.a_estrella_b_estrella_c_estrella())
        self.algoritmo = estado.recuperar("conv.algoritmo", "cerradura")
        self.reproductor = Reproductor(estado)
        self.cabecera = ft.Container()
        self.opciones = ft.Container()
        self.resultado = ft.Column(spacing=14)
        self.estado_cerradura: Optional[str] = None
        self.orden_er = estado.recuperar("conv.orden", "heuristica")
        self.salida: Optional[Automata] = None
        self._construir_cabecera()
        self.ejecutar(registrar=False)

    @property
    def a(self) -> Automata:
        return self.estado.actual

    # ------------------------------------------------------------------
    def _construir_cabecera(self) -> None:
        self.cabecera.content = ft.Column([
            ft.Row([
                selector_automata(self.estado, self.estado.indice, self._cambiar_automata),
                resumen_automata(self.a),
            ], spacing=14, wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            pestanas(ALGORITMOS, self.algoritmo, self._cambiar_algoritmo),
            texto(EXPLICACION[self.algoritmo], 12.5, T.texto_3),
        ], spacing=12)

    def _cambiar_automata(self, i: int) -> None:
        self.estado.seleccionar(i)
        self.estado_cerradura = None
        self._construir_cabecera()
        self.ejecutar()
        refrescar(self.cabecera)

    def _cambiar_algoritmo(self, clave: str) -> None:
        self.algoritmo = clave
        self.estado.recordar("conv.algoritmo", clave)
        self._construir_cabecera()
        self.ejecutar()
        refrescar(self.cabecera)

    # ------------------------------------------------------------------
    def ejecutar(self, registrar: bool = True) -> None:
        a = self.a
        self.salida = None
        self.opciones.content = None
        try:
            if self.algoritmo == "cerradura":
                self._cerradura(a)
            elif self.algoritmo == "lambda":
                self.salida, pasos, info = eliminar_lambda(a)
                self.reproductor.cargar(pasos)
                self.resultado.controls = self._resultado_lambda(info)
            elif self.algoritmo == "subconjuntos":
                self.salida, pasos, tabla = construir_afd(a)
                self.reproductor.cargar(pasos)
                self.resultado.controls = self._resultado_subconjuntos(tabla)
            elif self.algoritmo == "er":
                self._er(a)
            else:
                self._cadena(a)
        except ValueError as exc:
            self.reproductor.cargar([])
            self.resultado.controls = [aviso(str(exc), "error")]
        if registrar:
            nombre = dict(ALGORITMOS)[self.algoritmo]
            self.estado.registrar(f"{nombre} aplicado a «{a.nombre}»", ft.Icons.TRANSFORM)
        refrescar(self.opciones, self.resultado)

    # ------------------------------------------------------------------
    def _cerradura(self, a: Automata) -> None:
        if not a.estados:
            raise ValueError("El autómata no tiene estados.")
        if self.estado_cerradura not in a.estados:
            self.estado_cerradura = a.inicial or a.estados[0]
        self.opciones.content = ft.Row([
            texto("Estado:", 13, T.texto_2),
            ft.Dropdown(value=self.estado_cerradura, dense=True, width=180, border_radius=RADIO_CHICO,
                        options=[ft.DropdownOption(key=q, text=q) for q in a.estados],
                        on_select=lambda e: self._elegir_estado(e.control.value)),
        ], spacing=10)
        _, pasos = cerradura_con_pasos(a, self.estado_cerradura)
        self.reproductor.cargar(pasos)
        clausuras = tabla_cerraduras(a)
        filas = [["q", "λ-clausura(q)", "¿contiene un estado de F?"]]
        for q in a.estados:
            filas.append([q, conjunto(clausuras[q], a._orden),
                          "sí" if clausuras[q] & a.aceptacion else "no"])
        papel = ("Al simular un AFN-λ, el conjunto activo inicial es λ-clausura(q0), y después de leer cada "
                 "símbolo se vuelve a aplicar la clausura: así las transiciones λ se recorren sin consumir "
                 "símbolos. Un estado cuya clausura contiene un estado de F acepta la cadena vacía.")
        self.resultado.controls = [
            tarjeta(ft.Column([tabla_control(filas), texto(papel, 12.5, T.texto_3)], spacing=12),
                    "λ-clausura de todos los estados", ft.Icons.TABLE_CHART_OUTLINED),
        ]

    def _elegir_estado(self, q: str) -> None:
        self.estado_cerradura = q
        self.ejecutar(registrar=False)

    def _resultado_lambda(self, info: dict) -> list[ft.Control]:
        agregadas = [f"δ'({q},{s}) ∋ {d}" for q, s, d in info["agregadas"]]
        return [tarjeta(ft.Column([
            resumen_automata(self.salida, "AFN resultante:"),
            ft.Row([chip(f"{len(info['agregadas'])} transiciones agregadas", T.primario),
                    chip(f"{len(info['eliminadas'])} transiciones λ eliminadas", T.lambda_),
                    chip("nuevos de aceptación: " + (", ".join(info["nuevas_finales"]) or "ninguno"), T.exito)],
                   spacing=8, wrap=True),
            texto("Transiciones agregadas: " + ("; ".join(agregadas) if agregadas else "ninguna"), 12.5, T.texto_2,
                  mono=True, selectable=True),
            acciones_resultado(self.estado, lambda: self.salida, f"{self.a.nombre} (sin λ)"),
        ], spacing=12), "Resultado", ft.Icons.CHECK_CIRCLE_OUTLINE)]

    def _resultado_subconjuntos(self, tabla) -> list[ft.Control]:
        n = len(self.a.estados)
        return [tarjeta(ft.Column([
            resumen_automata(self.salida, "AFD resultante:"),
            texto(f"El AFN tiene {n} estados; la cota es 2^{n} = {2 ** n} subconjuntos y se generaron "
                  f"{len(self.salida.estados)} (sólo los alcanzables desde el inicial).", 13, T.texto_2),
            tabla_control(tabla),
            acciones_resultado(self.estado, lambda: self.salida, f"{self.a.nombre} (AFD)"),
        ], spacing=12), "Tabla de transiciones del AFD", ft.Icons.GRID_ON)]

    # ------------------------------------------------------------------
    def _er(self, a: Automata) -> None:
        self.opciones.content = ft.Row([
            texto("Orden de eliminación:", 13, T.texto_2),
            pestanas([("heuristica", "Menos combinaciones primero"), ("q", "Orden de Q")], self.orden_er,
                     self._cambiar_orden),
        ], spacing=10, wrap=True)
        orden = None if self.orden_er == "heuristica" else list(a.estados)
        expr, pasos, usado = eliminar_estados(a, orden)
        self.reproductor.cargar(pasos)
        texto_er = a_texto(expr)
        if not a.es_determinista():
            nota = aviso("El método también se aplica a AFND y AFND-λ (las λ se tratan como la expresión λ).", "info")
        else:
            nota = ft.Container()
        self.resultado.controls = [tarjeta(ft.Column([
            ft.Container(ft.Text(texto_er, size=20, font_family=FUENTE_MONO, color=T.primario, selectable=True,
                                 weight=ft.FontWeight.W_700),
                         padding=16, border_radius=RADIO_CHICO, bgcolor=alfa(T.primario, 0.08),
                         border=ft.Border.all(1, alfa(T.primario, 0.3))),
            ft.Row([chip(f"longitud: {tamano(expr)} símbolos y operadores", T.texto_2),
                    chip("orden: " + ", ".join(usado), T.texto_2, mono=True)], spacing=8, wrap=True),
            ft.Row([texto("En el módulo re de Python:", 12.5, T.texto_3),
                    ft.Text(a_python(expr), font_family=FUENTE_MONO, size=13, color=T.acento, selectable=True)],
                   spacing=10, wrap=True),
            nota,
        ], spacing=12), "Expresión regular", ft.Icons.FUNCTIONS)]

    def _cambiar_orden(self, clave: str) -> None:
        self.orden_er = clave
        self.estado.recordar("conv.orden", clave)
        self.ejecutar(registrar=False)

    # ------------------------------------------------------------------
    def _cadena(self, a: Automata) -> None:
        sin_lambda, p1, _ = eliminar_lambda(a)
        afd, p2, _ = construir_afd(sin_lambda)
        minimo, p3, _ = minimizar(afd)
        etapas = [("1 · Original", a, None), ("2 · AFN sin λ", sin_lambda, p1), ("3 · AFD (subconjuntos)", afd, p2),
                  ("4 · AFD mínimo", minimo, p3)]
        self.salida = minimo
        self.reproductor.cargar(p1 + p2 + p3)
        tarjetas = []
        for titulo, aut, pasos in etapas:
            tarjetas.append(ft.Container(ft.Column([
                texto(titulo, 14, peso=ft.FontWeight.W_700),
                texto(f"{len(aut.estados)}", 30, T.primario, mono=True, peso=ft.FontWeight.W_800),
                texto("estados", 12, T.texto_3),
                resumen_automata(aut),
                *( [ft.TextButton("Ver estos pasos", on_click=lambda e, ps=pasos: self.reproductor.cargar(ps))]
                   if pasos else []),
            ], spacing=6), padding=16, border_radius=14, bgcolor=T.superficie, border=ft.Border.all(1, T.borde),
                col={"xs": 12, "md": 6, "xl": 3}))
        self.resultado.controls = [
            ft.ResponsiveRow(tarjetas, spacing=12, run_spacing=12),
            aviso(f"El AFD mínimo tiene {len(minimo.estados)} estados, no más que los {len(afd.estados)} del AFD "
                  "de subconjuntos.", "exito"),
            acciones_resultado(self.estado, lambda: self.salida, f"{a.nombre} (mínimo)"),
        ]

    # ------------------------------------------------------------------
    def vista(self) -> ft.Control:
        return ft.Column([
            titulo_pagina("Conversión de autómatas",
                          "Algoritmos paso a paso: λ-clausura, eliminación de λ, subconjuntos y autómata → ER.",
                          ft.Icons.TRANSFORM_ROUNDED, "Práctica 3"),
            tarjeta(ft.Column([self.cabecera, self.opciones], spacing=12)),
            tarjeta(self.reproductor.vista(), "Ejecución paso a paso", ft.Icons.TIMELINE),
            self.resultado,
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def construir(estado: Estado) -> ft.Control:
    return PaginaConversiones(estado).vista()
