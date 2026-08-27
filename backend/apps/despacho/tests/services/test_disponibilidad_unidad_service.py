import pytest

from apps.despacho.services.disponibilidad_unidad_service import (
    DisponibilidadUnidadService,
)


@pytest.mark.service
class TestDisponibilidadUnidadService:
    def test_consultar_when_no_history_returns_fuera_servicio(self, mock_pinot, mock_kafka):
        # Arrange
        service = DisponibilidadUnidadService()

        # Act
        data = service.consultar(1)

        # Assert
        assert data["estado_actual"] == "Fuera de servicio"
        assert data["incluido_en_despacho"] is False
        assert data["fechahora_ultimo_cambio"] is None
        assert data["condado"] == "Cuauhtémoc"

    def test_declarar_estado_when_valid_updates_state(
        self, mock_pinot, mock_kafka, unidad_con_estado_activa
    ):
        # Arrange
        service = DisponibilidadUnidadService()

        # Act
        result = service.declarar_estado(
            idunidademergencia=1,
            estadonuevo="Ocupada",
            idusuario=6,
        )
        consulta = service.consultar(1)

        # Assert
        assert result["estadoanterior"] == "Activa"
        assert result["estadonuevo"] == "Ocupada"
        assert consulta["estado_actual"] == "Ocupada"
        assert consulta["incluido_en_despacho"] is False


@pytest.mark.service
class TestHistorialDespachosUnidad:
    """Hallazgo #13: no habia forma de ver a que salio una unidad.

    El historial que ya existia solo cuenta cambios de estado (Activa / En
    mision / Fuera de servicio); saber cuando estuvo disponible no dice a que
    acudio.
    """

    def _sembrar_despacho(self, pinot_store, **campos):
        base = {
            "iddespacho": 1,
            "idaccidente": "ACC-1",
            "idunidademergencia": 1,
            "fechahoradespacho": 1_700_000_000_000,
            "fechahorallegada": None,
            "fechahoraretiro": None,
            "retiro_forzado": False,
            "activo": True,
        }
        pinot_store["Fact_Despacho"].append({**base, **campos})

    def test_lista_los_despachos_de_la_unidad_del_mas_reciente_atras(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        for i in (1, 2, 3):
            self._sembrar_despacho(pinot_store, iddespacho=i, idaccidente=f"ACC-{i}")
        service = DisponibilidadUnidadService()

        # Act
        items, next_cursor = service.listar_historial_despachos(1, limit=10)

        # Assert
        assert [i["iddespacho"] for i in items] == [3, 2, 1]
        assert next_cursor is None

    def test_incluye_los_despachos_ya_cerrados(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange — `list_activos_by_unidad` los omite; el historial no puede.
        self._sembrar_despacho(
            pinot_store,
            iddespacho=7,
            activo=False,
            fechahorallegada=1_700_000_100_000,
            fechahoraretiro=1_700_000_900_000,
        )
        service = DisponibilidadUnidadService()

        # Act
        items, _ = service.listar_historial_despachos(1)

        # Assert
        assert [i["iddespacho"] for i in items] == [7]
        assert items[0]["fase"] == "Retirada"

    def test_fase_distingue_el_retiro_forzado(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        self._sembrar_despacho(
            pinot_store,
            iddespacho=9,
            activo=False,
            fechahoraretiro=1_700_000_900_000,
            retiro_forzado=True,
        )
        service = DisponibilidadUnidadService()

        # Act
        items, _ = service.listar_historial_despachos(1)

        # Assert
        assert items[0]["fase"] == "Retiro forzado"

    def test_pagina_con_cursor_descendente(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        for i in range(1, 6):
            self._sembrar_despacho(pinot_store, iddespacho=i, idaccidente=f"ACC-{i}")
        service = DisponibilidadUnidadService()

        # Act
        primera, cursor = service.listar_historial_despachos(1, limit=2)
        segunda, _ = service.listar_historial_despachos(1, limit=2, cursor=cursor)

        # Assert
        assert [i["iddespacho"] for i in primera] == [5, 4]
        assert cursor == 4
        assert [i["iddespacho"] for i in segunda] == [3, 2]

    def test_unidad_inexistente_levanta_lookup_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = DisponibilidadUnidadService()

        # Act / Assert
        with pytest.raises(LookupError):
            service.listar_historial_despachos(99999)
