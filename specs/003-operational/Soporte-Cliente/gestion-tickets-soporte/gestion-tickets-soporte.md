# Módulo: Gestión de Tickets de Soporte

**Ubicación:** `specs/003-operational/Soporte-Cliente/gestion-tickets-soporte/`
**Departamento:** Soporte-Cliente

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API, RF/RN/CA, OpenAPI, Pinot/Kafka | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | **Interaction Capability (Fase B)** — FR-UI, layouts, CTAs; cita RF/RNF backend | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Especificar e implementar **backend** primero (contrato OpenAPI + servicios).
2. Luego **frontend**, con `Depends-on: ../backend` — no redefine estados, permisos ni payloads.
3. Cambiar `.specify/feature.json` → `…/gestion-tickets-soporte/backend` o `…/frontend` según la capa en curso.

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`gestion-tickets-soporte.md`), no `README.md`.

**Split capas:** Fase A 2026-07-30 (estructural); **Fase B 2026-07-30** — Interaction Capability extraída en [`frontend/spec.md`](./frontend/spec.md) (autoridad UI).
