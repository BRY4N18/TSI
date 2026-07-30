"""Resuelve el usuario receptor del escalado automático SLA (RN-TIC-005).

Prioridad (sin tabla de turnos):
1. Usuarios con rol activo `SupervisorSoporte` en Dim_Usuario_Rol.
2. Si hay varios y `SOPORTE_SUPERVISOR_USER_ID` está en esa lista → preferirlo.
3. Si hay varios sin preferencia → el menor `idusuario` (determinista).
4. Si nadie tiene el rol → fallback al env (bootstrap legacy).
"""

from __future__ import annotations

from django.conf import settings

from apps.soporte_cliente.domain_constants import ROL_SUPERVISOR_SOPORTE
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.role_repository import RoleRepository


class SupervisorSoporteRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()
        self._roles = RoleRepository(pinot=self.pinot)

    def get_supervisor_idusuario(self) -> int:
        ids = self._roles.list_user_ids_for_role(ROL_SUPERVISOR_SOPORTE)
        preferred = getattr(settings, "SOPORTE_SUPERVISOR_USER_ID", None)

        if ids:
            if preferred is not None and int(preferred) in ids:
                return int(preferred)
            return min(ids)

        if preferred is not None:
            return int(preferred)

        raise LookupError(
            "No hay usuario con rol SupervisorSoporte ni SOPORTE_SUPERVISOR_USER_ID configurado"
        )

    def get_supervisor(self) -> dict | None:
        idusuario = self.get_supervisor_idusuario()
        rows = self.pinot.query(
            "SELECT * FROM Dim_Usuarios WHERE idusuario = %(idusuario)s",
            {"idusuario": idusuario},
        )
        return rows[0] if rows else None
