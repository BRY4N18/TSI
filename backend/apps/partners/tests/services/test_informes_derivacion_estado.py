"""La derivación de estado de L1 tiene la misma precedencia que la operativa.

`Dim_Partner` **no guarda el estado**: los seis estados de incorporación se
derivan. `ConsultaPartnerService.derivar_estado` es la fuente de verdad, pero su
forma —una consulta a la bitácora por partner— no sirve sobre una página de
cincuenta.

`_derivar_estado` replica la precedencia alimentándose de dos consultas por
lote. Si las dos divergen, el mismo partner tendría un estado en su ficha y otro
en el listado, y nadie sabría cuál creer. Esta prueba las compara sobre los
mismos datos.
"""

from __future__ import annotations

import pytest

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_SANDBOX,
    CAMBIO_SOLICITUD_PRODUCCION,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    ESTADO_REGISTRADO,
    ESTADO_SUSPENDIDO,
    SIN_PLAN,
)
from apps.partners.services.informes_acceso_service import _derivar_estado


def _partner(**kwargs):
    base = {"idpartner": 1, "activo": True, "planapi": "Profesional"}
    base.update(kwargs)
    return base


def _cred(entorno, activo=True):
    return {"entorno": entorno, "activo": activo}


def _evento(tipo, fecha):
    return {"tipo_cambio": tipo, "fecha_cambio": fecha}


class TestPrecedencia:
    def test_suspendido_gana_sobre_todo_lo_demas(self):
        """Un partner suspendido con credencial de producción viva sigue
        suspendido: la suspensión es lo que decide si puede consumir."""
        estado = _derivar_estado(
            _partner(activo=False),
            [_cred(ENTORNO_PRODUCCION)],
            [_evento(CAMBIO_ACTIVACION_SANDBOX, 1)],
        )
        assert estado == ESTADO_SUSPENDIDO

    def test_sin_plan_es_registrado_aunque_la_cadena_este_vacia(self):
        """`''` es el centinela de «sin plan». Una guarda por nulidad
        (`is not None`) sería siempre cierta y nunca daría este estado."""
        assert _derivar_estado(_partner(planapi=SIN_PLAN), [], []) == ESTADO_REGISTRADO

    def test_una_solicitud_reciente_deja_pendiente_de_aprobacion(self):
        estado = _derivar_estado(
            _partner(),
            [_cred(ENTORNO_SANDBOX)],
            [
                _evento(CAMBIO_ACTIVACION_SANDBOX, 10),
                _evento(CAMBIO_SOLICITUD_PRODUCCION, 20),
            ],
        )
        assert estado == ESTADO_PENDIENTE_APROBACION

    def test_una_solicitud_ya_superada_no_deja_pendiente(self):
        """Solo cuenta el **último** evento: una solicitud antigua seguida de
        la activación no deja al partner esperando aprobación para siempre."""
        estado = _derivar_estado(
            _partner(),
            [_cred(ENTORNO_PRODUCCION)],
            [
                _evento(CAMBIO_SOLICITUD_PRODUCCION, 10),
                _evento(CAMBIO_ACTIVACION_SANDBOX, 20),
            ],
        )
        assert estado == ESTADO_PRODUCCION_ACTIVA

    def test_produccion_activa_exige_una_credencial_de_produccion_viva(self):
        assert (
            _derivar_estado(_partner(), [_cred(ENTORNO_PRODUCCION)], [])
            == ESTADO_PRODUCCION_ACTIVA
        )

    def test_una_credencial_de_produccion_revocada_no_da_produccion_activa(self):
        estado = _derivar_estado(
            _partner(), [_cred(ENTORNO_PRODUCCION, activo=False)], []
        )
        assert estado == ESTADO_PRUEBAS_ACTIVO

    def test_pruebas_activo_no_exige_credencial_viva(self):
        """Una credencial de pruebas vencida deja al partner aquí, listo para
        regenerar sin repetir el alta."""
        estado = _derivar_estado(
            _partner(), [], [_evento(CAMBIO_ACTIVACION_SANDBOX, 5)]
        )
        assert estado == ESTADO_PRUEBAS_ACTIVO

    def test_con_plan_y_sin_nada_mas_es_plan_asignado(self):
        assert _derivar_estado(_partner(), [], []) == ESTADO_PLAN_ASIGNADO


@pytest.mark.parametrize(
    "partner,credenciales,eventos",
    [
        (_partner(activo=False), [_cred(ENTORNO_PRODUCCION)], []),
        (_partner(planapi=SIN_PLAN), [], []),
        (_partner(), [_cred(ENTORNO_SANDBOX)], [_evento(CAMBIO_SOLICITUD_PRODUCCION, 9)]),
        (_partner(), [_cred(ENTORNO_PRODUCCION)], []),
        (_partner(), [], [_evento(CAMBIO_ACTIVACION_SANDBOX, 1)]),
        (_partner(), [], []),
    ],
)
def test_coincide_con_la_derivacion_operativa(partner, credenciales, eventos):
    """Dos derivaciones distintas del mismo estado deben coincidir.

    Si divergen, el mismo partner tendría un estado en su ficha y otro en el
    listado — y ninguna de las dos pantallas sabría que la otra discrepa.
    """
    from apps.partners.services.consulta_partner_service import ConsultaPartnerService

    class _HistorialFalso:
        """La versión operativa consulta la bitácora una vez por partner; aquí
        se le entrega la misma lista con la que se alimenta la de lote."""

        @staticmethod
        def list_by_partner(_idpartner, limit=200):
            return eventos

    servicio = ConsultaPartnerService.__new__(ConsultaPartnerService)
    servicio.historial = _HistorialFalso()

    ultimo = max(eventos, key=lambda e: e["fecha_cambio"], default=None)
    operativo = servicio.derivar_estado(
        partner, credenciales=credenciales, ultimo_evento=ultimo
    )

    assert _derivar_estado(partner, credenciales, eventos) == operativo
