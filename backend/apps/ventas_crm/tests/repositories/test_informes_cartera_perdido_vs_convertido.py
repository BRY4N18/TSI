"""T018 — «perdido» y «convertido» son conjuntos disjuntos (research D1).

Es la prueba que protege el defecto más caro de este módulo.

Un prospecto se vuelve inactivo por **dos motivos opuestos** y los dos dejan
`activo = false`: se perdió la oportunidad, o **se ganó** y ya es cliente. Un
listado de perdidos filtrado por `activo = false` incluiría los convertidos, es
decir **presentaría los éxitos comerciales como fracasos**.

Y no daría ningún error. Devolvería un número plausible y equivocado, que es la
peor clase de defecto: solo se detecta comparándolo con otra fuente, y mientras
tanto alimenta decisiones de jefatura sobre el rendimiento del equipo.

Las dos mitades
---------------
1. **Contra los datos**: con un perdido y un convertido sembrados a la vez, cada
   filtro devuelve exactamente uno.
2. **Contra el código**: que la condición SQL de `perdido` no sea `activo = false`.
   El doble en memoria no reproduce la distinción por sí solo, así que sin esta
   segunda mitad la primera podría pasar con una implementación equivocada.
"""

from __future__ import annotations

import inspect
import re

import pytest

from core.repositories.ventas_crm import informes_cartera_repository
from core.repositories.ventas_crm.informes_cartera_repository import (
    CONDICION_POR_ESTADO,
    ESTADO_ACTIVO,
    ESTADO_CONVERTIDO,
    ESTADO_PERDIDO,
    InformesCarteraRepository,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesCarteraRepository()


class TestLosDosConjuntosSonDisjuntos:
    def test_perdido_devuelve_exactamente_uno(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, estado=ESTADO_PERDIDO)

        assert [f["idprospecto"] for f in filas] == [8102]

    def test_convertido_devuelve_exactamente_uno(self, repo, dos_carteras):
        filas = repo.prospectos(limit=500, estado=ESTADO_CONVERTIDO)

        assert [f["idprospecto"] for f in filas] == [8103]

    def test_el_convertido_nunca_aparece_entre_los_perdidos(self, repo, dos_carteras):
        perdidos = {f["idprospecto"] for f in repo.prospectos(limit=500, estado=ESTADO_PERDIDO)}

        assert 8103 not in perdidos, (
            "el prospecto convertido (un exito comercial) aparece como perdido"
        )

    def test_el_perdido_nunca_aparece_entre_los_convertidos(self, repo, dos_carteras):
        convertidos = {
            f["idprospecto"] for f in repo.prospectos(limit=500, estado=ESTADO_CONVERTIDO)
        }

        assert 8102 not in convertidos

    def test_ninguno_de_los_dos_aparece_entre_los_activos(self, repo, dos_carteras):
        activos = {f["idprospecto"] for f in repo.prospectos(limit=500, estado=ESTADO_ACTIVO)}

        assert not ({8102, 8103} & activos)

    def test_sin_filtro_salen_los_tres_estados(self, repo, dos_carteras):
        todos = {f["idprospecto"] for f in repo.prospectos(limit=500)}

        assert {8101, 8102, 8103} <= todos


class TestLaCondicionSqlEsLaCorrecta:
    """La mitad que el doble en memoria no puede cubrir por sí sola."""

    def test_perdido_no_se_resuelve_con_activo_false(self):
        sql, params = CONDICION_POR_ESTADO[ESTADO_PERDIDO]

        assert "activo" not in sql.lower(), (
            "usar `activo = false` como equivalente de perdido incluye los convertidos"
        )
        assert params == {"motivo": "perdido"}

    def test_convertido_tampoco(self):
        sql, params = CONDICION_POR_ESTADO[ESTADO_CONVERTIDO]

        assert "activo" not in sql.lower()
        assert params == {"motivo": "convertido"}

    def test_perdido_y_convertido_filtran_por_motivos_distintos(self):
        _, perdido = CONDICION_POR_ESTADO[ESTADO_PERDIDO]
        _, convertido = CONDICION_POR_ESTADO[ESTADO_CONVERTIDO]

        assert perdido != convertido

    def test_activo_si_usa_la_bandera(self):
        # El único de los tres para el que `activo` es la condición correcta.
        sql, params = CONDICION_POR_ESTADO[ESTADO_ACTIVO]

        assert sql == "activo = true"
        assert params == {}

    def test_ningun_lugar_del_repositorio_usa_activo_false(self):
        fuente = inspect.getsource(informes_cartera_repository)
        consultas = re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)
        candidatos = consultas + [sql for sql, _ in CONDICION_POR_ESTADO.values()]

        for texto in candidatos:
            assert not re.search(r"activo\s*=\s*false", texto, re.IGNORECASE), texto

    def test_los_tres_estados_estan_declarados(self):
        assert set(CONDICION_POR_ESTADO) == {"activo", "perdido", "convertido"}, (
            "reducirlo a activo/inactivo pierde justo la distincion que importa"
        )
