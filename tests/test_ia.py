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


def _trozo(contenido=None, fin=None):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=contenido), finish_reason=fin)])


class _Flujo:
    def __init__(self, trozos, fin):
        self.trozos = trozos
        self.fin = fin

    def __aiter__(self):
        async def gen():
            # El razonamiento llega en trozos sin contenido, que no deben mostrarse.
            yield _trozo(None)
            for t in self.trozos:
                yield _trozo(t)
            yield _trozo(None, self.fin)
            yield SimpleNamespace(choices=[])      # trozo final con el uso de tokens
        return gen()


class ClienteFalso:
    """Imita ``client.chat.completions.create`` de la librería openai."""

    def __init__(self, trozos, fin="stop"):
        self.llamadas = []
        falso = self

        class _Completions:
            async def create(self_inner, **params):
                falso.llamadas.append(params)
                if params.get("stream"):
                    return _Flujo(trozos, fin)
                mensaje = SimpleNamespace(content="".join(trozos))
                return SimpleNamespace(choices=[SimpleNamespace(message=mensaje, finish_reason=fin)])

        self.chat = SimpleNamespace(completions=_Completions())


@pytest.fixture
def con_clave(monkeypatch):
    monkeypatch.setenv("IA_API_KEY", "clave-de-prueba")
    yield
    cliente.usar_cliente(None)


def correr(corrutina):
    return asyncio.run(corrutina)


def test_sin_clave_la_ia_esta_desactivada(monkeypatch):
    monkeypatch.delenv("IA_API_KEY", raising=False)
    assert not cliente.disponible()
    with pytest.raises(cliente.ErrorIA, match="IA_API_KEY"):
        correr(cliente.responder("s", [{"role": "user", "content": "hola"}]))


def test_por_omision_usa_groq_gratuito(monkeypatch):
    monkeypatch.delenv("IA_MODELO", raising=False)
    monkeypatch.delenv("IA_URL", raising=False)
    assert cliente.modelo() == "openai/gpt-oss-120b"
    assert cliente.url() == "https://api.groq.com/openai/v1"


def test_respuesta_en_streaming_y_parametros(con_clave, monkeypatch):
    monkeypatch.delenv("IA_MODELO", raising=False)
    falso = ClienteFalso(["Un AFD ", "tiene un ", "solo destino."])
    cliente.usar_cliente(falso)
    vistos = []
    texto = correr(cliente.responder("sistema", [{"role": "user", "content": "¿Qué es un AFD?"}], vistos.append))
    assert texto == "Un AFD tiene un solo destino."
    assert vistos[-1] == texto and len(vistos) == 3
    params = falso.llamadas[0]
    assert params["model"] == "openai/gpt-oss-120b" and params["stream"] is True
    assert params["messages"][0] == {"role": "system", "content": "sistema"}
    assert params["reasoning_effort"] == "low"


def test_otro_modelo_no_recibe_reasoning_effort(con_clave, monkeypatch):
    monkeypatch.setenv("IA_MODELO", "gemini-flash")
    falso = ClienteFalso(["ok"])
    cliente.usar_cliente(falso)
    correr(cliente.responder("s", [{"role": "user", "content": "x"}]))
    assert "reasoning_effort" not in falso.llamadas[0] and falso.llamadas[0]["model"] == "gemini-flash"


@pytest.mark.parametrize("trozos,fin", [([], "stop"), (["algo"], "content_filter")])
def test_rechazo_se_informa(con_clave, trozos, fin):
    cliente.usar_cliente(ClienteFalso(trozos, fin))
    with pytest.raises(cliente.ErrorIA, match="reformularla"):
        correr(cliente.responder("s", [{"role": "user", "content": "x"}]))


def test_respuesta_cortada_se_avisa(con_clave):
    cliente.usar_cliente(ClienteFalso(["mitad"], "length"))
    assert "se cortó" in correr(cliente.responder("s", [{"role": "user", "content": "x"}]))


def test_generar_json_con_esquema(con_clave):
    datos = {"titulo": "t", "enunciado": "e", "tipo": "expresion", "alfabeto": ["a"],
             "expresion_referencia": "a*", "dificultad": "básico"}
    falso = ClienteFalso([json.dumps(datos)])
    cliente.usar_cliente(falso)
    assert correr(cliente.generar_json("s", "pedido", ESQUEMA_EJERCICIO)) == datos
    formato = falso.llamadas[0]["response_format"]
    assert formato["type"] == "json_schema" and formato["json_schema"]["schema"] == ESQUEMA_EJERCICIO
    assert formato["json_schema"]["strict"] is True


def test_esquema_cumple_el_modo_estricto():
    # En modo estricto todas las propiedades deben ser obligatorias y no se admiten otras.
    assert set(ESQUEMA_EJERCICIO["required"]) == set(ESQUEMA_EJERCICIO["properties"])
    assert ESQUEMA_EJERCICIO["additionalProperties"] is False


def test_conversacion_envia_contexto_pero_guarda_solo_la_pregunta(con_clave):
    falso = ClienteFalso(["Respuesta"])
    cliente.usar_cliente(falso)
    conv = Conversacion()
    correr(conv.preguntar("¿Por qué se rechaza?", "Autómata X"))
    enviado = falso.llamadas[0]["messages"][-1]["content"]
    assert "Contexto de la pantalla" in enviado and "Autómata X" in enviado
    assert conv.historial == [{"role": "user", "content": "¿Por qué se rechaza?"},
                              {"role": "assistant", "content": "Respuesta"}]
    assert falso.llamadas[0]["messages"][0] == {"role": "system", "content": SISTEMA_TUTOR}


def test_conversacion_acota_el_historial_y_el_limite(con_clave, monkeypatch):
    monkeypatch.setenv("IA_LIMITE_SESION", "10")
    falso = ClienteFalso(["r"])
    cliente.usar_cliente(falso)
    conv = Conversacion()
    for i in range(10):
        correr(conv.preguntar(f"pregunta {i}"))
    # instrucciones del sistema + últimos turnos + pregunta actual
    assert len(falso.llamadas[-1]["messages"]) == MAX_MENSAJES + 2
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
