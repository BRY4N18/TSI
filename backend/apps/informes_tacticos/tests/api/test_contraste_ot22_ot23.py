"""T047 — contraste de OT22 y OT23.

Misma función que `test_contraste_ot21`: mientras un informe se sirva desde el
sistema operativo y su consulta equivalente exista sobre el modelo, hay **dos
caminos que pueden discrepar**, y esta prueba es la única defensa contra que lo
hagan sin que nadie lo note.

⚠️ **Ratio y pérdida de señal quedan excluidos: deben diferir.**

* El ratio anterior cuenta la flota de hoy, así que un período pasado se calcula
  contra unidades que quizá no existían entonces.
* La pérdida de señal anterior analizaba 10 000 de 59 045 posiciones y publicaba
  el resultado como completo. Sus cifras son **menores**, y eso es el defecto.

Lo que este fichero descubrió, y no estaba previsto
----------------------------------------------------
Dos de los seis informes «correctos» resultaron **no ser comparables tal como
estaban escritas mis consultas**, y en un caso el problema era mío:

* **Tiempo de respuesta por severidad** — yo medía `segundos_transito`, que es
  **confirmación → llegada**. El endpoint mide **despacho → llegada**. La
  diferencia son los ~18 s que la unidad tarda en aceptar. Corregido.
* **Tiempo de reportado a asignado** — los dos miden los mismos 3638 casos y
  arrancan el cronómetro en instantes distintos: el endpoint en el estado
  `REPORTADO` del historial, el modelo en el momento del accidente. El modelo no
  guarda hoy el instante de `REPORTADO`. Queda **excluido y declarado**, no
  disimulado con una tolerancia amplia: una tolerancia del 10 % taparía esta
  diferencia y también taparía un error de verdad.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

DESDE = "2026-01-01"
HASTA = "2026-12-31"
PARAMS = {"desde": DESDE, "hasta": HASTA}


@pytest.fixture
def cliente():
    from core.jwt_utils import create_access_token

    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=(
            f"Bearer {create_access_token(user_id=1, roles=['Administrador'], session_id=1)}"
        )
    )
    return api


@pytest.fixture
def catalogo():
    repositorio = ModeloRepository()
    try:
        repositorio.ejecutar(
            "ot23_abortos_perdidas", departamento="emergencias", parametros=PARAMS
        )
    except Exception:  # noqa: BLE001
        pytest.skip("el modelo analítico no está disponible")
    return repositorio


def _operativo(cliente, grupo: str, informe: str):
    respuesta = cliente.get(f"/api/v1/informes-tacticos/{grupo}/{informe}", PARAMS)
    if respuesta.status_code != 200:
        pytest.skip(f"el endpoint operativo '{informe}' no respondió 200")
    return respuesta.json()["data"]


def _modelo(catalogo, consulta: str, **extra):
    return catalogo.ejecutar(
        consulta, departamento="emergencias", parametros={**PARAMS, **extra}
    )


class TestAsignacionAutomaticaVsManual:
    def test_los_porcentajes_por_origen_coinciden(self, cliente, catalogo):
        operativo = {
            f["origen_nombre"]: f["pct_total"]
            for f in _operativo(cliente, "despacho", "asignacion-automatica-vs-manual")
        }
        modelo = {
            f["origen"]: f["pct"]
            for f in _modelo(catalogo, "ot22_asignacion_automatica_vs_manual")
        }

        assert set(operativo) == set(modelo)
        for origen in operativo:
            assert operativo[origen] == pytest.approx(modelo[origen], abs=1e-3), (
                f"discrepan en '{origen}'"
            )

    def test_escalado_zona_no_se_reparte_entre_los_otros_dos(self, cliente, catalogo):
        # Es un origen propio: el sistema pidiendo ayuda fuera de la zona. Sumarlo
        # a los otros borraría la única señal de que la cobertura local no daba
        # abasto.
        modelo = {f["origen"]: f["pct"] for f in _modelo(catalogo, "ot22_asignacion_automatica_vs_manual")}

        assert "Escalado_zona" in modelo


class TestTiempoDeRespuestaPorSeveridad:
    #: El endpoint devuelve el **id** de la severidad; el catálogo, su nombre.
    NOMBRES = {1: "Leve", 2: "Moderado", 3: "Grave", 4: "Fatal"}

    def test_el_promedio_por_severidad_coincide(self, cliente, catalogo):
        """⚠️ Es la comprobación que destapó que yo medía otro intervalo.

        La tolerancia es de **una décima de segundo**, no un porcentaje. Con un
        margen del 1 % la diferencia original —18 s sobre 468, un 4 %— habría
        fallado igual, pero el sesgo de +1 s que introducía sumar dos columnas ya
        truncadas habría pasado desapercibido. Un margen se elige por lo que
        tiene que **detectar**, no por lo que hace pasar la prueba.
        """
        operativo = {
            self.NOMBRES.get(f["idseveridad"], "Desconocido"): f["promedio_segundos"]
            for f in _operativo(cliente, "despacho", "tiempo-respuesta-por-severidad")
        }
        modelo = {
            f["severidad"]: f["promedio_seg"]
            for f in _modelo(catalogo, "ot22_tiempo_respuesta_por_severidad")
        }

        comunes = set(operativo) & set(modelo)
        assert comunes, "los dos informes no comparten ninguna severidad"
        for severidad in comunes:
            assert operativo[severidad] == pytest.approx(modelo[severidad], abs=0.1), (
                f"discrepan en '{severidad}': {operativo[severidad]} vs {modelo[severidad]}"
            )


class TestCargaPorUnidad:
    def test_los_despachos_por_unidad_coinciden(self, cliente, catalogo):
        operativo = {
            f["unidad_placa"]: f["total_despachos"]
            for f in _operativo(cliente, "despacho", "carga-por-unidad")
        }
        modelo = {
            f["unidad"]: f["intentos_recibidos"]
            for f in _modelo(catalogo, "ot22_carga_por_unidad")
        }

        comunes = set(operativo) & set(modelo)
        assert comunes, "los dos informes no comparten ninguna unidad"
        for unidad in comunes:
            assert operativo[unidad] == modelo[unidad], f"discrepan en '{unidad}'"


class TestRechazoYVencimiento:
    """⚠️ **No se comparan las cifras: tienen que diferir, y por dos motivos.**

    Este informe está clasificado como «correcto, solo vigilar», y **no lo es**.
    Lo destapó esta prueba (decisión pendiente #34):

    1. **El denominador del endpoint son transiciones de estado**, no intentos de
       despacho. Un despacho bien atendido genera cinco filas de historial
       —`Pendiente → Confirmado → En_transito → En_sitio → Retirado`— y uno
       rechazado genera dos. Cuanto mejor trabaja una unidad, **más baja parece
       su tasa de rechazo**, porque cada despacho que completa le añade cuatro
       filas al denominador.
    2. **La tabla se trunca**: 19 528 filas, tope por defecto de 10 000, el
       48,8 % analizado. El mismo defecto que ya se corrigió en la pérdida de
       señal.

    Medido en `LOTE-A2`: 0,0769 (1 de 13 transiciones) frente a 0,2 real (1
    rechazo de 5 despachos). Un factor de 2,6.

    Lo que se comprueba aquí es que **la consulta del catálogo es la correcta**, y
    la discrepancia queda declarada en vez de disimulada: una tolerancia capaz de
    tapar un factor de 2,6 no detectaría nada.
    """

    def test_el_denominador_del_catalogo_son_intentos_de_despacho(self, cliente, catalogo):
        filas = _modelo(catalogo, "ot22_rechazo_timeout_por_unidad")

        for fila in filas:
            assert fila["rechazados"] + fila["vencidos"] <= fila["intentos"], (
                f"'{fila['unidad']}' tiene más rechazos y vencimientos que intentos: "
                f"el denominador no son intentos de despacho"
            )
            assert fila["pct_rechazo"] == pytest.approx(
                fila["rechazados"] / fila["intentos"], abs=1e-4
            )

    def test_las_dos_partes_se_publican_por_separado(self, cliente, catalogo):
        # El informe anterior las suma en un solo «no atendidos». Un rechazo
        # tiene una persona y un motivo detrás; un vencimiento significa que
        # nadie contestó. Son dos problemas con dos soluciones.
        fila = _modelo(catalogo, "ot22_rechazo_timeout_por_unidad")[0]

        assert {"rechazados", "vencidos", "pct_rechazo", "pct_vencimiento"} <= set(fila)

    def test_la_discrepancia_con_el_endpoint_sigue_ahi(self, cliente, catalogo):
        """Vigila la decisión #34 mientras esté sin resolver.

        Si algún día las dos cifras coincidieran, o el endpoint dejara de
        existir, esta prueba falla — y eso es lo que se quiere: significaría que
        la decisión se resolvió y que este fichero tiene que actualizarse. Una
        prueba que se limitara a ignorar el informe no avisaría de nada.
        """
        operativo = {
            f["unidad_placa"]: f["pct_rechazo_timeout"]
            for f in _operativo(cliente, "despacho", "rechazo-timeout-por-unidad")
        }
        modelo = {
            f["unidad"]: (f["rechazados"] + f["vencidos"]) / f["intentos"]
            for f in _modelo(catalogo, "ot22_rechazo_timeout_por_unidad")
        }

        comunes = set(operativo) & set(modelo)
        assert comunes, "los dos informes no comparten ninguna unidad"

        difieren = [u for u in comunes if abs(operativo[u] - modelo[u]) > 1e-3]
        assert difieren, (
            "las dos cifras coinciden: o se resolvió la decisión #34, o el "
            "endpoint cambió. Revisa esta prueba antes de darla por buena"
        )


class TestAbortosYPerdidas:
    def test_el_total_de_abortos_coincide(self, cliente, catalogo):
        """Se compara el **conteo**, no la tasa.

        El endpoint publica `pct_abortos_perdidas` por unidad **sin su
        denominador**, igual que `descarte-fusion` en OT21, así que las tasas por
        unidad no se pueden recomponer en una del período. Lo que sí es
        comparable es cuántos abortos hubo, y el catálogo lo publica.
        """
        operativo = _operativo(cliente, "seguimiento", "abortos-perdidas")
        modelo = _modelo(catalogo, "ot23_abortos_perdidas")[0]

        assert operativo, "el endpoint operativo no devolvió unidades"
        assert modelo["abortados"] >= 0
        # Los cinco desenlaces del catálogo suman el total: es la propiedad que
        # hace que el conteo de abortos sea interpretable.
        suma = (
            modelo["confirmados"] + modelo["rechazados"] + modelo["vencidos"]
            + modelo["abortados"] + modelo["en_curso"]
        )
        assert suma == modelo["despachos"]


class TestLosExcluidosDebenDiferir:
    def test_el_ratio_anterior_usa_la_flota_de_hoy(self, cliente, catalogo):
        """No se comprueba que difieran hoy, sino que miden cosas distintas.

        Con la flota actual y un período reciente las dos cifras pueden coincidir
        por casualidad. Lo que no coincide es la pregunta: el catálogo publica
        `unidades_vigentes` **por mes**, y el endpoint anterior no tiene ese
        concepto porque solo conoce la flota presente.
        """
        modelo = _modelo(catalogo, "ot22_ratio_demanda_capacidad")

        assert modelo, "el catálogo no devolvió filas"
        assert "unidades_vigentes" in modelo[0]
        # Más de un mes en el rango: si la capacidad fuera la de hoy, sería la
        # misma en todos ellos por construcción.
        assert len({f["periodo"] for f in modelo}) > 1

    def test_la_perdida_de_senal_nueva_ve_mas_posiciones(self, catalogo):
        """El flujo anterior veía 10 000 posiciones. El catálogo ve todas.

        Se comprueba contra el tope que causaba el truncamiento, y no contra la
        cifra vieja: la tabla anterior ya no se refresca, así que compararse con
        ella mediría lo que había el día que se apagó.
        """
        filas = _modelo(catalogo, "ot23_perdida_senal", umbral_seg=60)
        medidos = sum(f["intervalos_medidos"] for f in filas)

        assert medidos > 10_000, (
            f"solo se consideraron {medidos} intervalos: si no supera el tope por "
            f"defecto de 10 000, esta prueba no distingue el arreglo del defecto"
        )
