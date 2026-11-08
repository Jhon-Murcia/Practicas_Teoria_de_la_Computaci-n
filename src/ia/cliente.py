"""Conexión con la API de Claude (Anthropic) para el asistente.

La clave se lee de la variable de entorno ``ANTHROPIC_API_KEY`` y nunca llega
al navegador: Flet ejecuta este código en el servidor. Si no hay clave, la IA
queda desactivada y el resto del sistema funciona igual.

Variables de entorno:

* ``ANTHROPIC_API_KEY``: clave de la API (obligatoria para usar la IA).
* ``IA_MODELO``: modelo a usar (por omisión ``claude-opus-5-5``).
* ``IA_LIMITE_SESION``: máximo de consultas por sesión del navegador
  (por omisión 40), para que un despliegue público no gaste sin control.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable, Optional

MODELO_POR_OMISION = "claude-opus-5-5"
# Modelos que admiten el reintento automático en el servidor cuando un filtro de
# seguridad rechaza la petición (parámetro ``fallbacks``). Haiku no lo admite.
CON_FALLBACK = ("claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5")
BETA_FALLBACK = "server-side-fallback-2026-07-01"


class ErrorIA(RuntimeError):
    """Error con un mensaje apto para mostrarse al usuario."""


def modelo() -> str:
    return os.getenv("IA_MODELO", "").strip() or MODELO_POR_OMISION


def limite_por_sesion() -> int:
    try:
        return max(1, int(os.getenv("IA_LIMITE_SESION", "40")))
    except ValueError:
        return 40


def disponible() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


_cliente = None


def _obtener_cliente():
    """Cliente asíncrono, creado la primera vez que se usa (las pruebas lo sustituyen)."""
    global _cliente
    if _cliente is None:
        import anthropic
        _cliente = anthropic.AsyncAnthropic(timeout=90.0, max_retries=2)
    return _cliente


def usar_cliente(cliente) -> None:
    """Sustituye el cliente (para pruebas sin red)."""
    global _cliente
    _cliente = cliente


def _parametros(sistema: str, mensajes: list[dict], max_tokens: int, formato: Optional[dict]) -> dict:
    salida: dict = {"effort": "low"}
    if formato is not None:
        salida["format"] = formato
    params = {
        "model": modelo(),
        "max_tokens": max_tokens,
        "system": sistema,
        "messages": mensajes,
        "output_config": salida,
        # Guarda en caché el prefijo estable (instrucciones del sistema).
        "cache_control": {"type": "ephemeral"},
    }
    return params


def _traducir_error(exc: Exception) -> ErrorIA:
    import anthropic
    if isinstance(exc, anthropic.AuthenticationError):
        return ErrorIA("La clave de la API no es válida. Revise ANTHROPIC_API_KEY.")
    if isinstance(exc, anthropic.PermissionDeniedError):
        return ErrorIA("La clave de la API no tiene permiso para usar este modelo.")
    if isinstance(exc, anthropic.NotFoundError):
        return ErrorIA(f"El modelo «{modelo()}» no existe o no está disponible. Revise IA_MODELO.")
    if isinstance(exc, anthropic.RateLimitError):
        return ErrorIA("Se alcanzó el límite de uso de la API. Intente de nuevo en un momento.")
    if isinstance(exc, anthropic.BadRequestError):
        return ErrorIA(f"La petición a la IA no es válida: {exc.message}")
    if isinstance(exc, anthropic.APIStatusError):
        return ErrorIA(f"El servicio de IA respondió con un error ({exc.status_code}). Intente más tarde.")
    if isinstance(exc, anthropic.APIConnectionError):
        return ErrorIA("No hay conexión con el servicio de IA.")
    return ErrorIA(f"Error inesperado del asistente: {exc}")


async def responder(sistema: str, mensajes: list[dict],
                    al_texto: Optional[Callable[[str], Awaitable[None] | None]] = None,
                    max_tokens: int = 8000) -> str:
    """Envía la conversación y devuelve el texto de la respuesta.

    ``al_texto`` recibe el texto acumulado mientras llega (streaming), para
    mostrar la respuesta poco a poco.
    """
    if not disponible():
        raise ErrorIA("El asistente no está configurado: falta la variable ANTHROPIC_API_KEY.")
    import anthropic
    cliente = _obtener_cliente()
    params = _parametros(sistema, mensajes, max_tokens, None)
    if modelo() in CON_FALLBACK:
        flujo = cliente.beta.messages.stream(betas=[BETA_FALLBACK], fallbacks="default", **params)
    else:
        flujo = cliente.messages.stream(**params)
    texto = ""
    try:
        async with flujo as stream:
            async for trozo in stream.text_stream:
                texto += trozo
                if al_texto is not None:
                    resultado = al_texto(texto)
                    if hasattr(resultado, "__await__"):
                        await resultado
            final = await stream.get_final_message()
    except anthropic.APIError as exc:
        raise _traducir_error(exc) from exc
    if final.stop_reason == "refusal":
        raise ErrorIA("La IA no pudo responder a esa consulta. Intente reformularla.")
    if final.stop_reason == "max_tokens":
        texto += "\n\n*(La respuesta se cortó por su longitud.)*"
    return texto


async def generar_json(sistema: str, pedido: str, esquema: dict, max_tokens: int = 4000) -> dict:
    """Pide una respuesta que cumpla un esquema JSON (salidas estructuradas)."""
    if not disponible():
        raise ErrorIA("El asistente no está configurado: falta la variable ANTHROPIC_API_KEY.")
    import anthropic
    cliente = _obtener_cliente()
    formato = {"type": "json_schema", "schema": esquema}
    params = _parametros(sistema, [{"role": "user", "content": pedido}], max_tokens, formato)
    try:
        if modelo() in CON_FALLBACK:
            flujo = cliente.beta.messages.stream(betas=[BETA_FALLBACK], fallbacks="default", **params)
        else:
            flujo = cliente.messages.stream(**params)
        async with flujo as stream:
            final = await stream.get_final_message()
    except anthropic.APIError as exc:
        raise _traducir_error(exc) from exc
    if final.stop_reason == "refusal":
        raise ErrorIA("La IA no pudo generar el contenido. Intente de nuevo.")
    texto = next((b.text for b in final.content if b.type == "text"), "")
    try:
        return json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ErrorIA("La IA devolvió un formato inesperado. Intente de nuevo.") from exc
