"""User and role management API views — CU-O04, CU-O13."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.cuentas_clientes.services.business_rbac_service import (
    BusinessRBACError,
    BusinessRBACService,
    ForbiddenRBACError,
)
from apps.cuentas_clientes.services.user_management_service import (
    ForbiddenUserManagementError,
    UserManagementError,
    UserManagementService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401


class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated401]

    def get(self, request: Request):
        service = UserManagementService()
        try:
            users = service.list_users(
                admin_roles=request.user.roles,
                cursor=request.query_params.get("cursor"),
                limit=int(request.query_params.get("limit", 20)),
            )
        except ForbiddenUserManagementError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(users)

    def post(self, request: Request):
        service = UserManagementService()
        try:
            user = service.create_user(request.data, admin_roles=request.user.roles)
        except ForbiddenUserManagementError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except UserManagementError as exc:
            return error_response("conflict", str(exc), "409", status_code=status.HTTP_409_CONFLICT)
        return success_response(user, status_code=status.HTTP_200_OK)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated401]

    def get(self, request: Request, user_id: int):
        service = UserManagementService()
        try:
            user = service.get_user(user_id, admin_roles=request.user.roles)
        except ForbiddenUserManagementError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except UserManagementError:
            return error_response("not_found", "Usuario no encontrado", "404", status_code=404)
        return success_response(user)

    def patch(self, request: Request, user_id: int):
        service = UserManagementService()
        try:
            user = service.update_user(user_id, request.data, admin_roles=request.user.roles)
        except ForbiddenUserManagementError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except UserManagementError:
            return error_response("not_found", "Usuario no encontrado", "404", status_code=404)
        return success_response(user)

    def delete(self, request: Request, user_id: int):
        service = UserManagementService()
        try:
            user = service.deactivate_user(user_id, admin_roles=request.user.roles)
        except ForbiddenUserManagementError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except UserManagementError:
            return error_response("not_found", "Usuario no encontrado", "404", status_code=404)
        return success_response(user)


class RoleListCreateView(APIView):
    permission_classes = [IsAuthenticated401]

    def get(self, request: Request):
        service = BusinessRBACService()
        try:
            roles = service.list_roles(admin_roles=request.user.roles)
        except ForbiddenRBACError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        return success_response(roles)

    def post(self, request: Request):
        service = BusinessRBACService()
        try:
            role = service.create_role(request.data, admin_roles=request.user.roles)
        except ForbiddenRBACError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except BusinessRBACError as exc:
            return error_response("conflict", str(exc), "409", status_code=status.HTTP_409_CONFLICT)
        return success_response(role)


class RoleDetailView(APIView):
    permission_classes = [IsAuthenticated401]

    def patch(self, request: Request, role_id: int):
        service = BusinessRBACService()
        try:
            role = service.update_role(role_id, request.data, admin_roles=request.user.roles)
        except ForbiddenRBACError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except BusinessRBACError:
            return error_response("not_found", "Rol no encontrado", "404", status_code=404)
        return success_response(role)

    def delete(self, request: Request, role_id: int):
        service = BusinessRBACService()
        try:
            role = service.deactivate_role(role_id, admin_roles=request.user.roles)
        except ForbiddenRBACError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except BusinessRBACError:
            return error_response("not_found", "Rol no encontrado", "404", status_code=404)
        return success_response(role)


class UserRoleAssignView(APIView):
    permission_classes = [IsAuthenticated401]

    def post(self, request: Request):
        user_id = request.data.get("idusuario")
        role_id = request.data.get("idrol")
        if user_id is None or role_id is None:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        service = BusinessRBACService()
        try:
            assignment = service.assign_role(
                int(user_id), int(role_id), admin_roles=request.user.roles
            )
        except ForbiddenRBACError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except BusinessRBACError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        return success_response(assignment)
