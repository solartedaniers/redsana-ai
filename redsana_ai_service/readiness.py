import logging
import threading

from redsana_ai import AnomalyDetector, NetworkMetricVector

logger = logging.getLogger(__name__)

# Muestras sintéticas solo para calentar el detector; nunca se devuelven ni se guardan.
_WARM_UP_HISTORY: list[NetworkMetricVector] = [(20.0, 2.0, 0.0), (21.0, 2.1, 0.0), (22.0, 2.2, 0.0), (21.0, 2.0, 0.0)]
_WARM_UP_LATEST: NetworkMetricVector = (21.0, 2.1, 0.0)


class ServiceReadiness:
    """Dice si el servicio ya calentó: tras un arranque en frío el primer ajuste de IsolationForest es lo más lento."""

    def __init__(self, detector: AnomalyDetector) -> None:
        self._detector = detector
        self._ready = threading.Event()

    @property
    def is_ready(self) -> bool:
        return self._ready.is_set()

    def warm_up(self) -> None:
        try:
            self._detector.evaluate(_WARM_UP_HISTORY, _WARM_UP_LATEST)
        except Exception:
            # Si el calentamiento falla no me declaro listo: es preferible que quien llama vea "encendiendo".
            logger.exception("AI service warm-up failed")
            return
        self._ready.set()

    def start_warm_up(self) -> None:
        # En un hilo aparte para que /health responda mientras tanto y Render vea el puerto abierto enseguida.
        threading.Thread(target=self.warm_up, name="ai-service-warm-up", daemon=True).start()
