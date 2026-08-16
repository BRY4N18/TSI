"""T028 — `reasignaciones` acepta rango **opcional**.

Es el primer listado de este departamento con esa forma; los otros tres son de
estado actual y rechazan el rango con `400`. La asimetría es deliberada: una
reasignación *ocurre en un instante*, así que acotarla por período tiene sentido;
una cartera *está* en un estado, y no lo tiene.

Y la mitad que más importa: **omitir el rango no es un error**. Devuelve el
histórico completo paginado, que es una petición perfectamente válida.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/ventas-crm"
RUTA = f"{BASE}/reasignaciones"


@pytest.mark.api
class TestSinRango:
    def test_es_200_no_400(self, api_client, admin_auth_headers, asignaciones_sembradas):
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200

    def test_devuelve_el_historico_completo(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 3

    def test_meta_no_declara_extremos_que_no_se_aplicaron(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "desde" not in cuerpo["meta"]["filtros"]
        assert "hasta" not in cuerpo["meta"]["filtros"]


@pytest.mark.api
class TestConRango:
    def test_solo_desde_acota(self, api_client, admin_auth_headers, asignaciones_sembradas):
        cuerpo = api_client.get(f"{RUTA}?desde=2026-08-06", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2

    def test_solo_hasta_acota(self, api_client, admin_auth_headers, asignaciones_sembradas):
        cuerpo = api_client.get(f"{RUTA}?hasta=2026-08-06", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2

    def test_ambos_extremos_acotan(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-05&hasta=2026-08-09", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_hasta_es_inclusiva(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        # La reasignación del 2026-08-06 debe entrar cuando `hasta` es ese día.
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-06&hasta=2026-08-06", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_los_extremos_aplicados_viajan_en_meta(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-01&hasta=2026-08-31", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["filtros"]["desde"] == "2026-08-01"
        assert cuerpo["meta"]["filtros"]["hasta"] == "2026-08-31"

    def test_rango_invertido_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{RUTA}?desde=2026-08-31&hasta=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_formato_no_iso_es_400(self, api_client, admin_auth_headers):
        assert api_client.get(f"{RUTA}?desde=ayer", **admin_auth_headers).status_code == 400


@pytest.mark.api
class TestQuienAceptaRangoYQuienNo:
    """Dos de los cuatro listados del departamento aceptan rango, y dos no.

    El criterio es si el listado describe un **suceso** o un **estado**:

    | Listado | Describe | Rango |
    |---|---|---|
    | `reasignaciones` | un traspaso ocurrido | ✅ |
    | `notificaciones-enviadas` | un aviso enviado | ✅ |
    | `prospectos` | la cartera de ahora | ❌ |
    | `demos-activas` | las demos vigentes ahora | ❌ |
    """

    @pytest.mark.parametrize("informe", ["prospectos", "demos-activas"])
    def test_los_de_estado_actual_rechazan_el_rango(
        self, api_client, admin_auth_headers, informe
    ):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400, (
            "un listado de estado actual no puede aceptar rango"
        )

    @pytest.mark.parametrize("informe", ["reasignaciones", "notificaciones-enviadas"])
    def test_los_de_hechos_del_periodo_lo_aceptan(
        self, api_client, admin_auth_headers, informe
    ):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 200

    @pytest.mark.parametrize("informe", ["reasignaciones", "notificaciones-enviadas"])
    def test_y_tambien_omitirlo(self, api_client, admin_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **admin_auth_headers).status_code == 200
