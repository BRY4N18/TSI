from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.asignacion_repository import AsignacionRepository

class AsignacionAutomaticaService:
    ROLE_BY_ORG = {"Público": "GerenteCuentasPublicas", "Privado": "GerenteVentas"}
    def __init__(self, prospectos=None, asignaciones=None, pinot=None, roles=None):
        self.prospectos = prospectos or ProspectoRepository()
        self.asignaciones = asignaciones or AsignacionRepository()
        self.pinot = pinot or PinotClient()
        self.roles = roles or RoleRepository()
    def asignar(self, prospecto):
        role = self.ROLE_BY_ORG[prospecto["tipo_organizacion"]]
        # Pinot no admite JOIN entre tablas: la resolución rol -> usuarios se hace
        # en dos consultas, igual que `RoleRepository.list_user_ids_for_role`.
        role_user_ids = self.roles.list_user_ids_for_role(role)
        if not role_user_ids: return None
        rows = self.pinot.query(
            "SELECT idusuario FROM Dim_Usuarios WHERE idusuario IN %(ids)s AND activo = true",
            {"ids": role_user_ids},
        ) or []
        candidates = sorted(int(row["idusuario"]) for row in rows)
        if not candidates: return None
        owner = min(candidates, key=lambda uid: (self.prospectos.count_active_by_user(uid), uid))
        updated = self.prospectos.update(prospecto["idprospecto"], {"idusuario": owner})
        assignment = self.asignaciones.create({"idprospecto": prospecto["idprospecto"],
            "idusuariogerenteanterior": None, "idusuariogerenteactual": owner,
            "tipoasignacion": "automatica", "motivo": None})
        return {"prospecto": updated, "asignacion": assignment}
