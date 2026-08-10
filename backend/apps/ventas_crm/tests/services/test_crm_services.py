import pytest

from apps.ventas_crm.domain import ConflictError, ValidationError
from apps.ventas_crm.permissions import IsCRMUser
from apps.ventas_crm.services.registro_prospecto_service import RegistroProspectoService
from apps.ventas_crm.services.asignacion_automatica_service import AsignacionAutomaticaService
from apps.ventas_crm.services.pipeline_service import PipelineService
from apps.ventas_crm.services.asignacion_manual_service import AsignacionManualService
from apps.ventas_crm.services.conversion_cliente_service import ConversionClienteService
from apps.ventas_crm.services.entrada_directa_service import EntradaDirectaService
from apps.ventas_crm.services.consulta_prospecto_service import ConsultaProspectoService
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository


PAYLOAD = {
    "nombres": "Ana",
    "apellidos": "Perez",
    "gmail": "ana@ex.com",
    "empresa": "Demo SA",
    "tipo_organizacion": "Privado",
    "cargo": "Compras",
    "telefono": "0991234567",
    "como_nos_conocio": "web",
}


@pytest.mark.unit
def test_is_crm_user_allows_gerente():
    # Arrange
    class U:
        is_authenticated = True
        roles = ["GerenteVentas"]

    class R:
        user = U()

    # Act / Assert
    assert IsCRMUser().has_permission(R(), None) is True


@pytest.mark.service
class TestRegistroYAsignacion:
    def test_registro_asigna_gerente_ventas(self, mock_pinot, mock_kafka):
        # Arrange / Act
        result = RegistroProspectoService().registrar(PAYLOAD)
        # Assert
        assert result["etapa_actual"] == "Nuevo"
        assert result["asignacion_automatica"]["ok"] is True
        assert result["idusuario"] == 20

    def test_registro_rechaza_telefono_invalido(self, mock_pinot, mock_kafka):
        with pytest.raises(ValidationError, match="telefono"):
            RegistroProspectoService().registrar({**PAYLOAD, "gmail": "bad.tel@ex.com", "telefono": "abc"})

    def test_registro_acepta_telefono_con_plus(self, mock_pinot, mock_kafka):
        result = RegistroProspectoService().registrar(
            {**PAYLOAD, "gmail": "plus.tel@ex.com", "telefono": "+593999000111"}
        )
        assert result["telefono"] == "+593999000111"

    def test_gmail_duplicado_conflict(self, mock_pinot, mock_kafka):
        RegistroProspectoService().registrar(PAYLOAD)
        with pytest.raises(ConflictError):
            RegistroProspectoService().registrar(PAYLOAD)


@pytest.mark.service
class TestPipelineService:
    def _prospecto_en(self, etapa, mock_pinot, mock_kafka):
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": f"{etapa}@ex.com"})
        svc = PipelineService()
        cur = "Nuevo"
        order = ["Contactado", "Calificado", "Propuesta", "Negociación"]
        for nxt in order:
            if cur == etapa:
                break
            if nxt == etapa or order.index(nxt) <= order.index(etapa) if etapa in order else True:
                out = svc.transicionar(
                    p["idprospecto"],
                    {"etapa_nueva": nxt, "etapa_actual_esperada": cur},
                    user_id=20,
                    roles=["GerenteVentas"],
                )
                p = out["prospecto"]
                cur = nxt
                if cur == etapa:
                    break
        return p

    def test_avance_ok_y_rechaza_salto(self, mock_pinot, mock_kafka):
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": "pipe@ex.com"})
        svc = PipelineService()
        out = svc.transicionar(
            p["idprospecto"],
            {"etapa_nueva": "Contactado", "etapa_actual_esperada": "Nuevo"},
            user_id=20,
            roles=["GerenteVentas"],
        )
        assert out["prospecto"]["etapa_actual"] == "Contactado"
        with pytest.raises(ConflictError):
            svc.transicionar(
                p["idprospecto"],
                {"etapa_nueva": "Propuesta", "etapa_actual_esperada": "Contactado"},
                user_id=20,
                roles=["GerenteVentas"],
            )

    def test_rechaza_ganado_en_pipeline(self, mock_pinot, mock_kafka):
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": "gan@ex.com"})
        with pytest.raises(ValidationError):
            PipelineService().transicionar(
                p["idprospecto"],
                {"etapa_nueva": "Ganado", "etapa_actual_esperada": "Nuevo"},
                user_id=20,
                roles=["GerenteVentas"],
            )


