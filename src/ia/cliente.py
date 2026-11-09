"""Conexión con el modelo de lenguaje que usa el asistente.

Por omisión se usa **Groq** (https://groq.com), que tiene un plan gratuito sin
tarjeta, con el modelo abierto ``openai/gpt-oss-120b``. Groq expone una API
compatible con la de OpenAI, así que la conexión se hace con la librería
``openai`` cambiando la dirección base. Por eso cualquier otro servicio
compatible (por ejemplo Gemini de Google, que también tiene plan gratuito)
sirve cambiando ``IA_URL`` e ``IA_MODELO``.

La clave nunca llega al navegador: Flet ejecuta este código en el servidor. Si
no hay clave, la IA queda desactivada y el resto del sistema funciona igual.

Variables de entorno:

* ``IA_API_KEY``: clave de la API (obligatoria para usar la IA).
* ``IA_URL``: dirección base de la API (por omisión la de Groq).
* ``IA_MODELO``: modelo a usar (por omisión ``openai/gpt-oss-120b``).
* ``IA_LIMITE_SESION``: máximo de consultas por sesión del navegador
  (por omisión 40), para que un despliegue público no agote la cuota gratuita.
"""

from __future__ import annotations

import json
import os
from typing import Awaitable, Callable, Optional

URL_POR_OMISION = "https://api.groq.com/openai/v1"
MODELO_POR_OMISION = "openai/gpt-oss-120b"


class ErrorIA(RuntimeError):
    """Error con un mensaje apto para mostrarse al usuario."""


def modelo() -> str:
    return os.getenv("IA_MODELO", "").strip() or MODELO_POR_OMISION


def url() -> str:
    return os.getenv("IA_URL", "").strip() or URL_POR_OMISION


def limite_por_sesion() -> int:
    try:
        return max(1, int(os.getenv("IA_LIMITE_SESION", "40")))
    except ValueError:
        return 40


def disponible() -> bool:
    return bool(os.getenv("IA_API_KEY", "").strip())


_cliente = None


def _obtener_cliente():
    """Cliente asíncrono, creado la primera vez que se usa (las pruebas lo sustituyen)."""
    global _cliente
    if _cliente is None:
        import openai
        _cliente = openai.AsyncOpenAI(api_key=os.getenv("IA_API_KEY", "").strip(), base_url=url(),
                                      timeout=90.0, max_retries=2)
    return _cliente


def usar_cliente(cliente) -> None:
    """Sustituye el cliente (para pruebas sin red)."""
    global _cliente
    _cliente = cliente


def _parametros(sistema: str, mensajes: list[dict], max_tokens: int) -> dict:
    params = {
        "model": modelo(),
        "messages": [{"role": "system", "content": sistema}, *mensajes],
        "max_completion_tokens": max_tokens,
    }
    # Los modelos gpt-oss razonan antes de responder; con esfuerzo bajo responden
    # más rápido y gastan menos de la cuota gratuita de tokens por minuto.
    if "gpt-oss" in modelo():
        params["reasoning_effort"] = "low"
    return params


def _traducir_error(exc: Exception) -> ErrorIA:
    import openai
    if isinstance(exc, openai.AuthenticationError):
        return ErrorIA("La clave de la API no es válida. Revise IA_API_KEY.")
    if isinstance(exc, openai.PermissionDeniedError):
        return ErrorIA("La clave de la API no tiene permiso para usar este modelo.")
    if isinstance(exc, openai.NotFoundError):
        return ErrorIA(f"El modelo «{modelo()}» no existe o no está disponible. Revise IA_MODELO.")
    if isinstance(exc, openai.RateLimitError):
        return ErrorIA("Se alcanzó el límite gratuito de uso de la IA. Espere un minuto e intente de nuevo "
                       "(si persiste, la cuota del día se agotó).")
    if isinstance(exc, openai.BadRequestError):
        return ErrorIA(f"La petición a la IA no es válida: {exc.message}")
    if isinstance(exc, openai.APIStatusError):
        return ErrorIA(f"El servicio de IA respondió con un error ({exc.status_code}). Intente más tarde.")
    if isinstance(exc, openai.APIConnectionError):
        return ErrorIA("No hay conexión con el servicio de IA.")
    return ErrorIA(f"Error inesperado del asistente: {exc}")


async def responder(sistema: str, mensajes: list[dict],
                    al_texto: Optional[Callable[[str], Awaitable[None] | None]] = None,
                    max_tokens: int = 3000) -> str:
    """Envía la conversación y devuelve el texto de la respuesta.

    ``al_texto`` recibe el texto acumulado mientras llega (streaming), para
    mostrar la respuesta poco a poco.
    """
    if not disponible():
        raise ErrorIA("El asistente no está configurado: falta la variable IA_API_KEY.")
    import openai
    cliente = _obtener_cliente()
    texto, fin = "", None
    try:
        flujo = await cliente.chat.completions.create(stream=True, **_parametros(sistema, mensajes, max_tokens))
        async for trozo in flujo:
            if not trozo.choices:
                continue
            opcion = trozo.choices[0]
            fin = opcion.finish_reason or fin
            # Sólo se muestra el contenido; el razonamiento interno no se envía al usuario.
            if opcion.delta.content:
                texto += opcion.delta.content
                if al_texto is not None:
                    resultado = al_texto(texto)
                    if hasattr(resultado, "__await__"):
                        await resultado
    except openai.APIError as exc:
        raise _traducir_error(exc) from exc
    if fin == "content_filter" or (not texto.strip() and fin != "length"):
        raise ErrorIA("La IA no pudo responder a esa consulta. Intente reformularla.")
    if fin == "length":
        texto += "\n\n*(La respuesta se cortó por su longitud.)*"
    return texto


async def generar_json(sistema: str, pedido: str, esquema: dict, max_tokens: int = 3000) -> dict:
    """Pide una respuesta que cumpla un esquema JSON (salidas estructuradas)."""
    if not disponible():
        raise ErrorIA("El asistente no está configurado: falta la variable IA_API_KEY.")
    import openai
    cliente = _obtener_cliente()
    formato = {"type": "json_schema", "json_schema": {"name": "respuesta", "strict": True, "schema": esquema}}
    try:
        respuesta = await cliente.chat.completions.create(
            response_format=formato, **_parametros(sistema, [{"role": "user", "content": pedido}], max_tokens))
    except openai.APIError as exc:
        raise _traducir_error(exc) from exc
    texto = respuesta.choices[0].message.content if respuesta.choices else ""
    try:
        return json.loads(texto or "")
    except json.JSONDecodeError as exc:
        raise ErrorIA("La IA devolvió un formato inesperado. Intente de nuevo.") from exc
