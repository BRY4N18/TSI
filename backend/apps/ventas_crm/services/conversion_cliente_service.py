from apps.ventas_crm.domain import ConflictError, ForbiddenError, NotFoundError, ValidationError
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.pipeline_repository import PipelineRepository

class ConversionClienteService:
    def __init__(self, prospectos=None, clientes=None, pipeline=None):
        self.prospectos, self.clientes, self.pipeline = prospectos or ProspectoRepository(), clientes or ClienteRepository(), pipeline or PipelineRepository()
    def convertir(self, idprospecto, data, *, user_id, roles, idempotency_key):
        if not idempotency_key: raise ValidationError("Idempotency-Key es requerido")
        p = self.prospectos.find_by_id(idprospecto)
        if not p: raise NotFoundError("Prospecto no encontrado")
        if user_id != p.get("idusuario") and "Administrador" not in roles: raise ForbiddenError("No es dueño del prospecto")
        if not p.get("activo", True) or p["etapa_actual"] != "Negociación" or data.get("etapa_actual_esperada") != "Negociación":
            raise ConflictError("Conversión requiere Negociación activa")
        nit = data.get("nit_identificacion")
        if not nit or self.clientes.exists_by_nit_any(nit): raise ConflictError("NIT ya registrado")
        cliente = self.clientes.create({"idprospecto": idprospecto, "nombre": f'{p["nombres"]} {p["apellidos"]}',
            "razon_social": p["empresa"], "tipo": data.get("tipo"), "nit_identificacion": nit, "admin_local_id": None,
            "estado": "Activo", "estado_onboarding": "Pendiente"})
        updated = self.prospectos.update(idprospecto, {"etapa_actual": "Ganado", "activo": False, "motivo_inactividad": "convertido"})
        transicion = self.pipeline.create({"id_prospecto": idprospecto, "etapa_anterior": "Negociación",
            "etapa_nueva": "Ganado", "notas": None, "motivo_perdida": None, "gerente_id": user_id})
        return {"prospecto": updated, "cliente": cliente, "transicion": transicion}
