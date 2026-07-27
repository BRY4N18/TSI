"""RF-NV-004 — list sales notifications with RBAC filter."""
from __future__ import annotations

from apps.ventas_crm.domain import ForbiddenError, ValidationError
from core.repositories.ventas_crm.notificacion_ventas_repository import (
    NotificacionVentasRepository,
)


class ConsultaNotificacionVentasService:
    def __init__(self, repository=None):
        self.repository = repository or NotificacionVentasRepository()

    def listar(
        self,
        *,
        user_id: int,
        roles: list[str],
        idusuario: int | None = None,
        regladisparada: str | None = None,
        id_prospecto: int | None = None,
        limit: int = 20,
        cursor: int | None = None,
    ) -> list[dict]:
        roles = roles or []
        is_admin = "Administrador" in roles
        is_gerente = bool({"GerenteVentas", "GerenteCuentasPublicas"} & set(roles))
        if not is_admin and not is_gerente:
            raise ForbiddenError("rol insuficiente")

        owner_filter: int | None
        if is_admin:
            owner_filter = idusuario
        else:
            if idusuario is not None and int(idusuario) != int(user_id):
                raise ForbiddenError("no puede filtrar notificaciones de otro usuario")
            owner_filter = int(user_id)

        if limit < 1 or limit > 100:
            raise ValidationError("limit fuera de rango")

        return self.repository.list(
            idusuariogerentenotificado=owner_filter,
            regladisparada=regladisparada,
            id_prospecto=id_prospecto,
            limit=limit,
            cursor=cursor,
        )
