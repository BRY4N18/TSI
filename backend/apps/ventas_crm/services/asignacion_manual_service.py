from apps.ventas_crm.domain import ConflictError, ForbiddenError, NotFoundError, ValidationError
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.asignacion_repository import AsignacionRepository

class AsignacionManualService:
    def __init__(self, prospectos=None, asignaciones=None):
        self.prospectos, self.asignaciones = prospectos or ProspectoRepository(), asignaciones or AsignacionRepository()
    def asignar(self, idprospecto, data, *, user_id, roles):
        prospecto = self.prospectos.find_by_id(idprospecto)
        if not prospecto: raise NotFoundError("Prospecto no encontrado")
        if not prospecto.get("activo", True): raise ConflictError("Prospecto terminal")
        target, motivo = data.get("idusuariogerenteactual"), data.get("motivo")
        if not target or not motivo: raise ValidationError("idusuariogerenteactual y motivo son requeridos")
        owner = prospecto.get("idusuario")
        if owner is None and "Administrador" not in roles: raise ForbiddenError("Solo Administrador asigna huérfanos")
        if owner is not None and user_id != owner and "Administrador" not in roles: raise ForbiddenError("No es dueño del prospecto")
        if data.get("idusuario_esperado") != owner: raise ConflictError("Asignación desactualizada")
        updated = self.prospectos.update(idprospecto, {"idusuario": int(target)})
        assignment = self.asignaciones.create({"idprospecto": idprospecto, "idusuariogerenteanterior": owner,
            "idusuariogerenteactual": int(target), "tipoasignacion": "manual", "motivo": motivo})
        return {"prospecto": updated, "asignacion": assignment}
