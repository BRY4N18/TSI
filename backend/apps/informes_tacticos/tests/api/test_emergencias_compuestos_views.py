"""T022 y T023 — el endpoint nuevo, y el viejo que **no** se apaga todavía."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.services.emergencias_compuestos_service import (
    CATALOGO,
    PUBLICADOS,
)
from core.jwt_utils import create_access_token

BASE = "/api/v1/informes-tacticos/emergencias"


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    """Sin esto, `JWTSessionAuthentication` valida la sesion contra un Pinot real.

    En la suite no hay ninguno levantado: la peticion espera a que venza el
    timeout de red y la excepcion acaba traducida en `AuthenticationFailed`, es
    decir un 401 donde el test espera 403 o 404. El sintoma enganya porque
    parece un fallo de permisos y es de infraestructura.
    """
    return mock_pinot


def _cliente(roles):
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=roles, session_id=1)}"
    )
    return api


@pytest.fixture
def director():
    return _cliente(["DirectorOperaciones"])


class TestElConjuntoPublicado:
    #: Informes que el módulo **vigila** y no sustituye: el endpoint que los
    #: sirve hoy es correcto, y su consulta existe aquí solo para contrastarlo.
    #:
    #: Se enumeran uno a uno, y no como `CATALOGO - PUBLICADOS`, porque esa resta
    #: se cumpliría sola: publicar uno de estos lo sacaría del conjunto restado y
    #: la prueba seguiría en verde. Una lista escrita a mano es lo único que
    #: obliga a que publicarlo sea una decisión y no un descuido.
    VIGILADOS = frozenset({
        "tiempo-asignado-cierre",
        "cierres-forzados",
        "distribucion-severidad",
        "distribucion-zona",
        "descarte-fusion",
        "ranking-ubicaciones",
        "impacto-humano",
        "asignacion-automatica-vs-manual",
        "tiempo-reportado-confirmado",
        "tiempo-respuesta-por-severidad",
        "rechazo-timeout-por-unidad",
        "carga-por-unidad",
        "abortos-perdidas",
    })

    def test_ningun_informe_correcto_se_publica_como_endpoint(self):
        """⚠️ La regla que no puede romperse al añadir historias.

        Estos informes ya los sirve `informes-tacticos-agregados`
        **correctamente**. Publicarlos aquí crearía dos endpoints que responden
        lo mismo leyendo de almacenes distintos: mientras coincidan nadie lo
        nota, y el día que difieran hay dos cifras verdaderas y ninguna forma de
        decidir cuál rige.
        """
        publicados_de_mas = self.VIGILADOS & PUBLICADOS

        assert not publicados_de_mas, (
            f"{sorted(publicados_de_mas)} se publican como endpoint, y su "
            f"endpoint actual ya es correcto: son dos verdades esperando a diferir"
        )

    def test_el_catalogo_esta_repartido_entre_publicados_y_vigilados(self):
        # Si una consulta nueva no cayera en ninguno de los dos grupos, la
        # prueba de arriba dejaría de cubrirla **sin fallar**.
        sin_clasificar = set(CATALOGO) - PUBLICADOS - self.VIGILADOS

        assert not sin_clasificar, (
            f"{sorted(sin_clasificar)} no están ni publicados ni declarados como "
            f"vigilados: nadie decidió si deben servirse"
        )

    def test_todo_lo_publicado_tiene_su_consulta_en_el_catalogo(self):
        assert PUBLICADOS <= set(CATALOGO)

    @pytest.mark.parametrize("informe", sorted(set(CATALOGO) - PUBLICADOS))
    def test_lo_no_publicado_no_es_accesible_por_http(self, director, informe):
        assert director.get(f"{BASE}/{informe}").status_code == 404


@pytest.mark.integration
class TestElEndpointPublicado:
    # Consulta ClickHouse real: sin el stack `tactico` levantado, la peticion
    # revienta con ConnectionError *antes* de devolver respuesta, asi que el
    # `pytest.skip` de mas abajo nunca llega a evaluarse. Por la definicion de
    # markers de `testing.md`, una prueba que necesita infraestructura real es
    # de integracion. Ver decisiones-pendientes.md #50.
    @pytest.mark.integration
    def test_responde_con_la_forma_del_contrato(self, director):
        respuesta = director.get(
            f"{BASE}/completitud-campos-criticos", {"desde": "2026-01-01", "hasta": "2026-12-31"}
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        # `meta` es la del contrato y la misma que la de los listados simples.
        # Añadirle campos propios de este módulo obligaría al frontend a tratar
        # estos informes como un caso aparte.
        assert set(cuerpo["meta"]) == {"periodo", "filtros"}
        assert set(cuerpo["meta"]["periodo"]) == {"desde", "hasta"}

        for fila in cuerpo["data"]:
            assert set(fila) == {"periodo", "casos", "completos", "pct_completitud"}

    # Consulta ClickHouse real: sin el stack `tactico` levantado, la peticion
    # revienta con ConnectionError *antes* de devolver respuesta, asi que el
    # `pytest.skip` de mas abajo nunca llega a evaluarse. Por la definicion de
    # markers de `testing.md`, una prueba que necesita infraestructura real es
    # de integracion. Ver decisiones-pendientes.md #50.
    @pytest.mark.integration
    def test_sin_rango_usa_los_ultimos_treinta_dias(self, director):
        respuesta = director.get(f"{BASE}/completitud-campos-criticos")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        from datetime import date, timedelta

        periodo = respuesta.json()["meta"]["periodo"]
        desde = date.fromisoformat(periodo["desde"])
        hasta = date.fromisoformat(periodo["hasta"])

        # 30 días **contando ambos extremos**: restar 30 daría 31.
        assert hasta - desde == timedelta(days=29)


class TestErroresDeEntrada:
    def test_un_informe_fuera_del_registro_da_404_enumerando_los_publicados(self, director):
        respuesta = director.get(f"{BASE}/no-existe")

        assert respuesta.status_code == 404
        assert "completitud-campos-criticos" in respuesta.json()["detail"]

    def test_un_rango_invertido_es_un_error_y_no_una_vuelta_al_defecto(self, director):
        # Silenciar el error y aplicar el defecto daría un informe correcto de un
        # período que nadie pidió.
        respuesta = director.get(
            f"{BASE}/completitud-campos-criticos", {"desde": "2026-12-31", "hasta": "2026-01-01"}
        )

        assert respuesta.status_code == 400

    def test_medio_rango_tambien_es_un_error(self, director):
        respuesta = director.get(f"{BASE}/completitud-campos-criticos", {"desde": "2026-01-01"})

        assert respuesta.status_code == 400


class TestPermisos:
    # Aunque solo comprueba el permiso, el `GET` concedido sigue camino hasta la
    # consulta y necesita ClickHouse. Recuperar esta cobertura en la suite
    # rapida pide una fixture `mock_clickhouse` equivalente a `mock_pinot`, que
    # hoy no existe. Ver decisiones-pendientes.md #50.
    @pytest.mark.integration
    def test_entra_la_autoridad_del_departamento(self):
        assert _cliente(["DirectorOperaciones"]).get(
            f"{BASE}/completitud-campos-criticos"
        ).status_code != 403

    @pytest.mark.parametrize(
        "roles", [["Operador"], ["Cliente"], ["Tecnico"], ["Administrador"], []]
    )
    def test_no_entra_quien_no_es_la_autoridad(self, roles):
        """Solo la autoridad del departamento lee gestión.

        El `Operador` **sí** ve los listados simples: un listado es su trabajo
        del día, un informe compuesto es una lectura de gestión sobre el trabajo
        de todos.

        ⚠️ El `Administrador` entraba aquí hasta el 2026-08-19. Se le retiró con
        el mismo argumento: opera el sistema y conserva los listados simples,
        pero la lectura de gestión es de quien responde del departamento.
        """
        assert _cliente(roles).get(f"{BASE}/completitud-campos-criticos").status_code == 403

    def test_sin_credencial_es_401_y_no_403(self):
        assert APIClient().get(f"{BASE}/completitud-campos-criticos").status_code == 401


# `TestElEndpointAnteriorSigueEnPie` se retiró el 2026-08-19.
#
# Existía para T023: mantener en pie `CompletitudCamposCriticosView` y su ruta
# `informes-tacticos/registro/...` mientras el tablero apuntara ahí, porque
# apagarla habría vaciado la pantalla en vez de migrarla. Su propio docstring
# decía que se retiraría «cuando se decida qué pasa con los endpoints del módulo
# sustituido».
#
# Esa decisión se tomó: los tres informes agregados (registro, despacho,
# seguimiento) se retiraron por completo. Leían Pinot directamente y quedaron
# sustituidos por los listados de casos y por las pantallas de gestión sobre el
# modelo analítico, que es lo que este archivo prueba.
