# Módulo: Registro de Accidentes

**Ubicación:** `specs/003-operational/Emergencias/registro-accidente/`  
**Departamento:** Emergencias  
**CUs:** CU-O56, CU-O58, CU-O73, CU-O57 (+ consulta/edición RF-REG-005)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API, RF/RN/CA, OpenAPI, Pinot/Kafka | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*.openapi.yaml`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | Interaction Capability (lista, workpanel, borrador UI) | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Specificar e implementar **backend** primero (contrato OpenAPI + servicios).
2. Luego **frontend**, con `Depends-on: ../backend` — no redefine estados, permisos ni payloads.
3. Cambiar `.specify/feature.json` → `…/registro-accidente/backend` o `…/frontend` según la capa en curso.

## Dependencias de módulo

- Requiere: `autenticacion-y-rbac`, `incorporacion-regional`
- Consumido por: `despacho-inteligente`, `evidencia-unidad`, `seguimiento-cierre-de-casos`

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`registro-accidente.md`), no `README.md`.

**Split capas:** Fase A estructural + Fase B Interaction en `frontend/` (FR-UI-001…010 Active).
