"""Superar el cupo mensual NO interrumpe el servicio (RN-APM-002).

El SRS es explícito y la spec dice que lo documenta «precisamente para que
nadie la corrija asumiendo que debería bloquear». Este archivo es esa
salvaguarda a nivel de API: si alguien introduce un corte por cupo, falla aquí.

Prueba lo contrario de lo habitual: que **no** pase nada.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/datos/accidentes"
ID_PARTNER = 880  # el que siembra la fixture de credencial


def _entorno_consumible(cupo=5):
    """Partner con cupo bajo, suscripción vigente, zonas y severidades."""
    for p in PINOT_STORE["Dim_Partner"]:
        if p["idpartner"] == ID_PARTNER:
            p["limitellamadasmes"] = cupo

    PINOT_STORE["Dim_Plan"].append({
        "idplan": ID_PARTNER,
        "nombre": "Profesional",
        "limites": '{"api_calls_mes": 5, "api_calls_minuto": 120}',
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
        "severidades_desbloqueadas": "[1, 2, 3, 4]",
    })
    PINOT_STORE["Dim_Preferencias_Cliente"].append(
        {"id_cliente": ID_PARTNER, "zonas_geograficas": "[10]"}
    )


def _consumo_previo(cuantas):
    """Consumo ya registrado que deja al partner por encima de su cupo."""
    for i in range(cuantas):
        PINOT_STORE["Fact_APIIntegracion"].append({
            "idapiintegracion": 10_000 + i,
            "idpartner": ID_PARTNER,
            "idcliente": ID_PARTNER,
            "idservicio": 2,
            "idestadointegracion": 2,
            "entorno": "Producción",
            "llamadas": 1,
            "errores": 0,
            "latencia": 90.0,
            "activo": True,
            "fechahora": 1_000_000,
            "fecha_actualizacion": 1_000_000,
        })


class TestSuperarElCupoNoBloquea:
    def test_con_el_cupo_ya_superado_la_llamada_devuelve_200(
        self, api_client, credencial_produccion_headers
    ):
        # Arrange — cupo de 5, ya consumió 50
        _entorno_consumible(cupo=5)
        _consumo_previo(50)

        # Act
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code == 200

    def test_la_llamada_por_encima_del_cupo_SI_se_registra_como_consumo(
        self, api_client, credencial_produccion_headers
    ):
        """Es la contraparte de no bloquear: se atiende y **se factura** como
        excedente. Si no se registrara, el exceso sería gratis."""
        # Arrange
        _entorno_consumible(cupo=5)
        _consumo_previo(50)
        antes = len(PINOT_STORE["Fact_APIIntegracion"])

        # Act
        api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert len(PINOT_STORE["Fact_APIIntegracion"]) == antes + 1

    def test_varias_llamadas_seguidas_por_encima_del_cupo_siguen_atendiendose(
        self, api_client, credencial_produccion_headers
    ):
        # Arrange
        _entorno_consumible(cupo=1)
        _consumo_previo(100)

        # Act
        codigos = [
            api_client.get(URL, **credencial_produccion_headers).status_code
            for _ in range(5)
        ]

        # Assert — ninguna degradación progresiva ni corte
        assert codigos == [200] * 5

    def test_ninguna_respuesta_menciona_el_cupo_como_motivo_de_rechazo(
        self, api_client, credencial_produccion_headers
    ):
        """Un 403 o 429 por cupo mensual sería el defecto que este archivo
        existe para impedir."""
        # Arrange
        _entorno_consumible(cupo=1)
        _consumo_previo(100)

        # Act
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code not in (403, 429)
