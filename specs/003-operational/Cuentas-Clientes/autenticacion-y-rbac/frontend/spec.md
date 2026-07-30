# Feature Specification: Autenticación y RBAC — Frontend

**Feature Branch / capa**: `autenticacion-y-rbac/frontend`
**Created**: 2026-07-30
**Status**: Active (Fase B — Interaction Capability)
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-AUT-*, RNF-AUT-*, CA-AUT-*). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

**Input**: Sesión Fase B — flujos de login, guards transversales, recuperación/cambio de contraseña y servicios admin RBAC ya implementados en Angular.

## Clarifications

### Session 2026-07-30 (UI)

- Q: ¿Dónde vive el home post-login? → A: `post-login-home.ts` — redirección por rol (`Operador` → accidentes, `Proveedor` → flota, etc.); respeta `returnUrl` explícito salvo hub genérico `/cuentas-clientes`.
- Q: ¿Pantallas admin de usuarios/roles/servidor? → A: Servicios (`user-role-admin`, `server-access-admin`) expuestos para integración; CRUD admin completo fuera del MVP visual de este módulo — guards e interceptor son la superficie transversal obligatoria.
- Q: ¿Rate limiting en login UI? → A: Hereda RNF-AUT-005 diferido del backend; la UI muestra error 401 genérico sin revelar si el correo existe.

## User Scenarios & Testing

### US-FE-1 — Iniciar y cerrar sesión (P1)

El usuario autenticado accede vía formulario de login, recibe token y navega al home por rol; puede cerrar sesión invalidando la sesión server-side (RF-AUT-001, RF-AUT-008).

**Independent Test**: Login válido → shell protegido; logout → siguiente ruta protegida redirige a login.

### US-FE-2 — Cambio obligatorio de contraseña (P1)

Tras login con `estadocredencial='Cambio contraseña'`, la UI fuerza pantalla de cambio antes de cualquier módulo operativo (RF-AUT-005, RN-AUT-005).

**Independent Test**: Credencial en estado cambio → no accede a rutas lazy hasta completar nuevo password.

### US-FE-3 — Recuperar contraseña (P1)

Flujo público de solicitud de reset y pantalla de cambio asociada a contraseña temporal por correo (RF-AUT-006).

**Independent Test**: Solicitud con correo registrado → mensaje de confirmación; siguiente login exige cambio.

### US-FE-4 — Guards y autorización por rol (P1)

Rutas lazy del shell exigen `SessionGuard`; rutas sensibles combinan `RoleGuard` con lista de roles del JWT (RF-AUT-002, RF-AUT-004).

**Independent Test**: Usuario sin rol requerido → 403 o redirect según patrón del guard.

### US-FE-5 — Interceptor Bearer (P1)

Todas las peticiones HTTP autenticadas incluyen `Authorization: Bearer` desde almacenamiento de sesión (RF-AUT-002).

## Functional Requirements (UI)

- **FR-UI-001**: Pantalla login (`login.page`) con campos correo/contraseña, estados loading/error 401 y enlace a recuperación (RF-AUT-001).
- **FR-UI-002**: CTA logout en shell que invoca API logout y limpia token local (RF-AUT-008).
- **FR-UI-003**: `AuthInterceptor` adjunta Bearer en requests autenticadas; no en rutas públicas de login/reset/autorregistro (RF-AUT-002).
- **FR-UI-004**: `SessionGuard` bloquea rutas del `AppShellComponent` sin sesión válida → redirect `/cuentas-clientes/auth/login` con `returnUrl`.
- **FR-UI-005**: `RoleGuard` valida `data.roles` contra claims del perfil post-login (RF-AUT-004).
- **FR-UI-006**: Tras login con cambio obligatorio, redirect a flujo de cambio de contraseña antes del home por rol (RF-AUT-005).
- **FR-UI-007**: Pantalla `password-reset` para solicitud (correo) y cambio de contraseña definitiva (RF-AUT-006).
- **FR-UI-008**: `resolvePostLoginPath` / `homePathForRoles` — destino inicial por rol tras login exitoso (RNF-AUT-004 UX).
- **FR-UI-009**: `AuthApiService` encapsula login/logout/refresh de perfil sin duplicar contratos OpenAPI en componentes.
- **FR-UI-010**: `UserRoleAdminService` y `ServerAccessAdminService` disponibles para pantallas admin futuras; guards reutilizables en rutas CU-O04/O13/O15.
- **FR-UI-011**: Mensajes de error de auth alineados al envelope `error/detail/code` del backend — sin filtrar existencia de usuarios (Security).

## Out of Scope

- Cambiar OpenAPI, validaciones de servidor, Kafka/Pinot o RF/RN del backend.
- Rate limiting / CAPTCHA en login (RNF-AUT-005 diferido).
- UI completa de revocación de sesiones activas (RF-AUT-007) — API consumible vía servicios admin.

## ISO/IEC 25010:2023 — Justificación

| Characteristic | Treatment |
|---|---|
| Interaction Capability | Núcleo — login, guards, flujos de credencial |
| Functional Suitability | FR-UI citan RF-AUT-001…008 y CA-AUT-* del backend |
| Security | Guards + interceptor; Principle V |
| Maintainability | Capa FE separada de `backend/` |
| Performance Efficiency | Hereda p95 login del backend; UI no bloquea más allá de spinner estándar |
| Reliability / Compatibility / Flexibility / Safety | N/A o heredadas |

**Traceability**: Índice del módulo [`../autenticacion-y-rbac.md`](../autenticacion-y-rbac.md).
