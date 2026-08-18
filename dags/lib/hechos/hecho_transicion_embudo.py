"""`hecho_transicion_embudo`: una fila por cambio de etapa (Ventas y CRM, US1).

El grano es la **transicion**, no el prospecto. Un prospecto que retrocede genera
otra fila, y el porcentaje de paso del embudo se calcula sobre esas filas: si se
midiera sobre prospectos unicos, un retroceso desapareceria y el embudo
cuadraria de una forma que no ocurrio.

⚠️ `notas` no se copia
----------------------
Es texto libre escrito por el ejecutivo. Ningun informe del catalogo lo agrupa,
y copiarlo publicaria dato interno sin que nadie lo pidiera.

⚠️ `segundos_en_etapa_anterior` ausente en la primera transicion
----------------------------------------------------------------
No habia etapa anterior. Cero significaria «paso al instante», y esa cifra
encabezaria el informe de permanencia con una mentira. La duracion se deriva
aqui, restando el instante de esta transicion menos el de la anterior del mismo
prospecto; el origen no la trae.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: Orden del embudo. `Perdido` es terminal y **no** es un avance.
ORDEN_ETAPA = {
    "Nuevo": 0,
    "Contactado": 1,
    "Calificado": 2,
    "Propuesta": 3,
    "Negociación": 4,
    "Negociacion": 4,
    "Ganado": 5,
}

ETAPAS_TERMINALES = frozenset({"Ganado", "Perdido"})

#: ⚠️ Sin `notas` ni `gerente_id`: texto libre e identidad de persona.
CONSULTA_PIPELINE = f"""
    SELECT id_transicion, id_prospecto, etapa_anterior, etapa_nueva,
           motivo_perdida, fecha_transicion
    FROM Fact_Pipeline
    LIMIT {LIMITE}
"""

CONSULTA_DIM_PROSPECTO = (
    "SELECT idprospecto, empresa, canal, tipo_organizacion FROM dim_prospecto FINAL"
)


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "transiciones": consultar_origen(CONSULTA_PIPELINE),
        "dim_prospecto": consultar_modelo(CONSULTA_DIM_PROSPECTO),
    }


def es_avance(etapa_anterior: str | None, etapa_nueva: str | None) -> int:
    """1 si el cambio sube (o entra) en el embudo; 0 si retrocede o se pierde.

    Ir a `Perdido` nunca es un avance: es el abandono. Ir a `Ganado` si lo es.
    Una etapa desconocida no se inventa como avance: sin orden, no hay evidencia
    de que el prospecto progresara.
    """
    nueva = (etapa_nueva or "").strip()
    if nueva == "Perdido":
        return 0
    if not (etapa_anterior or "").strip():
        return 1
    origen = ORDEN_ETAPA.get((etapa_anterior or "").strip())
    destino = ORDEN_ETAPA.get(nueva)
    if origen is None or destino is None:
        return 0
    return 1 if destino > origen else 0


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    """Una fila por transicion. Logica pura: no consulta ni escribe."""
    por_prospecto = {
        int(p["idprospecto"]): p
        for p in datos.get("dim_prospecto", [])
        if p.get("idprospecto") is not None
    }
    marca = ahora.strftime(FORMATO)
    filas: list[dict] = []

    grupos = agrupar_por(
        [
            t
            for t in datos.get("transiciones", [])
            if t.get("id_prospecto") is not None
        ],
        "id_prospecto",
    )
    for idprospecto, de_este in grupos.items():
        ordenados = sorted(
            de_este,
            key=lambda t: (t.get("fecha_transicion") or 0, t.get("id_transicion") or 0),
        )
        anterior: datetime | None = None
        for registro in ordenados:
            momento = a_datetime(registro.get("fecha_transicion"))
            if momento is None:
                continue

            dim = por_prospecto.get(int(idprospecto), {})
            etapa_nueva = _texto(registro.get("etapa_nueva")) or ETIQUETA_DESCONOCIDA
            etapa_anterior = _texto(registro.get("etapa_anterior"))

            filas.append(
                {
                    "idtransicion": registro["id_transicion"],
                    "fecha": momento.date().isoformat(),
                    "fechahora": texto_fecha(momento),
                    "idprospecto": int(idprospecto),
                    "empresa": dim.get("empresa") or ETIQUETA_DESCONOCIDA,
                    "canal": dim.get("canal") or ETIQUETA_DESCONOCIDA,
                    "tipo_organizacion": dim.get("tipo_organizacion"),
                    "etapa_anterior": etapa_anterior,
                    "etapa_nueva": etapa_nueva,
                    "es_avance": es_avance(etapa_anterior, etapa_nueva),
                    "es_terminal": 1 if etapa_nueva in ETAPAS_TERMINALES else 0,
                    "motivo_perdida": _texto(registro.get("motivo_perdida")),
                    # Ausente en la primera: no habia etapa anterior.
                    "segundos_en_etapa_anterior": (
                        int((momento - anterior).total_seconds()) if anterior else None
                    ),
                    "cargado_en": marca,
                }
            )
            anterior = momento

    return filas
