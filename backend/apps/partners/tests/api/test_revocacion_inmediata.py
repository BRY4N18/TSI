"""🎯 La ventana de exposicion esta cerrada (T014/T058, escenarios B y Q).

**Estos tests no admiten `sleep`, y eso es lo que prueban.**

Si hiciera falta esperar para que la credencial dejase de servir, lo que se
estaria midiendo es la ingesta de Pinot (5-15 s) y la ventana **seguiria
abierta**: una credencial comprometida serviria datos durante ese rato. El doble
de `conftest.py` escribe en memoria de inmediato, asi que aqui se fuerza el
escenario real —la credencial sigue `activo=true` en la base— y se comprueba que
**aun asi** se rechaza, porque la lista de denegacion la ataja antes.
"""

from __future__ import annotations

import pytest

from apps.partners.services.denylist_credenciales import DenylistCredenciales
from apps.partners.services.revocar_credencial_service import RevocarCredencialService
from apps.partners.services.suspender_partner_service import SuspenderPartnerService
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL_DATOS = "/api/v1/datos/accidentes"


def _simular_ingesta_pendiente(idcredencial: int) -> None:
    """Devuelve la credencial a `activo=true` en la base.

    Reproduce exactamente el estado real durante la ventana: el evento ya se
    publico en Kafka, pero Pinot **todavia no lo ha ingerido**, asi que quien
    consulte la tabla la vera activa. Sin esto el test pasaria por el motivo
    equivocado — por el doble, no por la lista de denegacion.
    """
    for credencial in PINOT_STORE["Dim_CredencialAPI"]:
        if credencial["idcredencial"] == idcredencial:
            credencial["activo"] = True


class TestRevocacionInmediata:
    def test_la_credencial_revocada_no_sirve_YA(
        self, api_client, credencial_produccion_headers
    ):
        # Arrange — la credencial funciona antes de revocarla
        assert api_client.get(URL_DATOS, **credencial_produccion_headers).status_code != 401

        # Act
        RevocarCredencialService().revocar(
            idcredencial=8802, idpartner_actor=880, motivo="expuesta"
        )
        _simular_ingesta_pendiente(8802)

        # Assert — sin esperar nada
        respuesta = api_client.get(URL_DATOS, **credencial_produccion_headers)
        assert respuesta.status_code == 401, (
            "La credencial revocada sigue sirviendo: la ventana de exposición "
            "de 5-15 s está abierta (RNF-PAC-001)"
        )

    def test_sin_la_lista_de_denegacion_la_credencial_seguiria_sirviendo(
        self, api_client, credencial_produccion_headers
    ):
        """El contrafáctico. Demuestra que quien cierra la ventana es la lista,
        no otra comprobación que estuviera cubriendo el caso por casualidad."""
        # Arrange
        RevocarCredencialService().revocar(
            idcredencial=8802, idpartner_actor=880, motivo="expuesta"
        )
        _simular_ingesta_pendiente(8802)
        DenylistCredenciales().retirar(8802)

        # Act
        respuesta = api_client.get(URL_DATOS, **credencial_produccion_headers)

        # Assert — sin la lista, pasa el filtro de autenticación
        assert respuesta.status_code != 401


class TestSuspensionInmediata:
    """§ 15 D4 — aquí la fuga es MAYOR: son todas sus credenciales a la vez."""

    def test_tras_suspender_ninguna_credencial_sirve_sin_esperar(
        self, api_client, credencial_produccion_headers, credencial_sandbox_headers
    ):
        # Act
        SuspenderPartnerService().suspender(
            idpartner=880, motivo="mora de 16 días", automatica=True
        )
        _simular_ingesta_pendiente(8801)
        _simular_ingesta_pendiente(8802)

        # Assert
        assert api_client.get(URL_DATOS, **credencial_produccion_headers).status_code == 401
        assert api_client.get(URL_DATOS, **credencial_sandbox_headers).status_code == 401

    def test_al_reactivar_las_restituidas_vuelven_a_servir_sin_esperar(
        self, api_client, credencial_produccion_headers
    ):
        """La simetría de § 15 D4: si no se retirara de la lista, el partner
        reactivado seguiría rechazado hasta que caducase el TTL."""
        from apps.partners.services.reactivar_partner_service import (
            ReactivarPartnerService,
        )

        # Arrange
        SuspenderPartnerService().suspender(
            idpartner=880, motivo="mora de 16 días", automatica=True
        )
        assert api_client.get(URL_DATOS, **credencial_produccion_headers).status_code == 401

        # Act
        ReactivarPartnerService().reactivar(idpartner=880, motivo="pagó")

        # Assert
        assert api_client.get(URL_DATOS, **credencial_produccion_headers).status_code != 401
