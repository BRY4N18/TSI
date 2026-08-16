"""T040 — quién accede a regiones y validaciones (FR-012).

Una región **no pertenece a ninguna empresa de flota**, y su estado es materia
de gobierno de la red: un proveedor recibe `403` en los dos listados.

Y los dos no van al mismo público. El §5.1 del SRS reparte la autoridad de este
departamento:

* el **Tecnológico** fija los criterios de validación → ve el detalle de por qué
  se rechaza una región;
* el de **Expansión** decide dónde crecer → ve el **estado** de las regiones,
  que es lo que le dice dónde puede hacerlo.

Darle a Expansión el historial de rechazos sería información que no cambia su
decisión; negarle el estado lo dejaría sin la suya.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/red-operativa"
REGIONES = f"{BASE}/regiones"
VALIDACIONES = f"{BASE}/validaciones-region"


@pytest.mark.api
class TestElProveedorNoAccede:
    @pytest.mark.parametrize("ruta", [REGIONES, VALIDACIONES])
    def test_recibe_403(self, api_client, proveedor_a_headers, ruta, regiones_sembradas):
        respuesta = api_client.get(ruta, **proveedor_a_headers)

        assert respuesta.status_code == 403

    @pytest.mark.parametrize("ruta", [REGIONES, VALIDACIONES])
    def test_y_no_se_le_filtra_ninguna_region(
        self, api_client, proveedor_a_headers, ruta, validaciones_sembradas
    ):
        respuesta = api_client.get(ruta, **proveedor_a_headers)

        assert "Centro Alerta" not in respuesta.content.decode()

    @pytest.mark.parametrize("ruta", [REGIONES, VALIDACIONES])
    def test_aunque_acceda_a_la_flota(
        self, api_client, proveedor_a_headers, ruta, dos_flotas
    ):
        # Tener flota no da voz sobre el gobierno de la red.
        assert api_client.get(f"{BASE}/flota", **proveedor_a_headers).status_code == 200
        assert api_client.get(ruta, **proveedor_a_headers).status_code == 403


@pytest.mark.api
class TestElDirectorTecnologico:
    """Fija los criterios de validación: accede a los dos."""

    def test_accede_a_regiones(
        self, api_client, director_tecnologico_headers, regiones_sembradas
    ):
        respuesta = api_client.get(REGIONES, **director_tecnologico_headers)

        assert respuesta.status_code == 200

    def test_accede_a_validaciones(
        self, api_client, director_tecnologico_headers, validaciones_sembradas
    ):
        respuesta = api_client.get(VALIDACIONES, **director_tecnologico_headers)

        assert respuesta.status_code == 200

    def test_ve_el_motivo_de_cada_rechazo(
        self, api_client, director_tecnologico_headers, validaciones_sembradas
    ):
        # Es lo que le permite ajustar los criterios.
        cuerpo = api_client.get(
            f"{VALIDACIONES}?limit=500", **director_tecnologico_headers
        ).json()

        motivos = {f["motivo"] for f in cuerpo["data"] if f["motivo"]}
        assert "cobertura insuficiente" in motivos


@pytest.mark.api
class TestElDirectorDeExpansion:
    """Decide dónde crecer: ve el estado, no el detalle de los rechazos."""

    def test_accede_a_regiones(
        self, api_client, director_expansion_headers, regiones_sembradas
    ):
        respuesta = api_client.get(REGIONES, **director_expansion_headers)

        assert respuesta.status_code == 200

    def test_no_accede_a_validaciones(
        self, api_client, director_expansion_headers, validaciones_sembradas
    ):
        """El detalle de por qué se rechaza no cambia su decisión."""
        respuesta = api_client.get(VALIDACIONES, **director_expansion_headers)

        assert respuesta.status_code == 403

    def test_ve_las_regiones_detenidas(
        self, api_client, director_expansion_headers, regiones_sembradas
    ):
        cuerpo = api_client.get(
            f"{REGIONES}?detenida_mas_de_dias=30&limit=500", **director_expansion_headers
        ).json()

        assert "Este Pendiente" in {f["nombre_region"] for f in cuerpo["data"]}


@pytest.mark.api
class TestElAdministrador:
    @pytest.mark.parametrize("ruta", [REGIONES, VALIDACIONES])
    def test_accede_a_los_dos(self, api_client, admin_auth_headers, ruta):
        assert api_client.get(ruta, **admin_auth_headers).status_code == 200


@pytest.mark.api
class TestSinAutenticar:
    @pytest.mark.parametrize("ruta", [REGIONES, VALIDACIONES])
    def test_es_401(self, api_client, mock_pinot, ruta):
        assert api_client.get(ruta).status_code == 401

    @pytest.mark.parametrize("ruta", [REGIONES, VALIDACIONES])
    def test_un_rol_ajeno_es_403(self, api_client, operator_auth_headers, ruta):
        assert api_client.get(ruta, **operator_auth_headers).status_code == 403


@pytest.mark.api
class TestSinAcotamiento:
    def test_las_regiones_declaran_alcance_total(
        self, api_client, director_tecnologico_headers, regiones_sembradas
    ):
        # Una región no pertenece a nadie: no hay eje que acotar.
        cuerpo = api_client.get(REGIONES, **director_tecnologico_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_las_validaciones_tambien(
        self, api_client, director_tecnologico_headers, validaciones_sembradas
    ):
        cuerpo = api_client.get(VALIDACIONES, **director_tecnologico_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"
