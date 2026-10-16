"""/health responde siempre, sin clave, y dice si el servicio ya terminó de calentar."""
from fastapi.testclient import TestClient
from redsana_ai import AnomalyDetector, DeviationClassification, NetworkMetricVector

from redsana_ai_service.config import ServiceSettings
from redsana_ai_service.main import create_app
from redsana_ai_service.readiness import ServiceReadiness


class _CountingDetector(AnomalyDetector):
    def __init__(self, fails: bool = False) -> None:
        self.calls = 0
        self._fails = fails

    def evaluate(self, history: list[NetworkMetricVector], latest: NetworkMetricVector) -> DeviationClassification | None:
        self.calls += 1
        if self._fails:
            raise RuntimeError("broken model")
        return None


def test_readiness_turns_ready_only_after_a_successful_warm_up() -> None:
    detector = _CountingDetector()
    readiness = ServiceReadiness(detector)

    assert readiness.is_ready is False
    readiness.warm_up()

    assert readiness.is_ready is True
    assert detector.calls == 1


def test_a_failed_warm_up_keeps_the_service_not_ready() -> None:
    readiness = ServiceReadiness(_CountingDetector(fails=True))

    readiness.warm_up()

    assert readiness.is_ready is False


def test_health_reports_not_ready_before_the_warm_up() -> None:
    readiness = ServiceReadiness(_CountingDetector())
    client = TestClient(create_app(ServiceSettings(_env_file=None), readiness))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ready": False}


def test_health_reports_ready_after_the_startup_warm_up() -> None:
    readiness = ServiceReadiness(_CountingDetector())
    with TestClient(create_app(ServiceSettings(_env_file=None), readiness)) as client:
        readiness.warm_up()  # el hilo de arranque corre aparte; lo fuerzo para no depender de tiempos
        response = client.get("/health")

    assert response.json() == {"status": "ok", "ready": True}


def test_api_docs_are_off_unless_enabled() -> None:
    closed = TestClient(create_app(ServiceSettings(_env_file=None), ServiceReadiness(_CountingDetector())))
    opened = TestClient(
        create_app(ServiceSettings(_env_file=None, enable_api_docs=True), ServiceReadiness(_CountingDetector()))
    )

    assert closed.get("/openapi.json").status_code == 404
    assert opened.get("/openapi.json").status_code == 200
