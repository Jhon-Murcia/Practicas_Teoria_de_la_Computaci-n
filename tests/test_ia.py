"""Pruebas del asistente de IA con un cliente simulado (no usan la red)."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from core import ejemplos
from ia import cliente
from ia.contexto import SUGERENCIAS, describir_automata
from ia.conversacion import MAX_MENSAJES, Conversacion
from ia.prompts import ESQUEMA_EJERCICIO, SISTEMA_TUTOR, mensaje_con_contexto, pedido_pista


class _Flujo:
    def __init__(self, trozos, stop_reason="end_turn"):
        self.trozos = trozos
        self.stop_reason = stop_reason

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    @property
    def text_stream(self):
        async def gen():
            for t in self.trozos:
                yield t
        return gen()

    async def get_final_message(self):
        texto = "".join(self.trozos)
        return SimpleNamespace(stop_reason=self.stop_reason,
                               content=[SimpleNamespace(type="text", text=texto)])


class ClienteFalso:
    """Imita ``client.messages.stream`` y ``client.beta.messages.stream``."""

    def __init__(self, trozos, stop_reason="end_turn"):
        self.llamadas = []
        falso = self

        class _Mensajes:
            def stream(self_inner, **params):
                falso.llamadas.append(params)
                return _Flujo(trozos, stop_reason)

        self.messages = _Mensajes()
        self.beta = SimpleNamespace(messages=_Mensajes())


@pytest.fixture
def con_clave(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-de-prueba")
    yield
    cliente.usar_cliente(None)


def correr(corrutina):
    return asyncio.run(corrutina)


def test_sin_clave_la_ia_esta_desactivada(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not cliente.disponible()
    with pytest.raises(cliente.ErrorIA, match="ANTHROPIC_API_KEY"):
        correr(cliente.responder("s", [{"role": "user", "content": "hola"}]))


def test_respuesta_en_streaming_y_parametros(con_clave, monkeypatch):
    monkeypatch.delenv("IA_MODELO", raising=False)
    falso = ClienteFalso(["Un AFD ", "tiene un ", "solo destino."])
    cliente.usar_cliente(falso)
    vistos = []
    texto = correr(cliente.responder("sistema", [{"role": "user", "content": "¿Qué es un AFD?"}], vistos.append))
    assert texto == "Un AFD tiene un solo destino."
    assert vistos[-1] == texto and len(vistos) == 3
    params = falso.llamadas[0]
    assert params["model"] == "claude-opus-5-5"
    assert params["fallbacks"] == "default" and params["betas"] == [cliente.BETA_FALLBACK]
    assert params["output_config"] == {"effort": "low"}
    assert "thinking" not in params and "temperature" not in params


def test_haiku_no_usa_fallbacks(con_clave, monkeypatch):
    monkeypatch.setenv("IA_MODELO", "claude-haiku-5-5")
    falso = ClienteFalso(["ok"])
    cliente.usar_cliente(falso)
    correr(cliente.responder("s", [{"role": "user", "content": "x"}]))
    assert "fallbacks" not in falso.llamadas[0] and falso.llamadas[0]["model"] == "claude-haiku-5-5"


def test_rechazo_se_informa(con_clave):
    cliente.usar_cliente(ClienteFalso([], stop_reason="refusal"))
    with pytest.raises(cliente.ErrorIA, match="reformularla"):
        correr(cliente.responder("s", [{"role": "user", "content": "x"}]))


def test_generar_json_con_esquema(con_clave):
    datos = {"titulo": "t", "enunciado": "e", "tipo": "expresion", "alfabeto": ["a"],
             "expresion_referencia": "a*", "dificultad": "básico"}
    falso = ClienteFalso([json.dumps(datos)])
    cliente.usar_cliente(falso)
    assert correr(cliente.generar_json("s", "pedido", ESQUEMA_EJERCICIO)) == datos
    formato = falso.llamadas[0]["output_config"]["format"]
    assert formato == {"type": "json_schema", "schema": ESQUEMA_EJERCICIO}


def test_conversacion_envia_contexto_pero_guarda_solo_la_pregunta(con_clave):
    falso = ClienteFalso(["Respuesta"])
    cliente.usar_cliente(falso)
    conv = Conversacion()
    correr(conv.preguntar("¿Por qué se rechaza?", "Autómata X"))
    enviado = falso.llamadas[0]["messages"][-1]["content"]
    assert "Contexto de la pantalla" in enviado and "Autómata X" in enviado
    assert conv.historial == [{"role": "user", "content": "¿Por qué se rechaza?"},
                              {"role": "assistant", "content": "Respuesta"}]
    assert falso.llamadas[0]["system"] == SISTEMA_TUTOR


def test_conversacion_acota_el_historial_y_el_limite(con_clave, monkeypatch):
    monkeypatch.setenv("IA_LIMITE_SESION", "10")
    falso = ClienteFalso(["r"])
    cliente.usar_cliente(falso)
    conv = Conversacion()
    for i in range(10):
        correr(conv.preguntar(f"pregunta {i}"))
    assert len(falso.llamadas[-1]["messages"]) == MAX_MENSAJES + 1
    with pytest.raises(cliente.ErrorIA, match="límite"):
        correr(conv.preguntar("una más"))


def test_instrucciones_prohiben_resolver_ejercicios():
    assert "No resuelves ejercicios" in SISTEMA_TUTOR
    assert "No construyes autómatas" in SISTEMA_TUTOR


def test_pista_no_incluye_la_referencia():
    texto = pedido_pista("Cadenas con dos aes", "b*ab*", "aa", True)
    assert "«aa»" in texto and "debería aceptarse" in texto and "sin darle la solución" in texto


def test_contexto_describe_el_automata():
    texto = describir_automata(ejemplos.termina_en_ab())
    assert "AFND" in texto and "δ(q0, a) ∋ q1" in texto and "No es determinista" in texto
    assert mensaje_con_contexto("hola", "") == "hola"


def test_hay_sugerencias_para_cada_seccion():
    from ui.aplicacion import MODULOS
    assert {m.clave for m in MODULOS} <= set(SUGERENCIAS)
