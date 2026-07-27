"""O118 — ingest demo interaction events."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from apps.ventas_crm.demo_tokens import parse_iso_expiracion
from apps.ventas_crm.domain import ForbiddenError, NotFoundError, ValidationError
from core.repositories.ventas_crm.interaccion_demo_repository import InteraccionDemoRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

TIPOS = {"click", "tiempo_seccion", "inicio_sesion", "fin_sesion"}


class IngestaInteraccionDemoService:
    def __init__(self, prospecto_repo=None, interaccion_repo=None):
        self.prospecto_repo = prospecto_repo or ProspectoRepository()
        self.interaccion_repo = interaccion_repo or InteraccionDemoRepository()

    def registrar(self, *, idprospecto_token: int, data: dict) -> dict:
        idprospecto = int(data.get("idprospecto") or 0)
        if idprospecto != int(idprospecto_token):
            raise ForbiddenError("token no corresponde al idprospecto")
        tipo = data.get("tipo_evento")
        seccion = data.get("seccion")
        if tipo not in TIPOS:
            raise ValidationError("tipo_evento inválido")
        if not seccion:
            raise ValidationError("seccion requerida")
        if tipo == "tiempo_seccion":
            meta = data.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError as exc:
                    raise ValidationError("metadata inválida") from exc
            if not isinstance(meta, dict) or "duracion_ms" not in meta:
                raise ValidationError("tiempo_seccion requiere metadata.duracion_ms")

        prospecto = self.prospecto_repo.find_by_id(idprospecto)
        if not prospecto:
            raise NotFoundError("Prospecto no encontrado")
        demo_exp = parse_iso_expiracion(prospecto.get("demo_expiracion"))
        now = datetime.now(timezone.utc)
        if demo_exp is None or now >= demo_exp:
            raise ForbiddenError("demo expirada")

        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)
        elif metadata is None:
            metadata = "{}"

        ts = data.get("timestamp_evento")
        if ts is None:
            ts = int(now.timestamp() * 1000)

        return self.interaccion_repo.create(
            {
                "idprospecto": idprospecto,
                "tipo_evento": tipo,
                "seccion": seccion,
                "metadata": metadata,
                "timestamp_evento": int(ts),
            }
        )
