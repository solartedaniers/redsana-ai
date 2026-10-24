from abc import ABC, abstractmethod

from redsana_ai.assistant.prompt import build_system_prompt
from redsana_ai.assistant.reply_guard import to_plain_text
from redsana_ai.chat.engine import ChatEngine, ChatTurn

# Mensajes previos que van al modelo: suficientes para seguir el hilo sin inflar el prompt.
CHAT_HISTORY_LIMIT = 12


class SecurityChat(ABC):
    """Interfaz del chat del asistente: quien llama da los datos reales ya armados, nunca su base de datos."""

    @abstractmethod
    def ask(
        self, user_context: str, history: list[ChatTurn], user_message: str, topic_context: str | None = None
    ) -> str:
        """history: la conversación previa en orden; topic_context: instrucciones extra del tema, si hay."""


class EngineSecurityChat(SecurityChat):
    """Responde un mensaje con el modelo, dándole las reglas, los datos reales y el historial reciente."""

    def __init__(self, engine: ChatEngine, history_limit: int = CHAT_HISTORY_LIMIT) -> None:
        self._engine = engine
        self._history_limit = history_limit

    def ask(
        self, user_context: str, history: list[ChatTurn], user_message: str, topic_context: str | None = None
    ) -> str:
        system_prompt = build_system_prompt(user_context, topic_context)
        turns = [*history[-self._history_limit :], ChatTurn("user", user_message)]
        return to_plain_text(self._engine.complete(system_prompt, turns))
