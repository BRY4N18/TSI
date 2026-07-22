"""Resuelve el usuario responsable del rol fijo "Supervisor de Soporte".

RN-TIC-005 (clarificación Session 2026-07-21): no existe tabla de turnos —
un único usuario configurado por defecto vía `settings.SOPORTE_SUPERVISOR_USER_ID`.
"""

from __future__ import annotations

from django.conf import settings

from core.pinot.client import PinotClient


class SupervisorSoporteRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def get_supervisor_idusuario(self) -> int:
        return settings.SOPORTE_SUPERVISOR_USER_ID

    def get_supervisor(self) -> dict | None:
        idusuario = self.get_supervisor_idusuario()
        rows = self.pinot.query(
            "SELECT * FROM Dim_Usuarios WHERE idusuario = %(idusuario)s",
            {"idusuario": idusuario},
        )
        return rows[0] if rows else None
