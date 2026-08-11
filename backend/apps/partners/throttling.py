"""Throttle por minuto de la API de datos (§ 15 D2).

ESTO NO ES LA APLICACION DE LA CUOTA COMERCIAL
----------------------------------------------
Son dos mecanismos distintos y el SRS los mezcla; la spec los separa a
proposito:

| | Cupo mensual | Limite por minuto |
|---|---|---|
| Que es | compromiso comercial | proteccion de plataforma |
| Al superarse | **nunca bloquea**: alerta y genera excedente facturable | devuelve **429** con `Retry-After` |
| Se factura | si, al cierre del periodo | **no**: no se atendio |

RN-APM-002 sigue intacta con este throttle: el cupo mensual sigue sin bloquear
y sigue generando excedente. Lo que se limita es el *ritmo* instantaneo, como
en cualquier API publica.

**Si alguna vez se te ocurre bloquear aqui por cupo mensual, no lo hagas.** El
SRS es explicito y la spec dice que lo documenta «precisamente para que nadie
la corrija asumiendo que deberia bloquear».

Consecuencia para el registro: una peticion rechazada con 429 **no genera fila**
en `Fact_APIIntegracion` (no se atendio, no es consumo facturable), pero **si**
en `Fact_LogLlamadaAPI` — para que el partner vea que le estan limitando y
ajuste su cliente.
"""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle

from apps.partners.authentication import PartnerAPIUser

# Centinela de `Dim_Partner.limitellamadasminuto`: sin cupo asignado.
# Un 0 seria un limite real de cero llamadas, por eso el centinela es -1.
SIN_CUPO = -1

SCOPE = "partner_api"


class PartnerRateThrottle(SimpleRateThrottle):
    """Limita el ritmo segun `Dim_Partner.limitellamadasminuto` de cada partner.

    El rate del scope en `settings` existe solo porque DRF exige uno declarado;
    el limite efectivo se toma del partner y sobrescribe al del scope.
    """

    scope = SCOPE

    def get_cache_key(self, request, view) -> str | None:
        usuario = getattr(request, "user", None)
        if not isinstance(usuario, PartnerAPIUser):
            # No es una llamada de API de partner: este throttle no aplica.
            return None

        limite = int(usuario.partner.get("limitellamadasminuto", SIN_CUPO))
        if limite == SIN_CUPO:
            # Sin cupo asignado no se throttlea. Es coherente con #07: un
            # partner sin plan tampoco puede emitir credenciales, asi que en la
            # practica no deberia llegar aqui; si llega, no se le bloquea por un
            # centinela.
            return None

        # El limite del partner manda sobre el rate del scope.
        self.num_requests = limite
        self.duration = 60

        return self.cache_format % {
            "scope": self.scope,
            "ident": f"partner-{usuario.idpartner}",
        }

    def wait(self) -> float | None:
        """Segundos hasta poder reintentar. DRF lo emite como `Retry-After`."""
        espera = super().wait()
        # Nunca devolver 0: un `Retry-After: 0` invita a reintentar de inmediato
        # y a volver a chocar contra el mismo limite.
        if espera is not None and espera < 1:
            return 1.0
        return espera
