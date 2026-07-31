"""Migrate Dim_UnidadEmergencia: zonacobertura (STRING) → idcondado (INT).

1. POST schema override (add idcondado; keep zonacobertura — Pinot add-only)
2. Reload REALTIME segments (new columns return 0 docs until reload)
3. Backfill Kafka snapshots so Pinot upserts populate idcondado

  docker exec -e DJANGO_SETTINGS_MODULE=config.settings -e PYTHONPATH=/app \\
    accidentes-django python /app/scripts/migrate_unidad_idcondado.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

PINOT_CONTROLLERS = (
    "http://pinot-controller:9000",
    "http://localhost:9000",
)
INT_NULL = -2147483648


def _controller_base() -> str:
    for base in PINOT_CONTROLLERS:
        try:
            r = requests.get(f"{base}/schemas", timeout=3)
            if r.status_code == 200:
                return base
        except requests.RequestException:
            continue
    raise RuntimeError("Pinot controller no reachable")


def _load_schema() -> dict:
    candidates = [
        Path(__file__).resolve().parents[2] / "database" / "esquemas.json",
        Path("/database/esquemas.json"),
    ]
    for path in candidates:
        if path.is_file():
            schemas = json.loads(path.read_text(encoding="utf-8"))
            for schema in schemas:
                if schema.get("schemaName") == "Dim_UnidadEmergencia":
                    return schema
    return {
        "schemaName": "Dim_UnidadEmergencia",
        "dimensionFieldSpecs": [
            {"name": "idunidademergencia", "dataType": "INT"},
            {"name": "idusuario", "dataType": "INT"},
            {"name": "idcliente", "dataType": "INT"},
            {"name": "tipopropiedad", "dataType": "STRING"},
            {"name": "placa", "dataType": "STRING"},
            {"name": "capacidad", "dataType": "STRING"},
            {"name": "zonacobertura", "dataType": "STRING"},
            {"name": "idcondado", "dataType": "INT"},
            {"name": "contactoproveedor", "dataType": "STRING"},
            {"name": "unidademergencia", "dataType": "STRING"},
            {"name": "tipounidademergencia", "dataType": "STRING"},
            {"name": "activo", "dataType": "BOOLEAN"},
        ],
        "metricFieldSpecs": [
            {"name": "latitud", "dataType": "DOUBLE"},
            {"name": "longitud", "dataType": "DOUBLE"},
        ],
        "dateTimeFieldSpecs": [
            {
                "name": "fecha_creacion",
                "dataType": "LONG",
                "format": "1:MILLISECONDS:EPOCH",
                "granularity": "1:MILLISECONDS",
            },
            {
                "name": "fecha_actualizacion",
                "dataType": "LONG",
                "format": "1:MILLISECONDS:EPOCH",
                "granularity": "1:MILLISECONDS",
            },
        ],
        "primaryKeyColumns": ["idunidademergencia"],
    }


def ensure_idcondado_in_schema(schema: dict) -> dict:
    dims = list(schema.get("dimensionFieldSpecs") or [])
    names = {d.get("name") for d in dims}
    if "idcondado" not in names:
        out: list[dict] = []
        for d in dims:
            out.append(d)
            if d.get("name") == "capacidad":
                out.append({"name": "idcondado", "dataType": "INT"})
        if "idcondado" not in {d.get("name") for d in out}:
            out.append({"name": "idcondado", "dataType": "INT"})
        dims = out
    schema["dimensionFieldSpecs"] = dims
    return schema


def schema_has_idcondado(base: str) -> bool:
    check = requests.get(f"{base}/schemas/Dim_UnidadEmergencia", timeout=10)
    if check.status_code != 200:
        return False
    names = {d["name"] for d in check.json().get("dimensionFieldSpecs", [])}
    return "idcondado" in names


def update_schema(base: str, schema: dict) -> bool:
    """Return True if schema was newly updated (caller should reload segments)."""
    if schema_has_idcondado(base):
        print("OK schema already has idcondado — skip update")
        return False
    url = f"{base}/schemas?override=true"
    resp = requests.post(url, json=schema, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Schema update failed {resp.status_code}: {resp.text}")
    print(f"OK schema Dim_UnidadEmergencia → idcondado INT ({resp.status_code})")
    return True


def reload_segments(base: str) -> None:
    """After adding columns, SELECT including them returns 0 docs until reload."""
    url = f"{base}/segments/Dim_UnidadEmergencia/reload?type=REALTIME&forceDownload=false"
    resp = requests.post(url, timeout=60)
    if resp.status_code not in (200, 201):
        print(f"WARN segment reload {resp.status_code}: {resp.text[:200]}")
        return
    print(f"OK segment reload: {resp.text[:180]}")
    time.sleep(5)


def _resolve_idcondado(row: dict[str, Any]) -> int | None:
    for key in ("idcondado", "zonacobertura"):
        raw = row.get(key)
        if raw is None or raw == "" or raw == "null":
            continue
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            continue
        if parsed == INT_NULL:
            continue
        return parsed
    return None


def _clean_str(value: Any) -> Any:
    if value is None or value == "null":
        return None
    return value


def backfill(*, default_idcondado: int | None = 1) -> int:
    import django

    django.setup()
    from core.repositories.red_operativa.unidad_emergencia_repository import (
        UnidadEmergenciaRepository,
    )

    repo = UnidadEmergenciaRepository()
    # Prefer columns that exist on live table; SELECT * after reload is safe.
    # Pinot broker default limit is 10 — must raise it for full backfill.
    rows = repo.pinot.query("SELECT * FROM Dim_UnidadEmergencia LIMIT 10000")
    count = 0
    for row in rows:
        idcondado = _resolve_idcondado(row)
        if idcondado is None and default_idcondado is not None:
            idcondado = int(default_idcondado)
            print(
                f"DEFAULT id={row.get('idunidademergencia')}: "
                f"sin fuente → idcondado={idcondado}"
            )
        if idcondado is None:
            print(f"SKIP id={row.get('idunidademergencia')}: sin idcondado/zonacobertura")
            continue
        # Already migrated?
        existing = row.get("idcondado")
        if (
            existing is not None
            and existing != INT_NULL
            and int(existing) == idcondado
            and _resolve_idcondado({"idcondado": existing}) is not None
        ):
            print(f"OK id={row.get('idunidademergencia')} already idcondado={idcondado}")
            continue
        payload = {
            "idunidademergencia": int(row["idunidademergencia"]),
            "idcliente": int(row["idcliente"]),
            "idcondado": idcondado,
            "tipopropiedad": _clean_str(row.get("tipopropiedad")),
            "placa": _clean_str(row.get("placa")) or "",
            "capacidad": _clean_str(row.get("capacidad")),
            "contactoproveedor": _clean_str(row.get("contactoproveedor")),
            "unidademergencia": _clean_str(row.get("unidademergencia")) or "",
            "tipounidademergencia": _clean_str(row.get("tipounidademergencia")) or "",
            "idusuario": row.get("idusuario") if row.get("idusuario") != INT_NULL else None,
            "activo": bool(row.get("activo", True)),
            "latitud": row.get("latitud"),
            "longitud": row.get("longitud"),
            "fecha_creacion": row.get("fecha_creacion"),
            "fecha_actualizacion": int(time.time() * 1000),
        }
        repo.kafka.publish(repo.TOPIC, payload)
        count += 1
        print(f"PUB id={payload['idunidademergencia']} idcondado={idcondado}")
    return count


def main() -> int:
    base = _controller_base()
    schema = ensure_idcondado_in_schema(_load_schema())
    updated = update_schema(base, schema)
    if updated:
        reload_segments(base)
    else:
        # Probe: after a prior add without reload, idcondado queries return 0 docs.
        try:
            import django

            django.setup()
            from core.pinot.client import PinotClient

            probe = PinotClient().query(
                "SELECT idunidademergencia, idcondado FROM Dim_UnidadEmergencia LIMIT 1"
            )
            total = PinotClient().query("SELECT count(*) AS c FROM Dim_UnidadEmergencia")
            ntotal = int((total[0] or {}).get("c") or 0) if total else 0
            if ntotal > 0 and not probe:
                print("WARN idcondado query empty while table has rows — reloading segments")
                reload_segments(base)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN probe skipped: {exc}")
    # Units created before idcondado existed have null zona; default 1 for demo.
    import os

    raw_default = os.environ.get("MIGRATE_DEFAULT_IDCONDADO", "1").strip()
    default_idcondado: int | None
    if raw_default.lower() in ("", "none", "skip"):
        default_idcondado = None
    else:
        default_idcondado = int(raw_default)
    n = backfill(default_idcondado=default_idcondado)
    print(f"OK backfill Kafka snapshots: {n} unidades")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
