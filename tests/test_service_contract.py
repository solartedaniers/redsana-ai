"""Contrato: por HTTP el servicio devuelve exactamente lo mismo que el paquete con las fixtures legacy
 (mismo prompt y turnos hacia el motor, mismo texto, mismas anomalías y mismos cortes)."""
from dataclasses import asdict
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redsana_ai import IsolationForestAnomalyDetector, StreakOutageDetector
from test_legacy_parity import LEGACY, TOPIC_CONTEXTS, _RecordingEngine

from redsana_ai_service.composition import get_chat_engine


@pytest.mark.parametrize("case", LEGACY["chat"])
def test_chat_over_http_matches_the_package(case: dict, service_app: FastAPI, service_client: TestClient) -> None:
    engine = _RecordingEngine()
    service_app.dependency_overrides[get_chat_engine] = lambda: engine

    response = service_client.post(
        "/v1/chat",
        json={
            "user_context": case["context"],
            "history": [{"role": role, "content": content} for role, content in case["history"]],
            "user_message": case["message"],
            "topic_context": TOPIC_CONTEXTS.get(case["topic"]),
        },
    )

    assert response.status_code == 200
    assert engine.calls == [case["engine_call"]]
    assert response.json() == {"reply": case["reply"]}


@pytest.mark.parametrize("case", LEGACY["briefing"])
def test_briefing_over_http_matches_the_package(case: dict, service_app: FastAPI, service_client: TestClient) -> None:
    engine = _RecordingEngine()
    service_app.dependency_overrides[get_chat_engine] = lambda: engine

    response = service_client.post("/v1/briefing", json={"user_context": case["context"], "language": case["language"]})

    assert response.status_code == 200
    assert engine.calls == [case["engine_call"]]
    assert response.json() == {"text": case["reply"]}


@pytest.mark.parametrize("case", LEGACY["anomaly"])
def test_anomaly_over_http_matches_the_package(case: dict, service_client: TestClient) -> None:
    history = [tuple(sample) for sample in LEGACY["anomaly_history"]]
    latest = tuple(case["latest"])
    expected = IsolationForestAnomalyDetector().evaluate(history, latest)

    response = service_client.post("/v1/anomaly/evaluate", json={"history": LEGACY["anomaly_history"], "latest": case["latest"]})

    assert response.status_code == 200
    classification = response.json()["classification"]
    assert (classification is not None) is case["is_anomalous"]
    assert classification == (asdict(expected) if expected else None)
    if classification:
        assert classification["deviating_metric"] == case["deviating_metric"]
        assert classification["severity"] == case["severity"]
        assert {"current": classification["current"], "typical": classification["typical"]} == case["message_params"]


@pytest.mark.parametrize("case", LEGACY["outage"])
def test_outage_over_http_matches_the_package(case: dict, service_client: TestClient) -> None:
    now = datetime.fromisoformat(LEGACY["outage_now"])
    window = [(now - timedelta(minutes=minutes_ago), loss) for minutes_ago, loss in case["window"]]
    expected = StreakOutageDetector().detect(window)

    response = service_client.post(
        "/v1/outage/detect",
        json={"window": [{"recorded_at": at.isoformat(), "packet_loss_percent": loss} for at, loss in window]},
    )

    assert response.status_code == 200
    episode = response.json()["episode"]
    parsed = None if episode is None else {
        "started_at": datetime.fromisoformat(episode["started_at"]).isoformat(),
        "recovered_at": datetime.fromisoformat(episode["recovered_at"]).isoformat(),
        "duration_minutes": episode["duration_minutes"],
        "severity": episode["severity"],
    }
    assert parsed == case["episode"]
    assert parsed == (None if expected is None else {
        "started_at": expected.started_at.isoformat(),
        "recovered_at": expected.recovered_at.isoformat(),
        "duration_minutes": expected.duration_minutes,
        "severity": expected.severity,
    })
