"""Vistas de los cuatro listados de OT18 — acceso seguro y controlado por rol.

Los cuatro son de **estado actual**: describen quien tiene acceso *ahora*, no en
un intervalo. Por eso heredan `admite_rango = False` y declarar `desde`/`hasta`
responde `400` en vez de ignorarse (FR-012).

`accesos-tecnicos` usa un permiso distinto a los otros tres: es el **unico**
listado del departamento al que accede el Director Tecnologico (§5.1 del SRS,
`acceso-tactico.md` §5).
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.cuentas_clientes.permissions import (
    InformesAccesosTecnicosPermission,
    InformesCuentasLecturaPermission,
)
from apps.cuentas_clientes.services.informes_acceso_service import InformesAccesoService
from core.auth.permissions import IsAuthenticated401
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, FiltroInvalido, ListadoBaseView
from core.repositories.cuentas_clientes.informes_acceso_repository import (
    CURSOR_ACCESOS,
    CURSOR_CREDENCIALES,
    CURSOR_SESIONES,
    CURSOR_USUARIOS,
    ORDEN_ACCESOS,
    ORDEN_CREDENCIALES,
    ORDEN_SESIONES,
    ORDEN_USUARIOS,
)


class _ListadoAccesoView(ListadoBaseView):
    """Base de los cuatro: estado actual y permiso de lectura del departamento."""

    permission_classes = [IsAuthenticated401, InformesCuentasLecturaPermission]
    admite_rango = False

    def servicio(self) -> InformesAccesoService:
        return InformesAccesoService()


class UsuariosPorRolView(_ListadoAccesoView):
    """L5 — una fila por usuario, con la lista de roles que ejerce."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_USUARIOS)
            cursor = CURSOR_USUARIOS.decodificar(request.query_params.get("cursor"))
            activo = self.parse_booleano(request.query_params, "activo")

            servicio = self.servicio()
            rol = request.query_params.get("rol") or None
            if rol is not None:
                # Se valida contra el catalogo vivo, no contra una lista fija:
                # un rol nuevo en `Dim_Rol` seria filtrable sin tocar el codigo,
                # y uno inexistente responde 400 nombrando los validos (FR-015).
                validos = servicio.roles_disponibles()
                if rol not in validos:
                    raise FiltroInvalido(
                        f"El filtro 'rol' no admite el valor '{rol}'; "
                        f"use uno de: {', '.join(validos)}."
                    )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = servicio.usuarios_por_rol(
            cursor=cursor, limit=limit, orden=orden, rol=rol, activo=activo
        )
        return listado_response(pagina, {"rol": rol, "activo": activo})


class SesionesActivasView(_ListadoAccesoView):
    """L6 — sesiones abiertas. El `token` nunca sale (research D7)."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_SESIONES)
            cursor = CURSOR_SESIONES.decodificar(request.query_params.get("cursor"))
            idusuario = self.parse_entero(request.query_params, "idusuario", minimo=1)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = self.servicio().sesiones_activas(
            cursor=cursor, limit=limit, orden=orden, idusuario=idusuario
        )
        return listado_response(pagina, {"idusuario": idusuario})


class CredencialesTemporalesView(_ListadoAccesoView):
    """L7 — credenciales pendientes de cambio. La `contrasena` nunca sale."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_CREDENCIALES)
            cursor = CURSOR_CREDENCIALES.decodificar(request.query_params.get("cursor"))
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = self.servicio().credenciales_temporales(
            cursor=cursor, limit=limit, orden=orden
        )
        return listado_response(pagina)


class AccesosTecnicosView(_ListadoAccesoView):
    """L8 — accesos tecnicos y su mapeo a roles de negocio (CU-O08).

    Unico listado del departamento con autoridad departamental por encima del
    Administrador. La `contrasena` de servidor nunca sale.
    """

    permission_classes = [IsAuthenticated401, InformesAccesosTecnicosPermission]

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_ACCESOS)
            cursor = CURSOR_ACCESOS.decodificar(request.query_params.get("cursor"))
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = self.servicio().accesos_tecnicos(cursor=cursor, limit=limit, orden=orden)
        return listado_response(pagina)
