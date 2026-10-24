"""POST /v1/anomaly/evaluate usa el mismo IsolationForestAnomalyDetector que el paquete."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

# El mismo historial estable de las fixtures legacy, con casos ya conocidos de normal y anómalo.
_HISTORY = json.loads((Path(__file__).parent / "fixtures" / "legacy_outputs.json").read_text(encoding="utf-8"))[
    "anomaly_history"
]


def test_a_normal_sample_has_no_classification(service_client: TestClient) -> None:
    response = service_client.post("/v1/anomaly/evaluate", json={"history": _HISTORY, "latest": [21.0, 2.1, 0.05]})

    assert response.status_code == 200
    assert response.json() == {"classification": None}


def test_a_latency_spike_is_classified(service_client: TestClient) -> None:
    response = service_client.post("/v1/anomaly/evaluate", json={"history": _HISTORY, "latest": [400.0, 2.0, 0.0]})

    assert response.status_code == 200
    classification = response.json()["classification"]
    assert classification == {"deviating_metric": "latency", "severity": "critical", "current": 400.0, "typical": 20.8}


def test_vectors_must_have_three_metrics(service_client: TestClient) -> None:
    response = service_client.post("/v1/anomaly/evaluate", json={"history": _HISTORY, "latest": [20.0, 2.0]})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_an_empty_history_is_rejected_instead_of_crashing(service_client: TestClient) -> None:
    response = service_client.post("/v1/anomaly/evaluate", json={"history": [], "latest": [20.0, 2.0, 0.0]})

    assert response.status_code == 422
