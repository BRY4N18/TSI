"""Push notification stub for Ventas-CRM demo alerts (logs when no provider)."""
from __future__ import annotations

import logging

logger = logging.getLogger("tsi.notificaciones.push")


class PushNotificationSender:
    def send(self, *, event: str, user_id: int, title: str, body: str) -> None:
        logger.info(
            "push_send",
            extra={"event": event, "user_id": user_id, "title": title, "body": body},
        )
