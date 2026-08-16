"""`dim_unidad`: una fila por **versión** de unidad, no por unidad.

Es la dimensión que justifica el modelo entero. El origen guarda el proveedor
actual de cada unidad y **nada historiza su cambio**: si mañana la unidad 7 pasa
del proveedor A al B, todo informe de rendimiento por proveedor reatribuye al B
los seis meses de trabajo del A — y la cifra parece correcta.

Aquí, cada despacho apunta a la **versión** vigente cuando ocurrió, así que
conserva su proveedor pase lo que pase después.

Lo que este módulo NO puede arreglar ⚠️
---------------------------------------
**El pasado anterior a la primera carga.** Nadie guardó a qué proveedor
pertenecía una unidad hace seis meses; ese dato no existe. Por eso todas las
versiones iniciales llevan `inicio_es_real = 0`: el modelo no arregla el pasado,
**impide que se siga rompiendo** desde hoy, y lo declara en vez de fingir que lo
sabe (research D2, T033).

Capacidad, una trampa del origen
--------------------------------
`Dim_UnidadEmergencia.capacidad` es **texto** en el origen, no número. Se
convierte aquí, y lo que no sea convertible queda ausente en vez de cero: una
unidad con capacidad "N/A" no tiene capacidad cero, tiene capacidad desconocida,
y un promedio que las confunda queda arrastrado hacia abajo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO
from lib.dimensiones.versionado import ATRIBUTOS_VERSIONADOS_UNIDAD, versionar_lote
from lib.clickhouse_http_client import query_clickhouse
from lib.pinot_http_client import query_pinot

LIMITE = 100_000

CONSULTA_UNIDADES = f"""
    SELECT idunidademergencia, unidademergencia, placa, tipounidademergencia,
           capacidad, idcliente, idcondado, zonacobertura
    FROM Dim_UnidadEmergencia
    LIMIT {LIMITE}
"""

CONSULTA_CLIENTES = f"SELECT idcliente, nombre, razon_social FROM Dim_Cliente LIMIT {LIMITE}"

CONSULTA_CONDADOS = f"SELECT idcondado, condado FROM Dim_Condado LIMIT {LIMITE}"

#: Las versiones vigentes ya cargadas. `FINAL` es obligatorio: sin él, una
#: unidad con dos versiones a medio fusionar devolvería ambas como vigentes y el
#: versionado compararía contra la equivocada.
CONSULTA_VIGENTES = """
    SELECT * FROM dim_unidad FINAL WHERE es_vigente = 1
"""


def _a_entero(valor: Any) -> int | None:
    """Capacidad textual → número, o ausente. **Nunca cero.**"""
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    return (
        consultar_origen(CONSULTA_UNIDADES),
        consultar_origen(CONSULTA_CLIENTES),
        consultar_origen(CONSULTA_CONDADOS),
        consultar_modelo(CONSULTA_VIGENTES),
    )


def aplanar(
    unidades: Iterable[Mapping[str, Any]],
    clientes: Iterable[Mapping[str, Any]],
    condados: Iterable[Mapping[str, Any]],
) -> list[dict]:
    """Fila del origen → fila candidata a versión, con proveedor y condado por nombre."""
    por_cliente = {c["idcliente"]: c for c in clientes}
    por_condado = {c["idcondado"]: c for c in condados}

    filas = []
    for u in unidades:
        cliente = por_cliente.get(u.get("idcliente"), {})
        condado = por_condado.get(u.get("idcondado"), {})
        filas.append(
            {
                "idunidademergencia": u["idunidademergencia"],
                "placa": u.get("placa") or ETIQUETA_DESCONOCIDA,
                "nombre_unidad": u.get("unidademergencia"),
                "tipo_unidad": u.get("tipounidademergencia"),
                "capacidad": _a_entero(u.get("capacidad")),
                "idcliente": u.get("idcliente") if u.get("idcliente") is not None else ID_DESCONOCIDO,
                "proveedor": cliente.get("nombre")
                or cliente.get("razon_social")
                or ETIQUETA_DESCONOCIDA,
                "idcondado": u.get("idcondado"),
                "condado": condado.get("condado"),
                "zona_cobertura": u.get("zonacobertura"),
            }
        )
    return filas


def _serializar(fila: dict) -> dict:
    """Fechas a texto para el almacén. `valido_hasta` ausente queda nulo, no época cero."""
    salida = dict(fila)
    for campo in ("valido_desde", "valido_hasta", "version"):
        valor = salida.get(campo)
        if isinstance(valor, datetime):
            salida[campo] = valor.strftime("%Y-%m-%d %H:%M:%S")
    return salida


def construir(
    unidades: Iterable[Mapping[str, Any]],
    clientes: Iterable[Mapping[str, Any]],
    condados: Iterable[Mapping[str, Any]],
    vigentes: Iterable[Mapping[str, Any]],
    ahora: datetime,
) -> list[dict]:
    """Filas a escribir. **Vacía si ninguna unidad cambió**, que es lo normal."""
    por_clave = {v["idunidademergencia"]: v for v in vigentes}
    filas = versionar_lote(
        aplanar(unidades, clientes, condados),
        por_clave,
        clave_negocio="idunidademergencia",
        atributos=ATRIBUTOS_VERSIONADOS_UNIDAD,
        ahora=ahora,
    )
    _verificar_sin_inicio_real(filas)
    return [_serializar(f) for f in filas]


def _verificar_sin_inicio_real(filas: Iterable[Mapping[str, Any]]) -> None:
    """Ninguna versión de unidad puede declarar un inicio real (T033, FR-021).

    Se comprueba aquí y no solo en una prueba porque es una afirmación **sobre el
    origen**, no sobre este código: nada historiza el cambio de unidad a
    proveedor. Si alguna vez el origen empezara a historizarlo, este error salta
    y obliga a decidir conscientemente —reconstruir el histórico— en vez de que
    la marca cambie de significado sin que nadie lo advierta.
    """
    mentirosas = [f for f in filas if f.get("inicio_es_real") == 1]
    if mentirosas:
        claves = sorted({f["idunidademergencia"] for f in mentirosas})
        raise ValueError(
            "versiones de unidad con inicio_es_real=1: el origen no historiza el "
            f"cambio de proveedor, así que esa fecha no puede ser real. Unidades: {claves}"
        )
