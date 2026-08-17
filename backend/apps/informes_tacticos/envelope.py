"""Construcción de la respuesta {data, meta} común a los 16 informes.

Reutiliza `core.api.response_envelope.success_response`; este módulo solo
arma la forma de `meta` (periodo + filtros) descrita en `data-model.md`.
"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response

from apps.informes_tacticos.periodo import Periodo
from core.api.response_envelope import success_response


def informe_response(data: Any, periodo: Periodo, filtros: dict[str, Any] | None = None) -> Response:
    meta = {"periodo": periodo.to_meta(), "filtros": filtros or {}}
    return success_response(data, meta=meta)


# `informe_compuesto_response` se retiró con el módulo compuesto anterior
# (decisión #20). Llevaba `materializado` y `ultima_corrida` porque cada informe
# tenía **su propia tabla**, refrescada por su propio DAG, y había que distinguir
# "el DAG aún no procesó este período" de "el período no tiene datos".
#
# En el modelo analítico esa distinción ya no existe: los informes se calculan
# sobre hechos compartidos que se cargan una vez, así que un período sin filas es
# un período sin datos y nada más. Reutilizar aquel envelope habría arrastrado un
# `materializado` que hoy sería siempre `True` — un campo que no informa de nada
# pero que el frontend seguiría mirando para decidir si pinta.


#: Informes cuya medida solo es exacta desde que el modelo empezó a versionar
#: (FR-034, Red Operativa).
#:
#: ⚠️ No es un aviso decorativo. Estos informes miden **tiempo en un estado**, y
#: el origen no historiza los cambios: la primera versión de cada entidad abre
#: por la izquierda con `inicio_es_real = 0`, es decir «hasta donde sabemos,
#: siempre fue así».
#:
#: Sin este campo, un informe de «tiempo hasta despublicar» sobre un período
#: anterior a la primera carga devolvería una cifra **calculada desde una fecha
#: inventada**, y sería indistinguible de una medición real. Publicar desde
#: cuándo es exacta convierte una cifra engañosa en una cifra con su límite
#: declarado.
def informe_con_medida_exacta(
    data: Any, periodo: Periodo, *, medida_exacta_desde: str | None,
    filtros: dict[str, Any] | None = None,
) -> Response:
    meta = {
        "periodo": {"desde": periodo.desde, "hasta": periodo.hasta},
        "filtros": filtros or {},
        # `None` significa «no depende del versionado», no «exacta desde
        # siempre»: son cosas distintas y confundirlas quitaría el aviso justo a
        # los informes que lo necesitan.
        "medida_exacta_desde": medida_exacta_desde,
    }
    return success_response(data, meta=meta)


def informe_acotado(
    data: Any, periodo: Periodo, *, acotado_a: str,
    filtros: dict[str, Any] | None = None,
) -> Response:
    """Envelope de los informes que pueden venir acotados por titularidad.

    ⚠️ `acotado_a` no es decoración. Una cifra acotada y una completa **se ven
    identicas**: «12 prospectos en pipeline» es lo mismo en pantalla tanto si son
    los del ejecutivo como si son los de todo el departamento.

    Sin este campo, un ejecutivo y su director verian la misma pantalla con
    cifras distintas y ninguno sabria por que — y la conversacion terminaria en
    «el informe esta mal» en vez de «estamos viendo cosas distintas».

    Vale `todos` o `propios`, nunca vacio: no declarar el alcance es peor que
    declararlo mal, porque lo segundo se discute y lo primero no se nota.
    """
    return success_response(
        data,
        meta={
            "periodo": {"desde": periodo.desde, "hasta": periodo.hasta},
            "filtros": filtros or {},
            "acotado_a": acotado_a,
        },
    )
