"""Lista de denegacion en memoria — cierra la ventana de ingesta (RNF-PAC-001).

El problema que resuelve
------------------------
Revocar y suspender escriben por Kafka, y **Pinot tarda 5-15 s en ingerirlo**.
Si la autenticacion de #08 solo mirase `Dim_CredencialAPI.activo`, una credencial
recien revocada **seguiria sirviendo datos durante esa ventana** — lo contrario
de lo que necesita una respuesta a incidente (`research.md` Decision 2).

Es un PUENTE, no una fuente de verdad paralela
----------------------------------------------
Pasado el TTL, la revocacion ya es visible en Pinot y esta lista deja de hacer
falta. `Dim_Partner.activo` y `Dim_CredencialAPI.activo` siguen siendo la unica
fuente de verdad (RN-PAC-012): esto solo adelanta un rechazo que Pinot confirmara
unos segundos despues. Nunca se consulta para AUTORIZAR, solo para DENEGAR.

Por que se llavea por `idcredencial` y no por `client_id`
---------------------------------------------------------
`client_id` **no es una columna** de `Dim_CredencialAPI`: es derivado
(`tsi-p{idpartner}-c{idcredencial}`, ver `SecretoService.generar_client_id`).
Guardar el derivado obligaria a reconstruirlo en cada punto de escritura y a
acertar con el `idpartner`; la clave real es el id de la credencial.

Deuda declarada (`plan.md`)
---------------------------
Vive en el cache de Django, que en este despliegue es `LocMemCache`: **por
proceso**. Con un proceso es exacta; con N, la revocacion solo cerraria la
ventana en el que la atendio. Es la MISMA deuda que el throttle de #08, no una
nueva: escalar horizontalmente exige un almacen compartido.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache

# Algo mayor que la ventana de ingesta de Pinot (5-15 s). Configurable para no
# tener que tocar codigo si esa ventana cambia (RNF-PAC-005).
TTL_SEGUNDOS_POR_DEFECTO = 60


class DenylistCredenciales:
    """Alta, consulta y retirada de credenciales denegadas al vuelo."""

    def __init__(self, ttl_segundos: int | None = None):
        self.ttl_segundos = int(
            ttl_segundos
            if ttl_segundos is not None
            else getattr(settings, "PARTNERS_DENYLIST_TTL_SEGUNDOS", TTL_SEGUNDOS_POR_DEFECTO)
        )

    @staticmethod
    def _clave(idcredencial: int) -> str:
        return f"partners:denylist:{int(idcredencial)}"

    def denegar(self, idcredencial: int) -> None:
        """Marca una credencial como no servible hasta que Pinot se ponga al dia."""
        cache.set(self._clave(idcredencial), True, timeout=self.ttl_segundos)

    def denegar_varias(self, idcredenciales) -> int:
        """La cascada de suspension deniega N credenciales de golpe (§ 15 D4)."""
        total = 0
        for idcredencial in idcredenciales:
            self.denegar(idcredencial)
            total += 1
        return total

    def contiene(self, idcredencial: int) -> bool:
        return bool(cache.get(self._clave(idcredencial), False))

    def retirar(self, idcredencial: int) -> None:
        """La reactivacion levanta la denegacion de lo que restituye.

        Sin esto, un partner reactivado seguiria rechazado hasta que caducase el
        TTL: la reactivacion no seria tal durante ese minuto (§ 15 D4).
        """
        cache.delete(self._clave(idcredencial))

    def retirar_varias(self, idcredenciales) -> int:
        total = 0
        for idcredencial in idcredenciales:
            self.retirar(idcredencial)
            total += 1
        return total
