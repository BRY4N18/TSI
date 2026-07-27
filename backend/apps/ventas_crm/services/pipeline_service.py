from apps.ventas_crm.domain import ConflictError, ForbiddenError, NotFoundError, ValidationError
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.pipeline_repository import PipelineRepository

class PipelineService:
    NEXT = {"Nuevo": "Contactado", "Contactado": "Calificado", "Calificado": "Propuesta", "Propuesta": "Negociación"}
    def __init__(self, prospectos=None, pipeline=None):
        self.prospectos, self.pipeline = prospectos or ProspectoRepository(), pipeline or PipelineRepository()
    def transicionar(self, idprospecto, data, *, user_id, roles):
        p = self.prospectos.find_by_id(idprospecto)
        if not p: raise NotFoundError("Prospecto no encontrado")
        if user_id != p.get("idusuario") and "Administrador" not in roles: raise ForbiddenError("No es dueño del prospecto")
        if not p.get("activo", True): raise ConflictError("Prospecto terminal")
        expected, new = data.get("etapa_actual_esperada"), data.get("etapa_nueva")
        if expected != p["etapa_actual"]: raise ConflictError("Etapa desactualizada")
        if new == "Ganado": raise ValidationError("Ganado requiere conversión")
        if new == "Perdido":
            if not data.get("motivo_perdida"): raise ValidationError("motivo_perdida es requerido")
            patch = {"etapa_actual": new, "activo": False, "motivo_inactividad": "perdido"}
        elif self.NEXT.get(p["etapa_actual"]) == new: patch = {"etapa_actual": new}
        else: raise ConflictError("Transición no permitida")
        updated = self.prospectos.update(idprospecto, patch)
        transition = self.pipeline.create({"id_prospecto": idprospecto, "etapa_anterior": p["etapa_actual"],
            "etapa_nueva": new, "notas": data.get("notas"), "motivo_perdida": data.get("motivo_perdida"), "gerente_id": user_id})
        return {"prospecto": updated, "transicion": transition}
