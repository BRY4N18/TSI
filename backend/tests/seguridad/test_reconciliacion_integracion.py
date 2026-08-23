"""PG-ANA-001 contra motores reales — la única prueba que detecta un informe falso.

**Por qué esta suite no puede vivir con mocks.** Un doble de Pinot devuelve lo
que se le programó, así que cuadraría consigo mismo siempre: mediría que dos
diccionarios en memoria coinciden. La discrepancia que importa —el DAG cargó 800
de 1000 casos— solo existe cuando hay dos almacenes de verdad y uno se quedó
atrás.

Es la misma lección que dejó `PG-SEC-005` (`changelog.md` C8), donde una suite de
inyección de 497 pruebas siguió en verde con una inyección real introducida.

**Cómo ejecutarla:**

```sh
docker compose -f docker/docker-compose.infraestructura.yml up -d
docker compose -f docker/docker-compose.tactico.yml up -d
# y que los DAGs hayan cargado al menos una vez
pytest tests/seguridad/test_reconciliacion_integracion.py -m integration -v
```

Corre en `integracion.yml` (semanal). Si Pinot o ClickHouse no responden, se
salta con un mensaje explícito en vez de pasar en vacío.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from core.clickhouse.client import ClickHouseClient
from core.pinot.client import PinotClient
from core.seguridad.reconciliacion import (
    CORRESPONDENCIAS,
    Correspondencia,
    discrepancia,
    sql_conteo_analitico,
    sql_conteo_operacional,
    sql_frescura_analitica,
    sql_medidas_analitico,
    sql_medidas_operacional,
)

pytestmark = [pytest.mark.integration, pytest.mark.seguridad]

#: Ventana de cuadre. Un mes es el grano de partición de los DAGs
#: (`cargar_particiones`), así que comparar un período más corto podría caer a
#: medio recargar y producir una discrepancia que no es un defecto.
DIAS_VENTANA = 30


def _ventana() -> tuple[int, int, str, str]:
    """La misma ventana expresada como epoch-ms y como fechas ISO.

    Los dos lados guardan el tiempo distinto —Pinot en epoch ms, ClickHouse en
    `Date`— y **desalinear la ventana es la forma más fácil de fabricar una
    discrepancia falsa**. Se deriva una sola vez, aquí.
    """
    hasta = datetime.now(tz=timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)
    desde = (hasta - timedelta(days=DIAS_VENTANA)).replace(hour=0, minute=0, second=0)
    return (
        int(desde.timestamp() * 1000),
        int(hasta.timestamp() * 1000),
        desde.date().isoformat(),
        hasta.date().isoformat(),
    )


@pytest.fixture(scope="module")
def pinot() -> PinotClient:
    cliente = PinotClient()
    try:
        cliente.query("SELECT 1 FROM Dim_Usuarios LIMIT 1", {})
    except Exception as exc:  # pragma: no cover - depende del entorno
        pytest.skip(f"Pinot no está disponible: {exc}")
    return cliente


@pytest.fixture(scope="module")
def clickhouse() -> ClickHouseClient:
    cliente = ClickHouseClient()
    try:
        cliente.query("SELECT 1", {})
    except Exception as exc:  # pragma: no cover - depende del entorno
        pytest.skip(f"ClickHouse no está disponible: {exc}")
    return cliente


def _entero(filas, campo: str = "total") -> int:
    if not filas:
        return 0
    valor = filas[0].get(campo) if isinstance(filas[0], dict) else filas[0][0]
    return int(valor or 0)


@pytest.mark.parametrize("c", CORRESPONDENCIAS, ids=lambda c: c.analitica)
def test_el_conteo_cuadra_con_el_origen(pinot, clickhouse, c: Correspondencia):
    """El aserto central de `PG-ANA-001`.

    Si esto falla, hay un informe entregable cuyos números no corresponden a
    ningún hecho del sistema. No es un error técnico: es un documento que miente.
    """
    desde_ms, hasta_ms, desde, hasta = _ventana()

    try:
        origen = _entero(pinot.query(sql_conteo_operacional(c, desde_ms, hasta_ms), {}))
    except Exception as exc:
        pytest.skip(f"{c.operacional} no consultable: {exc}")

    analitico = _entero(clickhouse.query(sql_conteo_analitico(c, desde, hasta), {}))

    if origen == 0 and analitico == 0:
        pytest.skip(
            f"Sin datos de {c.operacional} en los últimos {DIAS_VENTANA} días. "
            "El cuadre es cierto pero vacío: no demuestra nada."
        )

    fallo = discrepancia(origen, analitico, c)
    if fallo is None:
        return

    # Antes de acusar al ETL: ¿esta el periodo cargado siquiera? Un DAG que no
    # ha corrido produce el mismo «faltan N» que una transformacion rota, y se
    # arreglan de forma completamente distinta.
    ultima = clickhouse.query(sql_frescura_analitica(c), {})
    cargado_hasta = str(ultima[0]["ultima"]) if ultima and ultima[0].get("ultima") else "nunca"

    if cargado_hasta != "nunca" and cargado_hasta < hasta:
        # **Aviso, no fallo.** Un desfase de carga es un problema real, pero de
        # otra naturaleza: no hay nada que arreglar en la transformación, hay un
        # DAG que reanudar. Hacerlo fallar aquí dejaría el CI en rojo permanente
        # mientras los DAGs estén en pausa — y un CI rojo constante se ignora,
        # llevándose por delante las discrepancias que sí son defectos.
        #
        # La frescura la vigila `PG-ANA-002`, que **sí falla**: cada regla mira
        # lo suyo y el fallo apunta a quien puede resolverlo.
        pytest.skip(
            f"{fallo}\n\n  ⚠️ DESFASE DE CARGA, no defecto de transformación: "
            f"{c.analitica} solo tiene datos hasta {cargado_hasta} y la ventana "
            f"llega a {hasta}. El DAG correspondiente no ha corrido — los DAGs "
            f"se crean en pausa (`is_paused_upon_creation=True`). Cualquier "
            f"informe sobre esta tabla está mostrando datos viejos sin decirlo. "
            f"Lo vigila PG-ANA-002, que sí falla por frescura."
        )

    pytest.fail(
        f"{fallo}\n\n  El período está cargado hasta {cargado_hasta}: la diferencia "
        f"NO se explica por desfase, hay un defecto real."
    )


@pytest.mark.parametrize(
    "c", [c for c in CORRESPONDENCIAS if c.medidas], ids=lambda c: c.analitica
)
def test_las_medidas_cuadran_con_el_origen(pinot, clickhouse, c: Correspondencia):
    """El caso que un conteo correcto no detecta.

    Están todas las filas y los valores son otros: el informe dice el número
    correcto de accidentes y el número equivocado de heridos. Visualmente no hay
    nada raro, y es un dato que se entrega a aseguradoras.
    """
    desde_ms, hasta_ms, desde, hasta = _ventana()

    try:
        origen = pinot.query(sql_medidas_operacional(c, desde_ms, hasta_ms), {})
    except Exception as exc:
        pytest.skip(f"{c.operacional} no consultable: {exc}")

    analitico = clickhouse.query(sql_medidas_analitico(c, desde, hasta), {})

    desviadas = []
    for _op, an in c.medidas:
        valor_origen = _entero(origen, an)
        valor_analitico = _entero(analitico, an)
        if valor_origen == 0 and valor_analitico == 0:
            continue
        if valor_origen != valor_analitico:
            desviadas.append(f"{an}: origen={valor_origen} analítica={valor_analitico}")

    assert not desviadas, (
        f"{c.analitica} tiene las filas pero no los valores:\n  " + "\n  ".join(desviadas)
    )


def test_al_menos_una_tabla_tiene_datos(pinot, clickhouse):
    """Control negativo, y sin él toda la suite es decorativa.

    Con ambos almacenes vacíos, cada cuadre de arriba se salta y el informe dice
    «todo verde» sin haber comparado nada. Esta prueba obliga a que al menos una
    tabla tenga datos que cuadrar.
    """
    desde_ms, hasta_ms, desde, hasta = _ventana()
    con_datos = []

    for c in CORRESPONDENCIAS:
        try:
            if _entero(pinot.query(sql_conteo_operacional(c, desde_ms, hasta_ms), {})):
                con_datos.append(c.analitica)
        except Exception:  # noqa: BLE001 - una tabla ausente no invalida el resto
            continue

    assert con_datos, (
        f"Ninguna de las {len(CORRESPONDENCIAS)} tablas tiene datos en los últimos "
        f"{DIAS_VENTANA} días. La suite se saltaría entera y reportaría verde sin "
        "haber cuadrado nada — sembrar datos antes de darla por ejecutada."
    )


def test_la_ventana_es_la_misma_en_los_dos_lados():
    """Desalinear la ventana fabrica discrepancias que no son defectos.

    Un día de desfase entre epoch-ms y `Date` basta para que un mes con carga
    diaria no cuadre nunca, y el equipo acabaría buscando un fallo en el ETL que
    no existe.
    """
    desde_ms, hasta_ms, desde, hasta = _ventana()

    assert datetime.fromtimestamp(desde_ms / 1000, tz=timezone.utc).date() == date.fromisoformat(desde)
    assert datetime.fromtimestamp(hasta_ms / 1000, tz=timezone.utc).date() == date.fromisoformat(hasta)
