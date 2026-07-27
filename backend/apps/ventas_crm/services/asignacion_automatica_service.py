from core.pinot.client import PinotClient
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository
from core.repositories.ventas_crm.asignacion_repository import AsignacionRepository

class AsignacionAutomaticaService:
    ROLE_BY_ORG = {"Público": "GerenteCuentasPublicas", "Privado": "GerenteVentas"}
    def __init__(self, prospectos=None, asignaciones=None, pinot=None):
        self.prospectos = prospectos or ProspectoRepository()
        self.asignaciones = asignaciones or AsignacionRepository()
        self.pinot = pinot or PinotClient()
    def asignar(self, prospecto):
        role = self.ROLE_BY_ORG[prospecto["tipo_organizacion"]]
        rows = self.pinot.query(
            """SELECT u.idusuario FROM Dim_Usuarios u JOIN Dim_Usuario_Rol ur ON u.idusuario = ur.idusuario
               JOIN Dim_Rol r ON ur.idrol = r.idrol WHERE u.activo = true AND r.activo = true AND r.rol = %(role)s""",
            {"role": role},
        ) or []
        candidates = sorted(int(row["idusuario"]) for row in rows)
        if not candidates: return None
        owner = min(candidates, key=lambda uid: (self.prospectos.count_active_by_user(uid), uid))
        updated = self.prospectos.update(prospecto["idprospecto"], {"idusuario": owner})
        assignment = self.asignaciones.create({"idprospecto": prospecto["idprospecto"],
            "idusuariogerenteanterior": None, "idusuariogerenteactual": owner,
            "tipoasignacion": "automatica", "motivo": None})
        return {"prospecto": updated, "asignacion": assignment}
