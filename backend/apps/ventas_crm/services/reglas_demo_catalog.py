"""MVP rule catalog RN-NV-003 — pure functions, no I/O."""
from __future__ import annotations

import json
from typing import Any

REGLA_TIEMPO_PRECIOS = "tiempo_seccion_precios_5min"
REGLA_VISITO_PRICING = "visito_pricing_3x"
CANAL_POR_REGLA = {
    REGLA_TIEMPO_PRECIOS: "email",
    REGLA_VISITO_PRICING: "push",
}
UMBRAL_TIEMPO_MS = 300_000
UMBRAL_VISITAS = 3
SECCIONES_PRICING = {"precios", "pricing"}


def _metadata_dict(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def eventos_en_sesion(
    eventos: list[dict], *, inicio_ms: int, demo_expiracion_ms: int
) -> list[dict]:
    return [
        e
        for e in eventos
        if inicio_ms <= int(e.get("timestamp_evento") or 0) < demo_expiracion_ms
    ]


def eval_tiempo_seccion_precios(eventos_sesion: list[dict]) -> tuple[bool, int | None]:
    total = 0
    disparador = None
    for e in eventos_sesion:
        if e.get("tipo_evento") != "tiempo_seccion":
            continue
        if e.get("seccion") != "precios":
            continue
        meta = _metadata_dict(e.get("metadata"))
        total += int(meta.get("duracion_ms") or 0)
        disparador = int(e.get("idinteraccion") or 0) or disparador
        if total >= UMBRAL_TIEMPO_MS:
            return True, disparador
    return False, None


def eval_visito_pricing(eventos_sesion: list[dict]) -> tuple[bool, int | None]:
    visitas = [
        e
        for e in eventos_sesion
        if e.get("seccion") in SECCIONES_PRICING
        and e.get("tipo_evento") != "inicio_sesion"
    ]
    if len(visitas) >= UMBRAL_VISITAS:
        return True, int(visitas[UMBRAL_VISITAS - 1].get("idinteraccion") or 0) or None
    return False, None


def evaluar_reglas_mvp(eventos_sesion: list[dict]) -> list[dict[str, Any]]:
    """Return list of {regladisparada, canal, idinteraccion} for fulfilled rules."""
    fulfilled: list[dict[str, Any]] = []
    ok, iid = eval_tiempo_seccion_precios(eventos_sesion)
    if ok:
        fulfilled.append(
            {
                "regladisparada": REGLA_TIEMPO_PRECIOS,
                "canal": CANAL_POR_REGLA[REGLA_TIEMPO_PRECIOS],
                "idinteraccion": iid,
            }
        )
    ok, iid = eval_visito_pricing(eventos_sesion)
    if ok:
        fulfilled.append(
            {
                "regladisparada": REGLA_VISITO_PRICING,
                "canal": CANAL_POR_REGLA[REGLA_VISITO_PRICING],
                "idinteraccion": iid,
            }
        )
    return fulfilled
