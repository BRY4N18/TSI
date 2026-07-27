import pytest
from apps.ventas_crm.domain import ConflictError
from apps.ventas_crm.services.entrada_directa_service import EntradaDirectaService

pytestmark = pytest.mark.service

def test_entrada_directa_rechaza_nit_existente():
    class Clientes:
        def exists_by_nit_any(self, nit): return True
    with pytest.raises(ConflictError):
        EntradaDirectaService(Clientes()).registrar({"nombre": "A", "razon_social": "A", "tipo": "Proveedor", "nit_identificacion": "900"})
