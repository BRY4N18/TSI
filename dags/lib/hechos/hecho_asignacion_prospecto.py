"""`hecho_asignacion_prospecto`: una fila por asignacion (Ventas y CRM, US1).

⚠️ Es el primer historial del proyecto que el origen si guarda bien
-------------------------------------------------------------------
`Fact_Asignacion` trae el instante de cada cambio. La atribucion por ejecutivo
es exacta desde el primer dia, sin la marca de «inicio no real» que necesitan la
unidad y la region.

El ejecutivo se identifica por su **clave**, no por su nombre: es su funcion
dentro del informe de carga, el unico del departamento que desglosa por
ejecutivo. Un ranking de quien cierra menos seria vigilancia laboral; este
informe pregunta cuantos prospectos tiene cada cartera, y eso se responde con
la clave.

`tipoasignacion` del origen vale `automatica` / `manual`. El modelo guarda
`inicial` / `reasignacion`: lo que importa para la carga historica es si habia
dueno anterior, no el mecanismo. Un nulo en el ejecutivo previo es asignacion
inicial; cualquier otro valor, reasignacion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA
from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

TIPO_INICIAL = "inicial"
TIPO_REASIGNACION = "reasignación"

CONSULTA_ASIGNACION = f"""
    SELECT idasignacion, idprospecto, idusuariogerenteanterior,
           idusuariogerenteactual, tipoasignacion, motivo, fechahoraasignacion
    FROM Fact_Asignacion
    LIMIT {LIMITE}
"""

CONSULTA_DIM_PROSPECTO = (
    "SELECT idprospecto, empresa FROM dim_prospecto FINAL"
)


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "asignaciones": consultar_origen(CONSULTA_ASIGNACION),
        "dim_prospecto": consultar_modelo(CONSULTA_DIM_PROSPECTO),
    }


def tipo_de(idejecutivo_previo: Any) -> str:
    """Inicial si no habia dueno; reasignacion en cualquier otro caso.

    El origen distingue automatica/manual, que es el mecanismo. El modelo
    pregunta si la cartera cambio de manos, que es lo que reescribiria el
    pasado si se guardara el dueno en la dimension.
    """
    return TIPO_INICIAL if idejecutivo_previo is None else TIPO_REASIGNACION


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    """Una fila por asignacion. Logica pura: no consulta ni escribe."""
    por_prospecto = {
        int(p["idprospecto"]): p
        for p in datos.get("dim_prospecto", [])
        if p.get("idprospecto") is not None
    }
    marca = ahora.strftime(FORMATO)
    filas: list[dict] = []

    for registro in datos.get("asignaciones", []):
        momento = a_datetime(registro.get("fechahoraasignacion"))
        if momento is None:
            continue
        idejecutivo = registro.get("idusuariogerenteactual")
        if idejecutivo is None:
            # Sin ejecutivo entrante no hay atribucion posible.
            continue

        idprospecto = registro.get("idprospecto")
        dim = por_prospecto.get(int(idprospecto), {}) if idprospecto is not None else {}
        previo = registro.get("idusuariogerenteanterior")

        filas.append(
            {
                "idasignacion": registro["idasignacion"],
                "fecha": momento.date().isoformat(),
                "fechahora": texto_fecha(momento),
                "idprospecto": int(idprospecto) if idprospecto is not None else 0,
                "empresa": dim.get("empresa") or ETIQUETA_DESCONOCIDA,
                "idejecutivo": int(idejecutivo),
                "idejecutivo_previo": int(previo) if previo is not None else None,
                "tipo_asignacion": tipo_de(previo),
                "motivo": _texto(registro.get("motivo")),
                "cargado_en": marca,
            }
        )

    return filas
