"""PG-ANA-002 — la frescura del dato analítico, declarada y visible.

**La regla que falla cuando los datos envejecen.** `PG-ANA-001` cuadra los
números y, si detecta un desfase de carga, avisa y sigue: allí no hay nada que
arreglar en la transformación. Aquí sí falla, porque quien mira esto es quien
puede reanudar un DAG.

Cada regla vigila lo suyo y el fallo apunta a quien puede resolverlo. Mezclarlas
haría que un DAG en pausa tapara una discrepancia real, o al revés.

**Por qué importa que sea visible y no solo correcta.** Un informe con datos de
hace diez días no está roto: está desactualizado, que es distinto y peor, porque
se lee igual que uno al día. Quien lo firma no tiene forma de saberlo salvo que
el propio informe lo diga.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from core.clickhouse.client import ClickHouseClient
from core.seguridad.reconciliacion import CORRESPONDENCIAS, sql_frescura_analitica

pytestmark = [pytest.mark.integration, pytest.mark.seguridad]

#: Todos los DAGs del modelo analítico son **diarios** (`schedule` entre las 02:00
#: y las 04:00). Dos días de margen cubre el peor caso legítimo —la corrida de
#: hoy aún no ha llegado y la de ayer sí— sin tolerar un DAG parado.
#:
#: Tres días ya no serían margen: serían una corrida perdida sin que nadie
#: se entere.
DIAS_FRESCURA = 2


@pytest.fixture(scope="module")
def clickhouse() -> ClickHouseClient:
    cliente = ClickHouseClient()
    try:
        cliente.query("SELECT 1", {})
    except Exception as exc:  # pragma: no cover - depende del entorno
        pytest.skip(f"ClickHouse no está disponible: {exc}")
    return cliente


def _ultima_carga(clickhouse, correspondencia) -> date | None:
    filas = clickhouse.query(sql_frescura_analitica(correspondencia), {})
    if not filas or not filas[0].get("ultima"):
        return None
    crudo = str(filas[0]["ultima"])
    try:
        # `cargado_en` es DateTime: se recorta a la fecha porque el margen se
        # mide en dias y la hora exacta de la corrida no aporta.
        return date.fromisoformat(crudo[:10])
    except ValueError:  # pragma: no cover - formato inesperado
        return None


#: Una entrada por tabla, sin repetir las que se cuadran en dos mitades.
TABLAS = sorted({c.analitica: c for c in CORRESPONDENCIAS}.values(), key=lambda c: c.analitica)


@pytest.mark.parametrize("c", TABLAS, ids=lambda c: c.analitica)
def test_el_dato_analitico_no_supera_su_ventana_de_frescura(clickhouse, c):
    """El aserto de `PG-ANA-002`.

    Un fallo aquí **no es un defecto de código**: es un DAG que hay que reanudar.
    El mensaje lo dice, porque un «no cuadra» sin diagnóstico manda a depurar una
    transformación correcta.
    """
    ultima = _ultima_carga(clickhouse, c)

    if ultima is None:
        pytest.skip(
            f"{c.analitica} está vacía. Sin datos no hay frescura que medir — lo "
            "cubre el control de PG-ANA-001, que exige que alguna tabla tenga datos."
        )

    hoy = datetime.now(tz=timezone.utc).date()
    antiguedad = (hoy - ultima).days

    assert antiguedad >= 0, (
        f"{c.analitica} dice haberse cargado el {ultima}, en el futuro. "
        "`cargado_en` no se está poblando con el instante real de la corrida."
    )

    assert antiguedad <= DIAS_FRESCURA, (
        f"{c.analitica} tiene datos de hace {antiguedad} días (último: {ultima}), "
        f"y su DAG es diario.\n"
        f"  No hay nada roto en la transformación: el DAG no ha corrido. Los DAGs "
        f"se crean con `is_paused_upon_creation=True` y hay que reanudarlos en "
        f"Airflow (:8090).\n"
        f"  Mientras tanto, cualquier informe sobre esta tabla muestra datos de "
        f"hace {antiguedad} días **sin decirlo**, y se lee igual que uno al día."
    )


def test_la_ventana_de_frescura_es_coherente_con_la_cadencia_de_los_dags():
    """Un margen mayor que la cadencia deja pasar corridas perdidas.

    Con DAGs diarios y tres días de margen, se puede perder una corrida entera
    sin que nada avise — y la regla existiría sin proteger.
    """
    from pathlib import Path

    from django.conf import settings

    dags = Path(settings.BASE_DIR).parent / "dags" / "etl"
    if not dags.exists():  # pragma: no cover
        pytest.skip("dags/etl no disponible")

    import re

    horarios = []
    for fichero in dags.glob("dag_*.py"):
        horarios += re.findall(r'schedule="([^"]+)"', fichero.read_text(encoding="utf-8"))

    diarios = [h for h in horarios if h == "@daily" or re.match(r"^[\d ]+\*\s+\*\s+\*$", h)]
    assert len(diarios) == len(horarios), (
        f"Hay DAGs que no son diarios: {sorted(set(horarios) - set(diarios))}. "
        f"DIAS_FRESCURA={DIAS_FRESCURA} se calculó suponiendo cadencia diaria."
    )
    assert DIAS_FRESCURA <= 2, (
        "Con DAGs diarios, más de dos días de margen deja pasar una corrida "
        "perdida sin avisar."
    )


def test_toda_tabla_con_datos_declara_cuando_se_cargo(clickhouse):
    """La columna de fecha existe y se puebla: sin ella no hay frescura medible.

    Una tabla que no sepa decir cuándo se cargó es indistinguible de una al día,
    y ese es el estado en el que un informe miente sin que nadie pueda notarlo.
    """
    sin_fecha = []
    for c in TABLAS:
        try:
            filas = clickhouse.query(sql_frescura_analitica(c), {})
        except Exception as exc:  # noqa: BLE001
            sin_fecha.append(f"{c.analitica}: {exc}")
            continue
        if filas and str(filas[0].get("ultima", ""))[:4] in ("", "0000", "1970"):
            sin_fecha.append(f"{c.analitica}: columna cargado_en sin poblar")

    assert not sin_fecha, "Tablas sin frescura medible:\n  " + "\n  ".join(sin_fecha)
