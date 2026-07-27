from apps.ventas_crm.domain import ConflictError, ValidationError
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository

class EntradaDirectaService:
    REQUIRED = {"nombre", "razon_social", "tipo", "nit_identificacion"}
    def __init__(self, clientes=None): self.clientes = clientes or ClienteRepository()
    def registrar(self, data):
        missing = self.REQUIRED - set(k for k, v in data.items() if v not in (None, ""))
        if missing: raise ValidationError(f"Campos requeridos: {', '.join(sorted(missing))}")
        if self.clientes.exists_by_nit_any(data["nit_identificacion"]): raise ConflictError("NIT ya registrado")
        return self.clientes.create({**data, "idprospecto": None, "admin_local_id": None,
            "estado": "Activo", "estado_onboarding": "Pendiente"})
