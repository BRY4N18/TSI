"""T038 — una demo **sin fecha de expiración no se considera activa**.

De las dos lecturas posibles de «sin fecha», la contraria —tratarla como vigente
sin límite— daría acceso perpetuo a una demo que nadie concedió, y la mostraría
al gerente como una oportunidad viva que hay que atender.

La ausencia se descarta en **los dos pasos**, y eso es deliberado: el prefiltro
la deja fuera porque no hay nada que comparar, y el refinamiento la descartaría
igualmente si llegara. Una sola de las dos defensas bastaría hoy; tenerlas
ambas significa que cambiar una no abre el agujero.
"""

from __future__ import annotations

import pytest

from apps.ventas_crm.demo_tokens import parse_iso_expiracion
from apps.ventas_crm.services.informes_nutricion_service import InformesNutricionService
from apps.ventas_crm.tests.conftest import AHORA, GERENTE_A, _prospecto
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento
from core.repositories.ventas_crm.informes_nutricion_repository import (
    InformesNutricionRepository,
)

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)
PREFIJO_HOY = AHORA.strftime("%Y-%m-%d")


@pytest.fixture
def repo(mock_pinot):
    return InformesNutricionRepository()


class TestElPrefiltroLaDescarta:
    def test_una_demo_con_expiracion_nula_no_pasa(self, repo, demos_formato_mixto):
        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)

        assert 8405 not in {f["idprospecto"] for f in filas}

    def test_una_con_cadena_vacia_tampoco(self, repo, mock_pinot, gerentes_sembrados):
        from conftest import PINOT_STORE

        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8480, empresa="Demo Vacia", idusuario=GERENTE_A, expiracion="")
        )

        filas = repo.demos_con_expiracion_desde(prefijo_hoy=PREFIJO_HOY, limit=500)

        assert 8480 not in {f["idprospecto"] for f in filas}


class TestElRefinamientoTambien:
    def test_una_expiracion_no_interpretable_se_descarta(
        self, mock_pinot, gerentes_sembrados, reloj_fijo
    ):
        """Aunque el prefiltro la dejara pasar, no se supone vigente."""
        from conftest import PINOT_STORE

        # Un texto que ordena por encima del prefijo de hoy y que el parseador
        # no puede interpretar: llega al refinamiento y debe caer allí.
        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8481, empresa="Demo Basura", idusuario=GERENTE_A,
                       expiracion="9999-no-es-una-fecha")
        )

        assert parse_iso_expiracion("9999-no-es-una-fecha") is None

        pagina = InformesNutricionService(ahora=reloj_fijo).demos_activas(
            acotamiento=SIN_ACOTAR, limit=500
        )

        assert "Demo Basura" not in {f["empresa"] for f in pagina.filas}

    def test_no_se_cae_por_un_dato_corrupto(
        self, mock_pinot, gerentes_sembrados, reloj_fijo, demos_formato_mixto
    ):
        # Un endpoint de solo lectura no puede reventar por una fila mala: las
        # demás siguen siendo información útil.
        from conftest import PINOT_STORE

        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8482, empresa="Demo Corrupta", idusuario=GERENTE_A,
                       expiracion="9999-basura")
        )

        pagina = InformesNutricionService(ahora=reloj_fijo).demos_activas(
            acotamiento=SIN_ACOTAR, limit=500
        )

        assert "Demo Zeta" in {f["empresa"] for f in pagina.filas}


class TestNoSeInventaUnaExpiracion:
    def test_ninguna_fila_devuelta_lleva_expiracion_nula(
        self, mock_pinot, demos_formato_mixto, reloj_fijo
    ):
        pagina = InformesNutricionService(ahora=reloj_fijo).demos_activas(
            acotamiento=SIN_ACOTAR, limit=500
        )

        assert all(f["expiracion"] for f in pagina.filas)

    def test_ni_dias_restantes_nulo(self, mock_pinot, demos_formato_mixto, reloj_fijo):
        pagina = InformesNutricionService(ahora=reloj_fijo).demos_activas(
            acotamiento=SIN_ACOTAR, limit=500
        )

        assert all(isinstance(f["dias_restantes"], int) for f in pagina.filas)
