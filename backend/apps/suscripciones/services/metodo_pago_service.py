"""RF-SUSF-002 — método de pago (+ RN-021 hook)."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository
from apps.suscripciones.services.pasarela.simulador_pasarela import SimuladorPasarela


class MetodoPagoError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class MetodoPagoService:
    TIPOS = frozenset({"tarjeta", "transferencia", "paypal"})

    def __init__(
        self,
        metodos: MetodoPagoRepository | None = None,
        suscripciones: SuscripcionRepository | None = None,
        pasarela: SimuladorPasarela | None = None,
    ):
        self.metodos = metodos or MetodoPagoRepository()
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.pasarela = pasarela or SimuladorPasarela()

    def listar(self, idcliente: int) -> list[dict[str, Any]]:
        return self.metodos.list_by_cliente(idcliente)

    def registrar(
        self,
        *,
        idcliente: int,
        tipo: str,
        datos_pasarela: dict[str, Any],
    ) -> dict[str, Any]:
        if tipo not in self.TIPOS:
            raise MetodoPagoError("invalid_tipo", "tipo inválido")
        # Tokenización simulada — nunca persistir PAN/CVV
        pan = str(datos_pasarela.get("numero", datos_pasarela.get("pan", "0000")))
        ultimos = pan[-4:] if pan else "0000"
        token = f"tok_sim_{idcliente}_{tipo}_{ultimos}"
        anterior = self.metodos.find_activo(idcliente)
        nuevo = self.metodos.create(
            {
                "idcliente": idcliente,
                "tipo": tipo,
                "tokenpasarela": token,
                "ultimosdigitos": ultimos,
                "fechaexpiracion": datos_pasarela.get("fechaexpiracion"),
            }
        )
        if anterior:
            self.metodos.update(anterior["idmetodopago"], {"activo": False})
        regularizacion = False
        suscripcion = self.suscripciones.find_activa_by_cliente(idcliente)
        if suscripcion and suscripcion.get("estado") == "Suspendida":
            from apps.suscripciones.services.mora_suscripcion_service import MoraSuscripcionService

            MoraSuscripcionService().regularizar(id_suscripcion=suscripcion["id_suscripcion"])
            regularizacion = True
        return {"metodo": nuevo, "regularizacion_disparada": regularizacion}
