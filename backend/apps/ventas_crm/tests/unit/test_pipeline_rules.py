import pytest
from apps.ventas_crm.domain import ConflictError
from apps.ventas_crm.services.pipeline_service import PipelineService

pytestmark = pytest.mark.unit

def test_pipeline_rechaza_saltos():
    prospecto = {"idprospecto": 1, "idusuario": 20, "activo": True, "etapa_actual": "Nuevo"}
    class Pros:
        def find_by_id(self, _): return prospecto
        def update(self, _, patch): return {**prospecto, **patch}
    with pytest.raises(ConflictError):
        PipelineService(prospectos=Pros()).transicionar(1, {"etapa_actual_esperada": "Nuevo", "etapa_nueva": "Propuesta"}, user_id=20, roles=["GerenteVentas"])
