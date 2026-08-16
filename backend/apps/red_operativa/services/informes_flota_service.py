"""Servicio de la composición de la flota — L1 de OT12.

⚠️ La geografía se resuelve **por lotes**, nunca una consulta por fila (research D3)
------------------------------------------------------------------------------------
Dos consultas de catálogo por página —condados y estados—, independientemente de
si la página trae 5 unidades o 500.

Es el riesgo que la spec anotaba: con una consulta por fila, una flota de 500
unidades cuesta 500 consultas y el objetivo de 2 s deja de ser alcanzable. Y el
defecto no se nota con datos de prueba: con diez unidades las dos
implementaciones parecen igual de rápidas, que es justo por lo que la prueba de
rendimiento necesita volumen.

El patrón ya existía en `ubicacion_catalogo_repository.resolver_calles` para el
registro de accidentes. Aquí la cadena es más corta —la unidad se ubica por
**condado**, no por calle— así que se resuelve condado → estado geográfico.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.acotamiento import Acotamiento
from core.informes.paginacion import Orden, Pagina
from core.pinot.client import PinotClient
from core.repositories.red_operativa.informes_flota_repository import (
    CURSOR_FLOTA,
    ORDEN_FLOTA,
    InformesFlotaRepository,
)


class InformesFlotaService:
    def __init__(
        self,
        repo: InformesFlotaRepository | None = None,
        pinot: PinotClient | None = None,
    ):
        self.repo = repo or InformesFlotaRepository()
        self.pinot = pinot or PinotClient()

    def flota(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_FLOTA,
        idcondado: int | None = None,
        tipo_unidad: str | None = None,
        dado_de_alta: bool | None = None,
    ) -> Pagina:
        crudas = self.repo.unidades(
            cursor=cursor,
            limit=limit,
            orden=orden,
            proveedor=acotamiento.titular,
            idcondado=idcondado,
            tipo_unidad=tipo_unidad,
            dado_de_alta=dado_de_alta,
        )
        pagina = CURSOR_FLOTA.recortar(crudas, limit)

        geografia = self._resolver_geografia(
            [f.get("idcondado") for f in pagina.filas]
        )
        proveedores = self.repo.razones_sociales(
            [f.get("idcliente") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "placa": fila.get("placa"),
                    "nombre_unidad": fila.get("unidademergencia"),
                    "tipo_unidad": fila.get("tipounidademergencia"),
                    "capacidad": fila.get("capacidad"),
                    "proveedor": proveedores.get(fila.get("idcliente")),
                    # `None` cuando la unidad no tiene condado. La fila **no se
                    # omite**: sin condado no puede ser candidata en un despacho,
                    # y esa es justo la anomalía que la supervisión busca (FR-023).
                    "condado": geografia.get(fila.get("idcondado"), {}).get("condado"),
                    "estado_geografico": geografia.get(fila.get("idcondado"), {}).get(
                        "estado"
                    ),
                    "zona_cobertura": fila.get("zonacobertura"),
                    "tipo_propiedad": fila.get("tipopropiedad"),
                    # **Condición de alta, no disponibilidad.** El nombre del
                    # campo lo dice, y `meta.alcance` lo repite.
                    "dado_de_alta": fila.get("activo"),
                }
                for fila in pagina.filas
            ]
        )

    def tipos_disponibles(self) -> list[str]:
        return self.repo.tipos_disponibles()

    # ── Resolución geográfica por lotes ──────────────────────────────────────

    def _resolver_geografia(
        self, idcondados: Sequence[int]
    ) -> dict[int, dict[str, Any]]:
        """Condado y su estado geográfico, en **dos consultas fijas**.

        Dos y no una por fila. El número no depende del tamaño de la página, y
        eso lo comprueba `test_informes_flota_catalogo_lotes.py`.
        """
        ids = sorted({i for i in idcondados if i is not None})
        if not ids:
            return {}

        condados = self.pinot.query(
            "SELECT idcondado, condado, idestado FROM Dim_Condado "
            "WHERE idcondado IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        if not condados:
            return {}

        idestados = sorted(
            {c["idestado"] for c in condados if c.get("idestado") is not None}
        )
        estados = (
            self.pinot.query(
                "SELECT idestado, estado FROM Dim_Estado "
                "WHERE idestado IN %(ids)s LIMIT %(limit)s",
                {"ids": idestados, "limit": len(idestados)},
            )
            if idestados
            else []
        )
        nombre_estado = {e["idestado"]: e.get("estado") for e in estados}

        return {
            c["idcondado"]: {
                "condado": c.get("condado"),
                # Un condado cuyo estado no resuelve conserva su propio nombre:
                # media ubicación es más útil que ninguna.
                "estado": nombre_estado.get(c.get("idestado")),
            }
            for c in condados
        }
