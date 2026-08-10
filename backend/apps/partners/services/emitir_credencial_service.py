"""RF-PON-004 y RF-PON-005 — emision de credenciales nombradas (CU-O49).

SEGURIDAD — el secreto en claro:
  * se devuelve UNA sola vez, en el dict de retorno;
  * NO se persiste (solo su hash bcrypt);
  * NO viaja al evento Kafka;
  * NO se registra en la bitacora ni en logs.

Si el partner lo pierde, la via es emitir otra credencial. La
irrecuperabilidad es el requisito (RF-O49.2), no un efecto colateral.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_PRODUCCION,
    CAMBIO_ACTIVACION_SANDBOX,
    ENTORNO_PRODUCCION,
    ENTORNO_SANDBOX,
    ENTORNOS,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    NUNCA_EXPIRA,
    SANDBOX_VIGENCIA_DIAS,
    SIN_ACTIVACION,
    SIN_PLAN,
)
from apps.partners.services.secreto_service import SecretoService
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository


class EmitirCredencialError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class EmitirCredencialService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        secretos: SecretoService | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.secretos = secretos or SecretoService()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _vigencia_sandbox(self) -> int:
        vence = datetime.now(timezone.utc) + timedelta(days=SANDBOX_VIGENCIA_DIAS)
        return int(vence.timestamp() * 1000)

    def emitir(
        self,
        *,
        idpartner: int,
        nombre_credencial: str,
        entorno: str = ENTORNO_SANDBOX,
        ejecutado_por: str,
        excluir_de_unicidad: int | None = None,
    ) -> dict[str, Any]:
        """Emite una credencial y devuelve el secreto EN CLARO una sola vez.

        `excluir_de_unicidad` lo usa la revocacion de #09: el reemplazo lleva el
        MISMO nombre que la revocada, y Pinot todavia la veria activa durante la
        ventana de ingesta, dando una colision falsa que haria fallar una
        operacion urgente.
        """
        nombre = str(nombre_credencial or "").strip()
        if not nombre:
            raise EmitirCredencialError(
                "validation_error", "nombre_credencial es obligatorio y no puede estar vacío"
            )
        if entorno not in ENTORNOS:
            raise EmitirCredencialError("validation_error", f"entorno inválido: {entorno}")

        partner = self.partners.find_by_id(idpartner)
        if not partner:
            raise EmitirCredencialError("not_found", "Partner no encontrado")

        # RN-PON-013 — nada se habilita sobre un partner suspendido.
        if not partner.get("activo", False):
            raise EmitirCredencialError(
                "partner_suspendido", "No se pueden emitir credenciales de un partner suspendido"
            )

        # RF-PON-004 — la guarda compara contra el CENTINELA, no contra None.
        # Con el centinela implicito de Pinot ('null') esta condicion habria
        # sido siempre falsa y un partner sin plan podria emitir credenciales.
        if str(partner.get("planapi", SIN_PLAN)) == SIN_PLAN:
            raise EmitirCredencialError(
                "sin_plan",
                "El partner no tiene plan de acceso asignado; no puede emitir credenciales",
            )

        # RN-PON-014 — nombre unico ENTRE LAS ACTIVAS del mismo entorno.
        if self.credenciales.nombre_en_uso(
            idpartner, entorno, nombre, excluir=excluir_de_unicidad
        ):
            raise EmitirCredencialError(
                "nombre_duplicado",
                f"Ya existe una credencial activa llamada '{nombre}' en {entorno}",
            )

        # Produccion no expira por tiempo: lleva el centinela del ano 9999 para
        # que ningun job de expiracion la alcance (RF-PON-008).
        fecha_expiracion = (
            NUNCA_EXPIRA if entorno == ENTORNO_PRODUCCION else self._vigencia_sandbox()
        )

        secreto = self.secretos.generar()
        credencial = self.credenciales.create(
            {
                "idpartner": idpartner,
                "idcliente": int(partner["idcliente"]),
                "client_secret_hash": self.secretos.hash(secreto),  # solo el hash persiste
                "nombre_credencial": nombre,
                "entorno": entorno,
                "fecha_expiracion": fecha_expiracion,
            }
        )

        # Snapshot de la PRIMERA activacion de pruebas. La vigencia real vive
        # por credencial; estos campos son historia, no fuente de verdad.
        if entorno == ENTORNO_SANDBOX and int(
            partner.get("sandbox_activado", SIN_ACTIVACION)
        ) == SIN_ACTIVACION:
            self.partners.update(
                idpartner,
                {"sandbox_activado": self._now_ms(), "sandbox_expiracion": fecha_expiracion},
            )

        es_produccion = entorno == ENTORNO_PRODUCCION
        self.historial.registrar(
            idpartner=idpartner,
            tipo_cambio=(
                CAMBIO_ACTIVACION_PRODUCCION if es_produccion else CAMBIO_ACTIVACION_SANDBOX
            ),
            ejecutado_por=ejecutado_por,
            idcredencial=int(credencial["idcredencial"]),
            motivo=nombre,
            estado_anterior=ESTADO_PLAN_ASIGNADO if not es_produccion else ESTADO_PRUEBAS_ACTIVO,
            estado_nuevo=ESTADO_PRODUCCION_ACTIVA if es_produccion else ESTADO_PRUEBAS_ACTIVO,
        )

        # El secreto se adjunta SOLO en este retorno. La fila persistida y el
        # evento publicado llevan unicamente el hash.
        return {
            **{k: v for k, v in credencial.items() if k != "client_secret_hash"},
            "client_id": self.secretos.generar_client_id(
                idpartner, int(credencial["idcredencial"])
            ),
            "client_secret": secreto,
            "estado": ESTADO_PRODUCCION_ACTIVA if es_produccion else ESTADO_PRUEBAS_ACTIVO,
        }
