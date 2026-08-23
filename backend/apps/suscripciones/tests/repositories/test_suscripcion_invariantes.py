"""Invariantes al escribir una suscripción — decisión #44.

El modelo analítico **rodeaba** estos defectos al leer: `motivo_cancelacion` solo
si canceló, `vigencia_inconsistente` marcada y no corregida, las tres formas de
«sin motivo» unificadas a ausencia. Eso sigue estando bien; lo que faltaba era
dejar de producirlos.
"""

from __future__ import annotations

import pytest

from core.repositories.suscripciones.suscripcion_repository import (
    SuscripcionRepository,
)


@pytest.mark.repository
class TestElMotivoDeCancelacionExigeCancelacion:
    def _crear(self, **extra):
        return SuscripcionRepository().create(
            {"idcliente": 1, "idplan": 1, "precio": 49.0, **extra}
        )

    def test_activa_when_llega_con_motivo_no_lo_guarda(self, mock_pinot, mock_kafka):
        """⛔ El origen llegó a tener una `Activa` con motivo «prueba fin de ciclo».

        Quien leyera el motivo sin mirar el estado la contaría como baja.
        """
        repo = SuscripcionRepository()
        creada = self._crear()

        guardada = repo.update(
            creada["id_suscripcion"],
            {"estado": "Activa", "motivocancelacion": "prueba fin de ciclo"},
        )

        assert guardada["motivocancelacion"] is None
        assert guardada["fechacancelacion"] is None

    def test_suspendida_when_arrastra_motivo_previo_se_limpia(
        self, mock_pinot, mock_kafka
    ):
        repo = SuscripcionRepository()
        creada = self._crear()
        repo.update(
            creada["id_suscripcion"],
            {"estado": "Cancelada", "motivocancelacion": "cierre de operaciones"},
        )

        # Vuelve a un estado que no es cancelación: el motivo no puede quedarse.
        reactivada = repo.update(creada["id_suscripcion"], {"estado": "Suspendida"})

        assert reactivada["motivocancelacion"] is None

    def test_cancelada_when_lleva_motivo_real_lo_conserva(self, mock_pinot, mock_kafka):
        repo = SuscripcionRepository()
        creada = self._crear()

        cancelada = repo.update(
            creada["id_suscripcion"],
            {"estado": "Cancelada", "motivocancelacion": "cierre de operaciones"},
        )

        assert cancelada["motivocancelacion"] == "cierre de operaciones"

    @pytest.mark.parametrize("vacio", ["", "null", "   "])
    def test_cancelada_when_el_motivo_viene_vacio_queda_ausente(
        self, mock_pinot, mock_kafka, vacio
    ):
        """Las tres formas de «sin motivo» que llegaron a convivir en el origen."""
        repo = SuscripcionRepository()
        creada = self._crear()

        cancelada = repo.update(
            creada["id_suscripcion"],
            {"estado": "Cancelada", "motivocancelacion": vacio},
        )

        assert cancelada["motivocancelacion"] is None


@pytest.mark.repository
class TestLaVigenciaNoPuedeNacerInvertida:
    def test_fecha_fin_anterior_al_inicio_when_se_escribe_se_rechaza(
        self, mock_pinot, mock_kafka
    ):
        repo = SuscripcionRepository()
        creada = repo.create({"idcliente": 1, "idplan": 1, "precio": 49.0})

        with pytest.raises(ValueError, match="vigencia invertida"):
            repo.update(
                creada["id_suscripcion"],
                {
                    "fecha_inicio": creada["fecha_inicio"],
                    "fecha_fin": creada["fecha_inicio"] - 1,
                },
            )

    def test_fila_ya_invertida_when_se_suspende_no_bloquea(
        self, mock_pinot, mock_kafka
    ):
        """⚠️ Una fila histórica invertida **no** puede bloquear la operación.

        El origen sigue cobrándola: descartarla perdería un ingreso real. La
        validación mira solo el cambio que se está escribiendo.
        """
        repo = SuscripcionRepository()
        creada = repo.create({"idcliente": 1, "idplan": 1, "precio": 49.0})
        # Se ensucia la fila por debajo, como si viniera así del origen.
        from conftest import PINOT_STORE

        for fila in PINOT_STORE["Fact_Suscripcion"]:
            if fila["id_suscripcion"] == creada["id_suscripcion"]:
                fila["fecha_fin"] = fila["fecha_inicio"] - 1000

        suspendida = repo.update(creada["id_suscripcion"], {"estado": "Suspendida"})

        assert suspendida["estado"] == "Suspendida"


@pytest.mark.repository
class TestLoQueNoSeToca:
    def test_cancelada_when_se_guarda_conserva_activo_true(
        self, mock_pinot, mock_kafka
    ):
        """⛔ RN-017: la suscripción sigue activa hasta `fecha_fin`.

        Una `Cancelada` con `activo = true` **no** es un defecto — el cliente usa
        lo que pagó—, y por eso `estado_derivado` del modelo no mira `activo`.
        «Corregirlo» rompería la regla.
        """
        repo = SuscripcionRepository()
        creada = repo.create({"idcliente": 1, "idplan": 1, "precio": 49.0})

        cancelada = repo.update(creada["id_suscripcion"], {"estado": "Cancelada"})

        assert cancelada["activo"] is True
