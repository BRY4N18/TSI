"""Ayuda compartida por las pruebas que van contra el almacén de verdad.

Las pruebas de las fases 1 y 2 son de lógica pura y corren en cualquier sitio.
Estas no: comprueban **el modelo cargado**, y por tanto necesitan el stack
táctico levantado. Se saltan solas si no lo encuentran, en vez de fallar — un
fallo rojo por «no hay stack» entrena a ignorar los fallos rojos.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

#: Partición muy posterior a cualquier dato real. Las pruebas que necesitan
#: escribir lo hacen aquí y la descartan al terminar, para no tocar nunca las
#: cifras que otra prueba está comprobando.
PARTICION_DE_PRUEBA = 209912
FECHA_DE_PRUEBA = "2099-12-01"


def almacen_disponible() -> bool:
    try:
        query_clickhouse("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


def modelo_cargado() -> bool:
    """El almacén responde **y** los hechos tienen datos."""
    if not almacen_disponible():
        return False
    try:
        return int(query_clickhouse("SELECT count() AS n FROM hecho_accidente")[0]["n"]) > 0
    except Exception:  # noqa: BLE001
        return False


requiere_modelo = pytest.mark.skipif(
    not modelo_cargado(),
    reason="requiere el stack táctico levantado y el modelo cargado",
)


def contar(sql: str) -> int:
    return int(query_clickhouse(sql)[0]["n"])


# ── Casos de prueba en la partición aislada ──────────────────────────────────
#
# Las pruebas de los informes OT21 escriben casos fabricados y comprueban qué
# cifra sale. Comparten este constructor a propósito: si cada fichero trajera el
# suyo, un cambio en el esquema del hecho habría que perseguirlo por cuatro
# sitios, y el que se olvidara seguiría pasando con datos que ya no existen.


def caso(
    idaccidente: str,
    *,
    severidad: bool = True,
    ubicacion: bool = True,
    condado: str = "Cuauhtemoc",
    idcalle: int | None = 1,
    descartado: bool = False,
    duplicado: bool = False,
    cerrado: bool = False,
    heridos: int = 0,
    fallecidos: int = 0,
) -> dict:
    """Un caso del período de prueba, con cada rasgo puesto o quitado por separado.

    Los rasgos son independientes **porque en el dominio lo son**: descartado,
    fusionado y cerrado no son tres valores de un estado sino tres hechos
    distintos, y un caso puede estar cerrado sin ser ninguno de los otros dos.
    Un constructor que los tratara como excluyentes impediría escribir la prueba
    que comprueba justamente que no se confunden.
    """
    return {
        "idaccidente": idaccidente,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_accidente": f"{FECHA_DE_PRUEBA} 10:00:00",
        "franja_horaria": "manana",
        "idcalle": idcalle if ubicacion else None,
        "condado": condado if ubicacion else None,
        "ciudad": "Ciudad de Mexico" if ubicacion else None,
        "idseveridad": 1 if severidad else None,
        "severidad": "Leve" if severidad else None,
        "hora_cierre": f"{FECHA_DE_PRUEBA} 11:00:00" if cerrado else None,
        "num_heridos": heridos,
        "num_fallecidos": fallecidos,
        "num_victimas": heridos + fallecidos,
        "fue_descartado": 1 if descartado else 0,
        "es_duplicado": 1 if duplicado else 0,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cargar_casos(casos: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(c) for c in casos)
    execute_clickhouse(f"INSERT INTO hecho_accidente FORMAT JSONEachRow\n{payload}")


def limpiar_particion() -> None:
    """Descarta la partición de prueba. Nunca toca datos reales: la partición es
    `toYYYYMM('2099-12-01')`, muy posterior a cualquier caso del sistema."""
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


def ejecutar_informe(nombre: str, **parametros) -> list[dict]:
    """Ejecuta una consulta del catálogo sobre el período de prueba."""
    from lib.clickhouse_http_client import query_clickhouse
    from lib.consultas import cargar

    params = {"desde": FECHA_DE_PRUEBA, "hasta": FECHA_DE_PRUEBA}
    params.update({k: str(v) for k, v in parametros.items()})
    return query_clickhouse(cargar(nombre, departamento="emergencias"), params=params)


def despacho(
    iddespacho: int,
    *,
    idaccidente: str = "T0XX-caso",
    unidad: str = "TEST-001",
    proveedor: str = "Proveedor de prueba",
    condado: str = "Cuauhtemoc",
    severidad: str = "Leve",
    origen: str = "Automatico",
    numero_intento: int = 1,
    resultado: str = "confirmado",
    segundos_transito: int | None = 400,
    segundos_respuesta: int | None = 15,
    fecha: str | None = None,
) -> dict:
    """Un intento de despacho. **Una fila por intento**, no por caso.

    Ese grano es lo que hace calculable el indicador de primer intento: con grano
    de caso, los intentos fallidos no dejan rastro.
    """
    f = fecha or FECHA_DE_PRUEBA
    return {
        "iddespacho": iddespacho,
        "idaccidente": idaccidente,
        "fecha": f,
        "fechahora_despacho": f"{f} 10:00:00",
        "sk_unidad": 900000 + iddespacho,
        "idunidademergencia": 9001,
        "unidad": unidad,
        "proveedor": proveedor,
        "idorigendespacho": 1,
        "origen_despacho": origen,
        "idseveridad": 1,
        "severidad": severidad,
        "condado": condado,
        "hora_llegada": f"{f} 10:07:00" if segundos_transito is not None else None,
        "segundos_respuesta": segundos_respuesta,
        "segundos_transito": segundos_transito,
        "numero_intento": numero_intento,
        "resultado": resultado,
        "retiro_forzado": 0,
        "cargado_en": f"{f} 12:00:00",
        "version": f"{f} 12:00:00",
    }


def cargar_despachos(filas: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(f) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_despacho FORMAT JSONEachRow\n{payload}")


def limpiar_despachos() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_despacho DROP PARTITION {PARTICION_DE_PRUEBA}")


def ping(idping: int, *, segundos_desde_anterior: int | None, proveedor: str = "Proveedor de prueba") -> dict:
    return {
        "idping": idping,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
        "sk_unidad": 900001,
        "idunidademergencia": 9001,
        "proveedor": proveedor,
        "segundos_desde_anterior": segundos_desde_anterior,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def cargar_pings(filas: list[dict]) -> None:
    import json

    from lib.clickhouse_http_client import execute_clickhouse

    payload = "\n".join(json.dumps(f) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_ping_unidad FORMAT JSONEachRow\n{payload}")


def limpiar_pings() -> None:
    from lib.clickhouse_http_client import execute_clickhouse

    execute_clickhouse(f"ALTER TABLE hecho_ping_unidad DROP PARTITION {PARTICION_DE_PRUEBA}")
