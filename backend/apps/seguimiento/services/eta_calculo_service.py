"""ETA lineal basado en Haversine — RF-SEG-001."""

from __future__ import annotations

import math

from apps.despacho.services.despacho_math import haversine_km

# Velocidad urbana promedio para ETA lineal (km/h)
VELOCIDAD_PROMEDIO_KMH = 40.0


class EtaCalculoService:
    def distancia_restante_km(
        self,
        lat_unidad: float,
        lon_unidad: float,
        lat_destino: float,
        lon_destino: float,
    ) -> float:
        return haversine_km(lat_unidad, lon_unidad, lat_destino, lon_destino)

    def eta_minutos(
        self,
        lat_unidad: float,
        lon_unidad: float,
        lat_destino: float,
        lon_destino: float,
        *,
        velocidad_kmh: float = VELOCIDAD_PROMEDIO_KMH,
    ) -> int:
        dist = self.distancia_restante_km(lat_unidad, lon_unidad, lat_destino, lon_destino)
        if dist <= 0:
            return 0
        hours = dist / max(velocidad_kmh, 1.0)
        return max(1, int(math.ceil(hours * 60)))
