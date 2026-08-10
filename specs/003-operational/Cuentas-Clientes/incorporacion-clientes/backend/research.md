# Phase 0 Research - Incorporación de Clientes

**Numeración de CU corregida 2026-08-08** al catálogo vigente (ver `spec.md` Clarifications). Este documento narra decisiones en orden histórico; donde "O01" o "O12" aparecen ligados a "registro"/"plan"/"logo"/"configuración" son **capacidades retiradas sin CU vigente**, distintas del **CU-O12 vigente** (reenviar invitación).

## Decision 1: Contract-first con OpenAPI

- Decision: Definir primero `contracts/incorporacion-clientes.openapi.yaml` con todos los endpoints bajo `/api/v1/cuentas-clientes/...`.
- Rationale: Cumple `api-standards.md` y permite tipos TypeScript + tests de contrato antes de vistas DRF (django-expert).
- Alternatives considered:
  - Implementar vistas primero (rechazado: desalineación frontend/backend).
  - Un solo endpoint monolítico de onboarding (rechazado: no mapea registro directo / config. plan+logo / CU-O11 / CU-O12 por separado).

## Decision 2: Endpoints REST y semántica HTTP

- Decision:
  - `POST /cuentas-clientes` — registro directo (legado, retirado; solo Administrador, `Idempotency-Key`).
  - `PATCH /cuentas-clientes/{idcliente}/configuracion` — config. plan+logo (legado, retirado) + `estado_onboarding=Pendiente`.
  - `POST /cuentas-clientes/{idcliente}/logo/upload-url` — URL firmada Azure Blob (mismo patrón que gestion-cuentas).
  - `GET /cuentas-clientes/{idcliente}/onboarding/progreso` — CU-O11 (RF-O11.2) consulta de etapas.
  - `POST /cuentas-clientes/{idcliente}/onboarding/etapas` — CU-O11 completar etapa canónica.
  - `POST /cuentas-clientes/{idcliente}/invitacion/reenviar` — CU-O12 temp password + email.
- Rationale: Recursos anidados bajo cuenta; POST para comandos; PATCH para configuración parcial; envelope estándar.
- Alternatives considered:
  - `PUT` para configuración completa (rechazado: solo dos campos editables en config. plan+logo legado).
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
  - **Registro directo, config. plan+logo (legado), logo upload-url (pre-onboarding)**: solo rol `Administrador`.
  - **Onboarding progreso/etapas, reenviar invitación**: `Administrador` o `Cliente` si `user_id == admin_local_id`.
  - **CU-O12 Cliente**: solo puede reenviar invitación para `admin_local_id` propio (único usuario de la cuenta en este módulo).
- Rationale: api-authentication (JWT stateless + sesión); actores de spec §3.
- Alternatives considered:
  - Onboarding sin auth (rechazado: riesgo de seguridad).
  - Solo Administrador en todo el flujo (rechazado: CU-O11 actor Cliente).

## Decision 6: Etapas canónicas y transiciones de `estado_onboarding`

- Decision:
  - Catálogo fijo: `cambio_password` → `perfil_corporativo` → `preferencias`.
  - `Pendiente` (post CU-O10 aprobar) → `En progreso` (primera Fact_Onboarding) → `Completado` (3 obligatorias con `completado=true`).
  - `estado='Activo'` independiente de `estado_onboarding` (RN-ONB-008).
  - Etapa `preferencias` crea primera fila `Dim_Preferencias_Cliente` (RN-ONB-010).
  - Etapa `cambio_password`: validar `Dim_Credencial.estadocredencial='Activo'` o completar vía flujo auth existente antes de marcar etapa.
- Rationale: Clarificaciones sesión 2026-07-09.
- Alternatives considered:
  - Etapas dinámicas por plan en MVP (diferido: spec deja opcionales fuera de alcance detallado).

## Decision 7: Notificaciones SMTP y recordatorios

- Decision:
  - Autorregistro (CU-O09), aprobación/rechazo (CU-O10) y reenvío (CU-O12): `OnboardingNotificacionService` → `core/notificaciones` (mismo patrón gestion-cuentas). Fallo SMTP → log, no revierte operación.
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

## Decision 9: Registro directo transaccional lógico (legado, retirado)

- Decision: *(Histórico Phase 3)* `RegistroCuentaService` creaba `Activo` inmediato. **Superada 2026-07-25:** registro directo retirado (410, sin CU vigente); alta vía CU-O09→CU-O10.

## Decision 10: Cierre gaps 2026-07-25

- Decision:
  - Camino único CU-O09→CU-O10 para todos los tipos; registro directo / config. plan+logo (legado) → HTTP 410.
  - Soft-anular `Rechazado` → `Rechazado_Anulado`; NIT reutilizable en nuevo CU-O09.
  - Email SMTP en aprobar/rechazar; login permitido en pendiente; gate por módulo.
  - UI CU-O12 (reenviar invitación) en solicitudes Admin + wizard (configuracion sin ruta).
- Rationale: Decisiones producto Session 2026-07-25; elimina pantallas fantasma Admin.
- Alternatives considered:
  - Mantener registro directo legado no-Proveedor (rechazado).
  - Bloquear login hasta Activo (rechazado: gate por módulo).
  - Reintento NIT self-service tras Rechazado (rechazado: soft-anular Admin).
