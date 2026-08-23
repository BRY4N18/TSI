# `specs/Global/` — Especificaciones transversales

Specs que **no pertenecen a un módulo**: aplican a todo el sistema. Se distinguen de
`001-estrategico`, `002-tactico` y `003-operational` en que no hay un departamento dueño.

| Spec | Qué es | Reglas |
|---|---|---|
| [`PlanPruebas/`](PlanPruebas/) | **Catálogo maestro.** Las 57 reglas de validación con su estado de cobertura. No se implementa directamente. | Las 57 |
| [`Endurecimiento-Seguridad/`](Endurecimiento-Seguridad/) | Feature Speckit: aislamiento multi-tenant, JWT, inyección, datos sensibles. | `PG-SEC-*` |

## Cómo se relacionan

`PlanPruebas/spec.md` es un **documento de gobierno**, de la misma familia que
`.specify/docs/architecture/testing.md` o `design-system.md`: declara qué debe cumplir el sistema
y en qué estado está cada garantía. No tiene `plan.md` ni `tasks.md`, y no se le pasa
`/speckit-plan` — hacerlo sobre 49 reglas pendientes produciría un `tasks.md` inservible.

Lo que sí son features Speckit normales son los **bloques de reglas**, agrupados por lo que
comparten código, pruebas y criterios de aceptación:

| Feature prevista | Reglas | Por qué van juntas |
|---|---|---|
| `Endurecimiento-Seguridad` ✅ creada | 10 `PG-SEC-*` | Misma superficie (auth, permisos) y misma suite |
| `Integridad-Datos` | 8 `PG-OPE-*` + 6 `PG-ANA-*` | Ambas requieren la suite `integration` con Kafka/Pinot/ClickHouse |
| `Robustez-API` | 5 `PG-API-*` + 5 `PG-NEG-*` | Atacan la capa de vistas y serializadores |
| `Resiliencia-Operacion` | 6 `PG-RES-*` | Timeouts, degradación, sondas |
| `Frontend-Robustez` | 6 `PG-UI-*` | Angular y Playwright |

Las restantes (`PG-CFG-005`, `PG-CI-*`, `PG-DOC-*`) son sueltas y baratas: se resuelven fuera de
ciclo con entrada en `.specify/docs/changelog.md`, como se hizo con `PG-CFG-001/002/003` el
2026-08-23.

**Al cerrar cada feature** se actualiza el estado de sus reglas en `PlanPruebas/spec.md` y se
regenera `PlanPruebas/traceability.md`, que se cuenta desde el spec y no se escribe a mano.
