"""Reparto de permisos de la gestion de acceso (T012).

Las dos naturalezas del modulo se ven aqui mejor que en ningun otro sitio:

* **Revocar es autoservicio.** Lo hace el partner, sin aprobacion de nadie,
  porque esperar autorizacion ante una credencial expuesta es el peor
  comportamiento posible (RN-PAC-001).
* **Suspender y reactivar son control excepcional.** Solo Administrador. Y la
  reactivacion, ademas, no tiene equivalente automatico en ningun job.
"""

from __future__ import annotations

import pytest

from apps.partners.views.estado_acceso_views import ColaAccesoView, EstadoAccesoView
from apps.partners.views.revocacion_views import RevocarCredencialView
from apps.partners.views.suspension_views import (
    ReactivarPartnerView,
    SuspenderPartnerView,
)
from apps.partners.permissions import EsAdministrador, EsPartnerOGestor

pytestmark = pytest.mark.unit


class TestQuienPuedeQue:
    def test_suspender_y_reactivar_son_solo_del_administrador(self):
        assert SuspenderPartnerView.permission_classes == [EsAdministrador]
        assert ReactivarPartnerView.permission_classes == [EsAdministrador]

    def test_la_cola_de_trabajo_es_solo_del_administrador(self):
        """Es su vista de trabajo: qué partners esperan una decisión suya."""
        assert ColaAccesoView.permission_classes == [EsAdministrador]

    def test_revocar_lo_puede_hacer_el_partner(self):
        """No exige Administrador **a propósito**: la revocación es autoservicio
        reactivo. Si este test se «arreglara» poniendo `EsAdministrador`, se
        rompería RN-PAC-001."""
        assert RevocarCredencialView.permission_classes == [EsPartnerOGestor]

    def test_consultar_el_estado_lo_puede_hacer_el_partner(self):
        assert EstadoAccesoView.permission_classes == [EsPartnerOGestor]


class TestRoles:
    @pytest.mark.parametrize(
        "roles,esperado",
        [
            (["Administrador"], True),
            (["DesarrolladorAPIs"], False),
            (["PartnerIntegracion"], False),
            ([], False),
        ],
    )
    def test_es_administrador_no_admite_sustitutos(self, roles, esperado):
        """Ni siquiera el Desarrollador de APIs suspende: cortarle el acceso a
        un partner es una decisión de negocio, no de plataforma."""
        # Arrange
        request = type(
            "R", (), {"user": type("U", (), {"is_authenticated": True, "roles": roles})()}
        )()

        # Act / Assert
        assert EsAdministrador().has_permission(request, None) is esperado

    def test_sin_usuario_autenticado_no_hay_permiso(self):
        request = type("R", (), {"user": None})()
        assert EsAdministrador().has_permission(request, None) is False
        assert EsPartnerOGestor().has_permission(request, None) is False
