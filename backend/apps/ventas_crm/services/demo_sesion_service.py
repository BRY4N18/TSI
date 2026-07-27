"""O118 — open / resume demo session with grant HMAC."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from django.conf import settings

from apps.ventas_crm.demo_tokens import (
    format_iso_expiracion,
    issue_demo_session_token,
    parse_iso_expiracion,
    verify_demo_grant,
)
from apps.ventas_crm.domain import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from core.repositories.ventas_crm.interaccion_demo_repository import InteraccionDemoRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository


class DemoSesionService:
    def __init__(self, prospecto_repo=None, interaccion_repo=None):
        self.prospecto_repo = prospecto_repo or ProspectoRepository()
        self.interaccion_repo = interaccion_repo or InteraccionDemoRepository()

    def abrir(self, *, idprospecto: int, demo_grant: str) -> dict:
        if not idprospecto or not demo_grant:
            raise ValidationError("idprospecto y demo_grant son requeridos")
        if not verify_demo_grant(demo_grant, int(idprospecto)):
            raise UnauthorizedError("grant inválido o no corresponde al prospecto")

        prospecto = self.prospecto_repo.find_by_id(int(idprospecto))
        if not prospecto:
            raise NotFoundError("Prospecto no encontrado")
        if not prospecto.get("activo", True):
            raise ForbiddenError("Prospecto inactivo")

        now = datetime.now(timezone.utc)
        demo_exp = parse_iso_expiracion(prospecto.get("demo_expiracion"))

        if demo_exp is None:
            minutes = int(getattr(settings, "DEMO_SESSION_MINUTES", 30))
            demo_exp = now + timedelta(minutes=minutes)
            iso = format_iso_expiracion(demo_exp)
            updated = self.prospecto_repo.update_demo_expiracion(int(idprospecto), iso)
            if not updated:
                raise NotFoundError("Prospecto no encontrado")
            self.interaccion_repo.create(
                {
                    "idprospecto": int(idprospecto),
                    "tipo_evento": "inicio_sesion",
                    "seccion": "demo",
                    "metadata": "{}",
                    "timestamp_evento": int(now.timestamp() * 1000),
                }
            )
            token = issue_demo_session_token(
                idprospecto=int(idprospecto), demo_expiracion_iso=iso
            )
            return {
                "idprospecto": int(idprospecto),
                "demo_session_token": token,
                "demo_expiracion": iso,
                "modo": "primer_canje",
            }

        if now >= demo_exp:
            raise ForbiddenError("demo expirada")

        iso = format_iso_expiracion(demo_exp)
        token = issue_demo_session_token(
            idprospecto=int(idprospecto), demo_expiracion_iso=iso
        )
        return {
            "idprospecto": int(idprospecto),
            "demo_session_token": token,
            "demo_expiracion": iso,
            "modo": "resume",
        }
