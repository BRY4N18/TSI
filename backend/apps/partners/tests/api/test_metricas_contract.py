"""Lectura del consumo — métricas, consola y reporte (CU-O52).

Reúne T030–T034: los tres contratos de API, la separación de entornos y el
control de propiedad. Van juntos porque comparten el mismo montaje de consumo;
separarlos obligaría a duplicarlo cuatro veces.
"""

from __future__ import annotations

import pytest

from apps.partners.services.metricas_consumo_service import MetricasConsumoService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

# `partner_auth_headers` vincula el usuario 51 al cliente 1.
ID_CLIENTE = 1
ID_PARTNER = 890


@pytest.fixture
def partner_con_consumo(mock_pinot, mock_kafka):
    """Partner con cupo de 100 y consumo en AMBOS entornos."""
    PINOT_STORE["Dim_Partner"].append({
        "idpartner": ID_PARTNER,
        "idcliente": ID_CLIENTE,
        "nombrepartner": "Demo Métricas",
        "contacto_tecnico_nombre": "Ana",
        "contacto_tecnico_gmail": "ana@demo.com",
        "planapi": "Profesional",
        "limitellamadasmes": 100,
        "limitellamadasminuto": 120,
        "sandbox_activado": 1,
        "sandbox_expiracion": 253402300799000,
        "fecha_suspension": "",
        "motivo_suspension": "",
        "activo": True,
        "fecha_actualizacion": 1,
    })
    desde, hasta = MetricasConsumoService.periodo_actual()
    dentro = desde + 1000

    def consumo(entorno, cuantas, codigo=200, idservicio=1):
        for i in range(cuantas):
            PINOT_STORE["Fact_APIIntegracion"].append({
                "idapiintegracion": len(PINOT_STORE["Fact_APIIntegracion"]) + 1,
                "idpartner": ID_PARTNER,
                "idcliente": ID_CLIENTE,
                "idservicio": idservicio,
                "idestadointegracion": 2 if entorno == "Producción" else 1,
                "entorno": entorno,
                "llamadas": 1,
                "errores": 1 if codigo >= 400 else 0,
                "latencia": 100.0,
                "activo": True,
                "fechahora": dentro + i,
                "fecha_actualizacion": dentro + i,
            })

    consumo("Producción", 30)
    consumo("Producción", 2, codigo=500)
    consumo("Sandbox", 500)  # ruido: no debe contarse
    return ID_PARTNER


URL_METRICAS = f"/api/v1/partners/{ID_PARTNER}/metricas"


