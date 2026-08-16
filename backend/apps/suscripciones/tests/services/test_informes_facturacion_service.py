"""T031 — `dias_mora` y `dias_para_caducar` con instante inyectado.

Los dos dependen del ahora, que no es un dato de la tabla. Con el reloj real
estas pruebas solo podrían comprobar «que devuelve algún número», y el número es
lo que decide si alguien persigue un cobro o renueva una tarjeta.
"""

from __future__ import annotations

import pytest

from apps.suscripciones.services.informes_facturacion_service import (
    InformesFacturacionService,
)
from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A, CUENTA_B, DIA_MS
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)


@pytest.fixture
def servicio(mock_pinot, reloj_fijo):
    return InformesFacturacionService(ahora=reloj_fijo)


def _por_numero(pagina):
    return {f["numero_factura"]: f for f in pagina.filas}


class TestDiasMora:
    def test_es_exacto_para_el_instante_inyectado(self, servicio, facturas_sembradas):
        pagina = servicio.facturas(acotamiento=SIN_ACOTAR, limit=500)

        # Venció hace 25 días.
        assert _por_numero(pagina)["0001"]["dias_mora"] == 25

    def test_no_depende_del_reloj_del_sistema(self, mock_pinot, facturas_sembradas):
        diez_dias_despues = InformesFacturacionService(
            ahora=lambda: AHORA_MS + 10 * DIA_MS
        )

        pagina = diez_dias_despues.facturas(acotamiento=SIN_ACOTAR, limit=500)

        assert _por_numero(pagina)["0001"]["dias_mora"] == 35

    def test_una_factura_no_vencida_no_lleva_mora(self, servicio, facturas_sembradas):
        pagina = servicio.facturas(acotamiento=SIN_ACOTAR, limit=500)

        assert "dias_mora" not in _por_numero(pagina)["0004"]

    def test_la_clave_falta_en_vez_de_valer_cero(self, servicio, facturas_sembradas):
        # Un `0` se leería como «vence hoy» y pondría en la misma línea un cobro
        # urgente y uno que no lo es.
        pagina = servicio.facturas(acotamiento=SIN_ACOTAR, limit=500)

        for numero in ("0002", "0003", "0004"):
            assert "dias_mora" not in _por_numero(pagina)[numero]


class TestDiasParaCaducar:
    def test_es_exacto_para_el_instante_inyectado(self, servicio, metodos_pago_sembrados):
        pagina = servicio.metodos_de_pago(acotamiento=SIN_ACOTAR, limit=500)
        por_digitos = {f["ultimos_digitos"]: f for f in pagina.filas}

        assert por_digitos["4242"]["dias_para_caducar"] == 10
        assert por_digitos["9999"]["dias_para_caducar"] == 200

    def test_no_depende_del_reloj_del_sistema(self, mock_pinot, metodos_pago_sembrados):
        cinco_dias_despues = InformesFacturacionService(
            ahora=lambda: AHORA_MS + 5 * DIA_MS
        )

        pagina = cinco_dias_despues.metodos_de_pago(acotamiento=SIN_ACOTAR, limit=500)
        por_digitos = {f["ultimos_digitos"]: f for f in pagina.filas}

        assert por_digitos["4242"]["dias_para_caducar"] == 5

    def test_uno_ya_caducado_no_da_negativo(self, mock_pinot, cuentas_y_planes):
        from conftest import PINOT_STORE
        from apps.suscripciones.tests.conftest import TOKEN_PASARELA

        PINOT_STORE["Dim_MetodoPago"].append(
            {"idmetodopago": 7699, "idcliente": CUENTA_A, "tipo": "tarjeta",
             "tokenpasarela": TOKEN_PASARELA, "ultimosdigitos": "0000",
             "activo": True, "fechaexpiracion": AHORA_MS - 30 * DIA_MS,
             "fecha_actualizacion": AHORA_MS}
        )

        pagina = InformesFacturacionService(ahora=lambda: AHORA_MS).metodos_de_pago(
            acotamiento=SIN_ACOTAR, limit=500
        )
        por_digitos = {f["ultimos_digitos"]: f for f in pagina.filas}

        # `0` y no un número negativo: «ya caducó» no es «caduca en -30 días».
        assert por_digitos["0000"]["dias_para_caducar"] == 0


class TestTipoDeDocumento:
    def test_una_factura_normal_es_un_cargo(self, servicio, facturas_sembradas):
        pagina = servicio.facturas(acotamiento=SIN_ACOTAR, limit=500)

        assert all(f["tipo_documento"] == "cargo" for f in pagina.filas)

    def test_una_nota_de_credito_se_distingue(self, mock_pinot, facturas_sembradas):
        """research D6 — hoy la operación no las emite; se expone para cuando lo haga."""
        from conftest import PINOT_STORE

        PINOT_STORE["Fact_Factura"].append(
            {"id_factura": "NC-202608-00000001", "id_cliente": CUENTA_A,
             "id_suscripcion": 7001, "idmetodopago": 7601, "numero_factura": "NC01",
             "periodo": "2026-08", "estado_pago": "Pagada", "tipo": "nota",
             "es_nota_credito": True, "id_factura_original": "FAC-202606-00000001",
             "motivo_anulacion": "error de facturacion", "activo": True,
             "reintentos": 0, "monto_base": -100.0, "impuestos": -12.0,
             "monto_total": -112.0, "fecha_emision": AHORA_MS,
             "fecha_vencimiento": AHORA_MS, "fecha_actualizacion": AHORA_MS}
        )

        pagina = InformesFacturacionService(ahora=lambda: AHORA_MS).facturas(
            acotamiento=SIN_ACOTAR, limit=500
        )
        por_numero = _por_numero(pagina)

        assert por_numero["NC01"]["tipo_documento"] == "nota_credito"
        assert por_numero["0001"]["tipo_documento"] == "cargo"


class TestFormaDeLaFila:
    def test_no_expone_identificadores(self, servicio, facturas_sembradas):
        pagina = servicio.facturas(acotamiento=SIN_ACOTAR, limit=500)

        for fila in pagina.filas:
            assert "id_factura" not in fila
            assert "id_cliente" not in fila

    def test_resuelve_la_cuenta(self, servicio, facturas_sembradas):
        pagina = servicio.facturas(acotamiento=SIN_ACOTAR, limit=500)

        assert all(f["cuenta"] for f in pagina.filas)

    def test_el_acotamiento_se_aplica(self, servicio, facturas_sembradas):
        pagina = servicio.facturas(
            acotamiento=Acotamiento(titular=CUENTA_B, alcance="propios"), limit=500
        )

        assert {f["cuenta"] for f in pagina.filas} == {"Transportes Beltran Ltda."}
