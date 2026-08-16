"""T037 — el refinamiento y `dias_restantes` usan **el mismo instante** (research D3, D5).

Es la razón real de inyectar el reloj aquí, más allá de poder probarlo: si el
prefiltro usara el reloj del broker de Pinot y el cálculo el del proceso, una
demo podría aparecer con «0 días restantes» habiendo sido ya descartada, o
mostrarse como vigente una que el refinamiento debería haber quitado.

Un solo `ahora` para los dos elimina la clase entera de fallo.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from apps.ventas_crm.services.informes_nutricion_service import InformesNutricionService
from apps.ventas_crm.tests.conftest import AHORA, GERENTE_A
from core.informes.acotamiento import ACOTADO_PROPIOS, ACOTADO_TODOS, Acotamiento

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)
ACOTADO_A = Acotamiento(titular=GERENTE_A, alcance=ACOTADO_PROPIOS)


@pytest.fixture
def servicio(mock_pinot, reloj_fijo):
    return InformesNutricionService(ahora=reloj_fijo)


class TestElRefinamientoDescartaLoExpirado:
    def test_la_expirada_hoy_mas_temprano_no_aparece(self, servicio, demos_formato_mixto):
        # El prefiltro por día la deja pasar; el refinamiento debe quitarla.
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        assert "Demo Expirada" not in {f["empresa"] for f in pagina.filas}

    def test_la_que_no_tiene_fecha_no_se_considera_activa(
        self, servicio, demos_formato_mixto
    ):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        assert "Demo SinFecha" not in {f["empresa"] for f in pagina.filas}

    def test_las_tres_vigentes_si_aparecen(self, servicio, demos_formato_mixto):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        empresas = {f["empresa"] for f in pagina.filas}
        assert {"Demo Zeta", "Demo Offset", "Demo SinZona"} <= empresas


class TestDiasRestantes:
    def test_es_exacto_para_el_instante_inyectado(self, servicio, demos_formato_mixto):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f["dias_restantes"] for f in pagina.filas}

        # Las tres expiran en 3 días exactos desde `AHORA`.
        assert por_empresa["Demo Zeta"] == 3
        assert por_empresa["Demo Offset"] == 3
        assert por_empresa["Demo SinZona"] == 3

    def test_los_tres_formatos_dan_el_mismo_numero(self, servicio, demos_formato_mixto):
        """Si no lo dieran, el parseo estaría tratando los sufijos distinto."""
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)
        dias = {
            f["dias_restantes"]
            for f in pagina.filas
            if f["empresa"] in ("Demo Zeta", "Demo Offset", "Demo SinZona")
        }

        assert len(dias) == 1

    def test_una_demo_que_vence_en_horas_tiene_un_dia_no_cero(
        self, mock_pinot, gerentes_sembrados, reloj_fijo
    ):
        """Un `0` se leería como «ya venció», que es lo contrario."""
        from conftest import PINOT_STORE
        from apps.ventas_crm.tests.conftest import _prospecto

        en_seis_horas = (AHORA + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8460, empresa="Demo Urgente", idusuario=GERENTE_A,
                       expiracion=en_seis_horas)
        )

        pagina = InformesNutricionService(ahora=reloj_fijo).demos_activas(
            acotamiento=SIN_ACOTAR, limit=500
        )
        fila = next(f for f in pagina.filas if f["empresa"] == "Demo Urgente")

        assert fila["dias_restantes"] == 1

    def test_no_depende_del_reloj_del_sistema(self, mock_pinot, demos_formato_mixto):
        un_dia_despues = InformesNutricionService(ahora=lambda: AHORA + timedelta(days=1))

        pagina = un_dia_despues.demos_activas(acotamiento=SIN_ACOTAR, limit=500)
        por_empresa = {f["empresa"]: f["dias_restantes"] for f in pagina.filas}

        assert por_empresa["Demo Zeta"] == 2


class TestElMismoInstanteParaAmbosPasos:
    def test_una_demo_que_expira_justo_ahora_se_descarta_y_no_sale_con_cero(
        self, mock_pinot, gerentes_sembrados
    ):
        """El caso frontera donde los dos pasos podrían discrepar.

        Si el refinamiento usara un instante y el cálculo otro, esta demo
        aparecería con `dias_restantes` calculado sobre un instante en el que ya
        había expirado.
        """
        from conftest import PINOT_STORE
        from apps.ventas_crm.tests.conftest import _prospecto

        justo_ahora = AHORA.strftime("%Y-%m-%dT%H:%M:%SZ")
        PINOT_STORE["Dim_Prospecto"].append(
            _prospecto(8470, empresa="Demo Justo", idusuario=GERENTE_A,
                       expiracion=justo_ahora)
        )

        pagina = InformesNutricionService(ahora=lambda: AHORA).demos_activas(
            acotamiento=SIN_ACOTAR, limit=500
        )

        assert "Demo Justo" not in {f["empresa"] for f in pagina.filas}

    def test_ninguna_fila_devuelta_tiene_dias_restantes_no_positivo(
        self, servicio, demos_formato_mixto
    ):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        assert all(f["dias_restantes"] >= 1 for f in pagina.filas)


class TestFormaDeLaFila:
    def test_la_expiracion_se_devuelve_normalizada(self, servicio, demos_formato_mixto):
        # El consumidor no tiene por qué lidiar con los tres formatos del origen.
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        sufijos = {f["expiracion"][-6:] for f in pagina.filas}
        assert sufijos == {"+00:00"}

    def test_no_expone_identificadores_ni_contacto(self, servicio, demos_formato_mixto):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        for fila in pagina.filas:
            assert set(fila) == {
                "empresa", "nombre_contacto", "ejecutivo", "expiracion", "dias_restantes"
            }

    def test_resuelve_el_ejecutivo(self, servicio, demos_formato_mixto):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        fila = next(f for f in pagina.filas if f["empresa"] == "Demo Zeta")
        assert fila["ejecutivo"] == "Lucia Ramos"


class TestAcotamiento:
    def test_el_gerente_solo_ve_sus_demos(self, servicio, demos_formato_mixto):
        pagina = servicio.demos_activas(acotamiento=ACOTADO_A, limit=500)

        assert "Demo Ajena" not in {f["empresa"] for f in pagina.filas}

    def test_sin_acotar_se_ven_las_de_ambos(self, servicio, demos_formato_mixto):
        pagina = servicio.demos_activas(acotamiento=SIN_ACOTAR, limit=500)

        assert "Demo Ajena" in {f["empresa"] for f in pagina.filas}
