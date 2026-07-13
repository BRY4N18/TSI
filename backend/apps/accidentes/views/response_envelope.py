"""Standard API envelopes for accidentes endpoints."""

from apps.cuentas_clientes.views.error_response import (
    error_response,
    success_response,
)

__all__ = ["success_response", "error_response"]
