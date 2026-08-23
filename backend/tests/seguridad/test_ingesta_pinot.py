"""PG-OPE-001 y PG-OPE-002 — la ingesta no puede fallar en silencio.

**El fallo que esto detecta ya ocurrió en este proyecto.** Una tabla de Pinot sin
segmento consumiendo se comporta **exactamente igual** que una siembra que no
corrió: el endpoint responde `200` con una lista vacía. No hay error, no hay
aviso, y el operador concluye que no hubo accidentes.

Por eso la regla dice que un consumidor detenido **es un fallo, no un silencio**,
y por eso el corolario alcanza a toda la suite: ninguna prueba de listado puede
afirmar solo `status == 200`.

Solo se comprueba contra Pinot real. El doble en memoria no tiene consumidores
que detener, así que aquí un mock no mide nada.
"""

from __future__ import annotations

import json
import os
import urllib.request

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.seguridad]

CONTROLADOR = os.environ.get("PINOT_CONTROLLER_URL", "http://localhost:9000")

#: Segundos de retraso admisible sobre el tópico Kafka. Cero sería irreal —la
#: ingesta es asíncrona por diseño—, pero un minuto ya no es latencia: es un
#: consumidor que se quedó atrás.
LAG_MAXIMO_MS = 60_000


def _pedir(ruta: str):
    try:
        with urllib.request.urlopen(f"{CONTROLADOR}{ruta}", timeout=20) as respuesta:
            return json.loads(respuesta.read())
    except Exception as exc:  # pragma: no cover - depende del entorno
        pytest.skip(f"Controller de Pinot no disponible en {CONTROLADOR}: {exc}")


@pytest.fixture(scope="module")
def tablas_realtime() -> list[str]:
    """Solo las que ingieren de Kafka: una OFFLINE no tiene consumidor."""
    nombres = _pedir("/tables").get("tables", [])
    realtime = []
    for nombre in nombres:
        tipos = _pedir(f"/tables/{nombre}")
        if isinstance(tipos, dict) and "REALTIME" in tipos:
            realtime.append(nombre)
    if not realtime:
        pytest.skip("Ninguna tabla REALTIME registrada.")
    return realtime


# --- PG-OPE-001: hay alguien consumiendo -------------------------------------


def test_toda_tabla_realtime_tiene_un_segmento_consumiendo(tablas_realtime):
    """El aserto central.

    Una tabla sin segmento `CONSUMING` sigue respondiendo a las consultas — con
    lo que ingirió antes de pararse. Es la forma más silenciosa de perder datos:
    el sistema funciona, las respuestas llegan, y lo nuevo no entra.
    """
    detenidas = []

    for tabla in tablas_realtime:
        info = _pedir(f"/tables/{tabla}/consumingSegmentsInfo")
        mapa = (info or {}).get("_segmentToConsumingInfoMap") or {}

        estados = [
            consumidor.get("consumerState")
            for consumidores in mapa.values()
            for consumidor in consumidores
        ]
        if not estados:
            detenidas.append(f"{tabla}: ningún segmento consumiendo")
        elif "CONSUMING" not in estados:
            detenidas.append(f"{tabla}: estados {sorted(set(estados))}")

    assert not detenidas, (
        "Tablas sin consumidor activo — responden 200 con lo que ingirieron antes "
        "de pararse, así que un listado vacío parece «no hubo datos»:\n  "
        + "\n  ".join(detenidas)
    )


def test_ningun_servidor_deja_de_responder(tablas_realtime):
    """Un servidor mudo deja huecos que el conteo no delata.

    La consulta devuelve lo que sí respondió, sin decir que falta una partición.
    """
    mudos = []
    for tabla in tablas_realtime:
        info = _pedir(f"/tables/{tabla}/consumingSegmentsInfo") or {}
        if info.get("serversFailingToRespond", 0):
            mudos.append(f"{tabla}: {info['serversFailingToRespond']} servidor(es)")
    assert not mudos, "Servidores que no responden:\n  " + "\n  ".join(mudos)


# --- PG-OPE-002: lo publicado llega ------------------------------------------


def test_el_consumo_no_se_queda_atras_del_topico(tablas_realtime):
    """Reconciliación por offsets: lo publicado en Kafka está en Pinot.

    Es la versión barata de `PG-OPE-002` y cubre el caso general — comparar el
    offset consumido con el del tópico responde a «¿ha llegado todo?» sin tener
    que publicar nada.

    Un lag creciente es el aviso previo a la pérdida: el consumidor sigue vivo,
    marca `CONSUMING`, y cada vez va más atrás.
    """
    rezagadas = []

    for tabla in tablas_realtime:
        info = _pedir(f"/tables/{tabla}/consumingSegmentsInfo") or {}
        for consumidores in (info.get("_segmentToConsumingInfoMap") or {}).values():
            for consumidor in consumidores:
                offsets = consumidor.get("partitionOffsetInfo") or {}
                actuales = offsets.get("currentOffsetsMap") or {}
                ultimos = offsets.get("latestUpstreamOffsetMap") or {}

                for particion, actual in actuales.items():
                    arriba = ultimos.get(particion)
                    if arriba in (None, "", "-1") or actual in (None, "", "-1"):
                        continue
                    try:
                        atraso = int(arriba) - int(actual)
                    except ValueError:  # pragma: no cover
                        continue
                    if atraso > 0:
                        rezagadas.append(
                            f"{tabla} p{particion}: {atraso} mensajes sin consumir "
                            f"(consumido {actual}, tópico {arriba})"
                        )

    assert not rezagadas, (
        "Consumidores por detrás de su tópico. Están vivos y marcan CONSUMING, "
        "pero lo publicado todavía no es consultable:\n  " + "\n  ".join(rezagadas)
    )


def test_el_retraso_temporal_esta_dentro_del_margen(tablas_realtime):
    """El mismo control, medido en tiempo en vez de en mensajes.

    Un tópico de bajo volumen puede tener cero mensajes pendientes y aun así
    llevar horas sin ingerir nada; el offset no lo delata y el reloj sí.
    """
    lentas = []

    for tabla in tablas_realtime:
        info = _pedir(f"/tables/{tabla}/consumingSegmentsInfo") or {}
        for consumidores in (info.get("_segmentToConsumingInfoMap") or {}).values():
            for consumidor in consumidores:
                lags = (consumidor.get("partitionOffsetInfo") or {}).get("availabilityLagMs") or {}
                for particion, lag in lags.items():
                    try:
                        valor = int(lag)
                    except (TypeError, ValueError):
                        continue
                    if valor > LAG_MAXIMO_MS:
                        lentas.append(f"{tabla} p{particion}: {valor / 1000:.0f}s de retraso")

    assert not lentas, (
        f"Retraso de ingesta por encima de {LAG_MAXIMO_MS / 1000:.0f}s:\n  "
        + "\n  ".join(lentas)
    )


def test_hay_tablas_realtime_que_vigilar(tablas_realtime):
    """Control negativo.

    Si el descubrimiento fallara y devolviera una lista vacía, los asertos de
    arriba pasarían recorriendo nada — verde sin haber mirado una sola tabla.
    """
    assert len(tablas_realtime) >= 10, (
        f"Solo {len(tablas_realtime)} tablas REALTIME encontradas. El modelo "
        "dimensional tiene decenas: probablemente falló el descubrimiento y la "
        "suite está vigilando menos superficie de la que cree."
    )
