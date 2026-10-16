"""Único lugar donde el servicio construye las piezas de redsana_ai; cambiar una implementación es tocar solo aquí."""
from redsana_ai import AnomalyDetector, IsolationForestAnomalyDetector


def build_anomaly_detector() -> AnomalyDetector:
    # Parámetros por defecto del paquete: así el servicio da lo mismo que el modo local del backend.
    return IsolationForestAnomalyDetector()
