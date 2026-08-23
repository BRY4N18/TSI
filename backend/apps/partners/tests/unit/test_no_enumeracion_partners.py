"""PG-SEC-001 — un partner no puede enumerar el padrón ajeno iterando ids.

Las vistas cortaban con `404 Partner no encontrado` antes de comprobar la
propiedad, y solo después devolvían `403` si el partner era ajeno. Para un
Partner de integración eso es un oráculo: distingue «no existe» de «existe y no
es tuyo» sin llegar a ver un dato, y con eso deduce cuántos partners hay y en qué
rangos de id — es decir, qué competidores son clientes de TSI.

La separación era deliberada (ver el comentario que había en `metricas_views.py`)
y su razón era buena: que un id no exista no es un problema de permisos. Lo que
se comprueba aquí es la resolución del conflicto: el diagnóstico preciso se
conserva **para el gestor**, y se unifica para todos los demás.

Ver `decisiones-pendientes.md` #51.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.partners.permissions import (
    DENEGACION_UNIFICADA,
    PartnerInexistenteError,
    PropiedadPartnerError,
    resolver_partner_visible,
)

pytestmark = pytest.mark.unit

PARTNER_AJENO = {"idpartner": 7, "idcliente": 999}


def _peticion(roles: list[str], idusuario: int = 42):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles, idusuario=idusuario)
    return SimpleNamespace(user=usuario)


class _LookupFijo:
    """Resuelve siempre el mismo cliente, distinto del dueño de PARTNER_AJENO."""

    def resolve_idcliente(self, _idusuario: int) -> int:
        return 1


# --- El caso que importa: quien no es gestor no distingue los dos escenarios ---


def test_inexistente_y_ajeno_son_indistinguibles_para_un_partner(monkeypatch):
    """El corazón de la regla: mismo tipo de error y **mismo texto**.

    Si el mensaje difiere, la fuga sigue existiendo por el cuerpo de la
    respuesta aunque el código HTTP sea 403 en ambos casos — las vistas vuelcan
    `str(exc)` en `detail`.
    """
    peticion = _peticion(["PartnerIntegracion"])
    _forzar_lookup(monkeypatch)

    with pytest.raises(PropiedadPartnerError) as inexistente:
        resolver_partner_visible(peticion, None)

    with pytest.raises(PropiedadPartnerError) as ajeno:
        resolver_partner_visible(peticion, PARTNER_AJENO)

    assert str(inexistente.value) == str(ajeno.value)
    assert str(inexistente.value) == DENEGACION_UNIFICADA


def test_un_partner_nunca_recibe_el_error_de_inexistencia(monkeypatch):
    """`PartnerInexistenteError` viaja a un 404; no debe alcanzar a un no gestor."""
    _forzar_lookup(monkeypatch)
    peticion = _peticion(["PartnerIntegracion"])

    with pytest.raises(PropiedadPartnerError):
        resolver_partner_visible(peticion, None)


@pytest.mark.parametrize(
    "roles", [["PartnerIntegracion"], ["Operador"], ["Cliente"], []]
)
def test_ningun_rol_no_gestor_distingue_los_casos(monkeypatch, roles):
    _forzar_lookup(monkeypatch)
    peticion = _peticion(roles)

    with pytest.raises(PropiedadPartnerError) as exc:
        resolver_partner_visible(peticion, None)

    assert str(exc.value) == DENEGACION_UNIFICADA


# --- El gestor conserva el diagnóstico preciso ---


@pytest.mark.parametrize("rol", ["Administrador", "DesarrolladorAPIs"])
def test_el_gestor_si_distingue_un_id_inexistente(rol):
    """A quien puede operar sobre cualquier partner, el 404 no le revela nada.

    Sin esto la corrección degradaría el diagnóstico de la consola de gestión,
    que es justo lo que el diseño anterior quería evitar.
    """
    with pytest.raises(PartnerInexistenteError):
        resolver_partner_visible(_peticion([rol]), None)


@pytest.mark.parametrize("rol", ["Administrador", "DesarrolladorAPIs"])
def test_el_gestor_accede_a_un_partner_ajeno(rol):
    """Operar sobre partners ajenos es precisamente su trabajo."""
    assert resolver_partner_visible(_peticion([rol]), PARTNER_AJENO) is PARTNER_AJENO


# --- El caso legítimo sigue funcionando ---


def test_el_partner_accede_a_lo_suyo(monkeypatch):
    _forzar_lookup(monkeypatch)
    propio = {"idpartner": 3, "idcliente": 1}

    assert resolver_partner_visible(_peticion(["PartnerIntegracion"]), propio) is propio


def _forzar_lookup(monkeypatch):
    """Evita que `verificar_propiedad` consulte el almacén real."""
    import apps.soporte_cliente.services.cliente_lookup_service as modulo

    monkeypatch.setattr(modulo, "ClienteLookupService", _LookupFijo)
