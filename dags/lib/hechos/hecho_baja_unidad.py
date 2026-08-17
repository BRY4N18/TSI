"""`hecho_baja_unidad`: una fila por baja de unidad (Red Operativa, US1).

Sexto hecho del modelo, y el segundo que este departamento aporta. Reutiliza la
atribución histórica de `atribucion.py` sin añadir nada: el proveedor de la baja
es el de la versión vigente **al darse de baja**, no el de hoy.

⚠️ `con_caso_en_curso` se deriva, porque el origen no lo dice
--------------------------------------------------------------
Lo único que hay es `idaccidente` poblado o no. Una baja con accidente asociado
dejó un caso a medias; una sin él fue ordenada. Es la distinción que separa
«retiramos una unidad» de «retiramos una unidad que estaba atendiendo a alguien»,
y sobre ella se juzga a un proveedor.

⚠️ `motivo` entra al modelo, y es una excepción razonada
---------------------------------------------------------
El criterio de exclusión no es la longitud sino si el campo **se puede agrupar**.
`motivo` viene del catálogo operativo —«retiro por avería mecánica»— y es lo que
hace útil el informe de bajas: sin él solo se sabría cuántas hubo. Si algún día
admitiera texto redactado por quien da la baja, sale del modelo.

**`idusuario` no se copia**, aunque el origen lo trae: quien firma la baja es
identidad de persona, y la exclusión no la levanta ninguna autoridad.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO, SK_DESCONOCIDO
from lib.hechos.atribucion import resolver_unidad_historica, versiones_por_unidad
from lib.hechos.comun import FORMATO, a_datetime, indexar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: ⚠️ Sin `idusuario`: quien firma la baja es identidad de persona.
CONSULTA_BAJAS = f"""
    SELECT idbajaunidad, idunidademergencia, fechahora, tipobaja, motivo, idaccidente
    FROM Fact_BajaUnidad
    LIMIT {LIMITE}
"""

CONSULTA_DIM_UNIDAD = "SELECT * FROM dim_unidad FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "bajas": consultar_origen(CONSULTA_BAJAS),
        "dim_unidad": consultar_modelo(CONSULTA_DIM_UNIDAD),
    }


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por baja. Lógica pura: no consulta ni escribe."""
    versiones = versiones_por_unidad(datos.get("dim_unidad", []))
    # Para `dias_en_flota` hace falta el alta, que vive en la versión vigente.
    vigente_por_unidad = indexar_por(
        [u for u in datos.get("dim_unidad", []) if u.get("es_vigente") == 1],
        "idunidademergencia",
    )
    marca = ahora.strftime(FORMATO)

    filas = []
    for baja in datos.get("bajas", []):
        momento = a_datetime(baja.get("fechahora"))
        if momento is None:
            # Sin instante no hay partición posible. Es la única razón por la que
            # una baja no entra al modelo.
            continue

        idunidad = baja.get("idunidademergencia")
        version = resolver_unidad_historica(versiones, idunidad, momento)
        vigente = vigente_por_unidad.get(idunidad, {})
        idaccidente = baja.get("idaccidente")

        filas.append(
            {
                "idbaja": baja["idbajaunidad"],
                "fecha": momento.date().isoformat(),
                "fechahora": texto_fecha(momento),
                "sk_unidad": version["sk_unidad"] if version else SK_DESCONOCIDO,
                "idunidademergencia": idunidad if idunidad is not None else ID_DESCONOCIDO,
                "unidad": (version or {}).get("placa") or ETIQUETA_DESCONOCIDA,
                "proveedor": (version or {}).get("proveedor") or ETIQUETA_DESCONOCIDA,
                "idcondado": (version or {}).get("idcondado"),
                "condado": (version or {}).get("condado"),
                "tipo_baja": baja.get("tipobaja") or ETIQUETA_DESCONOCIDA,
                "motivo": baja.get("motivo"),
                # Derivado: el origen no lo dice de otra forma.
                "con_caso_en_curso": 1 if idaccidente else 0,
                "idaccidente": idaccidente,
                "dias_en_flota": _dias_en_flota(vigente.get("fecha_alta"), momento),
                "cargado_en": marca,
            }
        )
    return filas


def _dias_en_flota(fecha_alta: Any, baja: datetime) -> int | None:
    """Días entre el alta y la baja, o **ausente** si no se sabe cuándo entró.

    Ausente y no cero: un cero afirmaría que la unidad se dio de baja el mismo
    día que entró, que es una anomalía operativa digna de mirarse. Fabricarla a
    partir de un dato que falta llenaría el informe de rotación de unidades
    fantasma con vida de un día.
    """
    inicio = a_datetime(fecha_alta)
    if inicio is None:
        return None
    return max((baja - inicio).days, 0)
