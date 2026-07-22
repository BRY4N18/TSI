"""Resuelve el idcliente vinculado a un usuario (Dim_Usuario_Cliente)."""

from __future__ import annotations

from core.pinot.client import PinotClient


class ClienteLookupService:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def resolve_idcliente(self, idusuario: int) -> int | None:
        rows = self.pinot.query(
            "SELECT idcliente FROM Dim_Usuario_Cliente WHERE idusuario = %(idusuario)s",
            {"idusuario": idusuario},
        )
        if rows:
            return rows[0]["idcliente"]
        clientes = self.pinot.query(
            "SELECT idcliente FROM Dim_Cliente WHERE admin_local_id = %(idusuario)s",
            {"idusuario": idusuario},
        )
        return clientes[0]["idcliente"] if clientes else None
