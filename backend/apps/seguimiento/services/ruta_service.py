"""Servicio de ruteo por calles (OSRM) para el mapa de seguimiento."""

from __future__ import annotations

from core.osrm.client import OsrmClient, OsrmError


class RutaCoordenadasInvalidasError(Exception):
    """Raised when 'origen'/'destino' no son parseables como 'lat,lon'."""


def _parse_coord(raw: str) -> tuple[float, float]:
    try:
        lat_str, lon_str = raw.split(",")
        return float(lat_str), float(lon_str)
    except (ValueError, TypeError) as exc:
        raise RutaCoordenadasInvalidasError("Formato esperado: 'lat,lon'") from exc


class RutaService:
    """
    Proxy delgado hacia OSRM: nunca expone el motor de ruteo directo a
    internet (sin CORS propio, contenedor interno del compose). Si OSRM
    falla, no responde a tiempo, o no encuentra ruta, devuelve `puntos: []`
    — el frontend interpreta una lista vacía como "usar línea recta", ya que
    este servicio es de visualización/monitoreo, no debe bloquear al
    operador por un fallo de un servicio auxiliar.
    """

    def obtener_ruta(self, origen_raw: str, destino_raw: str) -> dict:
        origen_lat, origen_lon = _parse_coord(origen_raw)
        destino_lat, destino_lon = _parse_coord(destino_raw)

        try:
            puntos = OsrmClient().route(origen_lat, origen_lon, destino_lat, destino_lon)
        except OsrmError:
            return {"puntos": []}

        return {"puntos": [{"latitud": lat, "longitud": lon} for lat, lon in puntos]}
