"""API v1 URL routes for cuentas_clientes auth/RBAC."""

from django.urls import path

from apps.cuentas_clientes.views.auth_views import (
    LoginView,
    LogoutView,
    RevokeSessionView,
)
from apps.cuentas_clientes.views.cuenta_views import (
    BajaCuentaView,
    CuentaPerfilView,
    CuentaPreferenciasView,
    LogoUploadUrlView,
    TransferenciaPropiedadView,
    UsuariosElegiblesView,
)
from apps.cuentas_clientes.views.onboarding_views import (
    AnularRechazoProveedorView,
    AutorregistroProveedorView,
    CompletarOnboardingEtapaView,
    ConfigurarCuentaView,
    DecidirSolicitudProveedorView,
    ListarSolicitudesProveedorView,
    OnboardingProgresoView,
    ReenviarInvitacionView,
    RegistrarCuentaView,
)
from apps.cuentas_clientes.views.password_reset_views import PasswordResetView
from apps.cuentas_clientes.views.server_access_views import (
    ServerRoleAssignView,
    ServerRoleDetailView,
    ServerRoleListCreateView,
    ServerRoleMappingView,
    ServerUserDetailView,
    ServerUserListCreateView,
)
from apps.cuentas_clientes.views.user_role_views import (
    RoleDetailView,
    RoleListCreateView,
    UserDetailView,
    UserListCreateView,
    UserRoleAssignView,
)

urlpatterns = [
    # Auth (US1 + US4)
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/revoke-session", RevokeSessionView.as_view(), name="auth-revoke-session"),
    path("auth/password-reset", PasswordResetView.as_view(), name="auth-password-reset"),
    # Users & roles (US2) — static paths before parameterized routes
    path("usuarios/roles/asignar", UserRoleAssignView.as_view(), name="usuarios-roles-assign"),
    path("usuarios", UserListCreateView.as_view(), name="usuarios-list-create"),
    path("usuarios/<int:user_id>", UserDetailView.as_view(), name="usuarios-detail"),
    path("roles", RoleListCreateView.as_view(), name="roles-list-create"),
    path("roles/<int:role_id>", RoleDetailView.as_view(), name="roles-detail"),
    # Server access (US3)
    path("server-access/usuarios", ServerUserListCreateView.as_view(), name="server-users"),
    path(
        "server-access/usuarios/<int:server_user_id>",
        ServerUserDetailView.as_view(),
        name="server-users-detail",
    ),
    path("server-access/roles", ServerRoleListCreateView.as_view(), name="server-roles"),
    path(
        "server-access/roles/<int:server_role_id>",
        ServerRoleDetailView.as_view(),
        name="server-roles-detail",
    ),
    path(
        "server-access/asignar",
        ServerRoleAssignView.as_view(),
        name="server-role-assign",
    ),
    path(
        "server-access/mapeo",
        ServerRoleMappingView.as_view(),
        name="server-role-mapping",
    ),
    # Gestion de cuenta / incorporacion (CU-O14, O16; O01/O12 retirados → 410)
    path(
        "cuentas-clientes/autorregistro",
        AutorregistroProveedorView.as_view(),
        name="cuenta-autorregistro",
    ),
    path(
        "cuentas-clientes/solicitudes",
        ListarSolicitudesProveedorView.as_view(),
        name="cuenta-solicitudes",
    ),
    path("cuentas-clientes", RegistrarCuentaView.as_view(), name="cuenta-registro"),
    path(
        "cuentas-clientes/<int:idcliente>/aprobacion",
        DecidirSolicitudProveedorView.as_view(),
        name="cuenta-aprobacion",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/anular-rechazo",
        AnularRechazoProveedorView.as_view(),
        name="cuenta-anular-rechazo",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/configuracion",
        ConfigurarCuentaView.as_view(),
        name="cuenta-configuracion",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/onboarding/progreso",
        OnboardingProgresoView.as_view(),
        name="onboarding-progreso",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/onboarding/etapas",
        CompletarOnboardingEtapaView.as_view(),
        name="onboarding-etapas",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/invitacion/reenviar",
        ReenviarInvitacionView.as_view(),
        name="invitacion-reenviar",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/perfil",
        CuentaPerfilView.as_view(),
        name="cuenta-perfil",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/preferencias",
        CuentaPreferenciasView.as_view(),
        name="cuenta-preferencias",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/logo/upload-url",
        LogoUploadUrlView.as_view(),
        name="cuenta-logo-upload-url",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/usuarios-elegibles",
        UsuariosElegiblesView.as_view(),
        name="cuenta-usuarios-elegibles",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/transferencia-propiedad",
        TransferenciaPropiedadView.as_view(),
        name="cuenta-transferencia-propiedad",
    ),
    path(
        "cuentas-clientes/<int:idcliente>/baja",
        BajaCuentaView.as_view(),
        name="cuenta-baja",
    ),
]
