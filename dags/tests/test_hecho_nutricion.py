"""T044, T045, T054 — nutricion: un aviso ignorado no es latencia cero."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_interaccion_demo import construir as construir_demo  # noqa: E402
from lib.hechos.hecho_notificacion_ventas import construir as construir_aviso  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0, tzinfo=timezone.utc)
T0 = 1786622400000
T1 = T0 + 120_000


def _dim(idp=1):
    return {"idprospecto": idp, "empresa": "Acme", "canal": "Web"}


class TestLaDemoNoCopiaMetadata:
    def test_seccion_ausente_sigue_ausente(self):
        filas = construir_demo(
            {
                "interacciones": [
                    {
                        "idinteraccion": 1,
                        "idprospecto": 1,
                        "tipo_evento": "inicio_sesion",
                        "seccion": None,
                        "timestamp_evento": T0,
                    }
                ],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )
        assert filas[0]["seccion"] is None
        assert "metadata" not in filas[0]


class TestUnAvisoIgnoradoNoEsReaccionInstantanea:
    def test_sin_avance_posterior_la_duracion_va_ausente(self):
        filas = construir_aviso(
            {
                "notificaciones": [
                    {
                        "idnotificacion": 1,
                        "id_prospecto": 1,
                        "regladisparada": "inactividad",
                        "canal": "email",
                        "fechahoranotificacion": T0,
                    }
                ],
                "transiciones": [],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )

        assert filas[0]["hubo_avance"] == 0
        assert filas[0]["segundos_a_reaccion"] is None
        assert filas[0]["segundos_a_reaccion"] != 0

    def test_un_avance_posterior_si_cuenta(self):
        filas = construir_aviso(
            {
                "notificaciones": [
                    {
                        "idnotificacion": 1,
                        "id_prospecto": 1,
                        "regladisparada": "inactividad",
                        "canal": "email",
                        "fechahoranotificacion": T0,
                    }
                ],
                "transiciones": [
                    {
                        "id_prospecto": 1,
                        "etapa_anterior": "Contactado",
                        "etapa_nueva": "Calificado",
                        "fecha_transicion": T1,
                    }
                ],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )

        assert filas[0]["hubo_avance"] == 1
        assert filas[0]["segundos_a_reaccion"] == 120

    def test_un_retroceso_no_cuenta_como_reaccion(self):
        filas = construir_aviso(
            {
                "notificaciones": [
                    {
                        "idnotificacion": 1,
                        "id_prospecto": 1,
                        "regladisparada": "inactividad",
                        "canal": "email",
                        "fechahoranotificacion": T0,
                    }
                ],
                "transiciones": [
                    {
                        "id_prospecto": 1,
                        "etapa_anterior": "Calificado",
                        "etapa_nueva": "Contactado",
                        "fecha_transicion": T1,
                    }
                ],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )

        assert filas[0]["hubo_avance"] == 0
        assert filas[0]["segundos_a_reaccion"] is None
