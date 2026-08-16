"""Reconstrucción del histórico desde una bitácora del origen (T032).

Las tres primeras pruebas usan casos **tomados de `Fact_HistorialAccesoPartner`**,
no inventados: la bitácora real contiene eventos que no cambian nada y eventos
duplicados a milisegundos, y ambos producen versiones falsas si se toman al pie
de la letra.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.reconstruccion import (  # noqa: E402
    divergencias,
    reconstruir,
    reconstruir_entidad,
)
from lib.dimensiones.versionado import INICIO_DESCONOCIDO  # noqa: E402

AHORA = datetime(2026, 8, 14, 12, 0)


def _evento(anterior, nuevo, instante, idpartner=1):
    return {
        "idpartner": idpartner,
        "estado_anterior": anterior,
        "estado_nuevo": nuevo,
        "fecha_cambio": instante,
    }


def _reconstruir(eventos):
    return reconstruir_entidad(
        eventos,
        campo_anterior="estado_anterior",
        campo_nuevo="estado_nuevo",
        campo_instante="fecha_cambio",
        ahora=AHORA,
    )


class TestTrampasDeLaBitacoraReal:
    def test_un_evento_que_no_cambia_nada_no_abre_version(self):
        # Caso real: `revocacion_credencial` con Activo -> Activo. Se registró un
        # suceso, pero el atributo versionado no se movió.
        versiones = _reconstruir([_evento("Activo", "Activo", datetime(2026, 3, 1))])

        assert len(versiones) == 1
        assert versiones[0]["valor"] == "Activo"
        assert versiones[0]["es_vigente"] == 1

    def test_dos_eventos_duplicados_producen_una_sola_version(self):
        # Caso real: dos `desactivacion_por_cascada` del mismo partner con 46 ms
        # de diferencia y los mismos valores
        versiones = _reconstruir(
            [
                _evento("Activo", "Suspendido", datetime(2026, 3, 1, 10, 0, 0)),
                _evento("Activo", "Suspendido", datetime(2026, 3, 1, 10, 0, 0, 46000)),
            ]
        )

        assert len(versiones) == 2  # la inicial y la suspensión, no tres

    def test_la_version_anterior_al_primer_evento_no_declara_inicio_real(self):
        # Se conoce el valor de partida, pero no desde cuándo
        versiones = _reconstruir([_evento("Activo", "Suspendido", datetime(2026, 3, 1))])

        assert versiones[0]["valor"] == "Activo"
        assert versiones[0]["inicio_es_real"] == 0
        assert versiones[0]["valido_desde"] == INICIO_DESCONOCIDO


class TestCadenaDeCambios:
    def test_cada_cambio_abre_una_version_fechada(self):
        versiones = _reconstruir(
            [
                _evento("Basico", "Pro", datetime(2026, 3, 1)),
                _evento("Pro", "Enterprise", datetime(2026, 6, 1)),
            ]
        )

        assert [v["valor"] for v in versiones] == ["Basico", "Pro", "Enterprise"]
        assert [v["inicio_es_real"] for v in versiones] == [0, 1, 1]

    def test_solo_la_ultima_queda_vigente(self):
        versiones = _reconstruir(
            [
                _evento("Basico", "Pro", datetime(2026, 3, 1)),
                _evento("Pro", "Enterprise", datetime(2026, 6, 1)),
            ]
        )

        assert [v["es_vigente"] for v in versiones] == [0, 0, 1]
        assert versiones[-1]["valido_hasta"] is None

    def test_la_vigencia_es_continua(self):
        versiones = _reconstruir(
            [
                _evento("Basico", "Pro", datetime(2026, 3, 1)),
                _evento("Pro", "Enterprise", datetime(2026, 6, 1)),
            ]
        )

        for anterior, siguiente in zip(versiones, versiones[1:]):
            assert anterior["valido_hasta"] == siguiente["valido_desde"]

    def test_los_eventos_desordenados_se_ordenan_solos(self):
        # Pinot no garantiza orden de lectura, y una bitácora leída al revés
        # produciría una historia invertida sin que nada fallara
        versiones = _reconstruir(
            [
                _evento("Pro", "Enterprise", datetime(2026, 6, 1)),
                _evento("Basico", "Pro", datetime(2026, 3, 1)),
            ]
        )

        assert [v["valor"] for v in versiones] == ["Basico", "Pro", "Enterprise"]


class TestVariasEntidades:
    def test_cada_entidad_tiene_su_propia_historia(self):
        versiones = reconstruir(
            [
                _evento("Basico", "Pro", datetime(2026, 3, 1), idpartner=1),
                _evento("Activo", "Suspendido", datetime(2026, 4, 1), idpartner=2),
            ],
            clave_negocio="idpartner",
            campo_anterior="estado_anterior",
            campo_nuevo="estado_nuevo",
            campo_instante="fecha_cambio",
            ahora=AHORA,
        )

        del_uno = [v for v in versiones if v["idpartner"] == 1]
        del_dos = [v for v in versiones if v["idpartner"] == 2]

        assert [v["valor"] for v in del_uno] == ["Basico", "Pro"]
        assert [v["valor"] for v in del_dos] == ["Activo", "Suspendido"]

    def test_cada_version_recibe_una_clave_sustituta_distinta(self):
        versiones = reconstruir(
            [_evento("Basico", "Pro", datetime(2026, 3, 1))],
            clave_negocio="idpartner",
            campo_anterior="estado_anterior",
            campo_nuevo="estado_nuevo",
            campo_instante="fecha_cambio",
            ahora=AHORA,
        )

        assert len({v["sk"] for v in versiones}) == len(versiones)


class TestDivergencias:
    def test_detecta_una_bitacora_incompleta(self):
        # Una bitácora a la que le falta el último cambio produce una historia que
        # parece correcta y termina en un valor equivocado. Comprobar contra el
        # estado actual, que sí es fiable, es la forma barata de detectarlo.
        versiones = reconstruir(
            [_evento("Basico", "Pro", datetime(2026, 3, 1))],
            clave_negocio="idpartner",
            campo_anterior="estado_anterior",
            campo_nuevo="estado_nuevo",
            campo_instante="fecha_cambio",
            ahora=AHORA,
        )

        encontradas = divergencias(versiones, {1: "Enterprise"}, clave_negocio="idpartner")

        assert encontradas == [{"idpartner": 1, "reconstruido": "Pro", "actual": "Enterprise"}]

    def test_no_denuncia_nada_cuando_coinciden(self):
        versiones = reconstruir(
            [_evento("Basico", "Pro", datetime(2026, 3, 1))],
            clave_negocio="idpartner",
            campo_anterior="estado_anterior",
            campo_nuevo="estado_nuevo",
            campo_instante="fecha_cambio",
            ahora=AHORA,
        )

        assert divergencias(versiones, {1: "Pro"}, clave_negocio="idpartner") == []
