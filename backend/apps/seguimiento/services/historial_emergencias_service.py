"""RF-SEG-005 — historial operador con cursor pagination."""

from __future__ import annotations

import json
from typing import Any

from apps.accidentes.domain_constants import ESTADO_CERRADO
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from core.repositories.accidentes.ubicacion_catalogo_repository import UbicacionCatalogoRepository
from core.repositories.despacho.geografia_repository import GeografiaRepository
from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository
from core.pinot.client import PinotClient


class HistorialEmergenciasService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        geografia: GeografiaRepository | None = None,
        catalogo_repo: UbicacionCatalogoRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        pinot: PinotClient | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.geografia = geografia or GeografiaRepository()
        self.catalogo_repo = catalogo_repo or UbicacionCatalogoRepository()
        self.unidades = unidad_repo or UnidadEmergenciaRepository()
        self.pinot = pinot or PinotClient()

    def listar(
        self,
        *,
        cursor: str | None = None,
        limit: int = 20,
        estado: str | None = None,
        idseveridad: int | None = None,
        idunidademergencia: int | None = None,
        fecha_desde: int | None = None,
        fecha_hasta: int | None = None,
        idciudad: int | None = None,
        idestadoregion: int | None = None,
        solo_cerrados: bool = False,
        condados_permitidos: set[int] | None = None,
    ) -> dict[str, Any]:
        rows = self.pinot.query("SELECT * FROM Fact_Accidente", {})
        rows.sort(key=lambda r: r.get("horainicio") or r.get("fechahoraaccidente", 0), reverse=True)

        calles_ciudad = self._resolver_calles_por_ubicacion(idciudad, idestadoregion)

        # Fase 1: filtrar barato (sin tocar Fact_Despacho/catálogos) hasta juntar
        # como mucho `limit` candidatos. El trabajo caro (tiempos, ubicación,
        # unidad) se paga solo por esa página final, no por cada fila escaneada.
        candidatos: list[tuple[dict[str, Any], str, list[dict[str, Any]] | None]] = []
        for acc in rows:
            idaccidente = acc["idaccidente"]
            if cursor and idaccidente >= cursor:
                continue
            est = self.estado.get_current_estado(idaccidente)
            if solo_cerrados and est != ESTADO_CERRADO:
                continue
            if estado and est != estado:
                continue
            if idseveridad is not None and acc.get("idseveridad") != idseveridad:
                continue
            fecha_acc = acc.get("fechahoraaccidente", 0)
            if fecha_desde is not None and fecha_acc < fecha_desde:
                continue
            if fecha_hasta is not None and fecha_acc > fecha_hasta:
                continue
            if calles_ciudad is not None and acc.get("idcalle") not in calles_ciudad:
                continue
            if condados_permitidos is not None:
                idcalle = acc.get("idcalle")
                if idcalle is None:
                    continue
                idcondado = self.geografia.resolve_condado_from_idcalle(int(idcalle))
                if idcondado not in condados_permitidos:
                    continue

            despachos: list[dict[str, Any]] | None = None
            if idunidademergencia is not None:
                despachos = self.pinot.query(
                    "SELECT * FROM Fact_Despacho WHERE idaccidente = %(idaccidente)s",
                    {"idaccidente": idaccidente},
                )
                if not any(
                    int(d.get("idunidademergencia", 0)) == idunidademergencia for d in despachos
                ):
                    continue

            candidatos.append((acc, est, despachos))
            if len(candidatos) >= limit:
                break

        # Fase 2: resolver ubicaciones en un solo lote para toda la página
        # (mismo patrón batch que AccidenteRepository/UbicacionCatalogoRepository).
        idcalles = [acc.get("idcalle") for acc, _, _ in candidatos if acc.get("idcalle")]
        ubicaciones = self.catalogo_repo.resolver_calles(idcalles)

        items: list[dict[str, Any]] = []
        for acc, est, despachos in candidatos:
            idaccidente = acc["idaccidente"]
            if despachos is None:
                despachos = self.pinot.query(
                    "SELECT * FROM Fact_Despacho WHERE idaccidente = %(idaccidente)s",
                    {"idaccidente": idaccidente},
                )
            info = ubicaciones.get(acc.get("idcalle")) or {}
            ubicacion = ", ".join(v for v in (info.get("calle"), info.get("ciudad")) if v)
            items.append(
                {
                    "idaccidente": idaccidente,
                    "fecha": int(acc.get("horainicio") or acc.get("fechahoraaccidente", 0)),
                    "estado": est,
                    "severidad": acc.get("idseveridad", 1),
                    "ubicacion": ubicacion,
                    "tiempos": self._calcular_tiempos(acc, despachos),
                    "unidad_principal": self._unidad_principal(despachos),
                }
            )

        next_cursor = items[-1]["idaccidente"] if len(items) == limit else None
        return {"items": items, "next_cursor": next_cursor}

    def _resolver_calles_por_ubicacion(
        self, idciudad: int | None, idestadoregion: int | None
    ) -> set[int] | None:
        """Mismo patrón de AccidenteRepository.list_activos: resuelve ciudad/estado
        a un set de idcalle sobre el que filtrar (Pinot no hace JOIN aquí)."""
        if idciudad is not None:
            return {c["id"] for c in self.catalogo_repo.listar_calles(idciudad)}
        if idestadoregion is not None:
            condados = self.catalogo_repo.listar_condados(idestadoregion)
            ciudades: set[int] = set()
            for condado in condados:
                ciudades.update(c["id"] for c in self.catalogo_repo.listar_ciudades(condado["id"]))
            calles: set[int] = set()
            for idciudad_estado in ciudades:
                calles.update(c["id"] for c in self.catalogo_repo.listar_calles(idciudad_estado))
            return calles
        return None

    def _calcular_tiempos(self, acc: dict[str, Any], despachos: list[dict[str, Any]]) -> dict[str, Any]:
        """Tiempos clave del caso (RF-SEG-005), basados en el despacho principal
        (el confirmado más temprano). Cada valor en minutos, None si aún no aplica."""
        principal = self._despacho_principal(despachos)
        fecha_accidente = acc.get("fechahoraaccidente")
        respuesta = transito = atencion = None
        if principal and fecha_accidente:
            fechahoradespacho = principal.get("fechahoradespacho")
            fechahorallegada = principal.get("fechahorallegada")
            fechahoraretiro = principal.get("fechahoraretiro")
            if fechahoradespacho:
                respuesta = round((fechahoradespacho - fecha_accidente) / 60000, 1)
            if fechahoradespacho and fechahorallegada:
                transito = round((fechahorallegada - fechahoradespacho) / 60000, 1)
            if fechahorallegada and fechahoraretiro:
                atencion = round((fechahoraretiro - fechahorallegada) / 60000, 1)
        return {
            "respuesta_min": respuesta,
            "transito_min": transito,
            "atencion_min": atencion,
            "duracion_total_min": acc.get("duracionminutos"),
        }

    def _despacho_principal(self, despachos: list[dict[str, Any]]) -> dict[str, Any] | None:
        con_fecha = [d for d in despachos if d.get("fechahoradespacho")]
        if not con_fecha:
            return None
        return min(con_fecha, key=lambda d: d["fechahoradespacho"])

    def _unidad_principal(self, despachos: list[dict[str, Any]]) -> str | None:
        principal = self._despacho_principal(despachos)
        if not principal:
            return None
        unidad = self.unidades.find_by_id(int(principal["idunidademergencia"]))
        return (unidad or {}).get("unidademergencia")

    @staticmethod
    def condados_desde_preferencias(zonas_json: str) -> set[int]:
        try:
            zonas = json.loads(zonas_json or "[]")
            return {int(z) for z in zonas}
        except (json.JSONDecodeError, TypeError, ValueError):
            return set()
