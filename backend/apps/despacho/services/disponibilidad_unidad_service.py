"""CU-O30 — declarar y consultar disponibilidad de unidad."""

from __future__ import annotations

from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    ESTADO_EN_MISION,
    HistorialEstadoUnidadRepository,
)
from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


class DisponibilidadUnidadService:
    def __init__(
        self,
        historial_repo: HistorialEstadoUnidadRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
    ):
        self.historial_repo = historial_repo or HistorialEstadoUnidadRepository()
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()

    @staticmethod
    def incluido_en_despacho(estado_actual: str) -> bool:
        return estado_actual == ESTADO_ACTIVA

    def _resolve_unidad(self, idunidademergencia: int) -> dict:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        if not unidad or not unidad.get("activo", True):
            raise LookupError("Unidad no encontrada")
        return unidad

    def consultar(self, idunidademergencia: int) -> dict:
        unidad = self._resolve_unidad(idunidademergencia)
        estado_actual, fechahora = self.historial_repo.get_current_estado(idunidademergencia)
        return {
            "idunidademergencia": idunidademergencia,
            "estado_actual": estado_actual,
            "incluido_en_despacho": self.incluido_en_despacho(estado_actual),
            "fechahora_ultimo_cambio": fechahora,
            "placa": unidad.get("placa"),
            "tipounidademergencia": unidad.get("tipounidademergencia"),
            "capacidad": unidad.get("capacidad"),
            "idcondado": unidad.get("idcondado"),
        }

    def consultar_por_usuario(self, idusuario: int) -> dict:
        unidad = self.unidad_repo.find_by_usuario(idusuario)
        if not unidad:
            raise LookupError("Unidad no vinculada al usuario")
        return self.consultar(unidad["idunidademergencia"])

    def declarar_estado(
        self,
        *,
        idunidademergencia: int,
        estadonuevo: str,
        idusuario: int,
    ) -> dict:
        if estadonuevo == ESTADO_EN_MISION:
            # "En Misión" solo la asigna el sistema al confirmar un despacho
            # (confirmar_despacho_service) — no es una declaración manual válida.
            raise ValueError(f"Estado inválido: {estadonuevo}")
        self._resolve_unidad(idunidademergencia)
        record = self.historial_repo.append_estado(
            idunidademergencia=idunidademergencia,
            estadonuevo=estadonuevo,
            idusuario=idusuario,
        )
        return {
            "idhistorialestadosunidadesemergencias": record[
                "idhistorialestadosunidadesemergencias"
            ],
            "idunidademergencia": idunidademergencia,
            "estadoanterior": record["estadoanterior"],
            "estadonuevo": record["estadonuevo"],
            "fechahora": record["fechahora"],
        }

    def declarar_estado_por_usuario(
        self,
        *,
        idusuario: int,
        estadonuevo: str,
    ) -> dict:
        unidad = self.unidad_repo.find_by_usuario(idusuario)
        if not unidad:
            raise LookupError("Unidad no vinculada al usuario")
        return self.declarar_estado(
            idunidademergencia=unidad["idunidademergencia"],
            estadonuevo=estadonuevo,
            idusuario=idusuario,
        )

    def listar_historial(
        self,
        idunidademergencia: int,
        *,
        limit: int = 20,
        cursor: int | None = None,
    ) -> tuple[list[dict], str | None]:
        self._resolve_unidad(idunidademergencia)
        rows = self.historial_repo.list_by_unidad(
            idunidademergencia, limit=limit + 1, cursor=cursor
        )
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = str(rows[-1]["idhistorialestadosunidadesemergencias"])
        items = [
            {
                "idhistorialestadosunidadesemergencias": r[
                    "idhistorialestadosunidadesemergencias"
                ],
                "idunidademergencia": r["idunidademergencia"],
                "idestadounidademergencia": r.get("idestadounidademergencia"),
                "estadoanterior": r["estadoanterior"],
                "estadonuevo": r["estadonuevo"],
                "fechahora": r["fechahora"],
                "idusuario": r["idusuario"],
            }
            for r in rows
        ]
        return items, next_cursor
