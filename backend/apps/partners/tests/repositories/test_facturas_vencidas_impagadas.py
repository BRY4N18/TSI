"""La lectura de mora de `FacturaRepository` (T060, § 15 D3).

Existe porque `/speckit-analyze` encontro que **no habia ninguna**: solo
`list_by_cliente(limit=20)` —pensada para una pantalla— y
`find_by_suscripcion_periodo`. El job de mora no tenia camino de datos.
"""

from __future__ import annotations

import time

import pytest

from core.repositories.suscripciones.factura_repository import FacturaRepository
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.repository]

AHORA = int(time.time() * 1000)
DIA = 86_400_000


def _factura(id_factura, *, idcliente=1, dias_vencida=20, estado="Pendiente",
             tipo="excedente_api"):
    PINOT_STORE["Fact_Factura"].append({
        "id_factura": id_factura,
        "id_cliente": idcliente,
        "id_suscripcion": idcliente,
        "tipo": tipo,
        "estado_pago": estado,
        "monto_total": 10.0,
        "periodo": "2026-07",
        "fecha_emision": AHORA - dias_vencida * DIA,
        "fecha_vencimiento": AHORA - dias_vencida * DIA,
        "activo": True,
        "fecha_actualizacion": AHORA,
    })


class TestQueDevuelve:
    def test_encuentra_la_pendiente_vencida_de_excedente(self, mock_pinot, mock_kafka):
        # Arrange
        _factura("SI")

        # Act
        filas = FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA)

        # Assert
        assert [f["id_factura"] for f in filas] == ["SI"]

    def test_descarta_la_FALLIDA(self, mock_pinot, mock_kafka):
        """🎯 Es el disparador de Suscripciones (RF-SUSF-007). Contarla aquí
        haría que dos módulos suspendieran por la misma factura."""
        # Arrange
        _factura("FALLIDA", estado="Fallida")

        # Act / Assert
        assert FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA) == []

    def test_descarta_la_pagada_y_la_que_esta_en_disputa(self, mock_pinot, mock_kafka):
        # Arrange
        _factura("PAGADA", estado="Pagada")
        _factura("DISPUTA", estado="En disputa")

        # Act / Assert
        assert FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA) == []

    def test_descarta_la_de_suscripcion(self, mock_pinot, mock_kafka):
        # Arrange
        _factura("SUSCRIPCION", tipo="suscripcion")

        # Act / Assert
        assert FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA) == []

    def test_descarta_la_que_aun_no_vence(self, mock_pinot, mock_kafka):
        # Arrange
        _factura("FUTURA", dias_vencida=-5)

        # Act / Assert
        assert FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA) == []

    def test_descarta_las_de_OTRO_cliente(self, mock_pinot, mock_kafka):
        """`Fact_Factura` se une por `id_cliente`; no tiene `idpartner`."""
        # Arrange
        _factura("AJENA", idcliente=999)

        # Act / Assert
        assert FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA) == []

    def test_las_devuelve_de_la_mas_antigua_a_la_mas_reciente(self, mock_pinot, mock_kafka):
        """La primera es la que origina el ciclo de mora."""
        # Arrange
        _factura("RECIENTE", dias_vencida=3)
        _factura("ANTIGUA", dias_vencida=40)

        # Act
        filas = FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA)

        # Assert
        assert [f["id_factura"] for f in filas] == ["ANTIGUA", "RECIENTE"]

    def test_el_limite_por_defecto_no_se_queda_en_veinte(self, mock_pinot, mock_kafka):
        """`list_by_cliente` usa 20 porque pinta una pantalla. Un job que decide
        suspensiones no puede quedarse corto y no enterarse."""
        # Arrange
        for i in range(25):
            _factura(f"F{i}", dias_vencida=10 + i)

        # Act
        filas = FacturaRepository().vencidas_impagadas_de_excedente(1, ahora_ms=AHORA)

        # Assert
        assert len(filas) == 25
