"""`hecho_validacion_region`: un intento de validación de región (US2).

⚠️ `numero_intento` se calcula aquí, y es lo que hace calculable el indicador
-----------------------------------------------------------------------------
El origen no lo trae: guarda las validaciones sueltas, con su instante. El
ordinal sale de ordenarlas **dentro de cada región** por ese instante.

Sin él, una región rechazada dos veces y aprobada a la tercera contaría como
aprobada, y la tasa de aprobación al primer intento daría el mejor resultado
posible justamente en el caso que peor fue. Es el mismo mecanismo que en el hecho
de despacho, y el mismo motivo.

Los datos de hoy son exactamente ese caso: la región 2 tiene dos rechazos y una
aprobación.

⚠️ **`idusuario` no se copia**, aunque el origen lo trae
--------------------------------------------------------
El validador es una persona (FR-021). Un informe de validaciones desglosado por
quien las firma es un registro de decisiones individuales, y sobre él se juzgaría
a alguien por resultados que dependen de las regiones que le tocaron.

Es la exclusión que más cuesta ver de este departamento, porque parece
información de proceso. No lo es.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse
from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, SK_DESCONOCIDO
from lib.hechos.comun import FORMATO, a_datetime, agrupar_por, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

#: ⚠️ Sin `idusuario`: el validador es una persona.
CONSULTA_VALIDACIONES = f"""
    SELECT idvalidacionregion, idregionoperativa, fechahora, resultado, motivo
    FROM Dim_ValidacionRegion
    LIMIT {LIMITE}
"""

#: Del modelo: la versión de región vigente al validar.
CONSULTA_DIM_REGION = "SELECT * FROM dim_region FINAL"


def extraer(
    consultar_origen: Callable[[str], list[dict]] = query_pinot,
    consultar_modelo: Callable[[str], list[dict]] = query_clickhouse,
) -> dict[str, list[dict]]:
    return {
        "validaciones": consultar_origen(CONSULTA_VALIDACIONES),
        "dim_region": consultar_modelo(CONSULTA_DIM_REGION),
    }


def _instante(valor: Any) -> datetime | None:
    """Fecha de una version, venga del almacen (texto) o del origen (epoch-ms).

    Las dos fuentes conviven en este modulo: las validaciones llegan de Pinot en
    epoch-ms y las versiones de region del almacen como texto. Compararlas sin
    convertir haria que `"2100-01-01" < "2026-08-16"` fuese cierto por el orden
    alfabetico, y la version vigente saldria mal en cuanto una fecha cambiara de
    longitud.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, str):
        try:
            return datetime.strptime(valor, FORMATO)
        except ValueError:
            return None
    return a_datetime(valor)


def _version_vigente_en(versiones: list[Mapping[str, Any]], instante: datetime):
    """La versión de la región vigente en ese instante, o `None`.

    Devolver `None` en vez de la actual es lo que impide reatribuir: una región
    despublicada hoy no reescribe las validaciones de cuando estaba en curso.
    """
    for version in versiones:
        desde = _instante(version.get("valido_desde"))
        hasta = _instante(version.get("valido_hasta"))
        if desde is not None and desde <= instante and (hasta is None or instante < hasta):
            return version
    return None


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    """Una fila por intento de validación. Lógica pura: no consulta ni escribe."""
    versiones_por_region = agrupar_por(datos.get("dim_region", []), "idregionoperativa")
    marca = ahora.strftime(FORMATO)

    filas = []
    for idregion, validaciones in agrupar_por(
        datos.get("validaciones", []), "idregionoperativa"
    ).items():
        # ⚠️ El ordinal sale del **instante**, no del orden en que lleguen las
        # filas. Pinot no garantiza orden sin `ORDER BY`, así que confiar en el
        # de llegada haría que el «primer intento» cambiara entre dos corridas
        # sin que nada hubiera pasado.
        ordenadas = sorted(validaciones, key=lambda v: v.get("fechahora") or 0)

        for numero, validacion in enumerate(ordenadas, start=1):
            momento = a_datetime(validacion.get("fechahora"))
            if momento is None:
                # Sin instante no hay partición ni ordinal posibles.
                continue

            version = _version_vigente_en(versiones_por_region.get(idregion, []), momento)
            filas.append(
                {
                    "idvalidacion": validacion["idvalidacionregion"],
                    "fecha": momento.date().isoformat(),
                    "fechahora": texto_fecha(momento),
                    "sk_region": int(version["sk_region"]) if version else SK_DESCONOCIDO,
                    "idregionoperativa": idregion,
                    "nombre_region": (version or {}).get("nombre_region")
                    or ETIQUETA_DESCONOCIDA,
                    "resultado": validacion.get("resultado") or ETIQUETA_DESCONOCIDA,
                    # Ausente en las aprobaciones, y es correcto: no hubo nada
                    # que justificar. Convertirlo en categoría haría aparecer
                    # «sin motivo» como la causa de rechazo más frecuente.
                    "motivo": validacion.get("motivo"),
                    "numero_intento": numero,
                    "cargado_en": marca,
                }
            )
    return filas
