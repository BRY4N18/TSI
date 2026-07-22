"""RF-TIC-002 paso 3 (CU-O92) — comentarios y notas internas.

RN-TIC-002: las notas internas nunca deben exponerse al Cliente. El filtro se
aplica aquí en la capa de servicio, no solo en el frontend (Principio V).
"""

from __future__ import annotations

from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository


class ComentarTicketService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()

    def comentar(
        self,
        id_reclamo: int,
        *,
        mensaje: str,
        es_nota_interna: bool,
        idusuario: int,
    ) -> dict:
        if not self.reclamo_repo.find_by_id(id_reclamo):
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        return self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="comentario",
            mensaje=mensaje,
            es_nota_interna=es_nota_interna,
            idusuario=idusuario,
        )

    def listar_para_rol(self, id_reclamo: int, *, ocultar_notas_internas: bool) -> list[dict]:
        historial = self.historial_repo.list_by_ticket(id_reclamo)
        if ocultar_notas_internas:
            historial = [h for h in historial if not h.get("es_nota_interna")]
        return historial
