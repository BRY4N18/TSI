"""`hecho_accidente`: instantánea acumulada, **grano un caso registrado**.

Por qué una fila por caso y no una por transición
-------------------------------------------------
Un accidente no es un suceso puntual: es un proceso con hitos —se reporta, se
confirma, se asigna una unidad, llega, se cierra—. El origen lo guarda como
**23 215 filas de transición** para 4 252 casos, que es lo correcto para operar y
lo peor posible para preguntar «cuánto se tarda en llegar»: obliga a ordenar
transiciones y restar entre filas, en cada consulta y por cada informe.

Aquí cada caso es **una fila con una columna por hito**. «Reportado a
confirmado» pasa a ser una resta entre dos columnas de la misma fila.

Un hito no alcanzado va ausente ⚠️
-----------------------------------
Nunca cero, nunca la fecha de carga. Un caso abierto con hora de cierre puesta al
día de la carga aparecería como cerrado en cero minutos, y **hundiría cualquier
promedio de duración sin que nada fallara**.

Sobre `activo`, una trampa ya documentada
------------------------------------------
`Fact_Accidente.activo = false` **no significa una sola cosa**: cubre cerrado,
descartado y fusionado a la vez. Por eso este hecho no lo copia: deriva
`fue_descartado` y `es_duplicado` de los estados reales, que sí los distinguen.

De dónde salen las columnas desnormalizadas
--------------------------------------------
Severidad, ciudad y condado se copian **desde las dimensiones ya cargadas**, no
desde el origen. Es lo que garantiza que la copia y su dimensión no puedan
divergir — el fallo clásico de este diseño, que T026 vigila.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import resolver_o_desconocido
from lib.hechos.comun import (
    FORMATO,
    a_datetime,
    agrupar_por,
    franja_horaria,
    indexar_por,
    texto_fecha,
)
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: Estados del proceso, según `Dim_TipoEstadoAccidente` del origen.
ESTADO_REPORTADO = 2
ESTADO_ASIGNADO = 4
ESTADO_CERRADO = 6
ESTADO_DESCARTADO = 7
ESTADO_FUSIONADO = 8

CONSULTA_ACCIDENTES = f"""
    SELECT idaccidente, idseveridad, idcalle, idtiporeportado, idaccidenteorigen,
           fechahoraaccidente, duracionminutos, numvehiculos, numvictimas,
           numheridos, numfallecidos
    FROM Fact_Accidente
    LIMIT {LIMITE}
"""

CONSULTA_ESTADOS = f"""
    SELECT idaccidente, idtipoestadoincidente, fechahoramodificado
    FROM Fact_AccidenteTipoEstadoAccidente
    LIMIT {LIMITE}
"""

CONSULTA_DESPACHOS = f"""
    SELECT idaccidente, fechahoradespacho, fechahorallegada
    FROM Fact_Despacho
    LIMIT {LIMITE}
