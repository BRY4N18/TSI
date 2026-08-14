"""Membership repository — usuario to cliente account via admin_local_id only."""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


class CuentaUsuarioRepository:
    """Resolves which users belong to a cliente account (admin local only)."""

    def __init__(
        self,
        pinot: PinotClient | None = None,
        user_repo: UserRepository | None = None,
        cliente_repo: ClienteRepository | None = None,
    ):
        pinot = pinot or PinotClient()
        self.pinot = pinot
        self.user_repo = user_repo or UserRepository(pinot=pinot)
        self.cliente_repo = cliente_repo or ClienteRepository(pinot=pinot)

    def list_active_by_cliente(self, cliente_id: int) -> list[dict[str, Any]]:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return []
        admin_id = cliente.get("admin_local_id")
        if not admin_id:
            return []
        user = self.user_repo.find_by_id(admin_id)
        if user and user.get("activo", False):
            return [user]
        return []

    def user_belongs_to_cliente(self, user_id: int, cliente_id: int) -> bool:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return False
        return cliente.get("admin_local_id") == user_id

    def get_cliente_ids_for_user(self, user_id: int) -> list[int]:
        cliente = self.cliente_repo.find_by_admin_local(user_id)
        if cliente:
            return [cliente["idcliente"]]
        return []

    def list_miembros(self, cliente_id: int) -> list[dict[str, Any]]:
        """Usuarios activos que pertenecen a la organización del cliente.

        La pertenencia vive en `Dim_Usuario_Cliente`, que es lo que ya consultan
        Seguimiento (expedientes del cliente) y Soporte para resolver a qué
        cuenta pertenece un usuario. Los métodos de arriba la deducen del
        `admin_local_id`, y con ese criterio una organización tiene como mucho
        una persona — cuando el plan contratado limita precisamente el «número
        máximo de usuarios» de la organización.

        Se incluye al administrador local aunque no tenga fila de vínculo: es
        miembro por definición y su fila puede faltar en cuentas antiguas.
        """
        filas = self.pinot.query(
            "SELECT idusuario FROM Dim_Usuario_Cliente "
            "WHERE idcliente = %(idcliente)s AND activo = true LIMIT 200",
            {"idcliente": cliente_id},
        ) or []
        ids = {int(f["idusuario"]) for f in filas}

        cliente = self.cliente_repo.find_by_id(cliente_id)
        admin_id = cliente.get("admin_local_id") if cliente else None
        if admin_id:
            ids.add(int(admin_id))

        miembros = []
        for idusuario in sorted(ids):
            user = self.user_repo.find_by_id(idusuario)
            if user and user.get("activo", False):
                miembros.append(user)
        return miembros

    def es_miembro(self, user_id: int, cliente_id: int) -> bool:
        """¿Este usuario pertenece a la organización del cliente?"""
        return any(u["idusuario"] == user_id for u in self.list_miembros(cliente_id))

    def list_cuentas_del_usuario(self, user_id: int) -> list[dict[str, Any]]:
        """Cuentas a las que pertenece el usuario, por vínculo o por ser su admin local.

        Se usa en el login para rechazar a quien pertenece a una organización
        dada de baja (SRS §3.2.1). `get_cliente_ids_for_user` no sirve para eso:
        solo mira el `admin_local_id`, así que un miembro que no fuera el
        administrador quedaba fuera de la comprobación.
        """
        filas = self.pinot.query(
            "SELECT idcliente FROM Dim_Usuario_Cliente "
            "WHERE idusuario = %(idusuario)s AND activo = true LIMIT 50",
            {"idusuario": user_id},
        ) or []
        ids = {int(f["idcliente"]) for f in filas}

        cliente_admin = self.cliente_repo.find_by_admin_local(user_id)
        if cliente_admin:
            ids.add(int(cliente_admin["idcliente"]))

        cuentas = []
        for idcliente in sorted(ids):
            cliente = self.cliente_repo.find_by_id(idcliente)
            if cliente:
                cuentas.append(cliente)
        return cuentas
