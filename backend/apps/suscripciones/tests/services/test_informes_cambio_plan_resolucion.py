"""T038 — resolutor y motivo de rechazo son **ausentes** mientras siga pendiente.

Una solicitud pendiente todavía no la ha resuelto nadie. Devolver
`resuelta_por: null` junto a `estado: "Pendiente"` es redundante en el mejor caso
y contradictorio en el peor: invita a leer «alguien la resolvió y no sé quién».

Omitir la clave dice exactamente lo que pasa — aún no hay resolución.


⚠️ La espera se publica en **minutos**, no en días. Se medía con `// DIA_MS` y
las esperas reales —de 5 y 19 minutos— salían todas «0»: aritméticamente
correcto e inútil, porque la columna existe para ver cuál tarda. Los valores
esperados se escriben como `dias * 24 * 60` para que se siga leyendo el caso que
la prueba describe.
"""

from __future__ import annotations

import pytest

from apps.suscripciones.services.informes_cambio_plan_service import (
    InformesCambioPlanService,
)
from core.informes.acotamiento import ACOTADO_TODOS, Acotamiento

SIN_ACOTAR = Acotamiento(titular=None, alcance=ACOTADO_TODOS)


@pytest.fixture
def servicio(mock_pinot, reloj_fijo):
    return InformesCambioPlanService(ahora=reloj_fijo)


def _por_estado(pagina, estado):
    return [f for f in pagina.filas if f["estado"] == estado]


class TestLaPendiente:
    def test_no_trae_resolutor(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        for fila in _por_estado(pagina, "Pendiente"):
            assert "resuelta_por" not in fila

    def test_ni_motivo_de_rechazo(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        for fila in _por_estado(pagina, "Pendiente"):
            assert "motivo_rechazo" not in fila

    def test_ni_fecha_de_resolucion(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        for fila in _por_estado(pagina, "Pendiente"):
            assert "fecha_resolucion" not in fila

    def test_pero_si_su_motivo_de_solicitud(self, servicio, solicitudes_sembradas):
        # El motivo por el que se pidió el cambio existe desde el principio; no
        # es lo mismo que el motivo de rechazo.
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        pendientes = _por_estado(pagina, "Pendiente")
        assert all(f["motivo"] for f in pendientes)


class TestLaRechazada:
    def test_trae_su_resolutor(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        rechazada = _por_estado(pagina, "Rechazada")[0]
        assert rechazada["resuelta_por"] == "Ana Torres"

    def test_y_su_motivo_de_rechazo(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        rechazada = _por_estado(pagina, "Rechazada")[0]
        assert rechazada["motivo_rechazo"] == "mora pendiente"

    def test_y_su_fecha_de_resolucion(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        rechazada = _por_estado(pagina, "Rechazada")[0]
        assert rechazada["fecha_resolucion"] is not None


class TestDiasEspera:
    def test_es_exacto_para_el_instante_inyectado(self, servicio, solicitudes_sembradas):
        """T037 — la pendiente lleva 8 días esperando."""
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        pendientes = {f["cuenta"]: f for f in _por_estado(pagina, "Pendiente")}
        assert pendientes["Aseguradora Torres S.A."]["minutos_espera"] == 8 * 24 * 60

    def test_en_una_resuelta_se_mide_hasta_su_resolucion(
        self, servicio, solicitudes_sembradas
    ):
        """No hasta hoy.

        Si se midiera hasta hoy, una solicitud resuelta en un día seguiría
        acumulando «espera» para siempre y la bandeja mentiría sobre el tiempo
        de respuesta del equipo.
        """
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        rechazada = _por_estado(pagina, "Rechazada")[0]
        # Solicitada hace 3 días, resuelta hace 1: esperó 2.
        assert rechazada["minutos_espera"] == 2 * 24 * 60

    def test_no_depende_del_reloj_del_sistema(self, mock_pinot, solicitudes_sembradas):
        from apps.suscripciones.tests.conftest import AHORA_MS, DIA_MS

        cinco_dias_despues = InformesCambioPlanService(
            ahora=lambda: AHORA_MS + 5 * DIA_MS
        )

        pagina = cinco_dias_despues.solicitudes(acotamiento=SIN_ACOTAR, limit=500)
        pendientes = {f["cuenta"]: f for f in _por_estado(pagina, "Pendiente")}

        assert pendientes["Aseguradora Torres S.A."]["minutos_espera"] == 13 * 24 * 60

    def test_la_resuelta_no_se_mueve_con_el_reloj(self, mock_pinot, solicitudes_sembradas):
        from apps.suscripciones.tests.conftest import AHORA_MS, DIA_MS

        cinco_dias_despues = InformesCambioPlanService(
            ahora=lambda: AHORA_MS + 5 * DIA_MS
        )

        pagina = cinco_dias_despues.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        assert _por_estado(pagina, "Rechazada")[0]["minutos_espera"] == 2 * 24 * 60


class TestFormaYOrden:
    def test_resuelve_los_dos_planes(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        assert all(f["plan_actual"] and f["plan_solicitado"] for f in pagina.filas)

    def test_no_expone_identificadores(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)

        for fila in pagina.filas:
            assert "idsolicitud" not in fila
            assert "idplanactual" not in fila
            assert "idadminaprobador" not in fila

    def test_orden_ascendente_es_una_bandeja(self, servicio, solicitudes_sembradas):
        pagina = servicio.solicitudes(acotamiento=SIN_ACOTAR, limit=500)
        fechas = [f["fecha_solicitud"] for f in pagina.filas]

        assert fechas == sorted(fechas), "lo mas antiguo va primero: es una bandeja"
