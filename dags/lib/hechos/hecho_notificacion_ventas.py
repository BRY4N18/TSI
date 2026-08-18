"""`hecho_notificacion_ventas`: una fila por aviso al ejecutivo (Ventas y CRM, US3).

⚠️ `hubo_avance = 0` y `segundos_a_reaccion` ausente = aviso ignorado
---------------------------------------------------------------------
No es una reaccion instantanea. Contarlo como latencia cero haria que los
peores casos —los avisos que nadie atendio— **mejoraran** el indicador. La
reaccion se deriva aqui: el primer avance de etapa del mismo prospecto
*despues* del aviso. Si no hay ninguno, la duracion queda ausente y
`hubo_avance` en 0.

⚠️ `estado_envio` no se copia: ningun codigo la escribe.
⚠️ `idusuariogerentenotificado` no se copia: es identidad de persona.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, texto_fecha
from lib.hechos.hecho_transicion_embudo import es_avance
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: ⚠️ Sin `estado_envio` ni `idusuariogerentenotificado`.
CONSULTA_NOTIFICACION = f"""
    SELECT idnotificacion, id_prospecto, regladisparada, canal, fechahoranotificacion
    FROM Fact_NotificacionVentas
    LIMIT {LIMITE}
"""

CONSULTA_PIPELINE = f"""
    SELECT id_prospecto, etapa_anterior, etapa_nueva, fecha_transicion
    FROM Fact_Pipeline
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
        "notificaciones": consultar_origen(CONSULTA_NOTIFICACION),
        "transiciones": consultar_origen(CONSULTA_PIPELINE),
        "dim_prospecto": consultar_modelo(CONSULTA_DIM_PROSPECTO),
    }


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _primer_avance_posterior(
    transiciones: Iterable[Mapping[str, Any]], aviso: datetime
) -> datetime | None:
    """El primer avance de etapa despues del aviso, o nada.

    Un cambio que no es avance —un retroceso, o ir a Perdido— no cuenta como
    reaccion comercial: el ejecutivo no desatasco el embudo.
    """
    posteriores = []
    for transicion in transiciones:
        momento = a_datetime(transicion.get("fecha_transicion"))
        if momento is None or momento <= aviso:
            continue
        if es_avance(transicion.get("etapa_anterior"), transicion.get("etapa_nueva")):
            posteriores.append(momento)
    return min(posteriores) if posteriores else None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    """Una fila por aviso. Logica pura: no consulta ni escribe."""
    por_prospecto = {
        int(p["idprospecto"]): p
        for p in datos.get("dim_prospecto", [])
        if p.get("idprospecto") is not None
    }
    transiciones_por = agrupar_por(
        [
            t
            for t in datos.get("transiciones", [])
            if t.get("id_prospecto") is not None
        ],
        "id_prospecto",
    )
    marca = ahora.strftime(FORMATO)
    filas: list[dict] = []

    for registro in datos.get("notificaciones", []):
        momento = a_datetime(registro.get("fechahoranotificacion"))
        if momento is None:
            continue
        idprospecto = registro.get("id_prospecto")
        dim = por_prospecto.get(int(idprospecto), {}) if idprospecto is not None else {}
        reaccion = _primer_avance_posterior(
            transiciones_por.get(idprospecto, []), momento
        )

        filas.append(
            {
                "idnotificacion": registro["idnotificacion"],
                "fecha": momento.date().isoformat(),
                "fechahora": texto_fecha(momento),
                "idprospecto": int(idprospecto) if idprospecto is not None else 0,
                "empresa": dim.get("empresa") or ETIQUETA_DESCONOCIDA,
                "regla_disparada": (
                    _texto(registro.get("regladisparada")) or ETIQUETA_DESCONOCIDA
                ),
                "canal_aviso": _texto(registro.get("canal")) or ETIQUETA_DESCONOCIDA,
                "hubo_avance": 1 if reaccion is not None else 0,
                # Ausente si no hubo reaccion. Cero seria «reacciono al instante».
                "segundos_a_reaccion": (
                    int((reaccion - momento).total_seconds()) if reaccion else None
                ),
                "cargado_en": marca,
            }
        )

    return filas
