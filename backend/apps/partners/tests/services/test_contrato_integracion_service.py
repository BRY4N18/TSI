"""RF-PON-011 — contrato versionado POR SERVICIO (CU-O50).

El test central es el aislamiento entre servicios: sin la FK `id_servicio`, el
versionado de todos ellos colapsaria en una sola linea temporal.
"""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import (
    VERSION_RETIRADA,
    VERSION_SOPORTADA,
    VERSION_VIGENTE,
)
from apps.partners.services.contrato_integracion_service import (
    ContratoIntegracionError,
    ContratoIntegracionService,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]


@pytest.fixture
def servicios(mock_pinot, mock_kafka):
    """Dos servicios, como en el catalogo real."""
    PINOT_STORE.setdefault("Dim_Servicio", [])
    PINOT_STORE["Dim_Servicio"].extend(
        [
            {"id_servicio": 801, "nombre": "API Despacho", "tipo": "api", "activo": True},
            {"id_servicio": 802, "nombre": "API Accidentes", "tipo": "api", "activo": True},
        ]
    )
    return (801, 802)


class TestConsulta:
    def test_consultar_when_hay_vigente_devuelve_esa_y_el_listado(self, servicios):
        # Arrange
        servicio = ContratoIntegracionService()
        servicio.publicar(id_servicio=801, version="v1")

        # Act
        contrato = servicio.consultar(id_servicio=801)

        # Assert
        assert contrato["version"] == "v1"
        assert contrato["estado"] == VERSION_VIGENTE
        assert len(contrato["versiones"]) == 1

    def test_consultar_when_version_concreta_la_devuelve(self, servicios):
        # Arrange
        servicio = ContratoIntegracionService()
        servicio.publicar(id_servicio=801, version="v1")
        servicio.publicar(id_servicio=801, version="v2")

        # Act — v1 quedo soportada al publicarse v2
        contrato = servicio.consultar(id_servicio=801, version="v1")

        # Assert
        assert contrato["version"] == "v1"
        assert contrato["estado"] == VERSION_SOPORTADA

    def test_consultar_when_servicio_inexistente_raises(self, servicios):
        # Act / Assert
        with pytest.raises(ContratoIntegracionError) as exc:
            ContratoIntegracionService().consultar(id_servicio=99999)
        assert exc.value.code == "not_found"

    def test_consultar_when_version_inexistente_raises(self, servicios):
        # Arrange
        ContratoIntegracionService().publicar(id_servicio=801, version="v1")

        # Act / Assert
        with pytest.raises(ContratoIntegracionError) as exc:
            ContratoIntegracionService().consultar(id_servicio=801, version="v99")
        assert exc.value.code == "not_found"


class TestAislamientoPorServicio:
    def test_publicar_when_dos_servicios_no_interfieren(self, servicios):
        """§ 15 D1 — cada servicio lleva su propia linea de versionado.

        Es la razon por la que `id_servicio` es FK obligatoria: sin ella, los
        servicios compartirian version y publicar en uno degradaria al otro.
        """
        # Arrange
        servicio = ContratoIntegracionService()

        # Act — el servicio 801 avanza a v2; el 802 se queda en v1
        servicio.publicar(id_servicio=801, version="v1")
        servicio.publicar(id_servicio=802, version="v1")
        servicio.publicar(id_servicio=801, version="v2")

        # Assert
        assert servicio.consultar(id_servicio=801)["version"] == "v2"
        assert servicio.consultar(id_servicio=802)["version"] == "v1"

    def test_publicar_nueva_vigente_degrada_la_anterior_a_soportada(self, servicios):
        """Invariante: como maximo UNA vigente por servicio.

        La anterior pasa a `soportada`, no a `retirada`: los partners que aun no
        migraron deben poder seguir consultandola (RF-O50.2).
        """
        # Arrange
        servicio = ContratoIntegracionService()
        servicio.publicar(id_servicio=801, version="v1")

        # Act
        servicio.publicar(id_servicio=801, version="v2")

        # Assert
        versiones = {
            v["version"]: v["estado"]
            for v in PINOT_STORE["Dim_VersionContratoAPI"]
            if v["id_servicio"] == 801
        }
        assert versiones == {"v1": VERSION_SOPORTADA, "v2": VERSION_VIGENTE}
        vigentes = [e for e in versiones.values() if e == VERSION_VIGENTE]
        assert len(vigentes) == 1


class TestRetiro:
    def test_publicar_retirada_sin_fecha_raises(self, servicios):
        """RN-PON-012 — nada se retira sin fecha de retiro publicada."""
        # Arrange
        servicio = ContratoIntegracionService()
        servicio.publicar(id_servicio=801, version="v1")

        # Act / Assert
        with pytest.raises(ContratoIntegracionError) as exc:
            servicio.publicar(id_servicio=801, version="v1", estado=VERSION_RETIRADA)
        assert exc.value.code == "retiro_sin_fecha"

    def test_publicar_retirada_con_fecha_ok(self, servicios):
        # Arrange
        servicio = ContratoIntegracionService()
        servicio.publicar(id_servicio=801, version="v1")

        # Act
        resultado = servicio.publicar(
            id_servicio=801,
            version="v1",
            estado=VERSION_RETIRADA,
            fecha_retiro=1_900_000_000_000,
        )

        # Assert
        assert resultado["estado"] == VERSION_RETIRADA
        assert resultado["fecha_retiro"] == 1_900_000_000_000

    def test_publicar_when_estado_invalido_raises(self, servicios):
        # Act / Assert
        with pytest.raises(ContratoIntegracionError) as exc:
            ContratoIntegracionService().publicar(
                id_servicio=801, version="v1", estado="inventado"
            )
        assert exc.value.code == "validation_error"
