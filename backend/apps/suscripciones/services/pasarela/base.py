"""Puerto de pasarela de pago + simulador (RN-SUSF-024 / RNF-008)."""

from __future__ import annotations

import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ResultadoCobro:
    exitoso: bool
    codigo: str
    mensaje: str


class PasarelaPagoPort(ABC):
    @abstractmethod
    def cobrar(
        self,
        *,
        monto: float,
        tokenpasarela: str,
        idempotency_key: str,
        force_fail: bool = False,
    ) -> ResultadoCobro:
        raise NotImplementedError


class SimuladorPasarela(PasarelaPagoPort):
    """Éxito por defecto; BILLING_SIMULATOR_FAIL_RATE o force_fail controlan fallos."""

    def cobrar(
        self,
        *,
        monto: float,
        tokenpasarela: str,
        idempotency_key: str,
        force_fail: bool = False,
    ) -> ResultadoCobro:
        if force_fail:
            return ResultadoCobro(False, "FORCE_FAIL", "Fallo forzado de prueba")
        if not tokenpasarela:
            return ResultadoCobro(False, "SIN_METODO_PAGO", "Sin token de pasarela")
        try:
            rate = float(os.environ.get("BILLING_SIMULATOR_FAIL_RATE", "0") or "0")
        except ValueError:
            rate = 0.0
        # Deterministic-ish by idempotency key for retries of same key
        rnd = random.Random(idempotency_key)
        if rate > 0 and rnd.random() < rate:
            return ResultadoCobro(False, "SIM_DECLINED", "Simulador rechazó el cobro")
        return ResultadoCobro(True, "Exitoso", f"Cobro simulado OK monto={monto}")
