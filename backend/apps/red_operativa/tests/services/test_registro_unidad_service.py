import pytest

from unittest.mock import patch

from apps.red_operativa.services.proveedor_access_service import ProveedorAccessError
from apps.red_operativa.services.registro_unidad_service import RegistroUnidadService

PROVEEDOR = {"user_id": 3, "roles": ["Cliente"]}


@pytest.mark.service
class TestRegistroUnidadService:
    def _valid_data(self, **overrides):
        data = {
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "SVC-001",
            "contactoproveedor": "5551234",
            "unidademergencia": "Ambulancia Sur",
            "tipounidademergencia": "Ambulancia",
            "gmail": "unidad-svc@test.com",
        }
        data.update(overrides)
        return data

    def test_registrar_when_valid_creates_unidad(self, mock_pinot, mock_kafka):
        service = RegistroUnidadService()
        result = service.registrar(self._valid_data(), **PROVEEDOR)
        assert result["placa"] == "SVC-001"
        assert result["activo"] is True
        assert result["idcliente"] == 1
        assert result.get("usuario_creado") is True
        assert "invitacion_enviada" in result
        assert "password" not in result
        assert "temp_password" not in result

    def test_registrar_when_sin_gmail_crea_unidad_sin_usuario(self, mock_pinot, mock_kafka):
        # Arrange — SRS 3.5.1 / RF-O39.5-6: gmail es opcional en el alta
        # individual; la unidad queda en el catálogo sin acceso propio.
        service = RegistroUnidadService()
        data = self._valid_data(placa="SVC-SIN-GMAIL")
        data.pop("gmail")

        # Act
        result = service.registrar(data, **PROVEEDOR)

        # Assert
        assert result["placa"] == "SVC-SIN-GMAIL"
        assert result["activo"] is True
        assert result.get("idusuario") is None
        assert result["usuario_creado"] is False
        assert result["invitacion_enviada"] is False

    def test_registrar_when_placa_duplicada_raises_value_error(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        service = RegistroUnidadService()
        data = self._valid_data(placa=mock_unidad_emergencia["placa"], gmail="otra@test.com")
        with pytest.raises(ValueError):
            service.registrar(data, **PROVEEDOR)

    def test_registrar_when_idcondado_invalido_raises_lookup_error(self, mock_pinot, mock_kafka):
        service = RegistroUnidadService()
        data = self._valid_data(idcondado=999999, gmail="condado-bad@test.com")
        with pytest.raises(LookupError):
            service.registrar(data, **PROVEEDOR)

    def test_registrar_when_externa_sin_contacto_raises_key_error(self, mock_pinot, mock_kafka):
        service = RegistroUnidadService()
        data = self._valid_data(contactoproveedor=None, gmail="sin-contacto@test.com")
        with pytest.raises(KeyError):
            service.registrar(data, **PROVEEDOR)

    def test_registrar_when_tipopropiedad_invalido_raises_key_error(self, mock_pinot, mock_kafka):
        service = RegistroUnidadService()
        data = self._valid_data(tipopropiedad="Otro", gmail="tipo-bad@test.com")
        with pytest.raises(KeyError):
            service.registrar(data, **PROVEEDOR)

    def test_registrar_when_admin_raises_access_error(self, mock_pinot, mock_kafka):
        service = RegistroUnidadService()
        with pytest.raises(ProveedorAccessError):
            service.registrar(self._valid_data(), user_id=1, roles=["Administrador"])

    def test_registrar_when_gmail_liga_idusuario(self, mock_pinot, mock_kafka, pinot_store):
        service = RegistroUnidadService()
        result = service.registrar(
            self._valid_data(placa="SVC-GMAIL", gmail="unidad-svc2@test.com"),
            **PROVEEDOR,
        )
        assert result.get("idusuario") is not None
        assert result.get("usuario_creado") is True
        stored = next(
            (
                u
                for u in pinot_store["Dim_UnidadEmergencia"]
                if u.get("placa") == "SVC-GMAIL"
            ),
            None,
        )
        assert stored is not None
        assert stored.get("idusuario") == result["idusuario"]
        assert int(stored["idcliente"]) == 1

    @patch(
        "apps.cuentas_clientes.services.onboarding_notificacion_service."
        "OnboardingNotificacionService.notify_invitacion",
        return_value=False,
    )
    def test_registrar_when_smtp_fails_keeps_unidad(self, _mock_notify, mock_pinot, mock_kafka):
        service = RegistroUnidadService()
        result = service.registrar(
            self._valid_data(placa="SVC-SMTP", gmail="smtp-fail@test.com"),
            **PROVEEDOR,
        )
        assert result["invitacion_enviada"] is False
        assert result.get("invitacion_error")
        assert result["activo"] is True
