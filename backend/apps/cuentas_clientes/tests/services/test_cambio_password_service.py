"""CU-O04 — cambio de la contraseña temporal por una definitiva."""

from __future__ import annotations

import pytest

from apps.cuentas_clientes.services.cambio_password_service import (
    CambioPasswordError,
    CambioPasswordService,
)
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.service]

ID_USUARIO = 3


def _credencial_temporal(password: str = "TempInicial1") -> None:
    repo = CredentialRepository()
    for cred in PINOT_STORE["Dim_Credencial"]:
        if cred["idusuario"] == ID_USUARIO:
            cred["contrasena"] = repo.hash_password(password)
            cred["estadocredencial"] = "Cambio contraseña"
            return
    raise AssertionError("El doble no tiene credencial para el usuario de prueba")


class TestCambioPassword:
    def test_activa_la_credencial_al_definir_la_definitiva(self, mock_pinot, mock_kafka):
        """El paso que faltaba: sin él la cuenta quedaba inutilizable."""
        # Arrange
        _credencial_temporal()

        # Act
        data = CambioPasswordService().cambiar(
            user_id=ID_USUARIO,
            password_actual="TempInicial1",
            password_nueva="DefinitivaSegura9",
        )

        # Assert
        assert data["estadocredencial"] == "Activo"
        cred = CredentialRepository().find_by_user_id(ID_USUARIO)
        assert CredentialRepository().verify_password("DefinitivaSegura9", cred["contrasena"])

    def test_rechaza_si_la_actual_no_coincide(self, mock_pinot, mock_kafka):
        """Un token robado no debe bastar para apropiarse de la cuenta."""
        # Arrange
        _credencial_temporal()

        # Act / Assert
        with pytest.raises(CambioPasswordError) as exc:
            CambioPasswordService().cambiar(
                user_id=ID_USUARIO,
                password_actual="LaQueNoEs",
                password_nueva="DefinitivaSegura9",
            )
        assert exc.value.code == "unauthorized"

    def test_rechaza_una_contrasena_nueva_corta(self, mock_pinot, mock_kafka):
        # Arrange
        _credencial_temporal()

        # Act / Assert
        with pytest.raises(CambioPasswordError) as exc:
            CambioPasswordService().cambiar(
                user_id=ID_USUARIO, password_actual="TempInicial1", password_nueva="corta7"
            )
        assert exc.value.code == "validation_error"

    def test_rechaza_repetir_la_misma_contrasena(self, mock_pinot, mock_kafka):
        """Reutilizar la temporal dejaría la cuenta en el mismo riesgo que antes."""
        # Arrange
        _credencial_temporal()

        # Act / Assert
        with pytest.raises(CambioPasswordError) as exc:
            CambioPasswordService().cambiar(
                user_id=ID_USUARIO,
                password_actual="TempInicial1",
                password_nueva="TempInicial1",
            )
        assert exc.value.code == "validation_error"
