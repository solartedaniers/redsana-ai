"""Los parámetros de los detectores del servicio salen de las variables de entorno; por defecto son los del paquete."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from redsana_ai import IsolationForestAnomalyDetector, StreakOutageDetector
from redsana_ai_service.composition import build_anomaly_detector, build_outage_detector
from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.main import create_app
from redsana_ai_service.security import API_KEY_HEADER
from tests.test_service_outage import _window

_KEY = "test-service-key"


def test_by_default_the_service_detectors_are_the_package_ones() -> None:
    settings = ServiceSettings(_env_file=None)

    assert vars(build_anomaly_detector(settings)) == vars(IsolationForestAnomalyDetector())
    assert vars(build_outage_detector(settings)) == vars(StreakOutageDetector())


def test_the_environment_reaches_the_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTAGE_CRITICAL_DURATION_MINUTES", "2")
    client = TestClient(
        create_app(ServiceSettings(_env_file=None, ai_service_api_key=_KEY)), headers={API_KEY_HEADER: _KEY}
    )

    response = client.post("/v1/outage/detect", json={"window": _window((0, 0.0), (1, 100.0), (2, 100.0), (3, 0.0))})

    # Con el valor por defecto (15) este corte de 2 minutos es "warning".
    assert response.json()["episode"]["severity"] == "critical"


@pytest.mark.parametrize(
    "override",
    [
        {"anomaly_contamination": 0},
        {"anomaly_contamination": 0.6},
        {"anomaly_critical_z_score": 0},
        {"outage_packet_loss_threshold_percent": 101},
        {"outage_max_gap_minutes": 0},
        {"outage_critical_duration_minutes": 0},
    ],
)
def test_out_of_range_detector_settings_are_rejected(override: dict) -> None:
    with pytest.raises(ValidationError):
        ServiceSettings(_env_file=None, **override)
