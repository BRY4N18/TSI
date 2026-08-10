"""O122 + RF-NV-003 — evaluate demo rules on historical sessions."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings

from apps.ventas_crm.demo_tokens import parse_iso_expiracion
from apps.ventas_crm.services.despacho_notificacion_ventas_service import (
    CanalNoDisponibleError,
    DespachoNotificacionVentasService,
)
from apps.ventas_crm.services.reglas_demo_catalog import (
    evaluar_reglas_mvp,
    eventos_en_sesion,
)
from core.repositories.ventas_crm.interaccion_demo_repository import InteraccionDemoRepository
from core.repositories.ventas_crm.notificacion_ventas_repository import (
    NotificacionVentasRepository,
)
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

logger = logging.getLogger("tsi.ventas_crm.evaluacion_reglas")


def _utc_day_bounds(now: datetime | None = None) -> tuple[int, int]:
    now = now or datetime.now(timezone.utc)
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


class EvaluacionReglasDemoService:
    def __init__(
        self,
        prospecto_repo=None,
        interaccion_repo=None,
        notificacion_repo=None,
        despacho=None,
    ):
        self.prospecto_repo = prospecto_repo or ProspectoRepository()
        self.interaccion_repo = interaccion_repo or InteraccionDemoRepository()
        self.notificacion_repo = notificacion_repo or NotificacionVentasRepository()
        self.despacho = despacho or DespachoNotificacionVentasService()

    def run(self, *, now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        days = int(getattr(settings, "DEMO_REEVAL_DAYS", 7))
        since = now - timedelta(days=days)
        since_ms = int(since.timestamp() * 1000)
        day_start, day_end = _utc_day_bounds(now)

        inicios = self.interaccion_repo.list_inicio_sesion_recent(since_ms)
        created = 0
        skipped_orphan = 0
        skipped_dedup = 0
        skipped_expired_window = 0

        seen_sessions: set[tuple[int, int]] = set()
        for inicio in inicios:
            idprospecto = int(inicio.get("idprospecto") or 0)
            inicio_ms = int(inicio.get("timestamp_evento") or 0)
            key = (idprospecto, inicio_ms)
            if key in seen_sessions:
                continue
            seen_sessions.add(key)

            prospecto = self.prospecto_repo.find_by_id(idprospecto)
            if not prospecto:
                continue
            demo_exp = parse_iso_expiracion(prospecto.get("demo_expiracion"))
            if demo_exp is None:
                continue
            # Eligible if demo_expiracion within last N days (session may already be closed)
            if demo_exp < since:
                skipped_expired_window += 1
                continue
            demo_exp_ms = int(demo_exp.timestamp() * 1000)
            eventos = self.interaccion_repo.list_by_prospecto(idprospecto)
            sesion = eventos_en_sesion(
                eventos, inicio_ms=inicio_ms, demo_expiracion_ms=demo_exp_ms
            )
            fulfilled = evaluar_reglas_mvp(sesion)
            idusuario = prospecto.get("idusuario")
            if idusuario is None:
                if fulfilled:
                    skipped_orphan += 1
                continue

            for item in fulfilled:
                if self.notificacion_repo.exists_dedup_dia_utc(
                    id_prospecto=idprospecto,
                    regladisparada=item["regladisparada"],
                    day_start_ms=day_start,
                    day_end_ms=day_end,
                ):
                    skipped_dedup += 1
                    continue
                row = self.notificacion_repo.create(
                    {
                        "id_prospecto": idprospecto,
                        "idinteraccion": item.get("idinteraccion") or inicio.get("idinteraccion"),
                        "idusuariogerentenotificado": int(idusuario),
                        "regladisparada": item["regladisparada"],
                        "canal": item["canal"],
                    }
                )
                try:
                    self.despacho.despachar(row)
                except CanalNoDisponibleError:
                    logger.warning(
                        "canal_no_disponible",
                        extra={"canal": row.get("canal"), "idnotificacion": row.get("idnotificacion")},
                    )
                created += 1

        return {
            "created": created,
            "skipped_orphan": skipped_orphan,
            "skipped_dedup": skipped_dedup,
            "skipped_expired_window": skipped_expired_window,
            "sessions_scanned": len(seen_sessions),
        }
