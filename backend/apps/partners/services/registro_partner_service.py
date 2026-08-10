"""RF-PON-001 y RF-PON-002 — registrar el partner (CU-O48).

Un partner es siempre un cliente ya dado de alta: este modulo habilita a los
existentes, nunca los crea (RN-PON-001).
"""

from __future__ import annotations

import re
from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_REGISTRO,
    ESTADO_REGISTRADO,
    SIN_MOTIVO,
)
from core.pinot.client import PinotClient
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.partners.plan_read_repository import PlanReadRepository

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegistroPartnerError(Exception):
    """Registro rechazado. `code` mapea la respuesta HTTP."""

    def __init__(self, code: str, detail: str, **extra: Any):
        self.code = code
        self.detail = detail
        self.extra = extra
        super().__init__(detail)


class RegistroPartnerService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        planes: PlanReadRepository | None = None,
        pinot: PinotClient | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.planes = planes or PlanReadRepository()
        self.pinot = pinot or PinotClient()

    def _cliente_existe(self, idcliente: int) -> bool:
        rows = self.pinot.query(
            "SELECT idcliente FROM Dim_Cliente WHERE idcliente = %(idcliente)s LIMIT 1",
            {"idcliente": idcliente},
        )
        return bool(rows)

    def registrar(
        self,
        *,
        idcliente: int,
        nombrepartner: str,
        contacto_tecnico_nombre: str,
        contacto_tecnico_gmail: str,
        ejecutado_por: str,
    ) -> dict[str, Any]:
        """Registra el perfil. El partner queda SIN plan ni cupo (RF-PON-001).

        Orden de validaciones deliberado: se comprueba todo ANTES de escribir
        nada, para que un rechazo no deje rastro parcial.
        """
        if not str(nombrepartner or "").strip():
            raise RegistroPartnerError("validation_error", "nombrepartner es obligatorio")
        if not str(contacto_tecnico_nombre or "").strip():
            raise RegistroPartnerError(
                "validation_error", "contacto_tecnico_nombre es obligatorio"
            )
        if not _EMAIL.match(str(contacto_tecnico_gmail or "")):
            raise RegistroPartnerError(
                "validation_error", "contacto_tecnico_gmail no tiene formato de correo válido"
            )

        # 1. El cliente debe existir (RN-PON-001). Sin el, no hay partner posible.
        if not self._cliente_existe(idcliente):
            raise RegistroPartnerError(
                "not_found", "El cliente no existe; debe darse de alta primero"
            )

        # 2. Suscripcion vigente (RN-PON-011): el cupo se deriva de ella.
        if not self.planes.suscripcion_vigente(idcliente):
            raise RegistroPartnerError(
                "sin_suscripcion",
                "El cliente no tiene una suscripción vigente; el cupo del partner se deriva de ella",
            )

        # 3. Unicidad 1:1 (RN-PON-002). Pinot no soporta UNIQUE: se valida aqui.
        existente = self.partners.find_by_cliente(idcliente)
        if existente:
            raise RegistroPartnerError(
                "partner_duplicado",
                "El cliente ya tiene un perfil de partner. Para integrar desde varios "
                "sistemas, emita credenciales nombradas dentro del perfil existente",
                idpartner_existente=int(existente["idpartner"]),
            )

        partner = self.partners.create(
            {
                "idcliente": idcliente,
                "nombrepartner": nombrepartner.strip(),
                "contacto_tecnico_nombre": contacto_tecnico_nombre.strip(),
                "contacto_tecnico_gmail": contacto_tecnico_gmail.strip(),
            }
        )

        self.historial.registrar(
            idpartner=int(partner["idpartner"]),
            tipo_cambio=CAMBIO_REGISTRO,
            ejecutado_por=ejecutado_por,
            estado_anterior=SIN_MOTIVO,
            estado_nuevo=ESTADO_REGISTRADO,
        )

        # Respuesta construida EN MEMORIA: releer Pinot devolveria vacio durante
        # los 5-15 s de ingesta (research.md Decision 3).
        return {**partner, "estado": ESTADO_REGISTRADO}
