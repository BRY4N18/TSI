"""Server access API views — CU-O15."""

from __future__ import annotations

from rest_framework import status
from apps.cuentas_clientes.permissions import IsAuthenticated401
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.cuentas_clientes.services.server_access_service import (
    ForbiddenServerAccessError,
    ServerAccessError,
    ServerAccessService,
)
from apps.cuentas_clientes.views.error_response import error_response, success_response


class ServerUserListCreateView(APIView):
    permission_classes = [IsAuthenticated401]

    def get(self, request: Request):
        service = ServerAccessService()
        try:
            users = service.list_server_users(caller_roles=request.user.roles)
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(users)

    def post(self, request: Request):
        service = ServerAccessService()
        try:
            user = service.create_server_user(request.data, caller_roles=request.user.roles)
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(user, status_code=status.HTTP_200_OK)


class ServerUserDetailView(APIView):
    permission_classes = [IsAuthenticated401]

    def patch(self, request: Request, server_user_id: int):
        service = ServerAccessService()
        try:
            user = service.update_server_user(
                server_user_id, request.data, caller_roles=request.user.roles
            )
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except ServerAccessError:
            return error_response("not_found", "Usuario de servidor no encontrado", "404", status_code=404)
        return success_response(user)


class ServerRoleListCreateView(APIView):
    permission_classes = [IsAuthenticated401]

    def get(self, request: Request):
        service = ServerAccessService()
        try:
            roles = service.list_server_roles(caller_roles=request.user.roles)
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(roles)

    def post(self, request: Request):
        service = ServerAccessService()
        try:
            role = service.create_server_role(request.data, caller_roles=request.user.roles)
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(role, status_code=status.HTTP_200_OK)


class ServerRoleDetailView(APIView):
    permission_classes = [IsAuthenticated401]

    def patch(self, request: Request, server_role_id: int):
        service = ServerAccessService()
        try:
            role = service.update_server_role(
                server_role_id, request.data, caller_roles=request.user.roles
            )
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except ServerAccessError:
            return error_response("not_found", "Rol de servidor no encontrado", "404", status_code=404)
        return success_response(role)


class ServerRoleAssignView(APIView):
    permission_classes = [IsAuthenticated401]

    def post(self, request: Request):
        server_user_id = request.data.get("idusuariosservidor")
        server_role_id = request.data.get("idrolservidor")
        if server_user_id is None or server_role_id is None:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        service = ServerAccessService()
        try:
            assignment = service.assign_server_role(
                int(server_user_id), int(server_role_id), caller_roles=request.user.roles
            )
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(assignment)


class ServerRoleMappingView(APIView):
    permission_classes = [IsAuthenticated401]

    def post(self, request: Request):
        server_role_id = request.data.get("idrolservidor")
        app_role_id = request.data.get("idrol")
        if server_role_id is None or app_role_id is None:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        service = ServerAccessService()
        try:
            mapping = service.map_server_role_to_app_role(
                int(server_role_id), int(app_role_id), caller_roles=request.user.roles
            )
        except ForbiddenServerAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(mapping)
