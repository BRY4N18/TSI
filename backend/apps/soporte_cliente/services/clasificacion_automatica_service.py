"""RF-TIC-001 paso 2 — clasificación automática de tipo_incidencia y prioridad.

research.md Decision 4: sin motor de reglas configurable ni NLP/ML en esta
fase — emergencia activa vía `idaccidente` opcional (nota de implementación en
spec.md RF-TIC-001), luego reglas por palabra clave.
"""

from __future__ import annotations

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_DESCARTADO, ESTADO_FUSIONADO
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository

PRIORIDAD_CRITICO = "crítico"
PRIORIDAD_ALTA = "alta"
PRIORIDAD_MEDIA = "media"
PRIORIDAD_BAJA = "baja"

TIPO_EMERGENCIA_ACTIVA = "emergencia_activa"
TIPO_TECNICA = "tecnica"
TIPO_ACCESO = "acceso"
TIPO_CONSULTA_FUNCIONAL = "consulta_funcional"

_ESTADOS_CASO_INACTIVO = {ESTADO_CERRADO, ESTADO_DESCARTADO, ESTADO_FUSIONADO}

_KEYWORDS_TECNICA = ("no responde", "error 500", "caído", "caido", "inconsistente", "api")
_KEYWORDS_ACCESO = ("acceso", "login", "contraseña", "password", "usuario bloqueado")
_KEYWORDS_CONSULTA = ("cómo", "como", "duda", "consulta", "funciona")

_PRIORIDAD_POR_TIPO = {
    TIPO_TECNICA: PRIORIDAD_ALTA,
    TIPO_ACCESO: PRIORIDAD_MEDIA,
    TIPO_CONSULTA_FUNCIONAL: PRIORIDAD_BAJA,
}


class ClasificacionAutomaticaService:
    def __init__(self, estado_accidente_repo: EstadoAccidenteRepository | None = None):
        self.estado_accidente_repo = estado_accidente_repo or EstadoAccidenteRepository()

    def _tiene_emergencia_activa(self, idaccidente: str | None) -> bool:
        if not idaccidente:
            return False
        estado = self.estado_accidente_repo.get_current_estado(idaccidente)
        return bool(estado) and estado not in _ESTADOS_CASO_INACTIVO

    def clasificar(
        self,
        *,
        tipo: str,
        asunto: str,
        descripcion: str,
        idaccidente: str | None = None,
    ) -> dict[str, str] | None:
        if self._tiene_emergencia_activa(idaccidente):
            return {"tipo_incidencia": TIPO_EMERGENCIA_ACTIVA, "prioridad": PRIORIDAD_CRITICO}

        texto = f"{asunto} {descripcion}".lower()
        for tipo_incidencia, keywords in (
            (TIPO_TECNICA, _KEYWORDS_TECNICA),
            (TIPO_ACCESO, _KEYWORDS_ACCESO),
            (TIPO_CONSULTA_FUNCIONAL, _KEYWORDS_CONSULTA),
        ):
            if any(kw in texto for kw in keywords):
                return {
                    "tipo_incidencia": tipo_incidencia,
                    "prioridad": _PRIORIDAD_POR_TIPO[tipo_incidencia],
                }
        return None
