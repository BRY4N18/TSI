"""T017 — «sin cambio programado» es un centinela `0`, no una ausencia (research D2).

`cambio_plan_service.py` declara `SIN_CAMBIO_PROGRAMADO = 0`, así que **toda
suscripción sin cambio tiene un `0` guardado**, no un vacío.

Escribir el filtro como comprobación de nulidad sería **siempre cierto** —la base
analítica no almacena nulos y aquí además el código escribe un `0` explícito—, y
el listado devolvería **todas** las suscripciones como si todas tuvieran una
reducción de plan pendiente. No fallaría: daría un número plausible y
equivocado, alimentando una previsión de ingresos con reducciones inventadas.

Las dos mitades
---------------
1. **Contra los datos**: con una suscripción con cambio y otra sin él, el filtro
   devuelve exactamente una.
2. **Contra el código**: que la condición sea una comparación con el centinela y
   no una guarda de nulidad. El doble en memoria no reproduce el centinela por sí
   solo, así que sin esta mitad la primera podría pasar con una implementación
   equivocada.
"""

from __future__ import annotations

import inspect
import re

import pytest

from core.repositories.suscripciones import informes_suscripcion_repository
from core.repositories.suscripciones.informes_suscripcion_repository import (
    SIN_CAMBIO_PROGRAMADO,
    InformesSuscripcionRepository,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesSuscripcionRepository()


class TestElFiltroDistingueLosDosCasos:
    def test_con_cambio_devuelve_exactamente_una(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, con_cambio_programado=True)

        assert [f["id_suscripcion"] for f in filas] == [7001]

    def test_sin_cambio_devuelve_las_otras_dos(self, repo, dos_cuentas):
        filas = repo.suscripciones(limit=500, con_cambio_programado=False)
        ids = {f["id_suscripcion"] for f in filas}

        # Subconjunto y no igualdad: el store base ya trae una suscripción
        # propia, y esta prueba es sobre las tres sembradas aquí.
        assert {7002, 7003} <= ids
        assert 7001 not in ids

    def test_los_dos_conjuntos_son_disjuntos(self, repo, dos_cuentas):
        con = {f["id_suscripcion"] for f in repo.suscripciones(limit=500, con_cambio_programado=True)}
        sin = {f["id_suscripcion"] for f in repo.suscripciones(limit=500, con_cambio_programado=False)}

        assert not (con & sin)

    def test_y_juntos_son_todas(self, repo, dos_cuentas):
        con = {f["id_suscripcion"] for f in repo.suscripciones(limit=500, con_cambio_programado=True)}
        sin = {f["id_suscripcion"] for f in repo.suscripciones(limit=500, con_cambio_programado=False)}
        todas = {f["id_suscripcion"] for f in repo.suscripciones(limit=500)}

        assert con | sin == todas

    def test_sin_filtro_no_acota(self, repo, dos_cuentas):
        ids = {f["id_suscripcion"] for f in repo.suscripciones(limit=500)}

        assert {7001, 7002, 7003} <= ids

    def test_el_filtro_no_devuelve_todas(self, repo, dos_cuentas):
        """El síntoma exacto de la guarda de nulidad."""
        con_cambio = repo.suscripciones(limit=500, con_cambio_programado=True)
        todas = repo.suscripciones(limit=500)

        assert len(con_cambio) < len(todas), (
            "el filtro devolvio todas las suscripciones: se escribio como "
            "comprobacion de nulidad en vez de comparar contra el centinela"
        )


class TestLaCondicionSqlEsLaCorrecta:
    """La mitad que el doble en memoria no puede cubrir por sí sola."""

    @property
    def _fuente(self) -> str:
        return inspect.getsource(informes_suscripcion_repository)

    def test_no_hay_ninguna_guarda_de_nulidad_sobre_el_plan_programado(self):
        for patron in (r"idplan_programado\s+IS\s+NOT\s+NULL", r"idplan_programado\s+IS\s+NULL"):
            assert not re.search(patron, self._fuente, re.IGNORECASE), patron

    def test_la_condicion_compara_contra_el_centinela(self):
        # `> %(sin_cambio)s` / `<= %(sin_cambio)s`, parametrizado.
        assert "idplan_programado {comparador} %(sin_cambio)s" in self._fuente

    def test_el_centinela_es_cero(self):
        assert SIN_CAMBIO_PROGRAMADO == 0

    def test_coincide_con_el_valor_que_escribe_el_codigo_operativo(self):
        """Los dos módulos no pueden divergir.

        `core/` no importa de `apps/` —sería invertir las capas—, así que la
        coincidencia se comprueba aquí. Si el operativo cambiara el centinela,
        esta prueba falla en vez de dejar el informe filtrando contra un valor
        obsoleto: el mismo modo de fallo que "ACTIVA" contra "Activo".
        """
        from apps.suscripciones.services.cambio_plan_service import CambioPlanService

        assert SIN_CAMBIO_PROGRAMADO == CambioPlanService.SIN_CAMBIO_PROGRAMADO


class TestLaPresentacionTambienLoDistingue:
    def test_una_suscripcion_sin_cambio_no_devuelve_un_plan_cero(
        self, mock_pinot, dos_cuentas
    ):
        from apps.suscripciones.services.informes_suscripcion_service import (
            InformesSuscripcionService,
        )
        from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

        pagina = InformesSuscripcionService().suscripciones(
            acotamiento=Acotamiento(titular=None, alcance=ACOTADO_TODOS), limit=500
        )

        # Las dos sembradas sin cambio salen con `None`, no con un plan cero.
        de_las_cuentas = [
            f for f in pagina.filas
            if f["cuenta"] in ("Aseguradora Torres S.A.", "Transportes Beltran Ltda.")
        ]
        sin_cambio = [f for f in de_las_cuentas if f["cambio_programado"] is None]
        assert len(sin_cambio) == 2

    def test_la_que_si_lo_tiene_devuelve_el_nombre_del_plan(
        self, mock_pinot, dos_cuentas
    ):
        from apps.suscripciones.services.informes_suscripcion_service import (
            InformesSuscripcionService,
        )
        from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

        pagina = InformesSuscripcionService().suscripciones(
            acotamiento=Acotamiento(titular=None, alcance=ACOTADO_TODOS), limit=500
        )

        con_cambio = [f for f in pagina.filas if f["cambio_programado"] is not None]
        assert len(con_cambio) == 1
        # El contrato lo declara como objeto: el plan **y cuándo se aplica**.
        # Sin la fecha, el listado diría que hay un cambio sin decir cuándo.
        assert con_cambio[0]["cambio_programado"]["plan"] == "Basico"
        assert con_cambio[0]["cambio_programado"]["se_aplica_el"]

    def test_el_catalogo_no_se_consulta_por_el_plan_cero(self, repo, dos_cuentas):
        # No existe un plan con identificador cero: pedirlo sería una consulta
        # garantizada a no devolver nada.
        assert repo.nombres_de_plan([0, 0]) == {}
