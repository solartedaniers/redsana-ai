from abc import ABC, abstractmethod
from typing import Literal

from redsana_ai.assistant.prompt import build_system_prompt
from redsana_ai.assistant.reply_guard import to_plain_text
from redsana_ai.chat.engine import ChatEngine, ChatTurn

BriefingLanguage = Literal["es", "en"]

_LANGUAGE_NAMES: dict[BriefingLanguage, str] = {"es": "espanol", "en": "ingles"}

# Instrucción interna (el usuario no la ve y no se guarda) para el primer mensaje tras una evaluación.
# Los pesos no van aquí: los manda el backend en los datos del usuario, desde su configuración.
_BRIEFING_REQUEST = """\
El usuario acaba de enviar su evaluacion de seguridad. Escribe TU el primer mensaje \
de la conversacion, en {language}, en lenguaje sencillo y sin jerga:
1. Su puntaje y el desglose (cuestionario y analisis tecnico, con el peso de cada \
parte que dan los datos del usuario).
2. De donde sale el analisis tecnico: si se midio desde la app de escritorio, dilo con \
su fecha; si fue reutilizado de una medicion anterior, dilo con su fecha; si NO hay \
analisis tecnico, explica con honestidad que el puntaje es solo del cuestionario y que \
el cifrado WiFi y los puertos del router solo se pueden medir desde la app de escritorio.
3. Que encontro, empezando por lo mas urgente (puertos de riesgo abiertos como Telnet, \
cifrado WiFi debil, respuestas debiles del cuestionario), y como solucionar cada cosa.
4. Termina invitandolo a seguir preguntando.
Usa UNICAMENTE los "Datos actuales del usuario"; no inventes hallazgos. Se breve."""


class SecurityBriefing(ABC):
    """Interfaz del mensaje inicial tras una evaluación; guardarlo es trabajo de quien llama."""

    @abstractmethod
    def write(self, user_context: str, language: BriefingLanguage) -> str:
        """user_context: los datos reales del usuario ya armados, con su evaluación más reciente."""


class EngineSecurityBriefing(SecurityBriefing):
    """Redacta el resumen con el modelo a partir de las reglas del asistente y los datos reales."""

    def __init__(self, engine: ChatEngine) -> None:
        self._engine = engine

    def write(self, user_context: str, language: BriefingLanguage) -> str:
        system_prompt = build_system_prompt(user_context)
        request = _BRIEFING_REQUEST.format(language=_LANGUAGE_NAMES[language])
        return to_plain_text(self._engine.complete(system_prompt, [ChatTurn("user", request)]))
