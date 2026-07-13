# Phase 0 Research - Incorporación de Clientes

## Decision 1: Contract-first con OpenAPI

- Decision: Definir primero `contracts/incorporacion-clientes.openapi.yaml` con todos los endpoints bajo `/api/v1/cuentas-clientes/...`.
- Rationale: Cumple `api-standards.md` y permite tipos TypeScript + tests de contrato antes de vistas DRF (django-expert).
- Alternatives considered:
  - Implementar vistas primero (rechazado: desalineación frontend/backend).
  - Un solo endpoint monolítico de onboarding (rechazado: no mapea CUs O01/O12/O02/O08).

## Decision 2: Endpoints REST y semántica HTTP

- Decision:
  - `POST /cuentas-clientes` — CU-O01 registro (solo Administrador, `Idempotency-Key`).
  - `PATCH /cuentas-clientes/{idcliente}/configuracion` — CU-O12 plan/logo + `estado_onboarding=Pendiente`.
  - `POST /cuentas-clientes/{idcliente}/logo/upload-url` — URL firmada Azure Blob (mismo patrón que gestion-cuentas).
  - `GET /cuentas-clientes/{idcliente}/onboarding/progreso` — CU-O09 consulta de etapas.
  - `POST /cuentas-clientes/{idcliente}/onboarding/etapas` — CU-O02 completar etapa canónica.
  - `POST /cuentas-clientes/{idcliente}/invitacion/reenviar` — CU-O08 temp password + email.
- Rationale: Recursos anidados bajo cuenta; POST para comandos; PATCH para configuración parcial; envelope estándar.
- Alternatives considered:
  - `PUT` para configuración completa (rechazado: solo dos campos editables en O12).
  - Webhook para progreso (rechazado: fuera de api-standards REST del proyecto).

## Decision 3: Django Vista → Servicio → Repositorio + Kafka-only-write

- Decision:
  - **Vistas**: `onboarding_views.py` (DRF `APIView` por operación, patrón `auth_views.py`).
  - **Servicios**: `RegistroCuentaService`, `ConfiguracionCuentaService`, `OnboardingService`, `InvitacionService`, `OnboardingNotificacionService`.
  - **Repositorios**: extender `ClienteRepository`; nuevos `OnboardingRepository`, reutilizar `UserRepository`, `CredentialRepository`, `RoleRepository`, `PreferenciasClienteRepository`, `LogoUploadService`.
  - **Escritura Kafka**: `Dim_Cliente_topic`, `Dim_Usuarios_topic`, `Dim_Credencial_topic`, `Dim_Usuario_Rol_topic`, `Fact_Onboarding_topic`, `Dim_Preferencias_Cliente_topic`.
- Rationale: `architectural-patterns.md` vinculante; consistente con autenticacion-y-rbac y gestion-cuentas.
- Alternatives considered:
  - ORM PostgreSQL (rechazado: arquitectura Pinot+Kafka).
  - Escritura directa Pinot (rechazado).

## Decision 4: Membresía solo vía `admin_local_id` (clarificación spec)

- Decision: No usar `Dim_Usuario_Cliente`. Scope Cliente = `ClienteRepository.find_by_admin_local(user_id)`. `CuentaUsuarioRepository` en gestion-cuentas debe refactorizarse para consultar solo `admin_local_id` (tarea de alineación cross-módulo).
- Rationale: Clarificación RN-ONB-007 aprobada en spec.
- Alternatives considered:
  - Tabla puente `Dim_Usuario_Cliente` (rechazado por clarificación).
  - Claim `idcliente` en JWT (rechazado por ahora: evita breaking change en auth).

## Decision 5: Autenticación JWT + autorización (api-authentication)

