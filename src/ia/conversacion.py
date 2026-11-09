"""Conversación del asistente: historial, contexto de pantalla y límite de uso."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

from ia import cliente
from ia.prompts import SISTEMA_TUTOR, mensaje_con_contexto

MAX_MENSAJES = 8    # se envían sólo los últimos turnos, para no agotar la cuota gratuita de tokens


@dataclass
class Mensaje:
    rol: str        # "usuario" | "asistente" | "error"
    texto: str


@dataclass
class Conversacion:
    mensajes: list[Mensaje] = field(default_factory=list)
    historial: list[dict] = field(default_factory=list)   # formato de la API
    usadas: int = 0

    @property
    def restantes(self) -> int:
        return max(0, cliente.limite_por_sesion() - self.usadas)

    def limpiar(self) -> None:
        self.mensajes.clear()
        self.historial.clear()

    async def preguntar(self, pregunta: str, contexto: str = "",
                        al_texto: Optional[Callable[[str], Awaitable[None] | None]] = None,
                        sistema: str = SISTEMA_TUTOR) -> str:
        pregunta = pregunta.strip()
        if not pregunta:
            raise cliente.ErrorIA("Escriba una pregunta.")
        if self.restantes <= 0:
            raise cliente.ErrorIA(f"Se alcanzó el límite de {cliente.limite_por_sesion()} consultas en esta sesión.")
        self.mensajes.append(Mensaje("usuario", pregunta))
        envio = self.historial[-MAX_MENSAJES:] + [{"role": "user", "content": mensaje_con_contexto(pregunta, contexto)}]
        self.usadas += 1
        try:
            respuesta = await cliente.responder(sistema, envio, al_texto)
        except cliente.ErrorIA as exc:
            self.usadas -= 1          # una consulta fallida no cuenta para el límite
            self.mensajes.append(Mensaje("error", str(exc)))
            raise
        # En el historial se guarda la pregunta sin el contexto, que cambia con la pantalla.
        self.historial += [{"role": "user", "content": pregunta}, {"role": "assistant", "content": respuesta}]
        self.mensajes.append(Mensaje("asistente", respuesta))
        return respuesta
