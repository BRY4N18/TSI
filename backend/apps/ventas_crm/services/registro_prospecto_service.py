import re

from apps.ventas_crm.domain import ConflictError, ValidationError
from apps.ventas_crm.demo_tokens import issue_demo_grant
from apps.ventas_crm.services.asignacion_automatica_service import AsignacionAutomaticaService
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_TELEFONO_RE = re.compile(r"^\+?[0-9]{7,15}$")
_TEXTO_RE = re.compile(r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s'-]+$")


class RegistroProspectoService:
    REQUIRED = {
        "nombres",
        "apellidos",
        "gmail",
        "empresa",
        "tipo_organizacion",
        "cargo",
        "telefono",
        "como_nos_conocio",
    }

    def __init__(self, repository=None, auto_assigner=None):
        self.repository = repository or ProspectoRepository()
        self.auto_assigner = auto_assigner or AsignacionAutomaticaService()

    def registrar(self, data: dict) -> dict:
        missing = self.REQUIRED - {k for k, v in data.items() if v not in (None, "")}
        if missing:
            raise ValidationError(f"Campos requeridos: {', '.join(sorted(missing))}")
        if data["tipo_organizacion"] not in {"Público", "Privado"}:
            raise ValidationError("tipo_organizacion inválido")

        nombres = str(data["nombres"]).strip()
        apellidos = str(data["apellidos"]).strip()
        gmail = str(data["gmail"]).strip().lower()
        empresa = str(data["empresa"]).strip()
        cargo = str(data["cargo"]).strip()
        telefono = re.sub(r"[\s\-()]", "", str(data["telefono"]).strip())
        como_nos_conocio = str(data["como_nos_conocio"]).strip()

        if len(nombres) < 2 or not _TEXTO_RE.match(nombres):
            raise ValidationError("nombres debe tener al menos 2 caracteres y contener solo letras")
        if len(apellidos) < 2 or not _TEXTO_RE.match(apellidos):
            raise ValidationError("apellidos debe tener al menos 2 caracteres y contener solo letras")
        if not _EMAIL_RE.match(gmail):
            raise ValidationError("gmail inválido")
        if len(empresa) < 2:
            raise ValidationError("empresa debe tener al menos 2 caracteres")
        if len(cargo) < 2:
            raise ValidationError("cargo debe tener al menos 2 caracteres")
        if not _TELEFONO_RE.match(telefono):
            raise ValidationError(
                "telefono debe contener solo dígitos (opcional + al inicio), entre 7 y 15"
            )
        if len(como_nos_conocio) < 2:
            raise ValidationError("como_nos_conocio debe tener al menos 2 caracteres")

        payload = {
            "nombres": nombres,
            "apellidos": apellidos,
            "gmail": gmail,
            "empresa": empresa,
            "tipo_organizacion": data["tipo_organizacion"],
            "cargo": cargo,
            "telefono": telefono,
            "como_nos_conocio": como_nos_conocio,
            "valor_estimado": data.get("valor_estimado"),
            "demo_expiracion": None,
        }
        if self.repository.find_by_gmail(payload["gmail"]):
            raise ConflictError("gmail ya registrado")
        prospecto = self.repository.create(payload)
        demo_grant = issue_demo_grant(int(prospecto["idprospecto"]))
        assigned = self.auto_assigner.asignar(prospecto)
        if assigned:
            return {
                **assigned["prospecto"],
                "demo_grant": demo_grant,
                "asignacion_automatica": {
                    "ok": True,
                    "idusuariogerenteactual": assigned["prospecto"]["idusuario"],
                    "error": None,
                },
            }
        return {
            **prospecto,
            "demo_grant": demo_grant,
            "asignacion_automatica": {
                "ok": False,
                "idusuariogerenteactual": None,
                "error": "pool_vacio",
            },
        }
