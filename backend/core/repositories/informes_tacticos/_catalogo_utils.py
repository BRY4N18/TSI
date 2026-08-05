"""Resolución de nombres legibles para los informes tácticos (Pinot, solo lectura).

El sistema de diseño (`design-system.md` §5, "Patrón CRUD operativo") prohíbe
mostrar PKs crudas (`idcondado`, `idcliente`, `idusuario`, etc.) como dato
principal de la UI. Pinot no soporta JOIN, así que estas funciones resuelven
el nombre con una segunda consulta acotada por los IDs ya obtenidos — mismo
patrón que `DespachoRepository._unidades_by_condado`.
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


def unidades_by_id(pinot: PinotClient, ids: list[int]) -> dict[int, dict[str, Any]]:
    if not ids:
        return {}
    rows = pinot.query(
        "SELECT idunidademergencia, unidademergencia, placa FROM Dim_UnidadEmergencia "
        "WHERE idunidademergencia IN %(ids)s",
        {"ids": ids},
    )
    return {
        r["idunidademergencia"]: {"nombre": r["unidademergencia"], "placa": r["placa"]} for r in rows
    }


def condados_by_id(pinot: PinotClient, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    rows = pinot.query(
        "SELECT idcondado, condado FROM Dim_Condado WHERE idcondado IN %(ids)s", {"ids": ids}
    )
    return {r["idcondado"]: r["condado"] for r in rows}


def origenes_despacho(pinot: PinotClient) -> dict[int, str]:
    """Tabla pequeña y estable (3 valores) — se trae completa, sin filtrar por IDs."""
    rows = pinot.query("SELECT idorigendespacho, origendespacho FROM Dim_OrigenDespacho", {})
    return {r["idorigendespacho"]: r["origendespacho"] for r in rows}


def clientes_by_id(pinot: PinotClient, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    rows = pinot.query("SELECT idcliente, nombre FROM Dim_Cliente WHERE idcliente IN %(ids)s", {"ids": ids})
    return {r["idcliente"]: r["nombre"] for r in rows}
