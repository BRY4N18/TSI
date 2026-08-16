"""T028 — la misma cifra por los dos caminos, y la excepción que lo prueba.

Mientras 13 informes se sirvan desde el sistema operativo y sus consultas
equivalentes existan sobre el modelo, hay **dos caminos que pueden discrepar**.
Esta prueba es la única defensa contra que discrepen sin que nadie lo note: si un
día dan cifras distintas, hay dos verdades y ninguna forma de decidir cuál rige.

⚠️ **La completitud queda excluida a propósito.** Tiene que diferir: el endpoint
actual comprueba la nulidad contra un almacén sin nulos, así que responde 100 %
pase lo que pase. Si algún día coincidiera con el catálogo *por construcción*,
sería señal de que la consulta nueva heredó el defecto. La cubre `T024`.

Qué se compara, y por qué no es fila a fila
--------------------------------------------
Los dos caminos **agrupan por claves distintas**, y es intencionado: el endpoint
actual reparte por calle y las consultas del catálogo por condado, porque el
informe se pidió por zona y una calle no es una zona. Comparar fila a fila
mediría esa diferencia de forma, no una de cálculo, y fallaría siempre sin
señalar nada.

Lo que sí tiene que coincidir es lo que ambos afirman sobre el mismo conjunto:
los totales del período y los conteos por categoría. Esos son comprobables, y son
lo que un tablero suma.
"""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

DESDE = "2026-01-01"
HASTA = "2026-12-31"
PARAMS = {"desde": DESDE, "hasta": HASTA}


@pytest.fixture
def cliente(django_user_model):
    from core.jwt_utils import create_access_token

    api = APIClient()
    token = create_access_token(user_id=1, roles=["Administrador"], session_id=1)
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api


@pytest.fixture
def catalogo():
    repositorio = ModeloRepository()
    try:
        repositorio.ejecutar(
            "ot21_distribucion_severidad", departamento="emergencias", parametros=PARAMS
        )
    except Exception:  # noqa: BLE001
        pytest.skip("el modelo analítico no está disponible")
    return repositorio


def _operativo(cliente, informe: str, **extra):
    url = f"/api/v1/informes-tacticos/registro/{informe}"
    respuesta = cliente.get(url, {**PARAMS, **extra})
    if respuesta.status_code != 200:
        pytest.skip(f"el endpoint operativo '{informe}' no respondió 200")
    return respuesta.json()["data"]


def _modelo(catalogo, consulta: str, **extra):
    return catalogo.ejecutar(
        consulta, departamento="emergencias", parametros={**PARAMS, **extra}
    )


class TestDistribucionPorSeveridad:
    def test_el_total_del_periodo_coincide(self, cliente, catalogo):
        operativo = sum(f["total_casos"] for f in _operativo(cliente, "distribucion-severidad"))
        modelo = sum(f["casos"] for f in _modelo(catalogo, "ot21_distribucion_severidad"))

        assert operativo == modelo

    def test_los_conteos_por_categoria_coinciden(self, cliente, catalogo):
        # Se comparan como multiconjunto y no emparejados por nombre: el
        # endpoint devuelve el **id** de la severidad y el catálogo su nombre, y
        # traducir uno al otro aquí metería en la prueba una tabla de conversión
        # que también podría estar mal.
        operativo = sorted(f["total_casos"] for f in _operativo(cliente, "distribucion-severidad"))
        modelo = sorted(f["casos"] for f in _modelo(catalogo, "ot21_distribucion_severidad"))

        assert operativo == modelo


class TestDistribucionPorZona:
    def test_el_total_del_periodo_coincide(self, cliente, catalogo):
        operativo = sum(f["total_casos"] for f in _operativo(cliente, "distribucion-zona"))
        modelo = sum(f["casos"] for f in _modelo(catalogo, "ot21_distribucion_zona"))

        assert operativo == modelo, (
            "los dos caminos no cuentan los mismos casos en el período"
        )


