"""Envelope `{data, meta:{pagination, filtros}}` de los listados tacticos.

Reutiliza `core.api.response_envelope.success_response`, que ya fija la forma
`{data, meta}` de toda la API. Aqui solo se arma el `meta` propio del contrato
de listados (`contrato-informes-simples.md` §2).

Por que `filtros` viaja en la respuesta
---------------------------------------
No es redundante con lo que el consumidor pidio: refleja los filtros
**aplicados y ya normalizados**. Es la unica forma de que quien consulta
confirme como se interpreto su peticion — que `dias_minimo=7` se leyo como
entero, que el rango ausente significa "todo el historico" y no "hoy". Sin ello,
una divergencia de interpretacion solo se descubre cuando las cifras no cuadran.
"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response

from core.api.response_envelope import success_response
from core.informes.paginacion import Pagina


def listado_response(
    pagina: Pagina,
    filtros: dict[str, Any] | None = None,
    *,
    acotado_a: str | None = None,
    alcance: str | None = None,
) -> Response:
    """Envelope de un listado paginado.

    Un listado sin filas es `200` con `data: []`, **nunca 404** (SC-007): la
    ausencia de resultados es una respuesta valida a una consulta valida, no un
    recurso que no existe.

    `acotado_a` declara si el resultado esta limitado a la titularidad del
    solicitante (`propios`) o abarca a todos (`todos`). **Sin el, un resultado
    vacio es ambiguo**: un Gerente no puede distinguir "no hay prospectos
    perdidos" de "no hay prospectos perdidos *mios*", que es justo la ambiguedad
    que la negativa explicita del acotamiento pretende evitar.

    Es **opcional y aditivo**: los listados que no acotan —los ocho del modulo
    piloto— no lo declaran y su respuesta no cambia. Emitirlo siempre obligaria
    a que un listado sin eje de titularidad se inventara un valor.

    `alcance` declara **qué describe el listado**, para los casos en que su
    nombre podria leerse como otra cosa. Lo introduce el listado de flota de Red
    Operativa: `dado_de_alta` significa que la unidad **existe**, no que pueda
    acudir, y confundirlos llevaria a decidir cobertura sobre unidades fuera de
    servicio, ocupadas o ya en camino a otro accidente.

    Solo lo declara el listado que lo necesita. Anadirlo a todos convertiria una
    advertencia deliberada en ruido, y el consumidor dejaria de leerla.
    """
    meta: dict[str, Any] = {
        "pagination": pagina.to_meta(),
        "filtros": _sin_ausentes(filtros or {}),
    }
    if acotado_a is not None:
        meta["acotado_a"] = acotado_a
    if alcance is not None:
        meta["alcance"] = alcance
    return success_response(pagina.filas, meta=meta)


def _sin_ausentes(filtros: dict[str, Any]) -> dict[str, Any]:
    """Descarta los filtros no declarados.

    Un filtro que no se aplico no es un filtro con valor nulo: es un filtro que
    no esta. Emitir `{"tipo": null}` sugeriria que se filtro por un tipo nulo.
    """
    return {clave: valor for clave, valor in filtros.items() if valor is not None}
