"""Generacion y hash de secretos de credencial API (RNF-PON-002, RF-O49.2).

REGLA CENTRAL DEL MODULO: el secreto en claro existe UNICAMENTE dentro del
stack de la peticion que lo genera. No se persiste, no se registra en logs ni
trazas, no se incluye en mensajes de error y NO VIAJA AL EVENTO KAFKA — al
topic solo va el hash.

Si el partner lo pierde, la via es emitir una credencial nueva. La
irrecuperabilidad es el requisito (RF-O49.2), no un efecto colateral que
convenga suavizar.
"""

from __future__ import annotations

import secrets

import bcrypt

from apps.partners.domain_constants import SECRETO_BYTES

# Mismo factor de coste que `credential_repository.BCRYPT_ROUNDS`. No bajarlo
# para ganar latencia: si el p95 aprieta, la mitigacion es cachear el resultado
# de la verificacion durante una ventana corta (ver #08 research Decision 2),
# nunca debilitar el hash.
BCRYPT_ROUNDS = 12


class SecretoService:
    """Genera secretos de alta entropia y los hashea con bcrypt."""

    def generar(self) -> str:
        """Secreto en claro, ~256 bits de entropia criptografica.

        `token_urlsafe` produce texto seguro para cabeceras HTTP y para que el
        partner lo copie sin escapes.
        """
        return secrets.token_urlsafe(SECRETO_BYTES)

    def hash(self, secreto: str) -> str:
        """Hash bcrypt. Es lo unico que se persiste."""
        return bcrypt.hashpw(
            secreto.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        ).decode("utf-8")

    def verificar(self, secreto: str, hash_almacenado: str) -> bool:
        """Comprueba un secreto contra su hash (lo usara CU-O51 en #08)."""
        try:
            return bcrypt.checkpw(
                secreto.encode("utf-8"), hash_almacenado.encode("utf-8")
            )
        except (ValueError, TypeError):
            # Hash malformado o vacio: se trata como no coincidente, nunca como
            # excepcion que pudiera filtrar detalle del almacenamiento.
            return False

    def generar_client_id(self, idpartner: int, idcredencial: int) -> str:
        """Identificador publico de la credencial.

        No es secreto: viaja en cada peticion y puede aparecer en logs. Por eso
        no se deriva del secreto ni lo revela.
        """
        return f"tsi-p{idpartner}-c{idcredencial}"
