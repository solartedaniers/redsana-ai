# 🤖 RedSana AI (`redsana-ai`)

Paquete Python con la inteligencia artificial de RedSana: el asistente de seguridad conversacional (Groq), la detección de anomalías de red (IsolationForest) y la detección de cortes de conexión.

Es una librería: no lee variables de entorno ni conoce la base de datos. Todo lo que necesita (claves, modelo, tiempos de espera, parámetros y los datos reales del usuario) entra por constructor o por parámetro. El backend lo instala por URL de git, fijado a un tag, y lo arma en un único lugar de composición.

Además, este repo trae un **servicio HTTP** aparte (`redsana_ai_service`, FastAPI) que expone las mismas capacidades para desplegar la IA como servicio propio en Render. La librería no importa FastAPI ni sabe que el servicio existe; el backend elige entre usar la librería en su proceso (`AI_MODE=local`) o llamar al servicio (`AI_MODE=remote`).

## 🔗 Repositorios del proyecto

| Repositorio | Qué contiene |
|---|---|
| [redsana-frontend](https://github.com/solartedaniers/redsana-frontend) | App Angular + Tauri (web en Vercel, instalador en Releases) |
| [redsana-backend](https://github.com/solartedaniers/redsana-backend) | API FastAPI desplegada en Render; instala `redsana-ai` por tag |
| [redsana-ai](https://github.com/solartedaniers/redsana-ai) (este) | Paquete Python con el asistente y los detectores, y su servicio HTTP |

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
pip install -e ".[service,test]"
pytest
```

`tests/test_legacy_parity.py` compara el paquete con la salida que daba el backend antes de extraer la IA (`tests/fixtures/legacy_outputs.json`): el prompt, el briefing, la limpieza de Markdown, la validación de DNS y los detectores deben coincidir carácter a carácter. `tests/test_service_contract.py` pasa esas mismas fixtures por HTTP y exige que el servicio devuelva exactamente lo mismo que el paquete.

## Versiones

La versión está en `pyproject.toml` y cada versión publicada lleva un tag `vX.Y.Z`. El backend fija el tag en su `requirements.txt`; para publicar un cambio, sube la versión, crea el tag y actualiza el tag en el backend.

El servicio HTTP no forma parte del paquete instalable (`packages.find` solo incluye `redsana_ai`), así que agregarlo o cambiarlo no exige un tag nuevo: el backend en modo local sigue instalando la librería por su tag.

## Servicio HTTP (`redsana_ai_service`)

| Método y ruta | Clave | Qué hace |
|---|---|---|
| `GET /health` | No | `{"status": "ok", "ready": true/false}`. `ready` pasa a `true` cuando termina el calentamiento del detector tras arrancar. Es el health check de Render, lo que consulta el backend y lo que pide el frontend para despertar el servicio (GET silencioso `no-cors`, ver abajo). |
| `POST /v1/chat` | Sí | `SecurityChat.ask`: `{user_context, history, user_message, topic_context}` → `{reply}`. |
| `POST /v1/briefing` | Sí | `SecurityBriefing.write`: `{user_context, language}` → `{text}`. |
| `POST /v1/anomaly/evaluate` | Sí | `AnomalyDetector.evaluate`: `{history, latest}` (vectores `[latency_ms, jitter_ms, packet_loss_percent]`) → `{classification}` o `null`. |
| `POST /v1/outage/detect` | Sí | `OutageDetector.detect`: `{window: [{recorded_at, packet_loss_percent}]}` (de más nueva a más vieja) → `{episode}` o `null`. |

**Autenticación:** encabezado `X-AI-Service-Key` con el valor de `AI_SERVICE_API_KEY`. Sin clave configurada el servicio rechaza toda ruta protegida (503) en vez de quedar abierto.

**Errores:** siempre `{"code", "message"}`, con `code` estable: `invalid_api_key` (401), `validation_error` (422), `chat_engine_unavailable` (502; el detalle de Groq queda solo en el log), `service_misconfigured` (503), `http_error` e `internal_error` (500).

**Variables de entorno** (ver `.env.example`): `AI_SERVICE_API_KEY`, `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_API_URL`, `GROQ_TIMEOUT_SECONDS`, `GROQ_TEMPERATURE` y `ENABLE_API_DOCS` (documentación en `/docs`, apagada por defecto). Los parámetros de los detectores son los del paquete, para que el servicio dé lo mismo que el modo local del backend.

### Correrlo en local

```bash
pip install -e ".[service]"
copy .env.example .env          # Windows (cp en macOS/Linux); completa las claves
uvicorn redsana_ai_service.main:app --reload --port 8001
```

### Despliegue en Render

`render.yaml` describe el servicio: build `pip install -r requirements.txt` (instala este repo con el extra `service`), inicio `uvicorn redsana_ai_service.main:app --host 0.0.0.0 --port $PORT --forwarded-allow-ips="*"` y health check `/health`. La versión de Python sale de `.python-version`, la misma del backend. `AI_SERVICE_API_KEY` y `GROQ_API_KEY` se cargan en el panel de Render (`sync: false`).

En el plan gratuito Render apaga el servicio tras un rato sin peticiones y tarda cerca de un minuto en volver (incluye importar scikit-learn). Por eso el backend expone el estado de la IA (lista, encendiendo o no disponible) y la despierta al iniciar sesión, en vez de devolverle un error al usuario. Además, el frontend hace un GET silencioso a `/health` (variable `AI_SERVICE_PUBLIC_URL` del frontend) cada vez que el usuario inicia o restaura la sesión, abre el chat o pulsa Reintentar, porque una petición desde el navegador lo despierta aunque la del backend no lo logre. Nunca se dispara en segundo plano.
