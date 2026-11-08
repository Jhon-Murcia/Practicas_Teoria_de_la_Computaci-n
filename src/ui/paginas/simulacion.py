"""Simulación y validación de cadenas, paso a paso."""

from __future__ import annotations

import asyncio
from typing import Optional

import flet as ft

from core import ejemplos
from core.automata import LAMBDA, Automata, mostrar_simbolo
from core.lenguajes import mostrar
from core.simulacion import (Arbol, Nodo, Resultado, arbol_computacion, informe_lote, leer_lineas, simular,
                             validar_lote)
from ui.componentes.comunes import (aviso, boton, boton_icono, campo, chip, pestanas, refrescar, tarjeta, texto,
                                    titulo_pagina)
from ui.componentes.lienzo import Lienzo
from ia.contexto import describir_automata
from ui.estado import Estado
from ui.tema import FUENTE_MONO, RADIO_CHICO, T, alfa


def conjunto(estados, a: Automata) -> str:
    return "{" + ", ".join(sorted(estados, key=a._orden)) + "}" if estados else "∅"


class PaginaSimulacion:
    def __init__(self, estado: Estado):
        self.estado = estado
        estado.contexto_ia = self._contexto_ia
        if estado.actual is None:
            estado.agregar_automata(ejemplos.termina_en_ab())
        self.pestana = estado.recuperar("sim.pestana", "traza")
        self.entrada = campo("Cadena de entrada", estado.recuperar("sim.cadena", "aab"),
                             "λ o vacío para la cadena vacía", al_enviar=lambda e: self.validar(), expand=True)
        self.lienzo = Lienzo(estado.actual, editable=False, alto=430)
        self.resultado: Optional[Resultado] = None
        self.k = 0
        self.reproduciendo = False
        self.selector = ft.Container()
        self.cinta = ft.Container()
        self.detalle = ft.Column(spacing=12)
        self.banner = ft.Container()
        self.selector_pestana = ft.Container()
        self.inferior = ft.Column(spacing=12)
        self.controles = ft.Container()
        self.pruebas = campo("Una cadena por línea", estado.recuperar("sim.pruebas", "ab\naab\nba\nλ\nbab"),
                             multiline=True, min_lines=6, max_lines=12)
        self.tabla_pruebas = ft.Column(spacing=6)
        self.lote = []
        self.origen_lote = ""
        self._construir_selector()
        self.validar(registrar=False)

    @property
    def a(self) -> Automata:
        return self.estado.actual

    # ------------------------------------------------------------------
    def _construir_selector(self) -> None:
        self.selector.content = ft.Dropdown(
            value=str(self.estado.indice),
            options=[ft.DropdownOption(key=str(i), text=f"{x.nombre}  ·  {x.tipo}")
                     for i, x in enumerate(self.estado.automatas)],
            label="Autómata", width=330, dense=True, border_radius=RADIO_CHICO, border_color=T.borde,
            on_select=self._cambiar_automata,
        )

    def _cambiar_automata(self, e) -> None:
        self.estado.seleccionar(int(e.control.value))
        self.lienzo.usar(self.a)
        self.validar(registrar=False)

    def validar(self, registrar: bool = True) -> None:
        self.reproduciendo = False
        cadena = self.entrada.value or ""
        self.estado.recordar("sim.cadena", cadena)
        cadena = "" if cadena.strip() in ("λ", "lambda") else cadena
        self.resultado = simular(self.a, cadena)
        self.k = len(self.resultado.pasos)
        if registrar:
            r = self.resultado
            self.estado.registrar(f"«{mostrar(cadena)}» {'aceptada' if r.aceptada else 'rechazada'} por {self.a.nombre}",
                                  ft.Icons.PLAY_CIRCLE_OUTLINE, T.exito if r.aceptada else T.error)
        self._actualizar()

    def ir(self, k: int) -> None:
        if self.resultado is None:
            return
        self.k = max(0, min(k, len(self.resultado.pasos)))
        self._actualizar()

    async def _reproducir(self) -> None:
        if self.resultado is None:
            return
        if self.k >= len(self.resultado.pasos):
            self.k = 0
        self.reproduciendo = True
        self._actualizar()
        while self.reproduciendo and self.resultado and self.k < len(self.resultado.pasos):
            await asyncio.sleep(0.9)
            if not self.reproduciendo:
                break
            self.k += 1
            self._actualizar()
        self.reproduciendo = False
        self._actualizar()

    def alternar_reproduccion(self, e=None) -> None:
        if self.reproduciendo:
            self.reproduciendo = False
            self._actualizar()
        else:
            self.estado.page.run_task(self._reproducir)

    # ------------------------------------------------------------------
    # Estado visible en el paso k
    # ------------------------------------------------------------------
    def _activos(self) -> tuple[frozenset[str], list[tuple[str, str, str]]]:
        r = self.resultado
        if self.k == 0:
            return r.inicio, r.lambda_inicio
        p = r.pasos[self.k - 1]
        return p.despues, p.transiciones + p.transiciones_lambda

    def _actualizar(self) -> None:
        r = self.resultado
        activos, usadas = self._activos()
        terminado = self.k == len(r.pasos)
        if r.error and terminado:
            color = T.error
        elif terminado:
            color = T.exito if r.aceptada else T.error
        else:
            color = T.acento
        self.lienzo.resaltar(activos, {(o, d) for o, _, d in usadas}, color)
        self._construir_controles()
        self._construir_cinta()
        self._construir_banner()
        self._construir_detalle()
        self._construir_inferior()
        refrescar(self.controles, self.cinta, self.banner, self.detalle, self.inferior)

    def _construir_controles(self) -> None:
        n = len(self.resultado.pasos) if self.resultado else 0
        self.controles.content = ft.Row(
            [
                boton("Validar", lambda e: self.validar(), ft.Icons.PLAY_ARROW_ROUNDED),
                ft.Container(ft.Row([
                    boton_icono(ft.Icons.FIRST_PAGE, lambda e: self.ir(0), "Configuración inicial"),
                    boton_icono(ft.Icons.CHEVRON_LEFT, lambda e: self.ir(self.k - 1), "Paso anterior"),
                    boton_icono(ft.Icons.PAUSE if self.reproduciendo else ft.Icons.SLOW_MOTION_VIDEO,
                                self.alternar_reproduccion, "Reproducir paso a paso", T.primario),
                    boton_icono(ft.Icons.CHEVRON_RIGHT, lambda e: self.ir(self.k + 1), "Paso siguiente"),
                    boton_icono(ft.Icons.LAST_PAGE, lambda e: self.ir(n), "Resultado final"),
                ], spacing=0, tight=True), border_radius=11, bgcolor=T.superficie_2, border=ft.Border.all(1, T.borde)),
                chip(f"paso {self.k} / {n}", T.primario, mono=True),
            ],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _construir_cinta(self) -> None:
        r = self.resultado
        celdas = []
        if not r.simbolos:
            celdas.append(ft.Container(texto("λ", 16, T.lambda_, mono=True, peso=ft.FontWeight.W_700),
                                       width=44, height=44, alignment=ft.Alignment.CENTER, border_radius=8,
                                       bgcolor=alfa(T.lambda_, 0.12), border=ft.Border.all(1, alfa(T.lambda_, 0.4))))
        for i, s in enumerate(r.simbolos):
            leido = i < self.k
            actual = i == self.k - 1
            error = r.posicion_error == i + 1
            color = T.error if error else (T.primario if actual else (T.texto_3 if leido else T.texto))
            celdas.append(ft.Container(
                texto(s, 16, color, mono=True, peso=ft.FontWeight.W_700),
                width=max(44, 12 * len(s) + 20), height=44, alignment=ft.Alignment.CENTER, border_radius=8,
                bgcolor=alfa(color, 0.16) if actual or error else (T.superficie_3 if not leido else T.superficie_2),
                border=ft.Border.all(2 if actual else 1, color if actual or error else T.borde),
                tooltip=f"Símbolo {i + 1}",
            ))
        cabeza = ("Configuración inicial: aún no se ha leído ningún símbolo." if self.k == 0
                  else f"Se han leído {self.k} de {len(r.simbolos)} símbolos.")
        self.cinta.content = ft.Column([
            ft.Row([ft.Icon(ft.Icons.STRAIGHTEN, size=16, color=T.texto_3), texto("Cinta de entrada", 13, T.texto_2,
                                                                                    peso=ft.FontWeight.W_600),
                    texto(cabeza, 12, T.texto_3)], spacing=8),
            ft.Row(celdas, spacing=6, scroll=ft.ScrollMode.AUTO),
        ], spacing=10)

    def _construir_banner(self) -> None:
        r = self.resultado
        terminado = self.k == len(r.pasos)
        if r.error and terminado:
            self.banner.content = aviso(r.error, "error")
        elif not terminado:
            self.banner.content = aviso("Simulación en curso: avance con ▶ o reproduzca automáticamente.", "info",
                                        ft.Icons.HOURGLASS_TOP)
        else:
            ok = r.aceptada
            self.banner.content = ft.Container(
                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE if ok else ft.Icons.CANCEL, color=T.exito if ok else T.error,
                                size=30),
                        ft.Column([texto("CADENA ACEPTADA" if ok else "CADENA RECHAZADA", 16,
                                         T.exito if ok else T.error, peso=ft.FontWeight.W_800),
                                   texto(r.explicacion(self.a), 12.5, T.texto_2)], spacing=2, expand=True),
                        ft.TextButton("¿Por qué?", icon=ft.Icons.AUTO_AWESOME,
                                      tooltip="Pedir al asistente de IA que explique el resultado",
                                      on_click=lambda e: self.estado.preguntar_ia(
                                          "¿Por qué esta cadena se " + ("aceptó" if ok else "rechazó")
                                          + "? Explícalo recorriendo los estados."))],
                       spacing=12),
                padding=16, border_radius=12, bgcolor=alfa(T.exito if ok else T.error, 0.1),
                border=ft.Border.all(1, alfa(T.exito if ok else T.error, 0.4)),
            )

    def _fila(self, etiqueta: str, valor: str, color: Optional[str] = None) -> ft.Control:
        return ft.Row([texto(etiqueta, 12.5, T.texto_3, width=150),
                       texto(valor, 13, color or T.texto, mono=True, expand=True, selectable=True)],
                      vertical_alignment=ft.CrossAxisAlignment.START)

    def _construir_detalle(self) -> None:
        a, r = self.a, self.resultado
        filas: list[ft.Control] = []
        if self.k == 0:
            filas += [
                texto("Paso 0 · configuración inicial", 15, peso=ft.FontWeight.W_700),
                self._fila("Estado inicial", conjunto(r.inicio_sin_cerradura, a)),
                self._fila("Transiciones λ", ", ".join(f"{o}→{d}" for o, _, d in r.lambda_inicio) or "ninguna",
                           T.lambda_),
                self._fila("Activos (λ-clausura)", conjunto(r.inicio, a), T.acento),
            ]
        else:
            p = r.pasos[self.k - 1]
            filas += [
                texto(f"Paso {p.numero} · se lee «{p.simbolo}»", 15, peso=ft.FontWeight.W_700),
                self._fila("Activos antes", conjunto(p.antes, a)),
                self._fila("Transiciones", ", ".join(f"δ({o},{s})→{d}" for o, s, d in p.transiciones) or
                           "ninguna: la computación muere", T.texto if p.transiciones else T.error),
                self._fila("Tras leer (antes de λ-cl.)", conjunto(p.movimiento, a)),
                self._fila("Transiciones λ", ", ".join(f"{o}→{d}" for o, _, d in p.transiciones_lambda) or "ninguna",
                           T.lambda_),
                self._fila("Después de la λ-clausura", conjunto(p.despues, a), T.acento),
            ]
        activos, _ = self._activos()
        finales = activos & a.aceptacion
        filas.append(self._fila("Activos en F", conjunto(finales, a), T.exito if finales else T.texto_3))
        if a.descripcion:
            filas.append(ft.Container(texto(a.descripcion, 12, T.texto_3), padding=ft.Padding.only(top=6)))
        self.detalle.controls = filas

    # ------------------------------------------------------------------
    # Pestañas inferiores
    # ------------------------------------------------------------------
    def _cambiar_pestana(self, clave: str) -> None:
        self.pestana = clave
        self.estado.recordar("sim.pestana", clave)
        self._construir_inferior()
        refrescar(self.inferior)

    def _construir_inferior(self) -> None:
        self.selector_pestana.content = pestanas(
            [("traza", "Traza completa"), ("arbol", "Árbol de caminos"), ("pruebas", "Varias cadenas")],
            self.pestana, self._cambiar_pestana)
        if self.pestana == "arbol":
            cuerpo = self._arbol()
        elif self.pestana == "pruebas":
            cuerpo = ft.Column([
                ft.Row([ft.Container(self.pruebas, expand=True),
                        ft.Column([boton("Validar todas", self.probar_todas, ft.Icons.PLAYLIST_PLAY),
                                   boton("Cargar .txt", self.cargar_archivo, ft.Icons.UPLOAD_FILE, "secundario"),
                                   boton("Guardar informe", self.guardar_informe, ft.Icons.SAVE_ALT, "secundario")],
                                  spacing=8)],
                       vertical_alignment=ft.CrossAxisAlignment.START, spacing=12),
                self.tabla_pruebas,
            ], spacing=12)
        else:
            cuerpo = self._traza()
        self.inferior.controls = [self.selector_pestana, cuerpo]

    def _traza(self) -> ft.Control:
        a, r = self.a, self.resultado
        encabezado = ["#", "Activos antes", "Lee", "Transiciones", "λ", "Activos después"]
        anchos = [40, 170, 60, 280, 170, 170]

        def fila(valores, resaltar=False, cabecera=False):
            return ft.Container(
                ft.Row([texto(v, 12.5, T.texto_3 if cabecera else T.texto, mono=not cabecera, width=w,
                              peso=ft.FontWeight.W_700 if cabecera else None)
                        for v, w in zip(valores, anchos)], spacing=8),
                padding=ft.Padding.symmetric(horizontal=10, vertical=7), border_radius=8,
                bgcolor=T.primario_suave if resaltar else (T.superficie_2 if cabecera else None),
            )

        filas = [fila(encabezado, cabecera=True),
                 fila(["0", conjunto(r.inicio_sin_cerradura, a), "—", "—",
                       ", ".join(f"{o}→{d}" for o, _, d in r.lambda_inicio) or "—", conjunto(r.inicio, a)],
                      self.k == 0)]
        for p in r.pasos:
            filas.append(fila([str(p.numero), conjunto(p.antes, a), p.simbolo,
                               ", ".join(f"{o}→{d}" for o, _, d in p.transiciones) or "∅",
                               ", ".join(f"{o}→{d}" for o, _, d in p.transiciones_lambda) or "—",
                               conjunto(p.despues, a)], self.k == p.numero))
        return ft.Row([ft.Column(filas, spacing=2)], scroll=ft.ScrollMode.AUTO)

    def _arbol(self) -> ft.Control:
        arbol: Arbol = arbol_computacion(self.a, self.resultado.simbolos, max_nodos=300)
        lineas: list[ft.Control] = []

        def nodo(n: Nodo, prefijo: str, ultimo: bool, raiz: bool) -> None:
            conector = "" if raiz else ("└── " if ultimo else "├── ")
            via = "" if raiz else f"{mostrar_simbolo(n.via)} → "
            if n.aceptacion:
                fin, color = "  ✔ acepta", T.exito
            elif n.ciclo:
                fin, color = "  ↺ ciclo λ (se corta)", T.aviso
            elif n.muerto:
                fin, color = "  ✘ sin transición", T.error
            elif not n.hijos and n.leidos == len(self.resultado.simbolos):
                fin, color = "  ✘ no es de aceptación", T.error
            else:
                fin, color = "", T.texto
            lineas.append(ft.Text(
                spans=[ft.TextSpan(prefijo + conector, ft.TextStyle(color=T.texto_3)),
                       ft.TextSpan(via, ft.TextStyle(color=T.lambda_ if n.via == LAMBDA else T.acento)),
                       ft.TextSpan(n.estado, ft.TextStyle(color=T.texto, weight=ft.FontWeight.W_700)),
                       ft.TextSpan(f"  [{n.leidos}]", ft.TextStyle(color=T.texto_3)),
                       ft.TextSpan(fin, ft.TextStyle(color=color, weight=ft.FontWeight.W_600))],
                font_family=FUENTE_MONO, size=13, selectable=True))
            hijos = n.hijos
            for i, h in enumerate(hijos):
                nodo(h, prefijo + ("" if raiz else ("    " if ultimo else "│   ")), i == len(hijos) - 1, False)

        nodo(arbol.raiz, "", True, True)
        resumen = [chip(f"{arbol.nodos} nodos", T.texto_2, mono=True),
                   chip(f"{arbol.caminos_aceptacion} camino(s) de aceptación",
                        T.exito if arbol.caminos_aceptacion else T.error)]
        if arbol.truncado:
            resumen.append(chip("árbol truncado a 300 nodos", T.aviso))
        return ft.Column([
            ft.Row(resumen, spacing=8, wrap=True),
            texto("Cada rama es una computación posible. [n] = símbolos leídos al llegar al estado. "
                  "Las transiciones λ no consumen símbolos.", 12, T.texto_3),
            ft.Container(ft.Column(lineas, spacing=1), padding=14, border_radius=10, bgcolor=T.superficie_2),
        ], spacing=10)

    def probar_todas(self, e=None, origen: str = "") -> None:
        self.estado.recordar("sim.pruebas", self.pruebas.value)
        cadenas = leer_lineas(self.pruebas.value or "")
        self.lote = validar_lote(self.a, cadenas)
        self.origen_lote = origen
        aceptadas = sum(r.aceptada for r in self.lote)
        filas = [ft.Row([
            texto(mostrar(r.cadena), 13, mono=True, width=220),
            chip("aceptada" if r.aceptada else "rechazada", T.exito if r.aceptada else T.error),
            texto(r.error or ("finales: " + conjunto(r.finales, self.a)), 12, T.texto_3, expand=True),
        ], spacing=12) for r in self.lote[:400]]
        if len(self.lote) > 400:
            filas.append(texto(f"… {len(self.lote) - 400} más en el informe", 12, T.texto_3))
        self.tabla_pruebas.controls = [
            texto(f"{len(cadenas)} cadenas · {aceptadas} aceptadas · {len(cadenas) - aceptadas} rechazadas"
                  + (f" · archivo {origen}" if origen else ""), 13, T.texto_2, peso=ft.FontWeight.W_600), *filas]
        self.estado.registrar(f"Validadas {len(cadenas)} cadenas en {self.a.nombre}", ft.Icons.PLAYLIST_PLAY)
        refrescar(self.tabla_pruebas)

    async def cargar_archivo(self, e=None) -> None:
        archivo = await self.estado.abrir(["txt"])
        if archivo is None:
            return
        nombre, datos = archivo
        try:
            contenido = datos.decode("utf-8-sig")
        except UnicodeDecodeError:
            contenido = datos.decode("latin-1")
        self.pruebas.value = contenido
        refrescar(self.pruebas)
        self.probar_todas(origen=nombre)
        self.estado.notificar(f"{len(self.lote)} cadenas leídas de {nombre}.", "exito")

    async def guardar_informe(self, e=None) -> None:
        if not getattr(self, "lote", None):
            self.probar_todas()
        await self.estado.guardar("informe_validacion.txt", informe_lote(self.a, self.lote, self.origen_lote), ["txt"])

    # ------------------------------------------------------------------
    def _contexto_ia(self) -> str:
        r = self.resultado
        partes = [describir_automata(self.a)]
        if r is not None:
            partes.append(f"Cadena simulada: «{r.cadena or 'λ'}». Resultado: "
                          + ("aceptada" if r.aceptada else "rechazada") + f". {r.explicacion(self.a)}")
            partes.append(f"Paso mostrado: {self.k} de {len(r.pasos)}.")
            if self.k:
                p = r.pasos[self.k - 1]
                partes.append(f"En ese paso se lee «{p.simbolo}»: activos antes {conjunto(p.antes, self.a)}, "
                              f"después de la λ-clausura {conjunto(p.despues, self.a)}.")
        return "\n".join(partes)

    def vista(self) -> ft.Control:
        entrada = tarjeta(ft.Column([
            ft.Row([self.selector, self.entrada], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
            self.controles,
        ], spacing=12), "Entrada", ft.Icons.KEYBOARD_OUTLINED)
        izquierda = ft.Column([self.lienzo.control, tarjeta(self.cinta)], spacing=14)
        derecha = ft.Column([self.banner, tarjeta(self.detalle, "Paso actual", ft.Icons.TIMELINE)], spacing=14)
        return ft.Column([
            titulo_pagina("Simulación de autómatas",
                          "Valide cadenas y siga cada paso: estados activos, transiciones y λ-clausura.",
                          ft.Icons.PLAY_CIRCLE_ROUNDED, "Práctica 2"),
            entrada,
            ft.ResponsiveRow([ft.Container(izquierda, col={"xs": 12, "lg": 7}),
                              ft.Container(derecha, col={"xs": 12, "lg": 5})], spacing=16, run_spacing=16),
            tarjeta(self.inferior),
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def construir(estado: Estado) -> ft.Control:
    return PaginaSimulacion(estado).vista()
