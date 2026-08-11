"""Autenticación por credencial de API (RF-APM-001).

Dos poblaciones distintas: la API de datos se autentica con `client_id` +
`client_secret`; las pantallas, con JWT humano. **Ninguno vale en la puerta del
otro**, y ese cruce es lo que más se prueba aquí.

El acceso exige tres condiciones con tres dueños distintos (D2 de #09): la
credencial la valida la autenticación (401); el partner activo y la suscripción
vigente los valida el permiso (403).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from rest_framework import exceptions

from apps.partners.authentication import (
    CredencialAPIAuthentication,
    PartnerAPIUser,
    PartnerHabilitado,
)
from apps.partners.services.secreto_service import SecretoService

pytestmark = [pytest.mark.unit]

SECRETO = "secreto-de-prueba-para-autenticacion"
AHORA = 1_800_000_000_000
NUNCA_EXPIRA = 253402300799000


def _credencial(**over):
    base = {
        "idcredencial": 88,
        "idpartner": 12,
        "idcliente": 100,
        "client_secret_hash": SecretoService().hash(SECRETO),
        "nombre_credencial": "plataforma",
        "entorno": "Producción",
        "activo": True,
        "fecha_expiracion": NUNCA_EXPIRA,
    }
    return {**base, **over}


def _partner(**over):
    return {"idpartner": 12, "idcliente": 100, "activo": True, **over}


class _Pinot:
    """Doble de PinotClient que responde según la tabla consultada."""

    def __init__(self, credencial=None, partner=None):
        self._credencial = credencial
        self._partner = partner

    def query(self, sql, params=None):
        if "Dim_CredencialAPI" in sql:
            return [self._credencial] if self._credencial else []
        if "Dim_Partner" in sql:
            return [self._partner] if self._partner else []
        return []


def _request(client_id="tsi-p12-c88", secret=SECRETO):
    meta = {}
    if client_id is not None:
        meta["HTTP_X_CLIENT_ID"] = client_id
    if secret is not None:
        meta["HTTP_X_CLIENT_SECRET"] = secret
    return SimpleNamespace(META=meta)


def _auth(credencial=None, partner=None):
    return CredencialAPIAuthentication(pinot=_Pinot(credencial, partner))


class TestCredencialValida:
    def test_autentica_y_resuelve_partner_y_credencial(self):
        # Arrange
        auth = _auth(_credencial(), _partner())

        # Act
        usuario, _ = auth.authenticate(_request())

        # Assert
        assert isinstance(usuario, PartnerAPIUser)
        assert usuario.idpartner == 12
        assert usuario.idcredencial == 88
        assert usuario.entorno == "Producción"

    def test_el_cliente_de_api_no_tiene_roles_humanos(self):
        """Para que ningún permiso de pantalla lo acepte por accidente."""
        # Arrange
        auth = _auth(_credencial(), _partner())

        # Act
        usuario, _ = auth.authenticate(_request())

        # Assert
        assert usuario.roles == []


class TestCredencialRechazada:
    def test_credencial_inexistente_falla(self):
        # Arrange
        auth = _auth(credencial=None)

        # Act / Assert
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(_request())

    def test_credencial_revocada_falla(self):
        # Arrange
        auth = _auth(_credencial(activo=False), _partner())

        # Act / Assert
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(_request())

    def test_credencial_vencida_falla(self):
        """La vigencia se deriva del dato, no de que un job la haya marcado."""
        # Arrange
        auth = _auth(_credencial(fecha_expiracion=1000), _partner())

        # Act / Assert
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(_request())

    def test_secreto_incorrecto_falla(self):
        # Arrange
        auth = _auth(_credencial(), _partner())

        # Act / Assert
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(_request(secret="secreto-equivocado"))

    def test_partner_inexistente_falla(self):
        # Arrange
        auth = _auth(_credencial(), partner=None)

        # Act / Assert
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate(_request())

    def test_client_id_malformado_falla_sin_reventar(self):
        # Arrange
        auth = _auth(_credencial(), _partner())

        # Act / Assert
        for malo in ("basura", "tsi-p12", "tsi-xNN-cNN", "tsi-p12-cABC"):
            with pytest.raises(exceptions.AuthenticationFailed):
                auth.authenticate(_request(client_id=malo))


class TestUnJwtHumanoNoAutenticaAqui:
    def test_sin_cabeceras_de_credencial_devuelve_none(self):
        """Devolver None (y no fallar) hace que DRF responda 401 por ausencia de
        credenciales. Un JWT en `Authorization` no abre esta puerta."""
        # Arrange
        auth = _auth(_credencial(), _partner())
        peticion = SimpleNamespace(META={"HTTP_AUTHORIZATION": "Bearer un.jwt.humano"})

        # Act / Assert
        assert auth.authenticate(peticion) is None

    def test_solo_client_id_sin_secreto_no_autentica(self):
        # Arrange
        auth = _auth(_credencial(), _partner())

        # Act / Assert
        assert auth.authenticate(_request(secret=None)) is None

    def test_declara_authenticate_header_para_devolver_401_y_no_403(self):
        # Act / Assert
        assert _auth().authenticate_header(_request()) == "X-Client-Id"


class _PlanRead:
    def __init__(self, vigente):
        self._vigente = vigente

    def suscripcion_vigente(self, idcliente):
        return {"estado": "Activa"} if self._vigente else None


class TestPartnerHabilitado:
    """Condiciones 2 y 3 — autorización (403), no identidad (401)."""

    def _permiso(self, vigente=True):
        return PartnerHabilitado(planes=_PlanRead(vigente))

    def test_permite_cuando_partner_activo_y_suscripcion_vigente(self):
        # Arrange
        usuario = PartnerAPIUser(_partner(), _credencial())
        peticion = SimpleNamespace(user=usuario)

        # Act / Assert
        assert self._permiso().has_permission(peticion, None) is True

    def test_deniega_al_partner_suspendido(self):
        # Arrange
        usuario = PartnerAPIUser(_partner(activo=False), _credencial())
        peticion = SimpleNamespace(user=usuario)
        permiso = self._permiso()

        # Act / Assert
        assert permiso.has_permission(peticion, None) is False
        assert permiso.message == PartnerHabilitado.MENSAJE_PARTNER

    def test_deniega_cuando_la_suscripcion_no_esta_vigente(self):
        """Este era el hueco: un cliente con la suscripción suspendida seguía
        consumiendo la API aunque su partner estuviera perfecto."""
        # Arrange
        usuario = PartnerAPIUser(_partner(), _credencial())
        peticion = SimpleNamespace(user=usuario)
        permiso = self._permiso(vigente=False)

        # Act / Assert
        assert permiso.has_permission(peticion, None) is False
        assert permiso.message == PartnerHabilitado.MENSAJE_SUSCRIPCION

    def test_deniega_a_quien_no_sea_un_cliente_de_api(self):
        """Un usuario humano no puede colarse por esta puerta."""
        # Arrange
        peticion = SimpleNamespace(
            user=SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        )

        # Act / Assert
        assert self._permiso().has_permission(peticion, None) is False
