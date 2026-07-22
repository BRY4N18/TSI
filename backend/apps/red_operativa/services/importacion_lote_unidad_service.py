"""CU-O56 — importación en lote (todo-o-nada) de unidades de emergencia."""

from __future__ import annotations

from typing import Any

from apps.red_operativa.services.registro_unidad_service import RegistroUnidadService

MAX_FILAS = 500


class ImportacionLoteUnidadService:
    def __init__(self, registro_service: RegistroUnidadService | None = None):
        self.registro_service = registro_service or RegistroUnidadService()

    def importar(self, filas: list[dict[str, Any]]) -> dict[str, Any]:
        if len(filas) > MAX_FILAS:
            raise ValueError(f"El archivo excede el límite de {MAX_FILAS} unidades")

        placas_en_archivo: set[str] = set()
        fallidas: list[dict[str, Any]] = []

        for i, fila in enumerate(filas, start=1):
            placa = fila.get("placa")
            try:
                self.registro_service._validar(fila)
                if placa in placas_en_archivo:
                    raise ValueError(f"placa {placa} duplicada dentro del archivo")
                if self.registro_service.unidad_repo.find_by_placa_activa(placa):
                    raise ValueError(f"Ya existe una unidad activa con placa {placa}")
                if not self.registro_service.unidad_repo.condado_exists(fila["idcondado"]):
                    raise LookupError(f"idcondado {fila['idcondado']} no existe")
                placas_en_archivo.add(placa)
            except (KeyError, ValueError, LookupError) as exc:
                fallidas.append({"fila": i, "motivo": str(exc)})

        if fallidas:
            return {"insertadas": 0, "fallidas": fallidas}

        for fila in filas:
            self.registro_service.unidad_repo.create(fila)

        return {"insertadas": len(filas), "fallidas": []}
