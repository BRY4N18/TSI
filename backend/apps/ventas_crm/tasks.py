"""Periodic evaluation entrypoint (scheduler / Celery-compatible)."""
from __future__ import annotations

import logging

from apps.ventas_crm.services.evaluacion_reglas_demo_service import EvaluacionReglasDemoService

logger = logging.getLogger("tsi.ventas_crm.tasks")


def run_evaluacion_reglas_demo() -> dict:
    """Invoke rule evaluation. Wire to Celery beat / cron every ≤60s."""
    result = EvaluacionReglasDemoService().run()
    logger.info("evaluacion_reglas_demo", extra=result)
    return result


try:
    from celery import shared_task

    @shared_task(name="ventas_crm.evaluacion_reglas_demo")
    def evaluacion_reglas_demo_task():
        return run_evaluacion_reglas_demo()
except ImportError:  # pragma: no cover - celery optional in this repo

    def evaluacion_reglas_demo_task():
        return run_evaluacion_reglas_demo()
