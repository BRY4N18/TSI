"""Geocodificación inversa (Nominatim adapter stub for tests)."""

from __future__ import annotations

from typing import Any, Protocol

from apps.accidentes.services.cobertura_operativa_service import CoberturaOperativaService


class GeocoderClient(Protocol):
    def reverse(self, latitud: float, longitud: float) -> dict[str, Any]: ...


class NominatimGeocoderClient:
    """HTTP geocoder — tests patch this client."""

    def reverse(self, latitud: float, longitud: float) -> dict[str, Any]:
        return {
            "idcalle": 1,
            "calle": "Av. Reforma",
            "idciudad": 1,
            "ciudad": "Ciudad de México",
            "idestadoregion": 1,
            "estado": "CDMX",
            "precision_metros": 50.0,
        }


class GeocodificacionInversaService:
    def __init__(
        self,
        geocoder: GeocoderClient | None = None,
        cobertura: CoberturaOperativaService | None = None,
    ):
        self.geocoder = geocoder or NominatimGeocoderClient()
        self.cobertura = cobertura or CoberturaOperativaService()

    def sugerir(self, latitud: float, longitud: float) -> dict[str, Any]:
        geo = self.geocoder.reverse(latitud, longitud)
        idcalle = geo.get("idcalle")
        en_cobertura = self.cobertura.en_cobertura_por_calle(int(idcalle)) if idcalle else False
        return {
            "idcalle": idcalle,
            "ubicacion": geo,
            "precision_metros": geo.get("precision_metros"),
            "en_cobertura_operativa": en_cobertura,
        }
