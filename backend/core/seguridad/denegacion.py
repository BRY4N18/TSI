"""Denegacion uniforme de recursos no visibles (PG-SEC-001).

El patron que este modulo cierra aparece igual en varios modulos:

    recurso = repositorio.find_by_id(id)
    if not recurso:
        return 404 "No encontrado"      # <- NO EXISTE
    if not es_tuyo(recurso):
        return 403 "No es tuyo"         # <- EXISTE Y NO ES TUYO

Visto desde fuera, `404` y `403` son un **oraculo de enumeracion**: iterando
identificadores se deduce que recursos existen —cuantos clientes hay, si un
competidor esta dado de alta— sin llegar a ver un solo dato.

La disyuntiva 403-vs-404 es falsa: el codigo correcto **depende de quien
pregunta**. A un gestor, que opera sobre cualquier tenant por diseno, un `404` no
le revela nada y le conserva el diagnostico preciso. A todos los demas, «no
existe» y «no es tuyo» tienen que responder igual.

Ver `decisiones-pendientes.md` #51 y `contracts/respuestas-seguridad.md` §C1.
"""

from __future__ import annotations

from typing import Callable

from rest_framework import status

from core.api.response_envelope import error_response

#: Cuerpo unico de denegacion. Que el texto sea **el mismo** en ambos casos es el
#: requisito, no un descuido de redaccion: las vistas vuelcan el mensaje en
#: `detail`, asi que un texto distinto filtra la existencia por el cuerpo aunque
#: el codigo HTTP coincida.
DETALLE_UNIFICADO = "No tiene acceso a este recurso"


def respuesta_no_visible(es_gestor: bool, detalle_gestor: str = "Recurso no encontrado"):
    """Respuesta para «no existe» y para «no es tuyo», segun el actor.

    `es_gestor` decide: quien puede operar sobre cualquier tenant recibe el
    diagnostico preciso; el resto, una denegacion indistinguible.
    """
    if es_gestor:
        return error_response(
            "not_found", detalle_gestor, "not_found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return error_response(
        "forbidden", DETALLE_UNIFICADO, "acceso_denegado",
        status_code=status.HTTP_403_FORBIDDEN,
    )


def resolver_o_denegar(
    recurso: dict | None,
    pertenece: Callable[[dict], bool],
    es_gestor: bool,
    detalle_gestor: str = "Recurso no encontrado",
):
    """`None` si el actor puede verlo; si no, la respuesta de denegacion.

    Unifica las dos ramas en una sola decision para que sea imposible que
    diverjan al editar una de ellas por separado — que es como aparecio el
    oraculo en primer lugar.
    """
    if recurso is None or not (es_gestor or pertenece(recurso)):
        return respuesta_no_visible(es_gestor, detalle_gestor)
    return None
