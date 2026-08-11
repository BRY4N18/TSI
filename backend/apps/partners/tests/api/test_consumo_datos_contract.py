"""Contrato de `GET /api/v1/datos/accidentes` (CU-O51, T018).

El camino feliz: un partner con credencial de producción consulta expedientes,
recibe solo los de sus severidades y zonas contratadas, y la llamada queda
registrada en **las dos** tablas.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/datos/accidentes"
ID_PARTNER = 880  # el que siembra la fixture de credencial


@pytest.fixture
def entorno_consumible(credencial_produccion_headers):
    """Partner habilitado, con «Media» contratada y la zona 10."""
    PINOT_STORE["Dim_Plan"].append({
        "idplan": ID_PARTNER,
        "nombre": "Profesional",
        "limites": '{"api_calls_mes": 10000, "api_calls_minuto": 120}',
        "severidades_desbloqueadas": "null",
        "activo": True,
    })
    PINOT_STORE["Fact_Suscripcion"].append({
        "id_suscripcion": ID_PARTNER,
        "idcliente": ID_PARTNER,
        "idplan": ID_PARTNER,
        "estado": "Activa",
        "activo": True,
        "fecha_inicio": 1,
        "severidades_desbloqueadas": '["Media"]',
    })
    PINOT_STORE["Dim_Preferencias_Cliente"].append(
        {"id_cliente": ID_PARTNER, "zonas_geograficas": "[10]"}
    )
    return credencial_produccion_headers


def _accidente(idaccidente, idseveridad, idcalle):
    PINOT_STORE["Fact_Accidente"].append({
        "idaccidente": idaccidente,
        "idseveridad": idseveridad,
        "idcalle": idcalle,
        "fechahoraaccidente": 1_700_000_000_000,
        "activo": True,
    })


class TestCaminoFeliz:
    def test_devuelve_200_con_el_sobre_estandar(self, api_client, entorno_consumible):
        # Act
        response = api_client.get(URL, **entorno_consumible)

        # Assert
        assert response.status_code == 200
        cuerpo = response.json()
        assert "data" in cuerpo and "meta" in cuerpo

    def test_expone_el_alcance_aplicado_para_que_el_vacio_sea_explicable(
        self, api_client, entorno_consumible
    ):
        """Sin esto, un `[]` no distingue «no hubo accidentes» de «no tienes
        zonas contratadas», y el partner abriría un ticket para averiguarlo."""
        # Act
        meta = api_client.get(URL, **entorno_consumible).json()["meta"]

        # Assert
        assert meta["zonas_aplicadas"] == [10]
        assert meta["severidades_aplicadas"] == [1, 2]

    def test_una_severidad_fuera_del_plan_returns_403(
        self, api_client, entorno_consumible
    ):
        """403 y no lista vacía: pedir algo fuera de alcance no es «no hay
        resultados»."""
        # Act
        response = api_client.get(f"{URL}?idseveridad=4", **entorno_consumible)

        # Assert
        assert response.status_code == 403
        assert response.json()["code"] == "severidad_no_habilitada"

    def test_un_parametro_no_numerico_returns_400(
        self, api_client, entorno_consumible
    ):
        # Act / Assert
        assert api_client.get(
            f"{URL}?idseveridad=grave", **entorno_consumible
        ).status_code == 400


class TestLaLlamadaQuedaRegistradaEnLasDosTablas:
    def test_registra_consumo_y_log(self, api_client, entorno_consumible):
        # Act
        api_client.get(URL, **entorno_consumible)

        # Assert
        assert len(PINOT_STORE["Fact_APIIntegracion"]) == 1
        assert len(PINOT_STORE["Fact_LogLlamadaAPI"]) == 1

    def test_el_consumo_congela_el_entorno_de_la_credencial(
        self, api_client, entorno_consumible
    ):
        # Act
        api_client.get(URL, **entorno_consumible)

        # Assert
        fila = PINOT_STORE["Fact_APIIntegracion"][0]
        assert fila["entorno"] == "Producción"
        assert fila["idestadointegracion"] == 2

    def test_el_log_guarda_endpoint_metodo_y_codigo(
        self, api_client, entorno_consumible
    ):
        # Act
        api_client.get(URL, **entorno_consumible)

        # Assert
        log = PINOT_STORE["Fact_LogLlamadaAPI"][0]
        assert log["endpoint"] == URL
        assert log["metodohttp"] == "GET"
        assert log["codigohttp"] == 200

    def test_la_latencia_registrada_es_positiva(
        self, api_client, entorno_consumible
    ):
        """Una latencia de 0 delataría que la medición no envuelve la petición."""
        # Act
        api_client.get(URL, **entorno_consumible)

        # Assert
        assert PINOT_STORE["Fact_APIIntegracion"][0]["latencia"] > 0


class TestFiltradoPorAlcance:
    def test_solo_devuelve_severidades_y_zonas_contratadas(
        self, api_client, entorno_consumible
    ):
        # Arrange — la fixture de credencial no siembra Dim_Calle, así que sin
        # resolución de condado el filtro de zonas descarta todo: eso es
        # precisamente el fail-closed de RF-APM-003.
        _accidente(1, idseveridad=2, idcalle=100)
        _accidente(2, idseveridad=4, idcalle=100)

        # Act
        data = api_client.get(URL, **entorno_consumible).json()["data"]

        # Assert — ninguno pasa: no hay calle registrada que resuelva a la zona 10
        assert data == []
