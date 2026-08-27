"""CU-O78 — declarar y consultar disponibilidad de unidad."""

from __future__ import annotations

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.geografia_repository import GeografiaRepository
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
        geografia_repo: GeografiaRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
    ):
        self.historial_repo = historial_repo or HistorialEstadoUnidadRepository()
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.geografia_repo = geografia_repo or GeografiaRepository()
        self.despacho_repo = despacho_repo or DespachoRepository()

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
        idcondado = unidad.get("idcondado")
        condado = None
        if idcondado is not None:
            condado = self.geografia_repo.find_nombre(int(idcondado))
        return {
            "idunidademergencia": idunidademergencia,
            "estado_actual": estado_actual,
            "incluido_en_despacho": self.incluido_en_despacho(estado_actual),
            "fechahora_ultimo_cambio": fechahora,
            "placa": unidad.get("placa"),
            "tipounidademergencia": unidad.get("tipounidademergencia"),
            "capacidad": unidad.get("capacidad"),
            "idcondado": idcondado,
            "condado": condado,
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

    def listar_historial_despachos(
        self,
        idunidademergencia: int,
        *,
        limit: int = 20,
        cursor: int | None = None,
    ) -> tuple[list[dict], int | None]:
        """Despachos que ha atendido la unidad, del más reciente hacia atrás.

        Complementa `listar_historial`, que solo cuenta cambios de estado
        (Activa / En misión / Fuera de servicio). Saber cuándo una unidad estuvo
        disponible no dice **a qué acudió**, y eso es lo que la revisión del
        24/08/2026 echó en falta (hallazgo #13).

        Cada fila trae la fase alcanzada —despachada, en sitio, retirada— para
        que se lea de un vistazo cómo terminó cada salida.
        """
        self._resolve_unidad(idunidademergencia)
        rows, next_cursor = self.despacho_repo.list_historial_by_unidad(
            idunidademergencia, limit=limit, cursor=cursor
        )
        items = [
            {
                "iddespacho": r.get("iddespacho"),
                "idaccidente": r.get("idaccidente"),
                "fechahoradespacho": r.get("fechahoradespacho"),
                "fechahorallegada": r.get("fechahorallegada"),
                "fechahoraretiro": r.get("fechahoraretiro"),
                "retiro_forzado": bool(r.get("retiro_forzado")),
                "activo": bool(r.get("activo")),
                "fase": self._fase_despacho(r),
            }
            for r in rows
        ]
        return items, next_cursor

    @staticmethod
    def _fase_despacho(despacho: dict) -> str:
        """Fase alcanzada, derivada de los sellos de tiempo del propio despacho.

        Se deriva aquí y no en el cliente para que la lista y cualquier informe
        futuro cuenten la misma historia.
        """
        if despacho.get("fechahoraretiro"):
            return "Retiro forzado" if despacho.get("retiro_forzado") else "Retirada"
        if despacho.get("fechahorallegada"):
            return "En sitio"
        return "En camino" if despacho.get("activo") else "Sin llegada registrada"
