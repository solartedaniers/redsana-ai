# 🤖 RedSana AI (`redsana-ai`)

Paquete Python con la inteligencia artificial de RedSana: el asistente de seguridad conversacional (Groq), la detección de anomalías de red (IsolationForest) y la detección de cortes de conexión.

Es una librería: no lee variables de entorno ni conoce la base de datos. Todo lo que necesita (claves, modelo, tiempos de espera, parámetros y los datos reales del usuario) entra por constructor o por parámetro. El backend lo instala por URL de git, fijado a un tag, y lo arma en un único lugar de composición.

> Repositorios del proyecto: frontend · backend · IA (enlaces pendientes de publicar).

## Interfaz pública

Todo se importa desde `redsana_ai`. Cada capacidad es una interfaz (clase abstracta) con una implementación, para poder cambiarla después (por ejemplo por un adaptador HTTP) sin tocar a quien la usa.

| Interfaz | Implementación | Qué hace |
|---|---|---|
| `ChatEngine` | `GroqClient` | Envía el system prompt y los turnos al modelo y devuelve el texto. |
| `SecurityChat` | `EngineSecurityChat` | Responde un mensaje del usuario con las reglas del asistente, sus datos reales y el historial reciente. |
| `SecurityBriefing` | `EngineSecurityBriefing` | Redacta el primer mensaje tras una evaluación de seguridad (`"es"` o `"en"`). |
| `AnomalyDetector` | `IsolationForestAnomalyDetector` | Dice si la última medición es anómala frente a su historial y qué métrica se desvió. |
| `OutageDetector` | `StreakOutageDetector` | Detecta un corte total que acaba de recuperarse y su duración. |

Datos que entran y salen (dataclasses y tuplas simples, serializables a JSON): `ChatTurn`, `DeviationClassification`, `OutageEpisode`, `NetworkMetricVector` y `OutageSample`.

Utilidades: `build_system_prompt`, `family_mode_topic_context`, `to_plain_text` y `mentions_unexpected_dns`.

## Parámetros

| Clase | Parámetro | Por defecto | Significado |
|---|---|---|---|
| `GroqClient` | `api_key` | — | API key de Groq. |
| | `model` | — | Modelo de Groq. |
| | `timeout_seconds` | — | Espera máxima por respuesta. |
| | `temperature` | — | Creatividad del modelo (baja para copiar datos exactos). |
| | `api_url` | `https://api.groq.com/openai/v1/chat/completions` | Endpoint de chat completions. |
| | `user_agent` | `Mozilla/5.0 (compatible; RedSana-backend/1.0)` | Cloudflare bloquea el de urllib. |
| `EngineSecurityChat` | `history_limit` | `12` | Mensajes previos que van al modelo. |
| `IsolationForestAnomalyDetector` | `contamination` | `0.1` | Proporción esperada de anomalías. |
| | `random_state` | `42` | Semilla, para resultados reproducibles. |
| | `critical_z_score` | `3.0` | Desviación a partir de la cual es `critical`. |
| `StreakOutageDetector` | `packet_loss_threshold_percent` | `100.0` | Pérdida que cuenta como caída total. |
| | `max_gap_between_samples` | 5 min | Hueco máximo para afirmar un corte continuo. |
| | `critical_duration_minutes` | `15` | Duración a partir de la cual es `critical`. |

Constantes para quien consulta el historial: `ANOMALY_WINDOW_SIZE` (1440 mediciones ≈ 24 h), `OUTAGE_LOOKBACK_LIMIT` (120) y `CHAT_HISTORY_LIMIT` (12).

## Uso

```python
from redsana_ai import ChatTurn, EngineSecurityChat, GroqClient

engine = GroqClient(api_key="...", model="openai/gpt-oss-120b", timeout_seconds=30, temperature=0.2)
reply = EngineSecurityChat(engine).ask(
    user_context="- Dispositivos conectados: 3.",
    history=[ChatTurn("user", "hola")],
    user_message="¿mi red es segura?",
)
```

## Desarrollo y pruebas

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -e ".[test]"
pytest
```

`tests/test_legacy_parity.py` compara el paquete con la salida que daba el backend antes de extraer la IA (`tests/fixtures/legacy_outputs.json`): el prompt, el briefing, la limpieza de Markdown, la validación de DNS y los detectores deben coincidir carácter a carácter.

## Versiones

La versión está en `pyproject.toml` y cada versión publicada lleva un tag `vX.Y.Z`. El backend fija el tag en su `requirements.txt`; para publicar un cambio, sube la versión, crea el tag y actualiza el tag en el backend.
