"""OSRM (Open Source Routing Machine) read-only client."""

from __future__ import annotations

import requests


class OsrmError(Exception):
    """Raised when OSRM is unreachable, times out, or finds no route."""


class OsrmClient:
    """Thin client for the OSRM HTTP routing API (self-hosted, no API key)."""

    def __init__(self, base_url: str | None = None):
        from django.conf import settings

        self.base_url = base_url or settings.OSRM_URL

    def route(
        self, origen_lat: float, origen_lon: float, destino_lat: float, destino_lon: float
    ) -> list[tuple[float, float]]:
        """
        Return the street route between two points as a list of (lat, lon).

        Raises OsrmError on any failure (network, timeout, no route found) —
        callers must degrade gracefully (straight line) rather than propagate
        this as a hard failure, since this is a visualization concern only.
        """
        coords = f"{origen_lon},{origen_lat};{destino_lon},{destino_lat}"
        try:
            response = requests.get(
                f"{self.base_url}/route/v1/driving/{coords}",
                params={"overview": "full", "geometries": "geojson"},
                timeout=3,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OsrmError(f"OSRM request failed: {exc}") from exc

        body = response.json()
        if body.get("code") != "Ok" or not body.get("routes"):
            raise OsrmError(f"OSRM returned no route: {body.get('code')}")

        coordinates = body["routes"][0]["geometry"]["coordinates"]
        return [(lat, lon) for lon, lat in coordinates]
