# Modulo: Alta de Unidades

**Ubicacion:** `specs/003-operational/Red-Operativa/alta-unidades/`  
**Departamento:** Red-Operativa  
**CUs:** CU-O54, CU-O56, CU-O57, CU-O58 (CU-O59 retirado)

Indice global del modulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API, RF/RN/CA, OpenAPI | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | Lista + **página Detalles** + **página Formulario (crear/editar)**; SMTP/gmail; sin workpanel | `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/*`, `quickstart.md`, `tasks.md`, `checklists/` |

## Orden de trabajo

1. Backend primero (OpenAPI + servicios) — ya disponible.
2. Frontend: lista + Detalles (read) + Formulario (crear/editar) — **plan actualizado**; regenerar tasks e implementar (+ delta BE).
3. Cambiar `.specify/feature.json` entre capas según el trabajo (FE vs BE delta).

## Dependencias

- Requiere: autenticacion-y-rbac, infraestructura / cobertura regional según backend.
- Relacionado: evidencia-unidad (disponibilidad CU-O30).

## Convencion de nombres

El indice se llama **`alta-unidades.md`**, no `README.md`.

**Clarify 2026-07-30:** Sin workpanel. Dos páginas full (lectura vs formulario crear/editar). SMTP + gmail obligatorio. **Tasks regeneradas** T001–T032 en [`frontend/tasks.md`](./frontend/tasks.md). Siguiente: `/speckit-implement`.
