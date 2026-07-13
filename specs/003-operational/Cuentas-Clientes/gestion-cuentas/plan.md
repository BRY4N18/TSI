# Implementation Plan: Gestión de Cuenta de Cliente

**Branch**: `003-operational-cuentas-clientes-gestion-cuentas` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Cuentas-Clientes/gestion-cuentas/spec.md`

**Input**: Feature specification from `specs/003-operational/Cuentas-Clientes/gestion-cuentas/spec.md`

## Summary

Implementar gestión de cuenta corporativa (CU-O03, CU-O10, CU-O11) con enfoque **contract-first**: primero contrato OpenAPI REST bajo `api-standards.md`; luego backend Django/DRF en capas **Vista → Servicio → Repositorio** con escritura exclusiva vía Kafka; finalmente frontend Angular 17+ con servicios tipados, guards de autorización y aislamiento por cuenta.

## Traceability

- **Objetivo Operacional (OP)**: OP-TSI-CTA-01 (autogestión de cuenta corporativa con trazabilidad y seguridad).
- **UC cubiertos**: CU-O03, CU-O10, CU-O11.
- **Mapeo de cumplimiento**:
  - Contract-first REST versionado (`/api/v1/cuentas-clientes/...`).
  - Patrón Vista→Servicio→Repositorio; Kafka como único canal de escritura.
  - JWT + validación de sesión (dependencia autenticacion-y-rbac).
  - Notificaciones SMTP vía `core/notificaciones` (fallo no revierte operación).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend Angular 17+)

**Primary Dependencies**: Django 5 + DRF + JWT RS256, Kafka producer, Azure Blob (logo), SMTP (`core/notificaciones`), Angular standalone + RxJS

**Storage**: Apache Pinot (lectura) + Kafka (escritura de `Dim_Cliente`, `Dim_Preferencias_Cliente`, `Fact_Session`)

**Testing**: pytest/APITestCase (backend contract + service), Jasmine (Angular services/guards)

**Target Platform**: Linux containerizado (backend) + SPA web (frontend)

**Project Type**: Aplicación web (backend + frontend)

**Performance Goals**: Operaciones de perfil/preferencias p95 ≤ 300 ms; transferencia/baja p95 ≤ 500 ms; disponibilidad 99.9% (RNF-CTA-001)

**Constraints**: `/api/v1/`, envelope estándar, `Idempotency-Key` en escrituras, sin INSERT/UPDATE directo a Pinot, aislamiento tenant por `idcliente`

**Scale/Scope**: Módulo post-onboarding; actores Cliente (admin local) y Administrador global

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Functional Suitability: PASS — cubre CU-O03/O10/O11 y criterios CA-CTA-001..006.
- Reliability: PASS — baja expulsa sesiones; notificación fallida no revierte operación (RN-CTA-006).
- Performance Efficiency: PASS — objetivos p95 y disponibilidad 99.9% explicitados.
- Interaction Capability: PASS — guards Angular separan admin local, scope de cuenta y rol Administrador.
- Security: PASS — JWT + sesión + RBAC; Cliente solo accede a su `idcliente`; baja solo Administrador.
- Compatibility: PASS — contrato OpenAPI versionado; reutiliza patrones de autenticacion-y-rbac.
- Maintainability: PASS — capas Vista→Servicio→Repositorio; tipos TS alineados al contrato.
- Flexibility: PASS — logo vía URL Blob desacoplado de Pinot; SMTP por variables de entorno.
- Safety: PASS — baja lógica preserva datos históricos; revocación inmediata de sesiones.

Post-Design Gate: PASS (sin violaciones ni excepciones abiertas).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Cuentas-Clientes/gestion-cuentas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── gestion-cuentas.openapi.yaml
└── tasks.md                    # generado por /speckit-tasks
```

### Source Code (repository root)

```text
backend/
├── apps/cuentas_clientes/
│   ├── views/
│   │   └── cuenta_views.py              # Vista DRF (perfil, preferencias, transferencia, baja)
│   ├── services/
│   │   ├── cuenta_perfil_service.py
│   │   ├── cuenta_preferencias_service.py
│   │   ├── transferencia_propiedad_service.py
│   │   ├── baja_cuenta_service.py
│   │   └── cuenta_notificacion_service.py
│   └── tests/
│       ├── api/                         # Contract tests por endpoint
│       └── services/
└── core/
    ├── repositories/cuentas_clientes/
    │   ├── cliente_repository.py
    │   ├── preferencias_cliente_repository.py
    │   ├── cuenta_usuario_repository.py   # membresía usuario↔cuenta
    │   └── session_repository.py        # reutilizado; expulsión masiva en baja
    └── notificaciones/                    # SMTP transversal

frontend/src/app/
├── modules/cuentas-clientes/gestion-cuenta/
│   ├── models/                            # Tipos TS (contrato OpenAPI)
│   ├── services/
│   │   ├── cuenta-cliente-api.service.ts  # HTTP tipado al contrato
│   │   └── cuenta-cliente-facade.service.ts
│   ├── guards/
│   │   ├── cuenta-activa.guard.ts
│   │   ├── cuenta-scope.guard.ts
│   │   └── admin-local.guard.ts
│   └── pages/
│       ├── perfil/
│       ├── preferencias/
│       ├── transferencia/
│       └── baja/                           # solo Administrador
└── core/guards/
    └── administrador.guard.ts              # reutilizar si existe
```

**Structure Decision**: Misma app Django `cuentas_clientes` y módulo Angular `cuentas-clientes` que autenticacion-y-rbac, subcarpeta `gestion-cuenta/` para separar dominio. Escrituras publican a `Dim_Cliente_topic`, `Dim_Preferencias_Cliente_topic` y `Fact_Session_topic`.

## Implementation Order (contract-first)

1. **Contrato OpenAPI** (`contracts/gestion-cuentas.openapi.yaml`) — fuente de verdad.
2. **Backend**: repositorios → servicios → vistas DRF + permisos + tests de contrato.
3. **Frontend**: modelos TS → `CuentaClienteApiService` → guards → páginas (sin lógica de negocio en componentes).

## Complexity Tracking

Sin violaciones de constitution que requieran excepción.
