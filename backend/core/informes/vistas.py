"""Vista base de los listados tacticos simples.

Centraliza las **tres validaciones que el contrato exige rechazar en vez de
tolerar**, para que ninguno de los 64 listados las reimplemente —y las olvide—
por su cuenta:

1. **`limit` sobre el maximo → `400`.** No se recorta en silencio (FR-016).
2. **Rango de fechas en un listado de estado actual → `400`.** No se ignora
   (FR-012).
3. **Valor no reconocido en una enumeracion → `400` nombrando los validos.** No
   se descarta el filtro (FR-015).

Las tres comparten la misma logica: **fallar ruidosamente antes que devolver un
resultado plausible**. Un filtro ignorado devuelve el listado entero y parece
que funciono; un `limit` recortado devuelve 500 filas de las 5.000 pedidas y
parece completo. En los tres casos el consumidor solo lo descubriria cuadrando
cifras contra otra fuente, que es demasiado tarde.
"""

from __future__ import annotations

from typing import Any, Iterable

from rest_framework.request import Request
from rest_framework.views import APIView

from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado, Acotamiento, resolver
from core.informes.paginacion import CursorInvalido, LimiteInvalido, parse_limit
from core.informes.periodo import Periodo, PeriodoInvalido, parse_periodo


class FiltroInvalido(ValueError):
    """Un filtro recibido no es interpretable, o no esta entre los admitidos."""


#: Lo que una peticion mal formada puede lanzar, y que se traduce a `400`.
#: Se enumera para que la vista capture **esto** y no `Exception`: un fallo de
#: Pinot o un error de programacion deben subir como `500`, no disfrazarse de
#: peticion invalida y hacer creer al consumidor que la culpa es suya.
ERRORES_DE_VALIDACION = (PeriodoInvalido, LimiteInvalido, CursorInvalido, FiltroInvalido)


class ListadoBaseView(APIView):
    """Base de todo listado tactico simple.

    Las subclases declaran `admite_rango` y usan los ayudantes de parseo. La
    autenticacion es obligatoria y sin excepciones anonimas (contrato §2); el
    permiso concreto lo pone cada departamento.
    """

    permission_classes = [IsAuthenticated401]

    #: `False` en los listados de **estado actual**, que rechazan `desde`/`hasta`.
    #: Es el valor por defecto porque de los 32 endpoints solo unos pocos son de
    #: hechos del periodo: el caso raro se declara, el comun se hereda.
    admite_rango: bool = False

    def parse_peticion(self, request: Request) -> tuple[Periodo, int]:
        """Parsea periodo y `limit`, las dos validaciones que todo listado hace.

        Lanza `PeriodoInvalido` o `LimiteInvalido`; ambas las traduce a `400`
        `manejar_peticion_invalida`.
        """
        periodo = parse_periodo(request.query_params, admite_rango=self.admite_rango)
        limit = parse_limit(request.query_params)
        return periodo, limit

    @staticmethod
    def parse_enumeracion(
        query_params, nombre: str, validos: Iterable[str]
    ) -> str | None:
        """Lee un filtro de enumeracion, o `400` nombrando los valores validos.

        Nombrarlos no es cortesia: sin la lista, quien recibe el `400` no puede
        corregir la peticion sin leer la spec.
        """
        valor = query_params.get(nombre)
        if valor is None or valor == "":
            return None
        admitidos = list(validos)
        if valor not in admitidos:
            raise FiltroInvalido(
                f"El filtro '{nombre}' no admite el valor '{valor}'; "
                f"use uno de: {', '.join(sorted(admitidos))}."
            )
        return valor

    @staticmethod
    def parse_entero(query_params, nombre: str, *, minimo: int | None = None) -> int | None:
        """Lee un filtro numerico opcional."""
        crudo = query_params.get(nombre)
        if crudo is None or crudo == "":
            return None
        try:
            valor = int(crudo)
        except (TypeError, ValueError) as exc:
            raise FiltroInvalido(
                f"El filtro '{nombre}' debe ser un entero; se recibio '{crudo}'."
            ) from exc
        if minimo is not None and valor < minimo:
            raise FiltroInvalido(
                f"El filtro '{nombre}' debe ser mayor o igual que {minimo}; se recibio {valor}."
            )
        return valor

    @staticmethod
    def parse_booleano(query_params, nombre: str) -> bool | None:
        """Lee un filtro booleano opcional aceptando `true`/`false`.

        Cualquier otro valor es `400` en vez de "todo lo que no sea true es
        false": `activo=1` interpretado como `False` devolveria justo lo
        contrario de lo pedido, sin avisar.
        """
        crudo = query_params.get(nombre)
        if crudo is None or crudo == "":
            return None
        normalizado = str(crudo).strip().lower()
        if normalizado in ("true", "false"):
            return normalizado == "true"
        raise FiltroInvalido(
            f"El filtro '{nombre}' debe ser 'true' o 'false'; se recibio '{crudo}'."
        )

    @staticmethod
    def manejar_peticion_invalida(exc: Exception):
        """Traduce un fallo de validacion al envelope de error estandar."""
        return error_response("bad_request", str(exc), "400", status_code=400)

    @staticmethod
    def manejar_acceso_denegado(exc: AccesoDenegado):
        """Traduce una negativa de acotamiento a `403`.

        **`403` y no una lista vacia.** Devolver `200 data: []` a quien pidio la
        cartera ajena le oculta que pidio algo indebido, y le deja creer que
        simplemente no hay datos. El codigo es informacion.
        """
        return error_response("forbidden", str(exc), "403", status_code=403)

    def resolver_acotamiento(
        self,
        request: Request,
        *,
        roles_amplios,
        roles_acotados,
        parametro: str = "ejecutivo",
    ) -> Acotamiento:
        """Resuelve el acotamiento de la peticion desde el rol y `?<parametro>=`.

        El nombre del parametro cambia por departamento —`ejecutivo` en Ventas,
        `cliente` en Soporte— pero la regla no, y por eso vive aqui.
        """
        titular = self.parse_entero(request.query_params, parametro, minimo=1)
        return resolver(
            roles=getattr(request.user, "roles", []) or [],
            user_id=request.user.idusuario,
            roles_amplios=roles_amplios,
            roles_acotados=roles_acotados,
            titular_pedido=titular,
        )


def filtros_aplicados(**valores: Any) -> dict[str, Any]:
    """Azucar para armar `meta.filtros` desde los filtros ya normalizados."""
    return dict(valores)
