"""Lecturas de cascada de la bitacora (T010).

Son las que sostienen la reactivacion selectiva: si devuelven de mas, se
resucita una credencial comprometida; si devuelven de menos, el partner se queda
sin credenciales que si le correspondian.
"""

from __future__ import annotations

import pytest

from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.repository]


def _evento(idhistorial, tipo, *, idcredencial=-1, fecha=100, idpartner=1):
    PINOT_STORE["Fact_HistorialAccesoPartner"].append({
        "idhistorial": idhistorial,
        "idpartner": idpartner,
        "idcredencial": idcredencial,
        "tipo_cambio": tipo,
        "ejecutado_por": "Sistema",
        "motivo": "",
        "estado_anterior": "Activo",
        "estado_nuevo": "Suspendido",
        "fecha_cambio": fecha,
        "fecha_actualizacion": fecha,
    })


class TestUltimaSuspension:
    def test_encuentra_la_suspension_mas_reciente(self, mock_pinot, mock_kafka):
        # Arrange
        _evento(1, "suspension_automatica", fecha=100)
        _evento(2, "reactivacion", fecha=200)
        _evento(3, "suspension_manual", fecha=300)

        # Act
        evento = HistorialAccesoRepository().ultima_suspension(1)

        # Assert
        assert evento["idhistorial"] == 3

    def test_sin_suspensiones_devuelve_none(self, mock_pinot, mock_kafka):
        # Arrange
        _evento(1, "registro", fecha=100)

        # Act / Assert
        assert HistorialAccesoRepository().ultima_suspension(1) is None


class TestCredencialesDeLaUltimaCascada:
    def test_devuelve_las_del_ciclo_vigente(self, mock_pinot, mock_kafka):
        # Arrange
        _evento(1, "desactivacion_por_cascada", idcredencial=101, fecha=100)
        _evento(2, "desactivacion_por_cascada", idcredencial=102, fecha=100)
        _evento(3, "suspension_automatica", fecha=100)

        # Act
        ids = HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1)

        # Assert
        assert sorted(ids) == [101, 102]

    def test_NO_arrastra_las_de_una_suspension_anterior(self, mock_pinot, mock_kafka):
        """Restituir credenciales de un ciclo viejo devolvería a la vida algo
        que ya no correspondía: la reactivación es del ÚLTIMO corte."""
        # Arrange — ciclo antiguo con la 900, ciclo nuevo con la 101
        _evento(1, "desactivacion_por_cascada", idcredencial=900, fecha=100)
        _evento(2, "suspension_automatica", fecha=100)
        _evento(3, "reactivacion", fecha=200)
        _evento(4, "desactivacion_por_cascada", idcredencial=101, fecha=300)
        _evento(5, "suspension_manual", fecha=300)

        # Act
        ids = HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1)

        # Assert
        assert ids == [101]
        assert 900 not in ids

    def test_ignora_las_revocaciones_del_partner(self, mock_pinot, mock_kafka):
        """🎯 `revocacion_credencial` y `desactivacion_por_cascada` son tipos
        distintos justamente para esto."""
        # Arrange
        _evento(1, "revocacion_credencial", idcredencial=103, fecha=100)
        _evento(2, "desactivacion_por_cascada", idcredencial=101, fecha=200)
        _evento(3, "suspension_automatica", fecha=200)

        # Act
        ids = HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1)

        # Assert
        assert ids == [101]
        assert 103 not in ids

    def test_sin_suspension_previa_devuelve_lista_vacia(self, mock_pinot, mock_kafka):
        # Arrange
        _evento(1, "registro", fecha=100)

        # Act / Assert
        assert HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1) == []

    def test_encuentra_la_cascada_aunque_el_MILISEGUNDO_haya_avanzado(
        self, mock_pinot, mock_kafka
    ):
        """🎯 Regresión de un fallo real, detectado por la suite completa.

        Las filas de cascada se escriben ANTES que el evento de suspensión. La
        primera versión anclaba el corte en `fecha_cambio` de la suspensión, así
        que si el reloj avanzaba un milisegundo entre medias las filas quedaban
        «antes del corte» y se descartaban: **la reactivación no restituía nada,
        en silencio**. Solo fallaba con la máquina cargada.

        Aquí se fuerza ese desfase: cascada en 100, suspensión en 101.
        """
        # Arrange
        _evento(1, "desactivacion_por_cascada", idcredencial=101, fecha=100)
        _evento(2, "desactivacion_por_cascada", idcredencial=102, fecha=100)
        _evento(3, "suspension_automatica", fecha=101)

        # Act
        ids = HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1)

        # Assert
        assert sorted(ids) == [101, 102]

    def test_una_reactivacion_previa_cierra_el_ciclo_anterior(
        self, mock_pinot, mock_kafka
    ):
        """El límite hacia atrás no es solo otra suspensión: una reactivación
        también cierra el ciclo. Sin esto se arrastrarían credenciales de un
        corte ya resuelto."""
        # Arrange
        _evento(1, "desactivacion_por_cascada", idcredencial=900, fecha=100)
        _evento(2, "reactivacion", fecha=200)
        _evento(3, "desactivacion_por_cascada", idcredencial=101, fecha=300)
        _evento(4, "suspension_manual", fecha=301)

        # Act
        ids = HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1)

        # Assert
        assert ids == [101]

    def test_descarta_el_centinela(self, mock_pinot, mock_kafka):
        """Una fila de cascada con `-1` sería un error de escritura; activar la
        credencial «-1» no tendría sentido."""
        # Arrange
        _evento(1, "desactivacion_por_cascada", idcredencial=-1, fecha=100)
        _evento(2, "suspension_automatica", fecha=100)

        # Act / Assert
        assert HistorialAccesoRepository().credenciales_de_la_ultima_cascada(1) == []


class TestInmutabilidad:
    def test_el_repositorio_no_expone_update_ni_delete(self):
        """RN-PAC-013 — no es una convención que haya que recordar: es una
        capacidad que no existe."""
        assert not hasattr(HistorialAccesoRepository, "update")
        assert not hasattr(HistorialAccesoRepository, "delete")
