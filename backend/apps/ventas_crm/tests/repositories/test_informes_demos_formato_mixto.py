"""T035 — dos demos con la misma fecha y distinto sufijo salen o no salen **juntas**.

`demo_expiracion` es `STRING` y el sistema acepta tres formatos: sufijo `Z`,
sufijo `+00:00` y sin zona horaria. Comparar cadenas ISO-8601 lexicográficamente
solo funciona si el formato es idéntico en **todas** las filas.

Con los tres conviviendo, una comparación de la cadena completa da resultados
incorrectos **sin error visible**: unas demos vigentes desaparecen del listado y
nadie se entera, porque el informe sigue devolviendo `200` y una lista plausible.

**Si de las tres solo sale una, la comparación de texto se coló en la consulta.**

Por qué el prefijo sí es seguro
-------------------------------
`2026-08-14` son los mismos diez caracteres sea cual sea el sufijo, y ordenan
igual entre sí. El prefiltro trae de más —incluidas las que expiraron hoy más
temprano— y eso es deliberado: el refinamiento en el servicio las descarta con
precisión de segundo.
"""

from __future__ import annotations

import inspect
import re

import pytest

from core.repositories.ventas_crm import informes_nutricion_repository
from core.repositories.ventas_crm.informes_nutricion_repository import (
    InformesNutricionRepository,
)
from apps.ventas_crm.tests.conftest import AHORA

PREFIJO_HOY = AHORA.strftime("%Y-%m-%d")


@pytest.fixture
def repo(mock_pinot):
    return InformesNutricionRepository()


class TestLosTresFormatosSeTratanIgual:
    def test_las_tres_del_mismo_instante_salen_juntas(self, repo, demos_formato_mixto):
        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)

        ids = {f["idprospecto"] for f in filas}
        assert {8401, 8402, 8403} <= ids, (
            "faltan formatos: la comparacion de texto se colo en la consulta"
        )

    def test_ninguno_de_los_tres_queda_fuera_por_su_sufijo(
        self, repo, demos_formato_mixto
    ):
        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)
        por_id = {f["idprospecto"]: f["demo_expiracion"] for f in filas}

        assert por_id[8401].endswith("Z")
        assert por_id[8402].endswith("+00:00")
        assert not por_id[8403].endswith(("Z", "+00:00"))

    def test_las_tres_representan_el_mismo_instante(self, repo, demos_formato_mixto):
        """Si no lo fueran, esta prueba no demostraría lo que dice demostrar."""
        from apps.ventas_crm.demo_tokens import parse_iso_expiracion

        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)
        instantes = {
            parse_iso_expiracion(f["demo_expiracion"])
            for f in filas
            if f["idprospecto"] in (8401, 8402, 8403)
        }

        assert len(instantes) == 1


class TestElPrefiltroTraeDeMas:
    def test_la_expirada_hoy_pasa_el_prefiltro(self, repo, demos_formato_mixto):
        # Es deliberado: el prefijo es por día, y descartarla con precisión de
        # segundo es trabajo del servicio.
        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)

        assert 8404 in {f["idprospecto"] for f in filas}

    def test_la_que_no_tiene_fecha_no_pasa(self, repo, demos_formato_mixto):
        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)

        assert 8405 not in {f["idprospecto"] for f in filas}

    def test_una_expirada_ayer_no_pasa(self, repo, mock_pinot, gerentes_sembrados):
        from conftest import PINOT_STORE
        from datetime import timedelta
        from apps.ventas_crm.tests.conftest import GERENTE_A, _prospecto

        ayer = (AHORA - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8450, empresa="Demo Ayer", idusuario=GERENTE_A, expiracion=ayer)
        )

        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)

        assert 8450 not in {f["idprospecto"] for f in filas}


class TestElAcotamientoSeAplica:
    def test_el_titular_acota_las_demos(self, repo, demos_formato_mixto):
        from apps.ventas_crm.tests.conftest import GERENTE_B

        filas = repo.demos_con_expiracion_desde(
            prefijo_hoy=PREFIJO_HOY, limit=500, titular=GERENTE_B
        )

        assert {f["idprospecto"] for f in filas} == {8406}


class TestLaConsultaNoComparaLaCadenaCompleta:
    """La mitad que mira el código, porque el doble no puede probar la intención."""

    @property
    def _consultas(self) -> list[str]:
        fuente = inspect.getsource(informes_nutricion_repository)
        return re.findall(r'"(SELECT [^"]+)"', fuente, re.IGNORECASE)

    @property
    def _condiciones(self) -> list[str]:
        """Las condiciones del `WHERE`, que se arman aparte del `SELECT`."""
        fuente = inspect.getsource(informes_nutricion_repository)
        return re.findall(r'"([a-z_]+ [<>=]{1,2} %\([a-z_]+\)s)"', fuente)

    def test_la_comparacion_de_expiracion_usa_el_prefijo(self):
        sobre_expiracion = [c for c in self._condiciones if "demo_expiracion" in c]

        assert sobre_expiracion, "no se encontro la condicion de expiracion"
        for condicion in sobre_expiracion:
            # El nombre del parámetro es parte de la defensa: `prefijo_hoy`
            # obliga a quien lo lea a preguntarse por qué no es un instante.
            assert "%(prefijo_hoy)s" in condicion, condicion

    def test_no_se_compara_contra_un_instante_completo(self):
        for condicion in self._condiciones:
            if "demo_expiracion" not in condicion:
                continue
            assert "%(ahora)s" not in condicion
            assert "%(instante)s" not in condicion
            assert "%(expiracion)s" not in condicion

    def test_la_consulta_de_demos_enumera_sus_columnas(self):
        demos = next(c for c in self._consultas if "demo_expiracion" in c)

        assert not re.search(r"SELECT\s+\*", demos, re.IGNORECASE)
        assert "gmail" not in demos and "telefono" not in demos
