"""T042 — las cuentas de baja siguen apareciendo, y ninguna fila se omite.

Dos garantías **negativas**, que son las difíciles de detectar cuando fallan:

1. **Una cuenta dada de baja sigue en el listado, con su razón social intacta.**
   La baja es lógica; la fila sobrevive con su historial. Excluirlas convertiría
   un informe de *ciclo de vida* en uno de cuentas vivas.

2. **Una cuenta cuyo propietario no resuelve no se omite.** Es la anomalía que
   el informe existe para mostrar. Si se descartara, el listado quedaría
   consistente e incompleto, y nada avisaría: la cuenta simplemente no estaría.

Las dos comparten forma: el fallo no produce error, produce **una ausencia**. Y
una ausencia solo se detecta si alguien sabía que ese dato debía estar.
"""

from __future__ import annotations

import pytest

from apps.cuentas_clientes.services.informes_cuenta_service import InformesCuentaService
from core.repositories.cuentas_clientes.cliente_repository import ESTADO_CLIENTE_BAJA


@pytest.fixture
def servicio(mock_pinot):
    return InformesCuentaService()


class TestLaBajaEsLogica:
    def test_una_cuenta_dada_de_baja_sigue_apareciendo(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500)

        assert any(f["razon_social"] == "Cuenta Cerrada S.A." for f in pagina.filas)

    def test_conserva_su_razon_social_intacta(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500)

        fila = next(f for f in pagina.filas if f["estado"] == ESTADO_CLIENTE_BAJA)
        assert fila["razon_social"] == "Cuenta Cerrada S.A."

    def test_se_puede_filtrar_por_ese_estado(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500, estado=ESTADO_CLIENTE_BAJA)

        assert len(pagina.filas) == 1
        assert pagina.filas[0]["razon_social"] == "Cuenta Cerrada S.A."

    def test_conserva_su_propietario(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500, estado=ESTADO_CLIENTE_BAJA)

        assert pagina.filas[0]["propietario"] == "Operador Test"


class TestPropietarioQueNoResuelve:
    def test_la_fila_no_se_omite(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500)

        assert any(f["razon_social"] == "Cuenta Huerfana S.A." for f in pagina.filas)

    def test_el_propietario_se_marca_como_no_resuelto(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500)

        fila = next(f for f in pagina.filas if f["razon_social"] == "Cuenta Huerfana S.A.")
        # `null` es una afirmación honesta —"no se sabe quién"—; omitir la fila
        # sería una mentira silenciosa.
        assert fila["propietario"] is None

    def test_todas_las_cuentas_sembradas_salen(self, servicio, cuentas_sembradas):
        pagina = servicio.cuentas_por_estado(limit=500)

        razones = {f["razon_social"] for f in pagina.filas}
        assert {
            "Cuenta Viva S.A.",
            "Cuenta Cerrada S.A.",
            "Cuenta Huerfana S.A.",
        } <= razones


class TestCamposAusentes:
    def test_una_fecha_de_contrato_ausente_es_null_no_la_epoca(
        self, servicio, cuentas_sembradas
    ):
        pagina = servicio.cuentas_por_estado(limit=500)

        fila = next(f for f in pagina.filas if f["razon_social"] == "Cuenta Huerfana S.A.")
        assert fila["fecha_inicio_contrato"] is None

    def test_una_fecha_presente_se_devuelve_como_fecha_no_como_instante(
        self, servicio, cuentas_sembradas
    ):
        # El contrato la declara `format: date`.
        pagina = servicio.cuentas_por_estado(limit=500)

        fila = next(f for f in pagina.filas if f["razon_social"] == "Cuenta Viva S.A.")
        assert fila["fecha_inicio_contrato"] == "2026-08-01"


class TestTransferenciaSinPropietarioAnterior:
    def test_la_asignacion_inicial_no_se_omite(self, servicio, transferencias_sembradas):
        """Una cuenta recién creada no tiene propietario "anterior"."""
        pagina = servicio.transferencias_propiedad(limit=500)

        inicial = [f for f in pagina.filas if f["propietario_anterior"] is None]
        assert len(inicial) == 1
        assert inicial[0]["propietario_nuevo"] == "Admin Sistema"
