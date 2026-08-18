"""T019, T020, T032 — el ciclo del prospecto, en logica pura.

La primera transicion no tiene duracion cero: va ausente, porque no habia etapa
anterior. Cero significaria «paso al instante».
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_asignacion_prospecto import construir as construir_asig  # noqa: E402
from lib.hechos.hecho_asignacion_prospecto import tipo_de  # noqa: E402
from lib.hechos.hecho_transicion_embudo import construir as construir_tr  # noqa: E402
from lib.hechos.hecho_transicion_embudo import es_avance  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0, tzinfo=timezone.utc)
T0 = 1786622400000  # 2026-08-17 12:00 UTC approx — tests only need order
T1 = T0 + 3_600_000
T2 = T1 + 3_600_000


def _dim(idp=1, empresa="Acme", canal="Web"):
    return {"idprospecto": idp, "empresa": empresa, "canal": canal, "tipo_organizacion": "Privada"}


def _tr(idt, idp, nueva, *, anterior=None, motivo=None, cuando=T1):
    return {
        "id_transicion": idt,
        "id_prospecto": idp,
        "etapa_anterior": anterior,
        "etapa_nueva": nueva,
        "motivo_perdida": motivo,
        "fecha_transicion": cuando,
    }


class TestLaPrimeraTransicionNoTieneDuracionCero:
    def test_la_duracion_va_ausente_no_en_cero(self):
        filas = construir_tr(
            {"transiciones": [_tr(1, 1, "Contactado", anterior=None, cuando=T0)], "dim_prospecto": [_dim()]},
            AHORA,
        )

        assert filas[0]["segundos_en_etapa_anterior"] is None
        assert filas[0]["segundos_en_etapa_anterior"] != 0

    def test_la_segunda_si_tiene_duracion(self):
        filas = construir_tr(
            {
                "transiciones": [
                    _tr(1, 1, "Contactado", anterior="Nuevo", cuando=T0),
                    _tr(2, 1, "Calificado", anterior="Contactado", cuando=T1),
                ],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )
        por_id = {f["idtransicion"]: f for f in filas}

        assert por_id[1]["segundos_en_etapa_anterior"] is None
        assert por_id[2]["segundos_en_etapa_anterior"] == 3600


class TestEsAvance:
    def test_subir_de_etapa_es_avance(self):
        assert es_avance("Nuevo", "Contactado") == 1

    def test_retroceder_no_es_avance(self):
        assert es_avance("Calificado", "Contactado") == 0

    def test_perderse_no_es_avance(self):
        assert es_avance("Negociación", "Perdido") == 0

    def test_ganar_es_avance(self):
        assert es_avance("Negociación", "Ganado") == 1


class TestLaAsignacion:
    def test_sin_previo_es_inicial(self):
        assert tipo_de(None) == "inicial"

    def test_con_previo_es_reasignacion(self):
        assert tipo_de(7) == "reasignación"

    def test_no_copia_automatica_ni_manual(self):
        filas = construir_asig(
            {
                "asignaciones": [
                    {
                        "idasignacion": 1,
                        "idprospecto": 1,
                        "idusuariogerenteanterior": None,
                        "idusuariogerenteactual": 7,
                        "tipoasignacion": "automatica",
                        "motivo": "entrada",
                        "fechahoraasignacion": T0,
                    }
                ],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )

        assert filas[0]["tipo_asignacion"] == "inicial"
        assert "automatica" not in filas[0].values()

    def test_sin_instante_no_entra(self):
        filas = construir_asig(
            {
                "asignaciones": [
                    {
                        "idasignacion": 1,
                        "idprospecto": 1,
                        "idusuariogerenteanterior": None,
                        "idusuariogerenteactual": 7,
                        "tipoasignacion": "manual",
                        "motivo": None,
                        "fechahoraasignacion": None,
                    }
                ],
                "dim_prospecto": [_dim()],
            },
            AHORA,
        )
        assert filas == []
