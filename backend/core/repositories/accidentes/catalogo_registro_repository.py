"""Catálogos Dim_TipoReportado / Dim_ReferenciaEstacion (CU-O21)."""

from __future__ import annotations

from core.pinot.client import PinotClient


class CatalogoRegistroRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def listar_tipos_reportado(self) -> list[dict]:
        rows = self.pinot.query(
            """
            SELECT idtiporeportado AS id, tiporeportado AS nombre
            FROM Dim_TipoReportado
            WHERE activo = true
            ORDER BY tiporeportado
            """,
            {},
        )
        return rows

    def listar_referencias_estacion(self) -> list[dict]:
        rows = self.pinot.query(
            """
            SELECT idreferenciaestacion AS id, codigoaeropuerto AS nombre, zonahoraria
            FROM Dim_ReferenciaEstacion
            WHERE activo = true
            ORDER BY codigoaeropuerto
            """,
            {},
        )
        result = []
        for row in rows:
            codigo = row.get("nombre") or ""
            zona = row.get("zonahoraria")
            label = f"{codigo} ({zona})" if zona else codigo
            result.append({"id": row["id"], "nombre": label})
        return result
