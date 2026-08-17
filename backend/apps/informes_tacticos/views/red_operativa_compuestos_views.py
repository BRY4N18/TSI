"""Vista de los informes compuestos de Red Operativa.

Una vista parametrizada, como la de Emergencias, y sobre las mismas piezas: el
período con defecto de 30 días, el repositorio del modelo y el envelope. Este
módulo no aporta plomería propia, que es el punto.

⚠️ El permiso depende del **informe pedido**, no solo del usuario
------------------------------------------------------------------
La autoridad de este departamento está repartida, así que `has_permission` mira
`view.kwargs["informe"]` para saber de qué materia se trata. Es la razón de que
el nombre del informe viaje en la ruta y no en un parámetro de consulta: un
permiso no puede depender de algo que se lee después de concederlo.
"""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_con_medida_exacta
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import RedOperativaCompuestosPermission
from apps.informes_tacticos.services.red_operativa_compuestos_service import (
    NOTAS,
    PARAMETROS,
    InformeDesconocido,
    RedOperativaCompuestosService,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401

#: Informes que miden **tiempo en un estado** y por tanto dependen del versionado
#: (FR-034). Su medida solo es exacta desde que el modelo empezó a mirar.
DEPENDEN_DEL_VERSIONADO = frozenset({
    "disponibilidad-declarada",
    "tiempo-puesta-operacion",
    "rotacion-flota",
    "tiempo-perdida-a-despublicacion",
    "regiones-en-riesgo",
    # ⚠️ Faltaba, y es el que mas lo necesita: si no hay despublicaciones
    # observadas devuelve una tabla vacia, y una tabla vacia se lee como «nunca
    # paso» cuando lo que dice es «no lo vimos».
    "casos-activos-al-despublicar",
})


class RedOperativaCompuestoView(APIView):
    """`GET /informes-tacticos/red-operativa/<informe>`."""

    permission_classes = [IsAuthenticated401, RedOperativaCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_con_defecto(request.query_params)
        except PeriodoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = RedOperativaCompuestosService()
        try:
            extra = _leer_parametros(informe, request.query_params)
        except ValueError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        try:
            datos = servicio.calcular(informe, periodo, extra=extra)
        except InformeDesconocido:
            return error_response(
                "not_found",
                f"No existe el informe '{informe}'. "
                f"Publicados: {', '.join(servicio.informes_publicados())}.",
                "404",
                status_code=404,
            )

        respuesta = informe_con_medida_exacta(
            datos,
            periodo,
            medida_exacta_desde=_medida_exacta_desde(informe),
            filtros=dict(extra),
        )
        # La nota viaja **con la cifra**, no en la documentacion: quien lee el
        # numero no lee el contrato.
        if informe in NOTAS:
            respuesta.data["meta"].update(NOTAS[informe])
        return respuesta


def _leer_parametros(informe: str, query_params) -> dict:
    """Los parametros propios del informe, con su defecto declarado.

    Se validan aqui y no en la consulta porque el error tiene que llegar como un
    400 con su explicacion. Un valor mal escrito que llegara al almacen fallaria
    con un error de conversion de tipos que no dice cual era el problema, y quien
    consulta solo veria un 500.
    """
    valores = {}
    for nombre, defecto in PARAMETROS.get(informe, {}).items():
        crudo = query_params.get(nombre)
        if crudo is None:
            valores[nombre] = defecto
            continue
        try:
            valor = int(crudo)
        except (TypeError, ValueError):
            raise ValueError(f"'{nombre}' debe ser un numero entero.") from None
        if valor < 1:
            raise ValueError(f"'{nombre}' debe ser mayor que cero.")
        valores[nombre] = valor
    return valores


def _medida_exacta_desde(informe: str) -> str | None:
    """Desde cuándo la medida de este informe es exacta, o `None` si no aplica.

    Se resuelve consultando **el modelo**, no una constante: la fecha es el
    momento en que empezó a haber versiones, y ese momento cambia si el almacén
    se recarga desde cero. Una constante quedaría desfasada en silencio, que es
    justo el fallo que este campo existe para evitar.
    """
    if informe not in DEPENDEN_DEL_VERSIONADO:
        return None

    from core.clickhouse.client import ClickHouseClient

    filas = ClickHouseClient().query(
        # La primera versión **real** —no la que abre por la izquierda—: es
        # cuando el modelo empezó a observar cambios de verdad.
        "SELECT min(valido_desde) AS desde FROM dim_region FINAL WHERE inicio_es_real = 1",
        settings={"readonly": "1"},
    )
    desde = filas[0]["desde"] if filas else None
    # ClickHouse devuelve la época cero cuando no hay ninguna fila que cumpla.
    if not desde or str(desde).startswith("1970"):
        return None
    return str(desde)
