# Modulo: Alta de Unidades

**Ubicacion:** `specs/003-operational/Red-Operativa/alta-unidades/`
**Departamento:** Red-Operativa

Indice global del modulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API, RF/RN/CA, OpenAPI, Pinot/Kafka | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | Interaction Capability (Fase B) | `spec.md`, `plan.md`, `tasks.md`, `quickstart.md` |

## Orden de trabajo

1. Specificar e implementar **backend** primero (contrato OpenAPI + servicios).
2. Luego **frontend**, con `Depends-on: ../backend` — no redefine estados, permisos ni payloads.
3. Cambiar `.specify/feature.json` → `…/alta-unidades/backend` o `…/frontend` segun la capa en curso.

## Convencion de nombres

El archivo de indice del modulo se llama **igual que la carpeta del modulo** (`alta-unidades.md`), no `README.md`.

**Split capas:** Fase A 2026-07-30 (estructural); **Fase B 2026-07-30** — Interaction Capability extraída en [`frontend/spec.md`](./frontend/spec.md).
