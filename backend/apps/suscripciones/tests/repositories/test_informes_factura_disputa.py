"""T029 — una factura en disputa **no cuenta como mora** (research D3).

`En disputa` significa que el cliente abrió un reclamo y el sistema **dejó de
reintentar el cargo**. Presentarla como mora induce exactamente la acción que la
regla quiere evitar: perseguir un cobro que está en discusión. Es el defecto que
corrigió el hallazgo B41.

Nótese que la disputada sembrada **también está vencida**: si el filtro mirara
solo la fecha, la incluiría. Es el caso que distingue una implementación
correcta de una que parece correcta.
"""

from __future__ import annotations

import pytest

from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A
from core.repositories.suscripciones.informes_facturacion_repository import (
    ESTADO_EN_DISPUTA,
    ESTADOS_EN_MORA,
    InformesFacturacionRepository,
)


@pytest.fixture
def repo(mock_pinot):
    return InformesFacturacionRepository()


class TestElFiltroDeVencidas:
    def test_devuelve_solo_la_fallida(self, repo, facturas_sembradas):
        filas = repo.facturas(limit=500, cuenta=CUENTA_A, vencidas_antes_de=AHORA_MS)

        assert [f["id_factura"] for f in filas] == ["FAC-202606-00000001"]

    def test_excluye_la_disputada_aunque_este_vencida(self, repo, facturas_sembradas):
        filas = repo.facturas(limit=500, cuenta=CUENTA_A, vencidas_antes_de=AHORA_MS)

        assert "FAC-202607-00000002" not in {f["id_factura"] for f in filas}, (
            "la factura en disputa aparece como mora: el sistema dejo de "
            "cobrarla a proposito y perseguirla es el defecto que corrigio B41"
        )

    def test_la_disputada_esta_vencida_de_verdad(self, repo, facturas_sembradas):
        """Si no lo estuviera, la prueba de arriba no demostraría nada."""
        filas = repo.facturas(limit=500, cuenta=CUENTA_A)
        disputada = next(
            f for f in filas if f["id_factura"] == "FAC-202607-00000002"
        )

        assert disputada["fecha_vencimiento"] < AHORA_MS
        assert disputada["estado_pago"] == ESTADO_EN_DISPUTA

    def test_excluye_tambien_las_pagadas(self, repo, facturas_sembradas):
        filas = repo.facturas(limit=500, cuenta=CUENTA_A, vencidas_antes_de=AHORA_MS)

        assert "FAC-202608-00000003" not in {f["id_factura"] for f in filas}


class TestLaDisputadaSigueApareciendo:
    def test_sin_el_filtro_de_vencidas_sale_con_su_estado(self, repo, facturas_sembradas):
        # No se esconde: se muestra con su estado propio, que es información.
        filas = repo.facturas(limit=500, cuenta=CUENTA_A)
        por_id = {f["id_factura"]: f for f in filas}

        assert por_id["FAC-202607-00000002"]["estado_pago"] == ESTADO_EN_DISPUTA

    def test_se_puede_filtrar_por_ese_estado(self, repo, facturas_sembradas):
        filas = repo.facturas(
            limit=500, cuenta=CUENTA_A, estado_pago=ESTADO_EN_DISPUTA
        )

        assert [f["id_factura"] for f in filas] == ["FAC-202607-00000002"]


class TestLaConstanteNoSeDuplica:
    def test_se_importa_del_departamento_que_la_define(self):
        """El valor lo define Partners y lo consume Suscripciones.

        Es una rareza del modelo, no de esta spec. Lo que no se hace es
        duplicar la constante: un literal copiado es un desajuste esperando.
        """
        from apps.partners.domain_constants import FACTURA_EN_DISPUTA

        assert ESTADO_EN_DISPUTA == FACTURA_EN_DISPUTA

    def test_la_disputa_no_esta_entre_los_estados_de_mora(self):
        assert ESTADO_EN_DISPUTA not in ESTADOS_EN_MORA

    def test_los_estados_de_mora_son_los_dos_esperados(self):
        assert set(ESTADOS_EN_MORA) == {"Pendiente", "Fallida"}


class TestSinDiasDeMora:
    def test_la_disputada_no_lleva_dias_de_mora(self, mock_pinot, facturas_sembradas):
        from apps.suscripciones.services.informes_facturacion_service import (
            InformesFacturacionService,
        )
        from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

        pagina = InformesFacturacionService(ahora=lambda: AHORA_MS).facturas(
            acotamiento=Acotamiento(titular=CUENTA_A, alcance=ACOTADO_TODOS), limit=500
        )
        por_numero = {f["numero_factura"]: f for f in pagina.filas}

        # `None` y no `0`: un `0` se leería como «vence hoy», y esta factura no
        # está venciendo — está detenida a propósito.
        assert "dias_mora" not in por_numero["0002"]

    def test_la_fallida_si_lo_lleva(self, mock_pinot, facturas_sembradas):
        from apps.suscripciones.services.informes_facturacion_service import (
            InformesFacturacionService,
        )
        from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

        pagina = InformesFacturacionService(ahora=lambda: AHORA_MS).facturas(
            acotamiento=Acotamiento(titular=CUENTA_A, alcance=ACOTADO_TODOS), limit=500
        )
        por_numero = {f["numero_factura"]: f for f in pagina.filas}

        assert por_numero["0001"]["dias_mora"] == 25

    def test_la_pagada_tampoco(self, mock_pinot, facturas_sembradas):
        from apps.suscripciones.services.informes_facturacion_service import (
            InformesFacturacionService,
        )
        from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

        pagina = InformesFacturacionService(ahora=lambda: AHORA_MS).facturas(
            acotamiento=Acotamiento(titular=CUENTA_A, alcance=ACOTADO_TODOS), limit=500
        )
        por_numero = {f["numero_factura"]: f for f in pagina.filas}

        assert "dias_mora" not in por_numero["0003"]
