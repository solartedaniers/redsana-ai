from abc import ABC, abstractmethod
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Literal

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

NetworkMetricVector = tuple[float, float, float]  # (latency_ms, jitter_ms, packet_loss_percent)
DeviatingMetric = Literal["latency", "jitter", "packet_loss"]
DeviationSeverity = Literal["warning", "critical"]

# A una medición por minuto, 1440 muestras son ~24 h: así el entrenamiento cubre un ciclo día/noche completo.
ANOMALY_WINDOW_SIZE = 1440

# Desviaciones estándar a partir de las cuales una anomalía ya confirmada se considera grave y no leve.
SEVERITY_CRITICAL_Z_SCORE = 3.0

# Con contamination='auto' el umbral era inestable en ventanas de poca varianza; 0.1 es el valor clásico y estable.
ISOLATION_FOREST_CONTAMINATION = 0.1
ISOLATION_FOREST_RANDOM_STATE = 42


@dataclass(frozen=True)
class DeviationClassification:
    deviating_metric: DeviatingMetric
    severity: DeviationSeverity
    current: float
    typical: float


class AnomalyDetector(ABC):
    """Interfaz del detector: dice si la última muestra es anómala frente a su historial y, si lo es, qué fue."""

    @abstractmethod
    def evaluate(
        self, history: list[NetworkMetricVector], latest: NetworkMetricVector
    ) -> DeviationClassification | None:
        """None si latest es normal; history nunca incluye a latest."""


class IsolationForestAnomalyDetector(AnomalyDetector):
    """Única clase que conoce IsolationForest y StandardScaler; los crea en cada evaluación porque fit muta su estado."""

    def __init__(
        self,
        contamination: float = ISOLATION_FOREST_CONTAMINATION,
        random_state: int = ISOLATION_FOREST_RANDOM_STATE,
        critical_z_score: float = SEVERITY_CRITICAL_Z_SCORE,
    ) -> None:
        self._contamination = contamination
        self._random_state = random_state
        self._critical_z_score = critical_z_score

    def evaluate(
        self, history: list[NetworkMetricVector], latest: NetworkMetricVector
    ) -> DeviationClassification | None:
        if not self.is_anomalous(history, latest):
            return None
        return classify_deviation(history, latest, self._critical_z_score)

    def is_anomalous(self, history: list[NetworkMetricVector], latest: NetworkMetricVector) -> bool:
        """Entrena solo con history (la muestra nueva nunca entra a su propio baseline) y evalúa latest."""
        scaler = StandardScaler()
        model = IsolationForest(contamination=self._contamination, random_state=self._random_state)
        scaled_history = scaler.fit_transform(np.array(history))
        model.fit(scaled_history)
        scaled_latest = scaler.transform([latest])
        prediction = model.predict(scaled_latest)
        return bool(prediction[0] == -1)


def classify_deviation(
    history: list[NetworkMetricVector],
    latest: NetworkMetricVector,
    critical_z_score: float = SEVERITY_CRITICAL_Z_SCORE,
) -> DeviationClassification:
    """Decide qué métrica se desvió más y qué tan grave es con el z-score de cada una.
    El modelo decide SI hay anomalía; esto decide QUÉ fue y qué tan grave."""
    metrics: tuple[DeviatingMetric, ...] = ("latency", "jitter", "packet_loss")
    z_scores: dict[DeviatingMetric, float] = {}
    typical_values: dict[DeviatingMetric, float] = {}

    for index, metric in enumerate(metrics):
        column = [sample[index] for sample in history]
        average = mean(column)
        deviation = pstdev(column) or 1.0  # evita dividir por cero si history es constante
        z_scores[metric] = abs(latest[index] - average) / deviation
        typical_values[metric] = average

    deviating_metric = max(metrics, key=lambda metric: z_scores[metric])
    severity: DeviationSeverity = "critical" if z_scores[deviating_metric] >= critical_z_score else "warning"
    metric_index = metrics.index(deviating_metric)

    return DeviationClassification(
        deviating_metric=deviating_metric,
        severity=severity,
        current=round(latest[metric_index], 1),
        typical=round(typical_values[deviating_metric], 1),
    )