@pytest.mark.service
class TestAsignacionManual:
    def test_huerfano_solo_admin(self, mock_pinot, mock_kafka):
        # Force empty pool by removing role users temporarily
        from conftest import PINOT_STORE

        PINOT_STORE["Dim_Usuario_Rol"][:] = [
            r for r in PINOT_STORE["Dim_Usuario_Rol"] if r["idrol"] not in (7, 8)
        ]
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": "orphan@ex.com"})
        assert p["idusuario"] is None
        with pytest.raises(Exception):
            AsignacionManualService().asignar(
                p["idprospecto"],
                {"idusuariogerenteactual": 20, "motivo": "x", "idusuario_esperado": None},
                user_id=20,
                roles=["GerenteVentas"],
            )
        out = AsignacionManualService().asignar(
            p["idprospecto"],
            {"idusuariogerenteactual": 20, "motivo": "pool vacío — asignación inicial", "idusuario_esperado": None},
            user_id=1,
            roles=["Administrador"],
        )
        assert out["prospecto"]["idusuario"] == 20


@pytest.mark.service
class TestConversionYEntrada:
    def test_conversion_desde_negociacion(self, mock_pinot, mock_kafka):
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": "conv@ex.com"})
        pipe = PipelineService()
        cur = "Nuevo"
        for nxt in ["Contactado", "Calificado", "Propuesta", "Negociación"]:
            p = pipe.transicionar(
                p["idprospecto"],
                {"etapa_nueva": nxt, "etapa_actual_esperada": cur},
                user_id=20,
                roles=["GerenteVentas"],
            )["prospecto"]
            cur = nxt
        out = ConversionClienteService().convertir(
            p["idprospecto"],
            {"tipo": "Aseguradora", "nit_identificacion": "1790001", "etapa_actual_esperada": "Negociación"},
            user_id=20,
            roles=["GerenteVentas"],
            idempotency_key="11111111-1111-1111-1111-111111111111",
        )
        assert out["prospecto"]["motivo_inactividad"] == "convertido"
        assert out["cliente"]["idprospecto"] == p["idprospecto"]

    def test_entrada_directa_admin(self, mock_pinot, mock_kafka):
        out = EntradaDirectaService().registrar(
            {
                "nombre": "GAD",
                "razon_social": "GAD Demo",
                "tipo": "Municipio",
                "nit_identificacion": "1760002",
                "admin_local": {"nombres": "Ana", "apellidos": "Admin", "gmail": "gad.entrada@ex.com"},
            }
        )
        assert out["idprospecto"] is None
        assert out["estado_onboarding"] == "Pendiente"
        assert out["admin_local_id"] is not None

    def test_conversion_rechaza_tipo_faltante(self, mock_pinot, mock_kafka):
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": "conv-sintipo@ex.com"})
        pipe = PipelineService()
        cur = "Nuevo"
        for nxt in ["Contactado", "Calificado", "Propuesta", "Negociación"]:
            p = pipe.transicionar(
                p["idprospecto"],
                {"etapa_nueva": nxt, "etapa_actual_esperada": cur},
                user_id=20,
                roles=["GerenteVentas"],
            )["prospecto"]
            cur = nxt
        with pytest.raises(ValidationError):
            ConversionClienteService().convertir(
                p["idprospecto"],
                {"nit_identificacion": "1790099", "etapa_actual_esperada": "Negociación"},
                user_id=20,
                roles=["GerenteVentas"],
                idempotency_key="22222222-2222-2222-2222-222222222222",
            )

    def test_conversion_rechaza_tipo_invalido(self, mock_pinot, mock_kafka):
        p = RegistroProspectoService().registrar({**PAYLOAD, "gmail": "conv-tipomalo@ex.com"})
        pipe = PipelineService()
        cur = "Nuevo"
        for nxt in ["Contactado", "Calificado", "Propuesta", "Negociación"]:
            p = pipe.transicionar(
                p["idprospecto"],
                {"etapa_nueva": nxt, "etapa_actual_esperada": cur},
                user_id=20,
                roles=["GerenteVentas"],
            )["prospecto"]
            cur = nxt
        with pytest.raises(ValidationError):
            ConversionClienteService().convertir(
                p["idprospecto"],
                {"tipo": "Persona Natural", "nit_identificacion": "1790098", "etapa_actual_esperada": "Negociación"},
                user_id=20,
                roles=["GerenteVentas"],
                idempotency_key="33333333-3333-3333-3333-333333333333",
            )

    def test_entrada_directa_rechaza_tipo_invalido(self, mock_pinot, mock_kafka):
        with pytest.raises(ValidationError):
            EntradaDirectaService().registrar(
                {
                    "nombre": "X",
                    "razon_social": "X SA",
                    "tipo": "Persona Natural",
                    "nit_identificacion": "1760099",
                }
            )


@pytest.mark.service
def test_consulta_filtra_dueno(mock_pinot, mock_kafka):
    RegistroProspectoService().registrar({**PAYLOAD, "gmail": "own@ex.com"})
    mine = ConsultaProspectoService().listar(user_id=20, roles=["GerenteVentas"])
    assert all(p["idusuario"] == 20 for p in mine)
    all_admin = ConsultaProspectoService().listar(user_id=1, roles=["Administrador"])
    assert len(all_admin) >= len(mine)
