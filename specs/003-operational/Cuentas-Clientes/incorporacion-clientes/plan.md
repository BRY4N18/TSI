# Implementation Plan: Incorporación de Clientes

**Branch**: `003-operational-cuentas-clientes-incorporacion-clientes` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/spec.md`

**Input**: Feature specification from `specs/003-operational/Cuentas-Clientes/incorporacion-clientes/spec.md`

## Summary

Implementar alta, configuración y onboarding digital de clientes (CU-O01, O12, O02, O09, O08) con enfoque **contract-first**: primero contrato OpenAPI REST según `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía Kafka; finalmente frontend Angular 17+ con servicios tipados (`typescript-expert`), guards (`angular-architect`) y wizard de onboarding. Membresía usuario↔cuenta exclusivamente por `Dim_Cliente.admin_local_id` (sin `Dim_Usuario_Cliente`).

## Traceability

- **Objetivo Operacional (OP)**: OP-TSI-ONB-01 (incorporación B2B/B2G con onboarding trazable).
- **UC cubiertos**: CU-O01, CU-O12, CU-O02, CU-O09, CU-O08.
- **Mapeo de cumplimiento**:
  - Contract-first REST versionado (`/api/v1/cuentas-clientes/...`).
  - Patrón Vista→Servicio→Repositorio; Kafka como único canal de escritura.
  - JWT + validación de sesión (dependencia autenticacion-y-rbac).
  - SMTP vía `core/notificaciones`; fallo no revierte operación.
  - Recordatorios semanales día 30+ vía job programado (RN-ONB-004).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend Angular 17+)

**Primary Dependencies**: Django 5 + DRF + JWT RS256, Kafka producer, Azure Blob (logo), SMTP (`core/notificaciones`), Angular standalone + RxJS

**Storage**: Apache Pinot (lectura) + Kafka (escritura de `Dim_Cliente`, `Dim_Usuarios`, `Dim_Credencial`, `Dim_Usuario_Rol`, `Fact_Onboarding`, `Dim_Preferencias_Cliente`)

**Testing**: pytest/APITestCase (backend contract + service), Jasmine (Angular services/guards)

**Target Platform**: Linux containerizado (backend) + SPA web (frontend)

**Project Type**: Aplicación web (backend + frontend)

**Performance Goals**: Registro O01 < 3 min usuario (RNF-ONB-001); p95 registro API ≤ 800 ms; p95 etapa onboarding ≤ 500 ms; onboarding 24/7 (RNF-ONB-002)

**Constraints**: `/api/v1/`, envelope estándar, `Idempotency-Key` en escrituras, sin INSERT/UPDATE directo a Pinot, scope Cliente vía `admin_local_id`

**Scale/Scope**: Módulo prerequisito de gestion-cuentas; actores Administrador y Cliente (admin local)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Functional Suitability: PASS — cubre CU-O01/O12/O02/O09/O08 y CA-ONB-001..007.
- Reliability: PASS — progreso persistido en Fact_Onboarding; reanudación sin pérdida (RN-ONB-005).
- Performance Efficiency: PASS — RNF-ONB-001/002 explicitados; objetivos p95 en Technical Context.
- Interaction Capability: PASS — wizard Angular con guards de onboarding y rol.
- Security: PASS — JWT + sesión; O01/O12 solo Administrador; scope por `admin_local_id`.
- Compatibility: PASS — contrato OpenAPI versionado; reutiliza patrones auth y gestion-cuentas (logo Blob).
- Maintainability: PASS — capas Vista→Servicio→Repositorio; tipos TS alineados al contrato.
- Flexibility: PASS — etapas opcionales por plan diferidas; SMTP por env.
- Safety: PASS — sin borrado físico; credenciales temporales con cambio forzado.

Post-Design Gate: PASS (sin violaciones ni excepciones abiertas).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Cuentas-Clientes/incorporacion-clientes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── incorporacion-clientes.openapi.yaml
└── tasks.md                    # generado por /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── apps/cuentas_clientes/
│   ├── views/
│   │   └── onboarding_views.py           # Vista DRF (registro, config, onboarding, invitación)
│   ├── services/
│   │   ├── registro_cuenta_service.py    # CU-O01
│   │   ├── configuracion_cuenta_service.py # CU-O12
│   │   ├── onboarding_service.py         # CU-O02, O09
│   │   ├── invitacion_service.py         # CU-O08
│   │   └── onboarding_notificacion_service.py
│   ├── management/commands/
│   │   └── send_onboarding_reminders.py  # RN-ONB-004
│   └── tests/
│       ├── api/                          # Contract tests por endpoint
│       └── services/
└── core/
    ├── repositories/cuentas_clientes/
    │   ├── cliente_repository.py         # extender create/find_by_admin_local
    │   ├── onboarding_repository.py      # Fact_Onboarding
    │   ├── user_repository.py            # reutilizar
    │   ├── credential_repository.py      # reutilizar
    │   ├── role_repository.py            # reutilizar
    │   └── preferencias_cliente_repository.py
    └── notificaciones/

frontend/src/app/
├── modules/cuentas-clientes/incorporacion-clientes/
│   ├── models/
│   │   └── incorporacion-cliente.contract.ts
│   ├── services/
│   │   ├── incorporacion-cliente-api.service.ts
│   │   └── onboarding-facade.service.ts
│   ├── guards/
│   │   ├── admin-local-onboarding.guard.ts
│   │   ├── onboarding-pendiente.guard.ts
│   │   └── onboarding-completado.guard.ts
│   └── pages/
│       ├── registro/                     # Admin: O01
│       ├── configuracion/                # Admin: O12
│       └── onboarding-wizard/            # Cliente: O02
└── core/guards/
    └── administrador.guard.ts            # reutilizar
```

**Structure Decision**: Misma app Django `cuentas_clientes` y módulo Angular `cuentas-clientes`; subcarpeta `incorporacion-clientes/` separada de `gestion-cuenta/`. Añadir `Fact_Onboarding_topic` a `KAFKA_TOPICS` en `settings.py`. Refactorizar `CuentaUsuarioRepository` para alinear membresía con clarificación spec.

## Implementation Order (contract-first)

1. **Contrato OpenAPI** (`contracts/incorporacion-clientes.openapi.yaml`) — fuente de verdad.
2. **Backend**: repositorios → servicios → vistas DRF + permisos + tests de contrato + topic Kafka onboarding.
3. **Frontend**: modelos TS → `IncorporacionClienteApiService` → guards → páginas wizard.
4. **Job recordatorios**: management command + documentación cron en quickstart.
5. **Alineación gestion-cuentas**: refactor `CuentaUsuarioRepository` a `admin_local_id`.

## Complexity Tracking

| Violación / deuda | Justificación | Mitigación |
|-------------------|---------------|------------|
| `CuentaUsuarioRepository` usa `Dim_Usuario_Cliente` hoy | Implementado antes de clarificación RN-ONB-007 | Refactor en tarea de alineación post-onboarding |
| Etapas opcionales por plan sin catálogo | Fuera de alcance spec §13 | Hook en `OnboardingService` para extensión futura |
