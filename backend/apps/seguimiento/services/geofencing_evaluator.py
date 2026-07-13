"""Geofencing evaluator — RNF-SEG-002."""

from __future__ import annotations

from apps.despacho.services.despacho_math import haversine_km


class GeofencingEvaluator:
    """Evalúa entrada a radio con histéresis temporal."""

    def __init__(self) -> None:
        self._entry_ms: dict[int, int] = {}

    def distancia_metros(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        return haversine_km(lat1, lon1, lat2, lon2) * 1000.0

    def dentro_radio(
        self,
        lat: float,
        lon: float,
        dest_lat: float,
        dest_lon: float,
        radio_metros: float,
    ) -> bool:
        return self.distancia_metros(lat, lon, dest_lat, dest_lon) <= radio_metros

    def evaluar_llegada(
        self,
        *,
        iddespacho: int,
        lat: float,
        lon: float,
        dest_lat: float,
        dest_lon: float,
        fechahora_ms: int,
        radio_metros: float = 100.0,
        histéresis_seg: int = 30,
    ) -> bool:
        if not self.dentro_radio(lat, lon, dest_lat, dest_lon, radio_metros):
            self._entry_ms.pop(iddespacho, None)
            return False
        first = self._entry_ms.get(iddespacho)
        if first is None:
            self._entry_ms[iddespacho] = fechahora_ms
            return False
        elapsed = (fechahora_ms - first) / 1000.0
        return elapsed >= histéresis_seg

    def evaluar_llegada_desde_puntos(
        self,
        *,
        puntos: list[tuple[float, float, int]],
        dest_lat: float,
        dest_lon: float,
        fechahora_ms: int,
        radio_metros: float = 100.0,
        histéresis_seg: int = 30,
    ) -> bool:
        """Evalúa histéresis usando timestamps GPS persistidos (stateless entre requests)."""
        if not puntos:
            return False
        cur_lat, cur_lon, _ = puntos[-1]
        if not self.dentro_radio(cur_lat, cur_lon, dest_lat, dest_lon, radio_metros):
            return False
        session_start = fechahora_ms
        for lat, lon, t in sorted(puntos, key=lambda p: p[2], reverse=True):
            if t > fechahora_ms:
                continue
            if not self.dentro_radio(lat, lon, dest_lat, dest_lon, radio_metros):
                break
            session_start = t
        return (fechahora_ms - session_start) / 1000.0 >= histéresis_seg

    def reset(self, iddespacho: int) -> None:
        self._entry_ms.pop(iddespacho, None)
