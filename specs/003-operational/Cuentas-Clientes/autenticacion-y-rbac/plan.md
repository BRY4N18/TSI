# Implementation Plan: Autenticacion y RBAC

**Branch**: `003-operational-cuentas-clientes-autenticacion-y-rbac` | **Date**: 2026-07-09 | **Spec**: `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/spec.md`

**Input**: Feature specification from `specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/spec.md`

## Summary

Implementar autenticacion y control de acceso RBAC con enfoque contract-first: primero se definen contratos REST (`login`, `logout`, `revoke-session`, `password-reset`) bajo `api-standards.md`; luego se implementa backend Django/DRF en capas Vista -> Servicio -> Repositorio, y finalmente consumo frontend Angular mediante servicios tipados, interceptor JWT y guards por rol.

## Traceability

- **Objetivo Operacional (OP)**: OP-TSI-SEG-01 (acceso seguro y trazable por rol).
- **UC cubiertos**: CU-O04, CU-O05, CU-O06, CU-O07, CU-O13, CU-O15.
- **Mapeo de cumplimiento**:
  - Contract-first REST versionado (`/api/v1`) para compatibilidad.
  - Servicios y repositorios para enforcement de reglas de seguridad y auditabilidad.
  - Tareas por historia con criterios medibles y validación de aceptación.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend Angular 17+)

**Primary Dependencies**: Django 5 + Django REST Framework + JWT (RS256), Angular 17 standalone + RxJS

**Storage**: Apache Pinot (lectura) y Kafka como unico canal de escritura de eventos de dominio

**Testing**: pytest/APITestCase (backend), Jasmine/Karma o equivalente Angular para servicios/guards

**Target Platform**: Linux containerizado para backend y SPA web para frontend

**Project Type**: Aplicacion web (backend + frontend)

**Performance Goals**: CU-O05 con p95 <= 500 ms y disponibilidad mensual >= 99.5%

**Constraints**: API versionada `/api/v1/`, formato de error/ok estandar, validacion JWT + estado de sesion en cada request, sin escritura directa a Pinot

**Scale/Scope**: Modulo base para todos los demas modulos operativos; soporte a usuarios administrativos, operativos y tecnicos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Functional Suitability: PASS - cubre CU-O04/O05/O06/O07/O13/O15 y criterios de aceptacion.
- Reliability: PASS - estado de sesion centralizado en `Fact_Session` con cierre/revocacion.
- Performance Efficiency: PASS - objetivo p95/availability explicitado.
- Interaction Capability: PASS - frontend con guards y rutas por rol minimiza errores de operacion.
- Security: PASS - JWT RS256, RBAC, trazabilidad y validacion de sesion por request.
- Compatibility: PASS - API contract-first versionada (`/api/v1`) para integracion estable.
- Maintainability: PASS - patron por capas Vista->Servicio->Repositorio y contratos tipados.
- Flexibility: PASS - separacion backend/frontend y contratos versionados facilitan evolucion.
- Safety: PASS - modulo transversal que controla acceso a funcionalidades criticas.

Post-Design Gate: PASS (sin violaciones ni excepciones abiertas).

## Project Structure

### Documentation (this feature)

```text
specs/003-operational/Cuentas-Clientes/autenticacion-y-rbac/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── auth-rbac.openapi.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── apps/
│   └── cuentas_clientes/
│       ├── views/           # Vista (DRF views/viewsets)
│       ├── services/        # Casos de uso de autenticacion/RBAC
│       └── tests/           # Tests API/servicio/repositorio
└── core/
    └── repositories/
        └── cuentas_clientes/  # Capa unica de repositorios de dominio

frontend/
└── src/app/
    ├── modules/cuentas-clientes/
    │   └── auth/
    │       ├── pages/
    │       ├── services/
    │       └── guards/
    └── core/
        ├── interceptors/
        └── guards/
```

**Structure Decision**: Se adopta estructura web app backend/frontend definida en `project-structure.md`, con implementacion estricta del patron Vista->Servicio->Repositorio y consumo Angular por servicios/guards.

## Complexity Tracking

Sin violaciones de constitution que requieran excepcion.