- Decision:
  - Todos los endpoints requieren Bearer JWT + validación `Fact_Session` activa.
  - **O01, O12, logo upload-url (pre-onboarding)**: solo rol `Administrador`.
  - **Onboarding progreso/etapas, reenviar invitación**: `Administrador` o `Cliente` si `user_id == admin_local_id`.
  - **O08 Cliente**: solo puede reenviar invitación para `admin_local_id` propio (único usuario de la cuenta en este módulo).
- Rationale: api-authentication (JWT stateless + sesión); actores de spec §3.
- Alternatives considered:
  - Onboarding sin auth (rechazado: riesgo de seguridad).
  - Solo Administrador en todo el flujo (rechazado: CU-O02 actor Cliente).

## Decision 6: Etapas canónicas y transiciones de `estado_onboarding`

- Decision:
  - Catálogo fijo: `cambio_password` → `perfil_corporativo` → `preferencias`.
  - `Pendiente` (post O12) → `En progreso` (primera Fact_Onboarding) → `Completado` (3 obligatorias con `completado=true`).
  - `estado='Activo'` en O01 independiente de `estado_onboarding` (RN-ONB-008).
  - Etapa `preferencias` crea primera fila `Dim_Preferencias_Cliente` (RN-ONB-010).
  - Etapa `cambio_password`: validar `Dim_Credencial.estadocredencial='Activo'` o completar vía flujo auth existente antes de marcar etapa.
- Rationale: Clarificaciones sesión 2026-07-09.
- Alternatives considered:
  - Etapas dinámicas por plan en MVP (diferido: spec deja opcionales fuera de alcance detallado).

## Decision 7: Notificaciones SMTP y recordatorios

- Decision:
  - O01 y O08: `OnboardingNotificacionService` → `core/notificaciones` (mismo patrón gestion-cuentas). Fallo SMTP → log, no revierte operación.
  - RN-ONB-004: job programado Django (`management command` + cron/container) `send_onboarding_reminders` — correo semanal desde día 30; sin endpoint REST en MVP.
- Rationale: RNF-ONB-004; capacidad transversal de notificaciones.
- Alternatives considered:
  - Celery dedicado (diferido: proyecto individual; cron suficiente en MVP).
  - Recordatorios in-app (fuera de spec).

## Decision 8: Angular servicios tipados y guards (angular-architect + typescript-expert)

- Decision:
  - `models/incorporacion-cliente.contract.ts` — tipos 1:1 con OpenAPI `operationId`.
  - `IncorporacionClienteApiService` — HTTP tipado.
  - `OnboardingFacadeService` — orquesta wizard (progreso → etapa → siguiente).
  - Guards:
    - `AdministradorGuard` (core, reutilizar) — rutas registro/configuración.
    - `AdminLocalOnboardingGuard` — Cliente solo si `admin_local_id` de la cuenta en ruta.
    - `OnboardingPendienteGuard` — redirige a wizard si `estado_onboarding` ≠ `Completado`.
    - `OnboardingCompletadoGuard` — bloquea re-ingreso al wizard si ya completado.
  - Componentes standalone OnPush; sin lógica de negocio en templates.
- Rationale: Separación presentación/lógica; rutas lazy `cuentas-clientes/incorporacion-clientes/`.
- Alternatives considered:
  - NgRx global (rechazado: scope local del wizard).
  - Un guard monolítico (rechazado: baja testabilidad).

## Decision 9: Registro O01 transaccional lógico

- Decision: `RegistroCuentaService.registrar()` orquesta en orden: validar NIT/gmail únicos → crear `Dim_Usuarios` → `Dim_Credencial` (temp password, `estadocredencial='Cambio contraseña'`) → rol Cliente en `Dim_Usuario_Rol` → crear `Dim_Cliente` con `admin_local_id`, `estado='Activo'` → email invitación.
- Rationale: RF-ONB-001; atomicidad lógica vía servicio (eventos Kafka secuenciales; compensación manual en logs si fallo parcial).
- Alternatives considered:
  - Saga distribuida (rechazado: complejidad excesiva para MVP individual).