"""

CONSULTA_TIPOS = f"SELECT idtiporeportado, tiporeportado FROM Dim_TipoReportado LIMIT {LIMITE}"

#: Métrica añadida al implementar la fase 6: sin ella el índice de calidad no se
#: puede calcular desde el modelo y su tabla propia no se podría retirar.
CONSULTA_EVIDENCIA = f"SELECT idaccidente FROM Dim_EvidenciaFoto LIMIT {LIMITE}"

#: Desde el modelo, no desde el origen: la copia debe salir de la dimensión.
CONSULTA_DIM_SEVERIDAD = "SELECT idseveridad, severidad FROM dim_severidad FINAL"
CONSULTA_DIM_GEOGRAFIA = "SELECT idcalle, ciudad, condado FROM dim_geografia FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "accidentes": consultar_origen(CONSULTA_ACCIDENTES),
        "estados": consultar_origen(CONSULTA_ESTADOS),
        "despachos": consultar_origen(CONSULTA_DESPACHOS),
        "tipos": consultar_origen(CONSULTA_TIPOS),
        "evidencia": consultar_origen(CONSULTA_EVIDENCIA),
        "dim_severidad": consultar_modelo(CONSULTA_DIM_SEVERIDAD),
        "dim_geografia": consultar_modelo(CONSULTA_DIM_GEOGRAFIA),
    }


def _primer_instante(transiciones: Iterable[Mapping[str, Any]], estado: int) -> datetime | None:
    """Primera vez que el caso alcanzó ese estado. Ausente si nunca lo alcanzó.

    **La primera y no la última**: un caso puede reabrirse y volver a cerrarse, y
    «cuándo se cerró por primera vez» es lo que mide el proceso. Tomar la última
    mediría cuándo dejó de dar problemas, que es otra pregunta.
    """
    instantes = [
        a_datetime(t.get("fechahoramodificado"))
        for t in transiciones
        if t.get("idtipoestadoincidente") == estado
    ]
    presentes = [i for i in instantes if i is not None]
    return min(presentes) if presentes else None


def _minimo(valores: Iterable[Any]) -> datetime | None:
    presentes = [v for v in valores if v is not None]
    return min(presentes) if presentes else None


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por caso. Lógica pura: no consulta ni escribe."""
    estados_por_caso = agrupar_por(datos["estados"], "idaccidente")
    despachos_por_caso = agrupar_por(datos["despachos"], "idaccidente")
    tipos = indexar_por(datos["tipos"], "idtiporeportado")
    severidades = indexar_por(datos["dim_severidad"], "idseveridad")
    geografia = indexar_por(datos["dim_geografia"], "idcalle")
    evidencias_por_caso = {
        caso: len(filas) for caso, filas in agrupar_por(datos.get("evidencia", []), "idaccidente").items()
    }
    marca = ahora.strftime(FORMATO)

    filas = []
    for acc in datos["accidentes"]:
        idaccidente = acc["idaccidente"]
        momento = a_datetime(acc.get("fechahoraaccidente"))
        if momento is None:
            # Sin momento no hay partición ni franja posibles. Es la única razón
            # por la que un caso no entra al modelo, y no debería ocurrir nunca:
            # el origen la declara obligatoria.
            continue

        transiciones = estados_por_caso.get(idaccidente, [])
        despachos = despachos_por_caso.get(idaccidente, [])

        idcalle = acc.get("idcalle")
        geo = geografia.get(idcalle, {})
        idseveridad = acc.get("idseveridad")
        sev = severidades.get(idseveridad, {})

        filas.append(
            {
                "idaccidente": idaccidente,
                "fecha": momento.date().isoformat(),
                "fechahora_accidente": texto_fecha(momento),
                "franja_horaria": franja_horaria(momento),
                # El hecho conserva su calle aunque la dimensión no la tenga: la
                # referencia cae en la fila desconocida, el caso no se pierde.
                "idcalle": resolver_o_desconocido(idcalle, geografia) if idcalle is not None else None,
                "condado": geo.get("condado"),
                "ciudad": geo.get("ciudad"),
                "idseveridad": idseveridad,
                "severidad": sev.get("severidad"),
                "tipo_reportado": tipos.get(acc.get("idtiporeportado"), {}).get("tiporeportado"),
                "hora_confirmacion": texto_fecha(_primer_instante(transiciones, ESTADO_REPORTADO)),
                "hora_primera_asignacion": texto_fecha(
                    _primer_instante(transiciones, ESTADO_ASIGNADO)
                ),
                "hora_primera_llegada": texto_fecha(
                    _minimo(a_datetime(d.get("fechahorallegada")) for d in despachos)
                ),
                "hora_cierre": texto_fecha(_primer_instante(transiciones, ESTADO_CERRADO)),
                "num_vehiculos": acc.get("numvehiculos"),
                "num_heridos": acc.get("numheridos"),
                "num_victimas": acc.get("numvictimas"),
                "num_fallecidos": acc.get("numfallecidos"),
                "duracion_minutos": acc.get("duracionminutos"),
                "total_intentos_despacho": len(despachos),
                # Cero es correcto aquí y no es un centinela: «no se subió
                # ninguna evidencia» es una medición, no un dato que falte.
                "num_evidencias": evidencias_por_caso.get(idaccidente, 0),
                "fue_descartado": 1 if _primer_instante(transiciones, ESTADO_DESCARTADO) else 0,
                "es_duplicado": 1 if _primer_instante(transiciones, ESTADO_FUSIONADO) else 0,
                "duplicado_de": acc.get("idaccidenteorigen"),
                "cargado_en": marca,
                "version": marca,
            }
        )
    return filas