class TestMetricasContract:
    def test_devuelve_200_con_el_consumo_del_periodo(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Act
        response = api_client.get(URL_METRICAS, **partner_auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["llamadas"] == 32
        assert data["errores"] == 2

    def test_declara_hasta_cuando_son_fiables_los_datos(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        """Kafka tarda 5-15 s en ingerir: prometer tiempo real haría creer al
        partner que su última petición no se contó."""
        # Act
        data = api_client.get(URL_METRICAS, **partner_auth_headers).json()["data"]

        # Assert
        assert data["datos_hasta"] < data["periodo"]["hasta"]

    def test_calcula_el_porcentaje_contra_el_cupo(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Act
        data = api_client.get(URL_METRICAS, **partner_auth_headers).json()["data"]

        # Assert — 32 de 100
        assert data["cupo_mensual"] == 100
        assert data["porcentaje_consumido"] == 32.0
        assert data["llamadas_excedentes"] == 0

    def test_un_entorno_invalido_returns_400(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Act
        response = api_client.get(
            f"{URL_METRICAS}?entorno=Staging", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 400

    def test_partner_inexistente_returns_404(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/partners/404404/metricas", **devapis_auth_headers
        )

        # Assert
        assert response.status_code in (403, 404)


class TestSeparacionDeEntornos:
    """RN-APM-001 — mezclar pruebas y producción falsearía la facturación."""

    def test_por_defecto_solo_cuenta_produccion(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Act
        data = api_client.get(URL_METRICAS, **partner_auth_headers).json()["data"]

        # Assert — las 500 de Sandbox no aparecen
        assert data["entorno"] == "Producción"
        assert data["llamadas"] == 32

    def test_sandbox_se_consulta_pidiendolo_explicitamente(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Act
        data = api_client.get(
            f"{URL_METRICAS}?entorno=Sandbox", **partner_auth_headers
        ).json()["data"]

        # Assert
        assert data["llamadas"] == 500

    def test_el_excedente_nunca_se_calcula_con_consumo_de_pruebas(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        """Con 500 llamadas de sandbox y cupo 100, contarlas daría 400 de
        excedente facturable que el partner no debe."""
        # Act
        data = api_client.get(URL_METRICAS, **partner_auth_headers).json()["data"]

        # Assert
        assert data["llamadas_excedentes"] == 0


class TestPropiedadDeLasMetricas:
    def test_un_partner_no_ve_las_metricas_de_otro(
        self, api_client, partner_con_consumo, partner_ajeno_auth_headers
    ):
        # Act
        response = api_client.get(URL_METRICAS, **partner_ajeno_auth_headers)

        # Assert
        assert response.status_code == 403

    def test_un_partner_suspendido_SI_ve_las_suyas(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        """RN-APM-017: es una lectura que no cambia nada y le sirve justo para
        entender por qué se le suspendió. Negarla lo castigaría dos veces."""
        # Arrange
        for p in PINOT_STORE["Dim_Partner"]:
            p["activo"] = False

        # Act
        response = api_client.get(URL_METRICAS, **partner_auth_headers)

        # Assert
        assert response.status_code == 200

    def test_sin_token_returns_401(self, api_client, partner_con_consumo):
        # Act / Assert
        assert api_client.get(URL_METRICAS).status_code == 401


class TestConsolaLogsContract:
    URL = "/api/v1/logs-api"

    def _log(self, idpartner=ID_PARTNER, codigo=200, idlog=1):
        PINOT_STORE["Fact_LogLlamadaAPI"].append({
            "idlogllamadaapi": idlog,
            "idpartner": idpartner,
            "idcredencialapi": 1,
            "endpoint": "/api/v1/datos/accidentes",
            "metodohttp": "GET",
            "codigohttp": codigo,
            "latenciams": 80.0,
            "iporigen": 0,
            "fechallamada": 1000 + idlog,
            "fecha_actualizacion": 1000 + idlog,
        })

    def test_el_desarrollador_de_apis_ve_el_detalle(
        self, api_client, partner_con_consumo, devapis_auth_headers
    ):
        # Arrange
        self._log(idlog=1)

        # Act
        response = api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}", **devapis_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_un_partner_no_accede_a_los_registros_de_OTRO(
        self, api_client, partner_con_consumo, partner_ajeno_auth_headers
    ):
        """El partner sí ve los suyos (BE-DELTA-07), nunca los de otro.

        Hasta 2026-08-10 la consola era exclusiva del Desarrollador de APIs y
        este test comprobaba que **ningún** partner entraba. Eso contradecía
        RN-APM-009 —los errores se registran «para que el partner pueda
        diagnosticar sus propios fallos sin escalar»— y dejaba el bloque de
        errores del panel de consumo permanentemente vacío. Lo que se relajó fue
        el permiso de rol; el control de propiedad sigue intacto, que es lo que
        este test protege ahora.
        """
        # Act / Assert
        assert api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}", **partner_ajeno_auth_headers
        ).status_code == 403

    def test_sin_idpartner_returns_400(self, api_client, mock_pinot, mock_kafka, devapis_auth_headers):
        # Act / Assert
        assert api_client.get(self.URL, **devapis_auth_headers).status_code == 400

    def test_filtra_solo_errores(
        self, api_client, partner_con_consumo, devapis_auth_headers
    ):
        # Arrange
        self._log(codigo=200, idlog=1)
        self._log(codigo=500, idlog=2)

        # Act
        data = api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}&solo_errores=true", **devapis_auth_headers
        ).json()["data"]

        # Assert
        assert [f["codigohttp"] for f in data] == [500]

    def test_pagina_por_cursor(
        self, api_client, partner_con_consumo, devapis_auth_headers
    ):
        # Arrange
        for i in range(1, 6):
            self._log(idlog=i)

        # Act
        cuerpo = api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}&limit=2", **devapis_auth_headers
        ).json()

        # Assert
        assert len(cuerpo["data"]) == 2
        assert cuerpo["meta"]["pagination"]["next_cursor"] is not None


class TestReporteConsumoContract:
    URL = "/api/v1/reportes-consumo"

    def test_un_mes_sin_consumo_devuelve_ceros_no_error(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        """Que el partner no consumiera es una respuesta válida; un 404 le haría
        pensar que el reporte no existe."""
        # Act
        response = api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}&anio=2020&mes=1", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["llamadas"] == 0
        assert data["errores"] == 0

    def test_incluye_el_desglose_por_servicio(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Arrange
        desde, _ = MetricasConsumoService.periodo_actual()
        import datetime as _dt

        hoy = _dt.datetime.fromtimestamp(desde / 1000, _dt.timezone.utc)

        # Act
        data = api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}&anio={hoy.year}&mes={hoy.month}",
            **partner_auth_headers,
        ).json()["data"]

        # Assert
        assert data["llamadas"] == 32
        assert data["por_servicio"]

    def test_un_mes_invalido_returns_400(
        self, api_client, partner_con_consumo, partner_auth_headers
    ):
        # Act / Assert
        assert api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}&anio=2026&mes=13", **partner_auth_headers
        ).status_code == 400

    def test_un_partner_no_ve_el_reporte_de_otro(
        self, api_client, partner_con_consumo, partner_ajeno_auth_headers
    ):
        # Act / Assert
        assert api_client.get(
            f"{self.URL}?idpartner={ID_PARTNER}&anio=2026&mes=8",
            **partner_ajeno_auth_headers,
        ).status_code == 403
