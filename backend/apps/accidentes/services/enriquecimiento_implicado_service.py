"""RF-EVI-010 — implicados no conductores (CU-O46), ontología Dim_Implicado."""

from __future__ import annotations

from typing import Any

from core.audit.evidencia_service import AuditEvidenciaService
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository
from core.repositories.evidencia.implicado_repository import (
    ESTADOS_IMPLICADO,
    TIPOS_IMPLICADO,
    ImplicadoRepository,
)


class EnriquecimientoImplicadoService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        implicado_repo: ImplicadoRepository | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.implicado_repo = implicado_repo or ImplicadoRepository()
        self.audit = audit or AuditEvidenciaService()

    def listar(self, idaccidente: str, *, idusuario: int | None = None) -> list[dict[str, Any]]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        items = self.implicado_repo.list_activos_by_accidente(idaccidente)
        if idusuario is not None:
            self.audit.log_consultar_implicados_accidente(
                user_id=idusuario, idaccidente=idaccidente, count=len(items)
            )
        return items

    def registrar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        tipoimplicado: str,
        estadoimplicado: str,
        genero: str | None = None,
        edad: int | None = None,
    ) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")

        tipo = str(tipoimplicado or "").strip()
        estado = str(estadoimplicado or "").strip()
        if not tipo or not estado:
            raise ValueError("tipoimplicado y estadoimplicado son requeridos")
        if tipo not in TIPOS_IMPLICADO:
            raise ValueError(
                "tipoimplicado inválido; use Peaton, Pasajero, Testigo u Otro"
            )
        if estado not in ESTADOS_IMPLICADO:
            raise ValueError(
                "estadoimplicado inválido; use Ileso, Lesionado, Fallecido o Desconocido"
            )
        if edad is not None:
            try:
                edad = int(edad)
            except (TypeError, ValueError) as exc:
                raise ValueError("edad debe ser un entero ≥ 0") from exc
            if edad < 0:
                raise ValueError("edad debe ser un entero ≥ 0")

        gen = str(genero).strip() if genero is not None and str(genero).strip() else None

        record = self.implicado_repo.create(
            idaccidente=idaccidente,
            tipoimplicado=tipo,
            estadoimplicado=estado,
            genero=gen,
            edad=edad,
        )
        self.audit.log_registrar_implicado_accidente(
            user_id=idusuario,
            idaccidente=idaccidente,
            idimplicado=record["idimplicado"],
        )
        return record

    def desactivar(
        self, *, idaccidente: str, idimplicado: int, idusuario: int
    ) -> dict[str, Any]:
        current = self.implicado_repo.find_by_id(idimplicado)
        if not current or current.get("idaccidente") != idaccidente:
            raise LookupError("Implicado no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        record = self.implicado_repo.soft_delete(idimplicado=idimplicado)
        assert record is not None
        self.audit.log_desactivar_implicado_accidente(
            user_id=idusuario,
            idaccidente=idaccidente,
            idimplicado=idimplicado,
        )
        return record
