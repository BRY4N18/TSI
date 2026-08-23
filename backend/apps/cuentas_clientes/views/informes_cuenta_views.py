"""Vistas de los dos listados de OT17 — ciclo de vida de la cuenta.

Aqui se separan los dos tipos de listado que el contrato distingue, y es el
unico sitio del departamento donde conviven:

| Vista | Tipo | `desde`/`hasta` |
|---|---|---|
| `cuentas-por-estado` | Estado actual | **`400`** |
| `transferencias-propiedad` | Hechos del periodo | **opcionales** |

Que `transferencias-propiedad` acepte el rango y ademas permita omitirlo no es
una concesion: una bitacora sin rango es el historico completo, y paginarlo es
una peticion perfectamente valida (FR-013).
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.cuentas_clientes.permissions import InformesCuentasLecturaPermission
from apps.cuentas_clientes.services.informes_cuenta_service import InformesCuentaService
from core.auth.permissions import IsAuthenticated401
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, ListadoBaseView
from core.repositories.cuentas_clientes.cliente_repository import ESTADOS_CLIENTE
from core.repositories.cuentas_clientes.informes_cuenta_repository import (
    CURSOR_CUENTAS,
    CURSOR_TRANSFERENCIAS,
    ORDEN_CUENTAS,
    ORDEN_TRANSFERENCIAS,
)


class CuentasPorEstadoView(ListadoBaseView):
    """L3 — cuentas con su estado, **incluidas las dadas de baja**."""

    permission_classes = [IsAuthenticated401, InformesCuentasLecturaPermission]
    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_CUENTAS)
            cursor = CURSOR_CUENTAS.decodificar(request.query_params.get("cursor"))
            # Contra las constantes canonicas de `cliente_repository`, no contra
            # el enum del OpenAPI: aquel declaraba `Suspendido` y `Baja`, que no
            # existen, y habria rechazado con `400` un `Dado de baja` correcto.
            estado = self.parse_enumeracion(
                request.query_params, "estado", ESTADOS_CLIENTE
            )
            # `tipo` es texto libre: sus valores reales (`Corporativo`,
            # `Proveedor`) no forman un catalogo cerrado en ninguna tabla.
            tipo = request.query_params.get("tipo") or None
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesCuentaService().cuentas_por_estado(
            cursor=cursor, limit=limit, orden=orden, estado=estado, tipo=tipo
        )
        return listado_response(pagina, {"estado": estado, "tipo": tipo})


class TransferenciasPropiedadView(ListadoBaseView):
    """L4 — el unico de los ocho listados con rango de fechas (FR-013)."""

    permission_classes = [IsAuthenticated401, InformesCuentasLecturaPermission]
    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_TRANSFERENCIAS)
            cursor = CURSOR_TRANSFERENCIAS.decodificar(request.query_params.get("cursor"))
            idcliente = self.parse_entero(request.query_params, "idcliente", minimo=1)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesCuentaService().transferencias_propiedad(
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
            idcliente=idcliente,
        )
        return listado_response(pagina, {**periodo.to_meta(), "idcliente": idcliente})


class CatalogosCuentasView(ListadoBaseView):
    """Opciones de los desplegables «Cuenta» y «Usuario» de estos listados.

    Existen porque los filtros pedían identificadores numéricos a mano —«Cuenta
    (id)», «Usuario (id)»— mientras las tablas mostraban solo nombres: no había
    forma de averiguar el número desde la propia pantalla.

    ⚠️ **No se acota, y aquí eso es correcto.** Estos listados los ve solo el
    `Administrador` (`INFORMES_CUENTAS_ROLES`), que responde de todas las cuentas
    de la plataforma: no hay un alcance menor al que reducirlos. Si algún día
    entrara un rol con alcance propio, este catálogo **tendría que acotarse con
    él**, porque enumerar las cuentas ajenas dice quién más opera aunque el
    listado siga devolviendo lo de siempre.
    """

    permission_classes = [IsAuthenticated401, InformesCuentasLecturaPermission]
    admite_rango = False

    def get(self, request: Request):
        from core.api.response_envelope import success_response
        from core.informes.catalogos import CatalogosFiltrosRepository

        repo = CatalogosFiltrosRepository()
        return success_response(
            {"idcliente": repo.clientes(None), "idusuario": repo.usuarios(None)},
            meta={"acotado_a": "todos"},
        )
