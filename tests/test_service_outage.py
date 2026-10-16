"""POST /v1/outage/detect usa el mismo StreakOutageDetector que el paquete."""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _window(*samples: tuple[int, float]) -> list[dict]:
    return [
        {"recorded_at": (_NOW - timedelta(minutes=minutes_ago)).isoformat(), "packet_loss_percent": loss}
        for minutes_ago, loss in samples
    ]


def test_a_recovery_after_a_total_outage_is_reported(service_client: TestClient) -> None:
    response = service_client.post("/v1/outage/detect", json={"window": _window((0, 0.0), (1, 100.0), (2, 100.0), (3, 0.0))})

    assert response.status_code == 200
    episode = response.json()["episode"]
    assert datetime.fromisoformat(episode["started_at"]) == _NOW - timedelta(minutes=2)
    assert datetime.fromisoformat(episode["recovered_at"]) == _NOW
    assert episode["duration_minutes"] == 2
    assert episode["severity"] == "warning"


def test_no_episode_while_the_connection_is_still_down(service_client: TestClient) -> None:
    response = service_client.post("/v1/outage/detect", json={"window": _window((0, 100.0), (1, 100.0))})

    assert response.json() == {"episode": None}


def test_an_empty_window_has_no_episode(service_client: TestClient) -> None:
    response = service_client.post("/v1/outage/detect", json={"window": []})

    assert response.json() == {"episode": None}


def test_samples_need_a_valid_timestamp(service_client: TestClient) -> None:
    response = service_client.post(
        "/v1/outage/detect", json={"window": [{"recorded_at": "yesterday", "packet_loss_percent": 100.0}]}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
