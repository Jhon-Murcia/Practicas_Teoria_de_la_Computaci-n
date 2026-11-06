"""Ayuda contextual: guía de uso y convenciones de cada módulo."""

from __future__ import annotations

import flet as ft

from ui.componentes.comunes import tarjeta, texto, titulo_pagina
from ui.estado import Estado
from ui.tema import T

SECCIONES: list[tuple[str, object, str]] = [
    (
        "Convenciones generales", ft.Icons.RULE,
        """
* **λ** representa la cadena vacía. En los campos de texto puede escribir `λ`, `lambda` o dejar el campo vacío.
* Los alfabetos se escriben separando los símbolos con comas o espacios: `a, b, c` o `0 1`.
* Los conjuntos de cadenas se presentan en **orden canónico**: primero por longitud y, dentro de cada
  longitud, en el orden en que se escribió el alfabeto.
* Todas las pantallas permiten **exportar** los resultados a un archivo de texto. En el navegador
  (aplicación servida desde el contenedor) el archivo se descarga directamente.
""",
    ),
    (
        "Cadenas: prefijos, sufijos y subcadenas", ft.Icons.TEXT_FIELDS,
        """
* Un **prefijo** de *w* es cualquier *u* tal que *w = uv*; un **sufijo**, cualquier *v* tal que *w = uv*.
* El programa **incluye λ y la propia w** entre los prefijos y los sufijos, porque *w = λw = wλ*.
  Por eso una cadena de longitud *n* tiene exactamente **n + 1** prefijos y **n + 1** sufijos.
* Una **subcadena** es cualquier *v* tal que *w = uvx*. Hay *n − k + 1* posiciones para cada
  longitud *k*, de modo que el máximo de subcadenas distintas es **n(n+1)/2 + 1** (contando λ);
  se alcanza cuando todos los símbolos de *w* son distintos.
""",
    ),
    (
        "Lenguajes: Σ*, Σ⁺ y el límite de 200 000 cadenas", ft.Icons.ALL_INCLUSIVE,
        """
* **Σⁿ** contiene las |Σ|ⁿ cadenas de longitud exactamente *n*. En particular **Σ⁰ = {λ}**.
* **Σ\\*** = Σ⁰ ∪ Σ¹ ∪ Σ² ∪ … contiene a λ; **Σ⁺** = Σ¹ ∪ Σ² ∪ … no la contiene: Σ⁺ = Σ\\* − {λ}.
* Ambos conjuntos son infinitos, así que el programa los **trunca** a la longitud máxima elegida.
  El número de cadenas es Σ |Σ|ⁱ, que crece exponencialmente. Antes de generar, el programa
  calcula ese número con la fórmula y **rechaza** la operación si supera 200 000 cadenas.
""",
    ),
    (
        "Atajos", ft.Icons.KEYBOARD,
        """
* **Enter** en un campo de texto ejecuta la operación principal de la pantalla.
* El botón de la parte inferior del menú alterna entre el **tema oscuro** y el **claro**.
* Los valores que escriba en cada pantalla se conservan al navegar entre módulos.
""",
    ),
]


def construir(estado: Estado) -> ft.Control:
    tarjetas = [
        tarjeta(ft.Markdown(md.strip(), selectable=True, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB),
                titulo, icono)
        for titulo, icono, md in SECCIONES
    ]
    return ft.Column(
        [
            titulo_pagina("Ayuda y documentación",
                          "Guía rápida de uso y convenciones matemáticas adoptadas por el software.",
                          ft.Icons.HELP_ROUNDED),
            *tarjetas,
            texto("La documentación completa de cada práctica está en la carpeta docs/ del repositorio.",
                  12.5, T.texto_3),
        ],
        spacing=18,
    )
