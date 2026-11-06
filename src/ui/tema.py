"""Identidad visual del software: paletas, tipografías y medidas.

Las páginas leen los colores de :data:`T` en el momento de construirse. Al
cambiar de tema, la aplicación sustituye la paleta activa y reconstruye la
vista, de modo que no hace falta que cada control conozca ambos temas.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import flet as ft


@dataclass(frozen=True)
class Paleta:
    nombre: str
    fondo: str
    superficie: str
    superficie_2: str
    superficie_3: str
    borde: str
    texto: str
    texto_2: str
    texto_3: str
    primario: str
    primario_suave: str
    acento: str
    acento_suave: str
    exito: str
    exito_suave: str
    error: str
    error_suave: str
    aviso: str
    aviso_suave: str
    # Lienzo de autómatas
    lienzo: str
    rejilla: str
    estado: str
    estado_borde: str
    estado_texto: str
    transicion: str
    lambda_: str


OSCURO = Paleta(
    nombre="oscuro",
    fondo="#0A0E16",
    superficie="#111723",
    superficie_2="#161E2D",
    superficie_3="#1D2738",
    borde="#243047",
    texto="#E6EAF2",
    texto_2="#A3AEC2",
    texto_3="#6B7890",
    primario="#8B7CFF",
    primario_suave="#8B7CFF,0.13",
    acento="#2DD4BF",
    acento_suave="#2DD4BF,0.13",
    exito="#34D399",
    exito_suave="#34D399,0.13",
    error="#FB7185",
    error_suave="#FB7185,0.13",
    aviso="#FBBF24",
    aviso_suave="#FBBF24,0.13",
    lienzo="#0D121C",
    rejilla="#18202E",
    estado="#1A2335",
    estado_borde="#8B7CFF",
    estado_texto="#E6EAF2",
    transicion="#8C98AE",
    lambda_="#F59E0B",
)

CLARO = Paleta(
    nombre="claro",
    fondo="#F3F5FA",
    superficie="#FFFFFF",
    superficie_2="#F7F8FC",
    superficie_3="#EDF0F7",
    borde="#DCE1EC",
    texto="#151B2B",
    texto_2="#4B5670",
    texto_3="#8892A8",
    primario="#5B4BDB",
    primario_suave="#5B4BDB,0.09",
    acento="#0F9F8F",
    acento_suave="#0F9F8F,0.09",
    exito="#0E9F6E",
    exito_suave="#0E9F6E,0.09",
    error="#E11D48",
    error_suave="#E11D48,0.09",
    aviso="#B7791F",
    aviso_suave="#B7791F,0.09",
    lienzo="#FBFCFE",
    rejilla="#EEF1F7",
    estado="#FFFFFF",
    estado_borde="#5B4BDB",
    estado_texto="#151B2B",
    transicion="#5F6B85",
    lambda_="#C2410C",
)


class _TemaActivo:
    """Proxy mutable hacia la paleta en uso (``T.primario``, ``T.fondo``…)."""

    def __init__(self, paleta: Paleta):
        self._p = paleta

    def usar(self, paleta: Paleta) -> None:
        self._p = paleta

    @property
    def paleta(self) -> Paleta:
        return self._p

    @property
    def oscuro(self) -> bool:
        return self._p.nombre == "oscuro"

    def __getattr__(self, nombre: str):
        return getattr(self._p, nombre)


T = _TemaActivo(OSCURO)

FUENTE = "Inter"
FUENTE_MONO = "JetBrains Mono"

# Fuentes con licencia SIL OFL incluidas en src/assets/fonts para no depender
# de la red (en el contenedor y en modo web las fuentes remotas fallan por CORS).
FUENTES = {
    "Inter": "fonts/Inter.ttf",
    "JetBrains Mono": "fonts/JetBrainsMono.ttf",
}

RADIO = 14
RADIO_CHICO = 10
ESPACIO = 20


def tema_flet() -> ft.Theme:
    """Tema de Material que acompaña a la paleta activa."""
    return ft.Theme(
        color_scheme_seed=T.primario,
        font_family=FUENTE,
        color_scheme=ft.ColorScheme(
            primary=T.primario.split(",")[0],
            secondary=T.acento,
            surface=T.superficie,
            on_surface=T.texto,
            error=T.error,
            outline=T.borde,
        ),
        visual_density=ft.VisualDensity.COMFORTABLE,
    )


def alfa(color: str, opacidad: float) -> str:
    """Color con opacidad en el formato de Flet: ``"#8B7CFF,0.2"``."""
    return f"{color.split(',')[0]},{opacidad}"


__all__ = ["T", "OSCURO", "CLARO", "Paleta", "FUENTE", "FUENTE_MONO", "FUENTES", "RADIO",
           "RADIO_CHICO", "ESPACIO", "tema_flet", "alfa", "replace"]
