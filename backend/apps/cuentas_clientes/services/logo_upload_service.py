"""Logo upload URL service — Azure Blob presigned pattern."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService
from django.conf import settings


class LogoUploadError(Exception):
    """Logo upload URL generation failed."""


ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}


class LogoUploadService:
    """Generates presigned upload URL and final logo_url for Dim_Cliente."""

    def __init__(self, access: CuentaAccessService | None = None):
        self.access = access or CuentaAccessService()

    def create_upload_url(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        content_type: str,
        file_name: str | None = None,
    ) -> dict:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        self.access.ensure_cuenta_activa(cliente_id)

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise LogoUploadError("content_type invalido")

        blob_account = getattr(settings, "AZURE_BLOB_ACCOUNT_URL", "https://storage.example.com")
        ext = content_type.split("/")[-1]
        safe_name = file_name or f"logo-{uuid.uuid4().hex}.{ext}"
        blob_path = f"clientes/{cliente_id}/logos/{safe_name}"
        logo_url = f"{blob_account.rstrip('/')}/{blob_path}"
        upload_url = f"{logo_url}?sig=mock-presigned"
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

        return {
            "upload_url": upload_url,
            "logo_url": logo_url,
            "expires_at": expires_at,
        }
