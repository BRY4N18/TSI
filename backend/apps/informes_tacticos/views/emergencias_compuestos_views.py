"""Vista base de los informes compuestos de Emergencias.

Una vista parametrizada por el nombre del informe, no una clase por informe: lo
único que cambiaría entre veintiséis clases es una cadena.

El nombre llega por la URL, pero **no** se usa para construir nada: se busca en
el registro del servicio, y si no está, es un 404. La diferencia importa — si el
nombre se convirtiera en una ruta de fichero, la URL sería una forma de leer el
disco.
"""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import EmergenciasCompuestosPermission
from apps.informes_tacticos.services.emergencias_compuestos_service import (
    EmergenciasCompuestosService,
    InformeDesconocido,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401

#: Advertencias que viajan **con la cifra**, no en la documentación.
#:
#: ⚠️ FR-032. `segundos_referencia` es un valor **derivado del histórico**: el
#: sistema no guarda ninguna estimación de llegada, así que no hay ningún
#: compromiso que incumplir. Una desviación positiva significa «más lento de lo
#: habitual», nunca «incumplió un plazo».
#:
#: La nota va en la respuesta y no en el contrato porque quien lee la cifra no
#: lee el contrato. Sobre esta columna se toman decisiones sobre proveedores, y
#: la diferencia entre «tardó más de lo normal» y «rompió un acuerdo» es la
#: diferencia entre una conversación y una penalización.
NOTAS: dict[str, dict[str, str]] = {
    "desviacion-llegada": {
        "nota_referencia": (
            "Valor derivado del histórico; no es un objetivo ni un SLA."
        )
    },
}


class EmergenciasCompuestoView(APIView):
    """`GET /informes-tacticos/emergencias/<informe>`."""

    permission_classes = [IsAuthenticated401, EmergenciasCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_con_defecto(request.query_params)
        except PeriodoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = EmergenciasCompuestosService()
        try:
            extra = {
                parametro.nombre: parametro.leer(request.query_params.get(parametro.nombre))
                for parametro in servicio.parametros_de(informe)
            }
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

        # `meta` es la del contrato —`periodo` y `filtros`—, la misma que la de
        # los listados simples. Añadirle campos propios de este módulo obligaría
        # al frontend a tratar estos informes como un caso aparte.
        meta: dict[str, Any] = {
            "periodo": {"desde": periodo.desde, "hasta": periodo.hasta},
            "filtros": dict(extra),
        }
        if informe in NOTAS:
            meta.update(NOTAS[informe])

        return success_response(datos, meta=meta)
