"""Servicio de la cartera de prospectos — L1 de OT01/OT02.

Aplica el acotamiento por titularidad y da forma a la fila. Lo que **no** hace
es decidir quién ve qué: eso lo resuelve `core/informes/acotamiento.py`, que es
el mismo resolutor para los siete departamentos.

`motivo_perdida` solo cuando el estado es `perdido`
---------------------------------------------------
No es cosmético. Un prospecto convertido no tiene motivo de pérdida porque no se
perdió, y devolverle el campo —aunque fuera `null`— sugeriría que la pregunta
tiene sentido para él. El estado de la fila y la presencia del campo dicen lo
mismo, y así no pueden contradecirse.
"""

from __future__ import annotations

from typing import Any

from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.ventas_crm.informes_cartera_repository import (
    CURSOR_CARTERA,
    ESTADO_ACTIVO,
    ESTADO_CONVERTIDO,
    ESTADO_PERDIDO,
    MOTIVO_CONVERTIDO,
    MOTIVO_PERDIDO,
    ORDEN_CARTERA,
    InformesCarteraRepository,
)


class InformesCarteraService:
    def __init__(self, repo: InformesCarteraRepository | None = None):
        self.repo = repo or InformesCarteraRepository()

    def prospectos(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CARTERA,
        canal: str | None = None,
        tipo_organizacion: str | None = None,
        etapa: str | None = None,
        estado: str | None = None,
    ) -> Pagina:
        crudas = self.repo.prospectos(
            cursor=cursor,
            limit=limit,
            orden=orden,
            titular=acotamiento.titular,
            canal=canal,
            tipo_organizacion=tipo_organizacion,
            etapa=etapa,
            estado=estado,
        )
        pagina = CURSOR_CARTERA.recortar(crudas, limit)

        ejecutivos = self.repo.nombres_de_usuario(
            [f.get("idusuario") for f in pagina.filas]
        )
        # El motivo solo se consulta para las filas que de verdad lo tienen: una
        # consulta de menos cuando la pagina no trae ningun perdido.
        perdidos = [
            f["idprospecto"] for f in pagina.filas if _estado(f) == ESTADO_PERDIDO
        ]
        motivos = self.repo.motivos_de_perdida(perdidos)

        return pagina._replace(
            filas=[_fila(f, ejecutivos, motivos) for f in pagina.filas]
        )


def _estado(fila: dict[str, Any]) -> str:
    """Traduce el par (`activo`, `motivo_inactividad`) al estado del contrato.

    Se decide por el **motivo**, no por `activo`: es la misma regla que en el
    filtro del repositorio, y compartirla evita que un prospecto se filtre como
    perdido y se presente como convertido, o al reves.
    """
    if fila.get("activo"):
        return ESTADO_ACTIVO
    motivo = fila.get("motivo_inactividad")
    if motivo == MOTIVO_CONVERTIDO:
        return ESTADO_CONVERTIDO
    if motivo == MOTIVO_PERDIDO:
        return ESTADO_PERDIDO
    # Inactivo sin motivo declarado: no se supone ninguno de los dos. Decir
    # "perdido" convertiria un dato incompleto en una afirmacion comercial.
    return ESTADO_PERDIDO if motivo is None else str(motivo)


def _fila(
    cruda: dict[str, Any],
    ejecutivos: dict[int, str],
    motivos: dict[int, str],
) -> dict[str, Any]:
    estado = _estado(cruda)
    fila = {
        "empresa": cruda.get("empresa"),
        "nombre_contacto": _nombre(cruda),
        "cargo": cruda.get("cargo"),
        "tipo_organizacion": cruda.get("tipo_organizacion"),
        "canal_origen": cruda.get("como_nos_conocio"),
        "etapa_actual": cruda.get("etapa_actual"),
        # `None` cuando no resuelve, y la fila **no se omite**: un prospecto sin
        # dueno es un prospecto que nadie esta trabajando, justo la anomalia que
        # la supervision busca (research D7).
        "ejecutivo": ejecutivos.get(cruda.get("idusuario")),
        "estado": estado,
        "valor_estimado": cruda.get("valor_estimado"),
        "fecha_registro": a_iso(cruda.get("fecha_registro")),
    }
    if estado == ESTADO_PERDIDO:
        fila["motivo_perdida"] = motivos.get(cruda["idprospecto"])
    return fila


def _nombre(fila: dict[str, Any]) -> str:
    partes = [fila.get("nombres"), fila.get("apellidos")]
    return " ".join(p for p in partes if p).strip()
