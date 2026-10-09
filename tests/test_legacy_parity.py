"""Compara el paquete con la salida que daba el backend antes de extraer la IA (fixtures/legacy_outputs.json, generado
 con el commit 56affa6 del monorepo): prompt, turnos, limpieza y validación de DNS deben coincidir carácter a carácter."""
import json
from pathlib import Path

import pytest

from redsana_ai import ChatEngine, ChatTurn, EngineSecurityBriefing, EngineSecurityChat, family_mode_topic_context
from redsana_ai import mentions_unexpected_dns, to_plain_text

LEGACY = json.loads((Path(__file__).parent / "fixtures" / "legacy_outputs.json").read_text(encoding="utf-8"))

# Lo que el backend le pasa al paquete para el Modo familiar (app/domain/family_mode.py en el momento de la foto).
FAMILY_DNS = ("1.1.1.3", "1.0.0.3")
FAMILY_MODE_GUIDE_STEPS = (
    "Abrir el panel del router en el navegador (suele ser 192.168.0.1 o 192.168.1.1; viene en la etiqueta del router).",
    "Entrar con el usuario y la contraseña de administración del router (suelen estar en esa misma etiqueta).",
    'Buscar la sección "Internet", "WAN", "DHCP" o "LAN" y dentro la opción "DNS"; si está en automático, pasarla a manual.',
    f"Escribir {FAMILY_DNS[0]} como DNS primario y {FAMILY_DNS[1]} como DNS secundario.",
    "Guardar los cambios y reiniciar el router si lo pide.",
)
TOPIC_CONTEXTS = {"family_mode": family_mode_topic_context(*FAMILY_DNS, FAMILY_MODE_GUIDE_STEPS)}
MODEL_REPLY = "## Resumen\nTu puntaje es **68/100**. Cierra el puerto `23` __hoy__.\n### Pasos\n- uno"


class _RecordingEngine(ChatEngine):
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def complete(self, system_prompt: str, turns: list[ChatTurn]) -> str:
        self.calls.append({"system_prompt": system_prompt, "turns": [[turn.role, turn.content] for turn in turns]})
        return MODEL_REPLY


@pytest.mark.parametrize("case", LEGACY["chat"])
def test_chat_sends_the_same_prompt_and_turns_and_returns_the_same_text(case: dict) -> None:
    engine = _RecordingEngine()
    history = [ChatTurn(role, content) for role, content in case["history"]]

    reply = EngineSecurityChat(engine).ask(case["context"], history, case["message"], TOPIC_CONTEXTS.get(case["topic"]))

    assert engine.calls == [case["engine_call"]]
    assert reply == case["reply"]


@pytest.mark.parametrize("case", LEGACY["briefing"])
def test_briefing_sends_the_same_prompt_and_request_and_returns_the_same_text(case: dict) -> None:
    engine = _RecordingEngine()

    reply = EngineSecurityBriefing(engine).write(case["context"], case["language"])

    assert engine.calls == [case["engine_call"]]
    assert reply == case["reply"]


@pytest.mark.parametrize("case", LEGACY["plain_text"])
def test_plain_text_cleanup_is_unchanged(case: dict) -> None:
    assert to_plain_text(case["input"]) == case["output"]


@pytest.mark.parametrize("case", LEGACY["unexpected_dns"])
def test_unexpected_dns_check_is_unchanged(case: dict) -> None:
    assert mentions_unexpected_dns(case["input"], FAMILY_DNS) is case["output"]