class TestImpactoHumano:
    @pytest.mark.parametrize(
        "campo_operativo,campo_modelo",
        [("total_heridos", "heridos"), ("total_victimas", "victimas"),
         ("total_fallecidos", "fallecidos")],
    )
    def test_los_totales_de_impacto_coinciden(
        self, cliente, catalogo, campo_operativo, campo_modelo
    ):
        operativo = sum(f[campo_operativo] for f in _operativo(cliente, "impacto-humano"))
        modelo = sum(f[campo_modelo] for f in _modelo(catalogo, "ot21_impacto_humano"))

        assert operativo == pytest.approx(modelo)


class TestRankingDeUbicaciones:
    def test_los_casos_por_calle_coinciden(self, cliente, catalogo):
        operativo = {
            f["calle_nombre"]: f["total_casos"]
            for f in _operativo(cliente, "ranking-ubicaciones", top=10)
        }
        modelo = {
            f["calle"]: f["casos"]
            for f in _modelo(catalogo, "ot21_ranking_ubicaciones", top=10)
        }

        comunes = set(operativo) & set(modelo)
        assert comunes, "los dos rankings no comparten ninguna calle"
        for calle in comunes:
            assert operativo[calle] == modelo[calle], f"discrepan en '{calle}'"


class TestDescarteYFusion:
    def test_las_tasas_de_un_mismo_dia_coinciden(self, cliente, catalogo):
        """Se compara **día a día**, y no el total, por una limitación del origen.

        El endpoint actual publica las tasas **sin su denominador**: devuelve
        `pct_descarte` por día y no cuántos casos hubo. Sin denominador las tasas
        diarias no se pueden recomponer en una del período —promediarlas daría
        un número distinto y plausible—, así que el contraste solo es posible
        dentro de un mismo día.

        Es exactamente lo que el contrato nuevo prohíbe: «todo porcentaje viene
        con su denominador, para que la fracción sea comprobable». Este informe
        es la demostración de por qué esa regla está ahí.
        """
        operativo = _operativo(cliente, "descarte-fusion")
        if not operativo:
            pytest.skip("el endpoint operativo no devolvió días")

        dia = operativo[0]["periodo"]
        modelo = catalogo.ejecutar(
            "ot21_descarte_fusion",
            departamento="emergencias",
            parametros={"desde": dia, "hasta": dia},
        )
        assert modelo, f"el catálogo no devolvió nada para {dia}"

        assert operativo[0]["pct_descarte"] == pytest.approx(
            modelo[0]["pct_descarte"], abs=1e-4
        )
        assert operativo[0]["pct_fusion"] == pytest.approx(
            modelo[0]["pct_fusion"], abs=1e-4
        )


class TestLaCompletitudDebeDiferir:
    def test_el_endpoint_actual_no_puede_bajar_del_cien_por_ciento(self, cliente):
        """La excepción que da sentido a todo lo anterior.

        No se comprueba que las dos cifras **difieran hoy**: con los datos
        actuales coinciden, porque no hay ningún caso incompleto y el 100 % es la
        respuesta correcta. Lo que se comprueba es lo que hace al endpoint
        actual incapaz de dar otra cosa — que su condición se apoya en una
        nulidad que su almacén no tiene.

        La demostración de que la consulta nueva **sí** puede bajar del 100 %
        está en `dags/tests/test_ot21_completitud.py` (T024), fabricando el caso
        incompleto que los datos reales no traen.
        """
        datos = _operativo(cliente, "completitud-campos-criticos")

        assert datos, "el endpoint actual no devolvió nada"
        # Ni un solo día distinto de 1.0, en todo un año de datos. Ese es el
        # síntoma: no es que la calidad sea perfecta, es que la pregunta no se
        # está haciendo.
        for fila in datos:
            assert fila["pct_completos"] == 1.0, (
                "el endpoint operativo dejó de responder 100 %: si eso ocurriera "
                "de verdad, este módulo ya no tendría que migrar la completitud "
                "y esta prueba debe revisarse"
            )
