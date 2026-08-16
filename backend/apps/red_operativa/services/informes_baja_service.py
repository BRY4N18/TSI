"""Servicio de bajas de unidad — L2 de OT12 / CU-O42.

La regla que sostiene: **el caso afectado se devuelve en las bajas forzadas y
como ausencia en las normales** (research D5).

Una baja forzada significa que un accidente se quedó sin la unidad que lo
atendía y hubo que reasignar. Devolver el caso solo ahí es lo que distingue un
**incidente operativo** de una salida ordenada de flota; si el campo apareciera
siempre —vacío en las normales— el listado invitaría a leerlo como «baja sin
caso registrado», que es una anomalía distinta y que aquí no existe.
"""

from __future__ import annotations

from typing import Any

from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.red_operativa.informes_baja_repository import (
    CURSOR_BAJAS,
    ORDEN_BAJAS,
    TIPO_BAJA_FORZADA,
    InformesBajaRepository,
)


class InformesBajaService:
    def __init__(self, repo: InformesBajaRepository | None = None):
        self.repo = repo or InformesBajaRepository()

    def bajas(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_BAJAS,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        tipo_baja: str | None = None,
    ) -> Pagina:
        # `Fact_BajaUnidad` no guarda el proveedor, solo la unidad: cuando hay
        # acotamiento hay que resolver sus unidades antes. Es **una** consulta
        # adicional por petición, no una por fila.
        idunidades = (
            self.repo.unidades_de_proveedor(acotamiento.titular)
            if acotamiento.acotado
            else None
        )

        crudas = self.repo.bajas(
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
            tipo_baja=tipo_baja,
            idunidades=idunidades,
        )
        pagina = CURSOR_BAJAS.recortar(crudas, limit)

        unidades = self.repo.datos_de_unidad(
            [f.get("idunidademergencia") for f in pagina.filas]
        )
        proveedores = self.repo.razones_sociales(
            [u.get("idcliente") for u in unidades.values()]
        )
        ejecutores = self.repo.nombres_de_usuario(
            [f.get("idusuario") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                _fila(f, unidades, proveedores, ejecutores) for f in pagina.filas
            ]
        )


def _fila(
    cruda: dict[str, Any],
    unidades: dict[int, dict[str, Any]],
    proveedores: dict[int, str],
    ejecutores: dict[int, str],
) -> dict[str, Any]:
    unidad = unidades.get(cruda.get("idunidademergencia"), {})
    fila = {
        "placa": unidad.get("placa"),
        "proveedor": proveedores.get(unidad.get("idcliente")),
        "motivo": cruda.get("motivo"),
        "tipo_baja": cruda.get("tipobaja"),
        "ejecutada_por": ejecutores.get(cruda.get("idusuario")),
        "fecha": a_iso(cruda.get("fechahora")),
    }
    if cruda.get("tipobaja") == TIPO_BAJA_FORZADA:
        # Solo aquí. Es la traza de impacto que el SRS exige: qué accidente se
        # quedó sin unidad.
        fila["caso_afectado"] = cruda.get("idaccidente")
    return fila
