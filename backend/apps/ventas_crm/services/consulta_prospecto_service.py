from apps.ventas_crm.domain import ForbiddenError, NotFoundError
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.asignacion_repository import AsignacionRepository
from core.repositories.ventas_crm.pipeline_repository import PipelineRepository

class ConsultaProspectoService:
    def __init__(self, prospectos=None, asignaciones=None, pipeline=None):
        self.prospectos, self.asignaciones, self.pipeline = prospectos or ProspectoRepository(), asignaciones or AsignacionRepository(), pipeline or PipelineRepository()
    def listar(self, *, user_id, roles, **filters):
        return self.prospectos.list(owner_id=None if "Administrador" in roles else user_id, **filters)
    def detalle(self, idprospecto, *, user_id, roles):
        p = self.prospectos.find_by_id(idprospecto)
        if not p: raise NotFoundError("Prospecto no encontrado")
        if "Administrador" not in roles and p.get("idusuario") != user_id: raise ForbiddenError("No es dueño del prospecto")
        return {**p, "historial_asignacion": self.asignaciones.list_by_prospecto(idprospecto),
                "historial_pipeline": self.pipeline.list_by_prospecto(idprospecto)}
