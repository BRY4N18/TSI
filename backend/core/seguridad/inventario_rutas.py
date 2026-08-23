"""Inventario de rutas derivado del enrutador de Django (PG-SEC-001, PG-SEC-002).

Por que existe: las suites de aislamiento y de roles necesitan recorrer **todos**
los endpoints, y una lista escrita a mano envejece en cuanto alguien anade una
ruta. Peor aun, sigue reportando «todo cubierto» mientras deja huecos — produce
confianza infundada, que es peor que no tener suite.

Derivarlo del `URLResolver` es lo unico que satisface SC-002: una ruta nueva sin
prueba de aislamiento hace **fallar** la suite en vez de pasar desapercibida.

Es el mismo criterio que ya se aplico al registro de secretos de `PG-CFG-002`,
que se comprueba contra `settings.py` en vez de mantenerse a mano.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from django.urls import URLPattern, URLResolver, get_resolver

#: Prefijo de la API versionada. Todo lo demas (admin de Django, estaticos) queda
#: fuera del alcance de las suites de seguridad de este bloque.
PREFIJO_API = "api/v1/"

#: Un parametro de path se considera identificador de recurso si su nombre
#: contiene «id». Cubre `<int:idpartner>`, `<int:user_id>` y `<uuid:idcaso>`.
_PARAM = re.compile(r"<(?:(?P<conv>[^:>]+):)?(?P<nombre>[^>]+)>")

#: Metodos que DRF resuelve por convencion de nombre en las vistas de clase.
_METODOS = ("get", "post", "put", "patch", "delete", "head", "options")


@dataclass(frozen=True)
class RutaInventariada:
    """Una ruta registrada, con lo que las suites necesitan saber de ella."""

    patron: str
    vista: Any
    parametros: tuple[str, ...] = ()
    parametros_id: tuple[str, ...] = ()
    metodos: tuple[str, ...] = ()
    permission_classes: tuple[Any, ...] = field(default=())

    @property
    def nombre_vista(self) -> str:
        return getattr(self.vista, "__name__", repr(self.vista))

    @property
    def tiene_identificador(self) -> bool:
        return bool(self.parametros_id)

    def __str__(self) -> str:  # pragma: no cover - solo para mensajes de fallo
        return f"{self.patron} -> {self.nombre_vista}"


def _extraer_parametros(patron: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    nombres = tuple(m.group("nombre") for m in _PARAM.finditer(patron))
    ids = tuple(n for n in nombres if "id" in n.lower())
    return nombres, ids


def _metodos_de(vista: Any) -> tuple[str, ...]:
    """Metodos HTTP que la vista implementa realmente.

    Se lee de la clase y no de `http_method_names`, que enumera los *admitidos*
    por Django e incluiria metodos sin handler.
    """
    return tuple(m for m in _METODOS if hasattr(vista, m))


def _permisos_de(vista: Any) -> tuple[Any, ...]:
    return tuple(getattr(vista, "permission_classes", ()) or ())


def _recorrer(resolver: URLResolver, prefijo: str = "") -> list[RutaInventariada]:
    """Recorre el arbol de resolvers acumulando el prefijo de cada `include()`.

    El recorrido tiene que ser recursivo: `config/urls.py` monta once modulos con
    `include()`, y cada uno puede anidar mas. Un recorrido plano solo veria los
    once prefijos y ninguna ruta real.
    """
    rutas: list[RutaInventariada] = []
    for entrada in resolver.url_patterns:
        patron = prefijo + str(entrada.pattern)
        if isinstance(entrada, URLResolver):
            rutas.extend(_recorrer(entrada, patron))
        elif isinstance(entrada, URLPattern):
            vista = getattr(entrada.callback, "view_class", None) or entrada.callback
            parametros, ids = _extraer_parametros(patron)
            rutas.append(
                RutaInventariada(
                    patron=patron,
                    vista=vista,
                    parametros=parametros,
                    parametros_id=ids,
                    metodos=_metodos_de(vista),
                    permission_classes=_permisos_de(vista),
                )
            )
    return rutas


@lru_cache(maxsize=1)
def inventariar() -> tuple[RutaInventariada, ...]:
    """Todas las rutas de la API versionada.

    Cacheado: el recorrido es deterministico dentro de un proceso y las suites lo
    piden una vez por prueba parametrizada.
    """
    todas = _recorrer(get_resolver())
    return tuple(r for r in todas if r.patron.startswith(PREFIJO_API))


def rutas_con_identificador() -> tuple[RutaInventariada, ...]:
    """Las que aceptan un id en el path: el alcance de la prueba de aislamiento."""
    return tuple(r for r in inventariar() if r.tiene_identificador)
