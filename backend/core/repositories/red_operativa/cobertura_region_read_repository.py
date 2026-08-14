"""Cobertura geográfica región ↔ unidades activas (CU-O62 / RN-REGON-005).

Regla confirmada: puente Dim_RegionOperativaEstadoRegion.idestadoregion →
Dim_Condado (idestadoregion|idestado) → Dim_UnidadEmergencia.idcondado (activo).
"""

from __future__ import annotations

from core.pinot.client import PinotClient


class CoberturaRegionReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # Sin `LIMIT`, Pinot recorta a 10 filas. Aquí eso no es un detalle de
    # rendimiento: si la región tiene más de 10 condados y los diez que devuelve el
    # recorte no tienen unidades, el conteo da 0 y la región se **despublica sola**,
    # sin revisión humana, teniendo cobertura real. Es la única acción que el SRS
    # permite al sistema tomar por su cuenta, así que un falso positivo saca de
    # operación una zona que sí podía atender casos.
    LIMITE_CONDADOS = 1000
    LIMITE_UNIDADES = 10000

    def count_unidades_activas(self, idregionoperativa: int) -> int:
        idscondado = self._condados_de_la_region(idregionoperativa)
        if not idscondado:
            return 0
        rows = self.pinot.query(
            """
            SELECT idunidademergencia FROM Dim_UnidadEmergencia
            WHERE idcondado IN %(idscondado)s AND activo = true
            LIMIT %(limite)s
            """,
            {"idscondado": idscondado, "limite": self.LIMITE_UNIDADES},
        )
        return len(rows)

    def _condados_de_la_region(self, idregionoperativa: int) -> list[int]:
        links = self.pinot.query(
            "SELECT idestadoregion FROM Dim_RegionOperativaEstadoRegion "
            "WHERE idregionoperativa = %(idregionoperativa)s LIMIT %(limite)s",
            {"idregionoperativa": idregionoperativa, "limite": self.LIMITE_CONDADOS},
        )
        idsestado = [row["idestadoregion"] for row in links]
        if not idsestado:
            return []
        condados = self.pinot.query(
            "SELECT idcondado FROM Dim_Condado WHERE idestado IN %(idsestado)s "
            "LIMIT %(limite)s",
            {"idsestado": idsestado, "limite": self.LIMITE_CONDADOS},
        )
        # Fallback: algunos seeds usan idestadoregion en lugar de idestado
        if not condados:
            condados = self.pinot.query(
                "SELECT idcondado FROM Dim_Condado WHERE idestadoregion IN %(idsestado)s "
                "LIMIT %(limite)s",
                {"idsestado": idsestado, "limite": self.LIMITE_CONDADOS},
            )
        return [row["idcondado"] for row in condados]
