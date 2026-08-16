"""T008 — el versionado de región, y la confusión que el origen le tiende.

Dos bloques:

1. **El versionado**, que reutiliza `versionado.py` sin modificarlo: un cambio de
   estado abre versión y cierra la anterior; recargar sin cambios **no escribe
   nada**; la primera versión abre por la izquierda.
2. **La separación de los dos «estados»**, que es lo propio de esta dimensión.

Lógica pura: `construir` no consulta ni escribe.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_region import aplanar, construir  # noqa: E402
from lib.dimensiones.versionado import INICIO_DESCONOCIDO  # noqa: E402

AHORA = datetime(2026, 8, 16, 12, 0, 0)
DESPUES = datetime(2026, 9, 1, 12, 0, 0)

#: El origen, tal como está hoy: el ciclo de vida en la región y la geografía en
#: la tabla que se llama «estado de región».
REGIONES = [{"idregionoperativa": 1, "nombreregion": "Centro", "estadoregion": "Producción"}]
ESTADOS_GEO = [{"idestadoregion": 1, "estadoregion": "Ciudad de Mexico"}]
RELACION_GEO = [{"idregionoperativa": 1, "idestadoregion": 1}]


def _construir(regiones=None, vigentes=(), ahora=AHORA):
    return construir(
        regiones if regiones is not None else REGIONES,
        ESTADOS_GEO, RELACION_GEO, vigentes, ahora,
    )


class TestLosDosEstadosSonCosasDistintas:
    """⚠️ Lo propio de esta dimensión, y la trampa que el origen tiende.

    `Dim_RegionOperativa.estadoregion` es `Producción`; `Dim_EstadoRegion.
    estadoregion` es «Ciudad de Mexico». Tienen el mismo nombre de columna y
    significan cosas sin relación.
    """

    def test_el_ciclo_de_vida_sale_de_la_region(self):
        fila = aplanar(REGIONES, ESTADOS_GEO, RELACION_GEO)[0]

        assert fila["estado_ciclo_vida"] == "Producción"

    def test_la_geografia_no_se_toma_por_ciclo_de_vida(self):
        # El fallo que esto impide: un informe de «regiones publicadas» que
        # leyera la geografía devolvería todas o ninguna, y las dos respuestas
        # parecen plausibles.
        fila = aplanar(REGIONES, ESTADOS_GEO, RELACION_GEO)[0]

        assert fila["estado_geo"] == "Ciudad de Mexico"
        assert fila["estado_ciclo_vida"] != fila["estado_geo"]

    def test_una_region_sin_relacion_geografica_no_pierde_su_ciclo_de_vida(self):
        # La geografía es opcional; el ciclo de vida no. Perder la primera deja
        # la región sin ubicar; perder el segundo la saca de todos los informes.
        fila = aplanar(REGIONES, ESTADOS_GEO, [])[0]

        assert fila["estado_ciclo_vida"] == "Producción"
        assert fila["estado_geo"] is None

    def test_una_region_sin_estado_no_se_queda_vacia(self):
        sin_estado = [{"idregionoperativa": 9, "nombreregion": "X", "estadoregion": None}]

        assert aplanar(sin_estado, ESTADOS_GEO, RELACION_GEO)[0]["estado_ciclo_vida"] == "Desconocido"


class TestElVersionado:
    def test_la_primera_version_abre_por_la_izquierda(self):
        """No empieza el día de la carga.

        Si empezara hoy, todo hecho anterior quedaría sin versión que lo cubra y
        se atribuiría a «desconocido»: el modelo perdería de golpe la atribución
        de todo el histórico.
        """
        filas = _construir()

        assert len(filas) == 1
        assert filas[0]["valido_desde"] == INICIO_DESCONOCIDO.strftime("%Y-%m-%d %H:%M:%S")
        assert filas[0]["es_vigente"] == 1

    def test_la_primera_version_no_declara_un_inicio_real(self):
        """T006. El estado se conoce; desde cuándo, no.

        El origen guarda el estado presente y lo sobrescribe: no historiza el
        cambio. Marcarlo como real afirmaría que la región entró en producción el
        día de la primera carga.
        """
        assert _construir()[0]["inicio_es_real"] == 0

    def test_recargar_sin_cambios_no_escribe_nada(self):
        """Lo normal es que nada cambie, y el mecanismo no debe penalizarlo.

        Escribir una versión idéntica en cada corrida llenaría la dimensión de
        filas iguales y, peor, movería `valido_desde` cada día: la atribución
        histórica dejaría de funcionar sin que nada fallara.
        """
        vigente = dict(_construir()[0])
        vigente["valido_desde"] = INICIO_DESCONOCIDO

        assert _construir(vigentes=[vigente], ahora=DESPUES) == []

    def test_un_cambio_de_estado_abre_version_y_cierra_la_anterior(self):
        vigente = dict(_construir()[0])
        vigente["valido_desde"] = INICIO_DESCONOCIDO

        despublicada = [
            {"idregionoperativa": 1, "nombreregion": "Centro", "estadoregion": "Despublicada"}
        ]
        filas = _construir(regiones=despublicada, vigentes=[vigente], ahora=DESPUES)

        assert len(filas) == 2, "deberían escribirse la cerrada y la nueva"
        cerrada = next(f for f in filas if f["es_vigente"] == 0)
        nueva = next(f for f in filas if f["es_vigente"] == 1)

        assert cerrada["estado_ciclo_vida"] == "Producción"
        assert nueva["estado_ciclo_vida"] == "Despublicada"
        # Sin hueco ni solape: la anterior cierra donde la nueva abre.
        assert cerrada["valido_hasta"] == nueva["valido_desde"]

    def test_la_version_posterior_si_declara_un_inicio_real(self):
        # Ese cambio sí se observó, entre dos corridas: su fecha es un hecho.
        vigente = dict(_construir()[0])
        vigente["valido_desde"] = INICIO_DESCONOCIDO
        despublicada = [
            {"idregionoperativa": 1, "nombreregion": "Centro", "estadoregion": "Despublicada"}
        ]

        nueva = next(
            f for f in _construir(regiones=despublicada, vigentes=[vigente], ahora=DESPUES)
            if f["es_vigente"] == 1
        )

        assert nueva["valido_desde"] == DESPUES.strftime("%Y-%m-%d %H:%M:%S")

    def test_un_cambio_de_geografia_no_abre_version(self):
        """Solo `estado_ciclo_vida` versiona.

        La geografía de una región no cambia; si cambiara, sería otra región.
        Versionar por ella abriría versiones nuevas cada vez que alguien
        corrigiera una etiqueta, y la dimensión crecería sin que nada de negocio
        hubiera pasado.
        """
        vigente = dict(_construir()[0])
        vigente["valido_desde"] = INICIO_DESCONOCIDO

        otra_geo = [{"idestadoregion": 1, "estadoregion": "Estado de Mexico"}]
        filas = construir(REGIONES, otra_geo, RELACION_GEO, [vigente], DESPUES)

        assert filas == []

    def test_cada_version_tiene_su_propia_clave(self):
        vigente = dict(_construir()[0])
        vigente["valido_desde"] = INICIO_DESCONOCIDO
        despublicada = [
            {"idregionoperativa": 1, "nombreregion": "Centro", "estadoregion": "Despublicada"}
        ]

        filas = _construir(regiones=despublicada, vigentes=[vigente], ahora=DESPUES)
        claves = {f["sk_region"] for f in filas}

        assert len(claves) == 2, (
            "las dos versiones comparten clave: los hechos no podrían distinguirlas"
        )

    def test_la_clave_es_sk_region_y_no_sk_unidad(self):
        # `versionado.py` nombra la clave `sk_unidad` por defecto. Reutilizarlo
        # sin pasar `campo_sk` habría escrito una columna que esta tabla no
        # tiene, y la inserción fallaría con un error sobre columnas y no sobre
        # esto.
        fila = _construir()[0]

        assert "sk_region" in fila
        assert "sk_unidad" not in fila
