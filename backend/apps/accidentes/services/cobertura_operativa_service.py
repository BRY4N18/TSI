"""Cobertura operativa service wrapper."""

from core.repositories.accidentes.region_operativa_repository import RegionOperativaRepository


class CoberturaOperativaService:
    def __init__(self, region_repo: RegionOperativaRepository | None = None):
        self.region_repo = region_repo or RegionOperativaRepository()

    def en_cobertura_por_calle(self, idcalle: int) -> bool:
        idestado = self.region_repo.resolve_estado_from_calle(idcalle)
        if idestado is None:
            return False
        return self.region_repo.is_estado_en_produccion(idestado)
