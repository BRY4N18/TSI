"""T071 — contraste de los dos informes correctos de OT25.

Tercera y última pieza de la defensa contra dos verdades, junto con T028 y T047.

Lo que encontró, que tampoco estaba previsto
---------------------------------------------
**`tiempo-asignado-cerrado` no es contrastable, y la razón es un defecto del
endpoint** (decisión pendiente #35). Atribuye cada caso a **una sola** unidad con
un diccionario por comprensión:

    unidad_por_accidente = {d["idaccidente"]: d["idunidademergencia"] for d in despachos}

Para un caso con varios despachos gana **el último que devuelva Pinot**, y Pinot
no garantiza orden sin `ORDER BY`. Son 441 casos de 3651 —el 12 %—, así que la
cifra por unidad puede cambiar entre dos ejecuciones idénticas sin que nada haya
cambiado en los datos.

No es que el modelo y el endpoint midan distinto: es que el endpoint no mide
siempre lo mismo. Contrastarlo con una tolerancia sería contrastar contra un
número que se mueve solo.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

PARAMS = {"desde": "2026-01-01", "hasta": "2026-12-31"}


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
            "ot25_cierres_forzados", departamento="emergencias", parametros=PARAMS
        )
    except Exception:  # noqa: BLE001
        pytest.skip("el modelo analítico no está disponible")
    return repositorio


def _operativo(cliente, informe: str, **extra):
    respuesta = cliente.get(
        f"/api/v1/informes-tacticos/seguimiento/{informe}", {**PARAMS, **extra}
    )
    if respuesta.status_code != 200:
        pytest.skip(f"el endpoint operativo '{informe}' no respondió 200")
    return respuesta.json()["data"]


def _modelo(catalogo, consulta: str, **extra):
    return catalogo.ejecutar(
        consulta, departamento="emergencias", parametros={**PARAMS, **extra}
    )


class TestCierresForzados:
    """⚠️ **Tampoco se comparan las cifras: miden cosas distintas** (decisión #36).

    Dos conceptos con nombres casi iguales y un factor de 451 entre ellos:

    * `Fact_Despacho.retiro_forzado` —lo que mide el catálogo— vale 1 en **una**
      fila de 4314.
    * El «cierre forzado» del endpoint es una transición a `Retirado` **con
      `idusuario` poblado**: retiro manual desde central, frente al automático
      por vencimiento. Son **451** de 3310.

    El modelo **no puede** reproducir hoy la segunda definición, y no por
    descuido: lo que distingue un retiro manual de uno automático es la presencia
    de `idusuario`, y la identidad de persona está excluida del modelo por
    decisión constitucional.

    La salida es un booleano derivado al cargar —«el retiro fue manual»— que
    conserve el hecho sin la identidad. Es un cambio de esquema pendiente.
    """

    def test_el_catalogo_publica_el_denominador(self, cliente, catalogo):
        # Lo que el endpoint anterior no hace: publica `pct_cierres_forzados` sin
        # decir sobre cuántos, así que sus tasas diarias no se pueden recomponer
        # en una del período. Es la tercera vez que aparece el mismo obstáculo, y
        # es lo que el contrato nuevo prohíbe.
        fila = _modelo(catalogo, "ot25_cierres_forzados")[0]

        assert {"casos", "cerrados", "con_retiro_forzado"} <= set(fila)

    def test_la_discrepancia_con_el_endpoint_sigue_ahi(self, cliente, catalogo):
        """Vigila la decisión #36 mientras esté sin resolver.

        Si las dos cifras coincidieran, o sería casualidad de un día tranquilo o
        significaría que la decisión se resolvió; en los dos casos hay que mirar
        esta prueba antes de darla por buena.
        """
        operativo = _operativo(cliente, "cierres-forzados")
        if not operativo:
            pytest.skip("el endpoint operativo no devolvió días")

        con_cierres = [d for d in operativo if d["pct_cierres_forzados"] > 0]
        assert con_cierres, (
            "el endpoint no reporta ningún cierre forzado: sin ellos esta "
            "comprobación no distingue las dos definiciones"
        )

        dia = con_cierres[0]["periodo"]
        modelo = catalogo.ejecutar(
            "ot25_cierres_forzados",
            departamento="emergencias",
            parametros={"desde": dia, "hasta": dia},
        )

        assert modelo[0]["pct_con_retiro_forzado"] != pytest.approx(
            con_cierres[0]["pct_cierres_forzados"], abs=1e-3
        ), (
            "las dos cifras coincidieron: o se resolvió la decisión #36, o es "
            "casualidad de este día. Revisa esta prueba antes de darla por buena"
        )


class TestTiempoAsignadoACierre:
    """⚠️ No se comparan las cifras: el endpoint no devuelve siempre la misma."""

    def test_el_catalogo_no_atribuye_el_caso_a_una_unidad_arbitraria(self, catalogo):
        """La consulta del catálogo mide el caso, que es de quien es la duración.

        «Cuánto tardó en cerrarse» es una propiedad del **caso**, no de una
        unidad: la unidad no controla cuándo se cierra el expediente. Repartir esa
        duración entre unidades exige elegir una, y elegirla arbitrariamente —lo
        que hace el endpoint— produce una cifra que depende del orden en que
        lleguen las filas.

        El catálogo no elige: agrupa por período y publica `sin_cerrar` aparte.
        """
        fila = _modelo(catalogo, "ot25_tiempo_asignado_a_cierre")[0]

        assert "unidad" not in fila
        assert {"casos", "cerrados", "sin_cerrar"} <= set(fila)

    def test_los_casos_sin_cerrar_quedan_fuera_del_promedio(self, catalogo):
        # Un caso abierto no ha durado nada todavía: está durando. Meterlo con lo
        # que lleva acumulado haría que el informe mejorara al aumentar el
        # trabajo pendiente.
        fila = _modelo(catalogo, "ot25_tiempo_asignado_a_cierre")[0]

        assert fila["cerrados"] + fila["sin_cerrar"] == fila["casos"]
        assert fila["cerrados"] > 0
        assert fila["promedio_min"] is not None

    def test_la_discrepancia_con_el_endpoint_sigue_ahi(self, cliente, catalogo):
        """Vigila la decisión #35 mientras esté sin resolver.

        No se comprueba una diferencia numérica —no habría con qué compararla—
        sino que **los dos siguen midiendo cosas distintas**: el endpoint entrega
        una fila por unidad y el catálogo una por período. Si algún día
        coincidieran en forma, esta prueba falla y hay que revisarla.
        """
        operativo = _operativo(cliente, "tiempo-asignado-cerrado")
        if not operativo:
            pytest.skip("el endpoint operativo no devolvió filas")

        assert "idunidademergencia" in operativo[0], (
            "el endpoint dejó de agrupar por unidad: revisa la decisión #35 "
            "antes de dar por buena esta prueba"
        )
        assert len(_modelo(catalogo, "ot25_tiempo_asignado_a_cierre")) == 1
