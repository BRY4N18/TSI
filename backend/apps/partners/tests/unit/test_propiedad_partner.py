"""Control de propiedad: nadie opera sobre el perfil de otro.

Este defecto se omitio por error en Red Operativa, Emergencias y en tres
endpoints de Soporte (`decisiones-pendientes.md` #14). Aqui se centraliza en
`verificar_propiedad` y se cubre con tests para que no vuelva a pasar.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.partners.permissions import (
    PropiedadPartnerError,
    es_gestor,
    es_gestor_informes,
    verificar_propiedad,
)

pytestmark = [pytest.mark.unit]


class _Lookup:
    """Doble de ClienteLookupService."""

    def __init__(self, idcliente):
        self._idcliente = idcliente

    def resolve_idcliente(self, idusuario):
        return self._idcliente


def _request(roles, idusuario=51):
    return SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True, roles=roles, idusuario=idusuario)
    )


PARTNER = {"idpartner": 1, "idcliente": 100}


class TestPropiedad:
    def test_partner_propio_no_lanza(self):
        # Arrange
        request = _request(["PartnerIntegracion"])

        # Act / Assert — no lanza
        verificar_propiedad(request, PARTNER, lookup=_Lookup(100))

    def test_partner_ajeno_lanza(self):
        # Arrange — el usuario pertenece al cliente 999, el partner al 100
        request = _request(["PartnerIntegracion"])

        # Act / Assert
        with pytest.raises(PropiedadPartnerError):
            verificar_propiedad(request, PARTNER, lookup=_Lookup(999))

    def test_partner_sin_cliente_resuelto_lanza(self):
        """Si no se puede resolver el cliente, se deniega: fail-closed."""
        # Arrange
        request = _request(["PartnerIntegracion"])

        # Act / Assert
        with pytest.raises(PropiedadPartnerError):
            verificar_propiedad(request, PARTNER, lookup=_Lookup(None))

    def test_partner_inexistente_lanza(self):
        # Arrange
        request = _request(["PartnerIntegracion"])

        # Act / Assert
        with pytest.raises(PropiedadPartnerError):
            verificar_propiedad(request, None, lookup=_Lookup(100))


class TestExencionDeGestores:
    def test_administrador_opera_sobre_cualquier_partner(self):
        """Su trabajo es operar sobre partners ajenos."""
        # Arrange
        request = _request(["Administrador"])

        # Act / Assert — no lanza aunque el cliente no coincida
        verificar_propiedad(request, PARTNER, lookup=_Lookup(999))

    def test_desarrollador_apis_opera_sobre_cualquier_partner(self):
        # Arrange
        request = _request(["DesarrolladorAPIs"])

        # Act / Assert
        verificar_propiedad(request, PARTNER, lookup=_Lookup(999))

    def test_es_gestor_distingue_los_roles(self):
        # Act / Assert
        assert es_gestor(_request(["Administrador"])) is True
        assert es_gestor(_request(["DesarrolladorAPIs"])) is True
        assert es_gestor(_request(["PartnerIntegracion"])) is False
        assert es_gestor(_request(["Cliente"])) is False
        # FR-014a: el Director lee informes, no opera la consola.
        assert es_gestor(_request(["DirectorTecnologico"])) is False

    def test_es_gestor_informes_incluye_al_director(self):
        assert es_gestor_informes(_request(["Administrador"])) is True
        assert es_gestor_informes(_request(["DesarrolladorAPIs"])) is True
        assert es_gestor_informes(_request(["DirectorTecnologico"])) is True
        assert es_gestor_informes(_request(["PartnerIntegracion"])) is False


class TestVerificarPropiedadNoDevuelveBooleano:
    def test_lanza_en_vez_de_devolver_false(self):
        """Devuelve None y lanza: asi es imposible ignorar el resultado.

        Un `if not verificar_propiedad(...)` olvidado seria justo el error que
        este diseno previene.
        """
        # Arrange
        request = _request(["PartnerIntegracion"])

        # Act
        resultado = verificar_propiedad(request, PARTNER, lookup=_Lookup(100))

        # Assert
        assert resultado is None
