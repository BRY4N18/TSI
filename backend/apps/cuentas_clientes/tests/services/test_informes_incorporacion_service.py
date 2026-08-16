"""T031 — la antigüedad, calculada con un instante inyectado (research D5).

Sin inyectar el reloj, estas pruebas sólo podrían comprobar «que devuelve algún
número», y el número es justamente lo que importa: es lo que ordena la bandeja y
lo que decide qué solicitudes se consideran atascadas.

El ancla es `reloj_fijo` = `BASE_MS + 10 días`, así que las tres solicitudes
sembradas llevan **10, 5 y 1 días** esperando.
"""

from __future__ import annotations

import pytest

from apps.cuentas_clientes.services.informes_incorporacion_service import (
    DIA_MS,
    InformesIncorporacionService,
)
from apps.cuentas_clientes.tests.conftest import BASE_MS


@pytest.fixture
def servicio(mock_pinot, reloj_fijo):
    return InformesIncorporacionService(ahora=reloj_fijo)


class TestDiasTranscurridos:
    def test_son_exactos_para_el_instante_inyectado(
        self, servicio, solicitudes_pendientes_sembradas
    ):
        pagina = servicio.solicitudes_pendientes(limit=500)
        por_razon = {f["razon_social"]: f["dias_transcurridos"] for f in pagina.filas}

        assert por_razon["Aseguradora Norte S.A."] == 10
        assert por_razon["Municipio del Valle"] == 5
        assert por_razon["Grúas del Sur Ltda."] == 1

    def test_no_dependen_del_reloj_del_sistema(
        self, mock_pinot, solicitudes_pendientes_sembradas
    ):
        """Dos instantes distintos dan resultados distintos y predecibles."""
        un_dia_despues = InformesIncorporacionService(
            ahora=lambda: BASE_MS + 11 * DIA_MS
        )

        pagina = un_dia_despues.solicitudes_pendientes(limit=500)
        por_razon = {f["razon_social"]: f["dias_transcurridos"] for f in pagina.filas}

        assert por_razon["Aseguradora Norte S.A."] == 11

    def test_una_fecha_ausente_da_none_no_cero(self, mock_pinot, reloj_fijo):
        from conftest import PINOT_STORE
        from core.pinot.tiempo import SIN_FECHA
        from core.repositories.cuentas_clientes.cliente_repository import (
            ESTADO_CLIENTE_PENDIENTE,
        )

        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 7500,
                "razon_social": "Sin Fecha S.A.",
                "tipo": "Corporativo",
                "estado": ESTADO_CLIENTE_PENDIENTE,
                "fecha_creacion": SIN_FECHA,
                "fecha_actualizacion": 0,
            }
        )

        pagina = InformesIncorporacionService(ahora=reloj_fijo).solicitudes_pendientes(
            limit=500
        )
        fila = next(f for f in pagina.filas if f["razon_social"] == "Sin Fecha S.A.")

        # `0` diría "llegó hoy", lo contrario de no saber cuándo llegó — y en una
        # bandeja ordenada por antigüedad la mandaría al final de la cola.
        assert fila["dias_transcurridos"] is None
        assert fila["fecha_solicitud"] is None


class TestDiasMinimoViajaAlWhere:
    """El filtro se traduce a fecha de corte y filtra en Pinot, no en Python.

    Aplicarlo después de paginar devolvería páginas incompletas sin avisar: el
    `LIMIT` ya habría recortado antes de descartar nada.
    """

    def test_corte_de_siete_dias_deja_solo_las_mas_antiguas(
        self, servicio, solicitudes_pendientes_sembradas
    ):
        pagina = servicio.solicitudes_pendientes(limit=500, dias_minimo=7)

        assert [f["razon_social"] for f in pagina.filas] == ["Aseguradora Norte S.A."]

    def test_corte_de_cinco_dias_incluye_la_de_exactamente_cinco(
        self, servicio, solicitudes_pendientes_sembradas
    ):
        # "Al menos 5 días" incluye la que lleva justo 5: el límite es inclusivo.
        pagina = servicio.solicitudes_pendientes(limit=500, dias_minimo=5)

        assert {f["razon_social"] for f in pagina.filas} == {
            "Aseguradora Norte S.A.",
            "Municipio del Valle",
        }

    def test_corte_de_cero_no_descarta_nada(
        self, servicio, solicitudes_pendientes_sembradas
    ):
        pagina = servicio.solicitudes_pendientes(limit=500, dias_minimo=0)

        assert len(pagina.filas) == 3

    def test_sin_corte_devuelve_todas(self, servicio, solicitudes_pendientes_sembradas):
        assert len(servicio.solicitudes_pendientes(limit=500).filas) == 3

    def test_la_traduccion_a_fecha_de_corte(self):
        corte = InformesIncorporacionService._fecha_de_corte(BASE_MS + 10 * DIA_MS, 7)

        assert corte == BASE_MS + 3 * DIA_MS

    def test_sin_dias_minimo_no_hay_corte(self):
        assert InformesIncorporacionService._fecha_de_corte(BASE_MS, None) is None


class TestOrdenDeBandeja:
    def test_lo_mas_antiguo_va_primero(self, servicio, solicitudes_pendientes_sembradas):
        pagina = servicio.solicitudes_pendientes(limit=500)
        dias = [f["dias_transcurridos"] for f in pagina.filas]

        assert dias == sorted(dias, reverse=True), (
            "una bandeja pone delante lo que lleva mas tiempo esperando"
        )


class TestOnboardingIncompleto:
    def test_solo_las_etapas_sin_completar(self, servicio, onboarding_sembrado):
        pagina = servicio.onboarding_incompleto(limit=500)

        etapas = [(f["razon_social"], f["etapa"]) for f in pagina.filas]
        assert ("Aseguradora Norte S.A.", "verificacion_documental") in etapas
        assert ("Municipio del Valle", "verificacion_documental") not in etapas

    def test_un_cliente_puede_tener_dos_etapas_pendientes(
        self, servicio, onboarding_sembrado
    ):
        # Es una fila por etapa, no por cliente: el listado responde "¿dónde
        # está detenido?", y un cliente puede estarlo en más de un sitio.
        pagina = servicio.onboarding_incompleto(limit=500)

        del_cliente = [
            f for f in pagina.filas if f["razon_social"] == "Aseguradora Norte S.A."
        ]
        assert len(del_cliente) == 2

    def test_resuelve_la_razon_social(self, servicio, onboarding_sembrado):
        pagina = servicio.onboarding_incompleto(limit=500)

        assert all(f["razon_social"] for f in pagina.filas)
        assert all("id_cliente" not in f for f in pagina.filas)

    def test_dias_detenido_es_exacto(self, servicio, onboarding_sembrado):
        pagina = servicio.onboarding_incompleto(limit=500)
        por_etapa = {f["etapa"]: f["dias_detenido"] for f in pagina.filas}

        assert por_etapa["verificacion_documental"] == 10
        assert por_etapa["configuracion_inicial"] == 6

    def test_filtra_por_etapa(self, servicio, onboarding_sembrado):
        pagina = servicio.onboarding_incompleto(limit=500, etapa="configuracion_inicial")

        assert [f["etapa"] for f in pagina.filas] == ["configuracion_inicial"]
