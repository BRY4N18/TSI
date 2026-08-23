"""Session validation service — JWT + Fact_Session per request."""

from __future__ import annotations

import logging

from core.jwt_utils import TokenExpiredError, TokenInvalidError, verify_access_token
from core.repositories.cuentas_clientes.session_repository import SessionRepository

logger = logging.getLogger(__name__)


class SessionValidationError(Exception):
    """Session is not valid for access."""


class AlmacenSesionNoDisponible(Exception):
    """No se pudo **comprobar** si la sesion sigue activa.

    Distinta de `SessionValidationError` a proposito: «revocada» y «no se puede
    comprobar si esta revocada» son cosas distintas y antes se trataban igual,
    porque ambas terminaban en excepcion. Solo la segunda admite degradacion, y
    solo en la cadena critica (PG-SEC-003).
    """


class SessionValidationService:
    """Validates JWT signature and session state on each protected request."""

    def __init__(self, session_repo: SessionRepository | None = None):
        self.session_repo = session_repo or SessionRepository()

    def validate_token_and_session(self, token: str, *, degradable: bool = False) -> dict:
        """Valida firma y sesion. `degradable` solo lo activa la cadena critica.

        Con `degradable=True`, una **caida del almacen** deja pasar la peticion
        con la validacion criptografica ya hecha —firma, expiracion, emisor—,
        renunciando unicamente a comprobar la revocacion. Una sesion **revocada**
        se sigue denegando: eso no es degradacion, es la respuesta correcta.

        Ver `core/seguridad/cadena_critica.py` para el porque y las nueve rutas.
        """
        try:
            claims = verify_access_token(token)
        except TokenExpiredError as exc:
            raise SessionValidationError("Token expired") from exc
        except TokenInvalidError as exc:
            raise SessionValidationError("Invalid token") from exc

        session_id = int(claims["session_id"])

        try:
            activa = self.session_repo.is_active(session_id)
        except Exception as exc:
            # Aqui NO se sabe si la sesion es valida: el almacen no responde.
            if not degradable:
                raise AlmacenSesionNoDisponible(
                    "No se pudo verificar el estado de la sesion"
                ) from exc
            # Cadena critica: se continua con lo que la criptografia ya probo.
            # Se registra en WARNING porque es una excepcion de seguridad real y
            # debe poder auditarse despues: sin esta linea, la ventana en que se
            # admitieron sesiones sin verificar no queda en ninguna parte.
            logger.warning(
                "Sesion %s admitida sin verificar revocacion: almacen no disponible "
                "y la peticion pertenece a la cadena critica (PG-SEC-003).",
                session_id,
            )
            return claims

        if not activa:
            # Revocada de verdad. Se deniega **tambien** en la cadena critica.
            raise SessionValidationError("Session closed or revoked")

        return claims
