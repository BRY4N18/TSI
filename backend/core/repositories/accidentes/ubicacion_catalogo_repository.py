"""Catálogo geográfico Dim_Pais/Dim_Estado/Dim_Condado/Dim_Ciudad/Dim_Calle
para la selección manual en cascada (RF-REG-006 punto 3, Escenario 5)."""

from __future__ import annotations

from core.pinot.client import PinotClient


class UbicacionCatalogoRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def listar_paises(self) -> list[dict]:
        return self.pinot.query(
            "SELECT idpais AS id, pais AS nombre FROM Dim_Pais WHERE activo = true ORDER BY pais"
        )

    def listar_estados(self, idpais: int) -> list[dict]:
        return self.pinot.query(
            """
            SELECT idestado AS id, estado AS nombre FROM Dim_Estado
            WHERE idpais = %(idpais)s AND activo = true ORDER BY estado
            """,
            {"idpais": idpais},
        )

    def listar_condados(self, idestado: int) -> list[dict]:
        return self.pinot.query(
            """
            SELECT idcondado AS id, condado AS nombre FROM Dim_Condado
            WHERE idestado = %(idestado)s AND activo = true ORDER BY condado
            """,
            {"idestado": idestado},
        )

    def listar_ciudades(self, idcondado: int) -> list[dict]:
        return self.pinot.query(
            """
            SELECT idciudad AS id, ciudad AS nombre FROM Dim_Ciudad
            WHERE idcondado = %(idcondado)s AND activo = true ORDER BY ciudad
            """,
            {"idcondado": idcondado},
        )

    def listar_calles(self, idciudad: int) -> list[dict]:
        return self.pinot.query(
            """
            SELECT idcalle AS id, calle AS nombre FROM Dim_Calle
            WHERE idciudad = %(idciudad)s AND activo = true ORDER BY calle
            """,
            {"idciudad": idciudad},
        )

    def resolver_calles(self, idcalles: list[int]) -> dict[int, dict]:
        """Resuelve un lote de idcalle a nombres legibles (calle, ciudad, estado).

        Pinot en este proyecto no usa JOINs entre tablas: se consulta cada
        dimensión por lote (IN) y se combina en Python, igual que los filtros
        geográficos de AccidenteRepository.list_activos.
        """
        idcalles = list({i for i in idcalles if i is not None})
        if not idcalles:
            return {}

        calles = self.pinot.query(
            "SELECT idcalle, calle, idciudad FROM Dim_Calle WHERE idcalle IN %(ids)s",
            {"ids": idcalles},
        )
        idciudades = list({c["idciudad"] for c in calles if c.get("idciudad") is not None})
        ciudades = (
            self.pinot.query(
                "SELECT idciudad, ciudad, idcondado FROM Dim_Ciudad WHERE idciudad IN %(ids)s",
                {"ids": idciudades},
            )
            if idciudades
            else []
        )
        idcondados = list({c["idcondado"] for c in ciudades if c.get("idcondado") is not None})
        condados = (
            self.pinot.query(
                "SELECT idcondado, condado, idestado FROM Dim_Condado WHERE idcondado IN %(ids)s",
                {"ids": idcondados},
            )
            if idcondados
            else []
        )
        idestados = list({c["idestado"] for c in condados if c.get("idestado") is not None})
        estados = (
            self.pinot.query(
                "SELECT idestado, estado FROM Dim_Estado WHERE idestado IN %(ids)s",
                {"ids": idestados},
            )
            if idestados
            else []
        )

        ciudad_por_id = {c["idciudad"]: c for c in ciudades}
        condado_por_id = {c["idcondado"]: c for c in condados}
        estado_por_id = {e["idestado"]: e for e in estados}

        resultado: dict[int, dict] = {}
        for calle in calles:
            ciudad = ciudad_por_id.get(calle.get("idciudad"))
            condado = condado_por_id.get(ciudad["idcondado"]) if ciudad else None
            estado = estado_por_id.get(condado["idestado"]) if condado else None
            resultado[calle["idcalle"]] = {
                "calle": calle.get("calle"),
                "ciudad": ciudad.get("ciudad") if ciudad else None,
                "estado": estado.get("estado") if estado else None,
            }
        return resultado
