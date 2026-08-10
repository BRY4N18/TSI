# Módulo: Onboarding de Partners API

**Ubicación:** `specs/003-operational/Partners-API/partner-api-onboarding/`  
**Departamento:** Partners y API  
**CUs:** CU-O48, CU-O49, CU-O50  
**SRS:** §3.4.1 «Módulo: Onboarding de Partners API»

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API, RF/RN/CA, OpenAPI, Pinot/Kafka | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*.openapi.yaml`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | Interaction Capability (consola de partners, workpanel de incorporación, portal del partner) | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Specificar e implementar **backend** primero (contrato OpenAPI + servicios).
2. Luego **frontend**, con `Depends-on: ../backend` — no redefine estados, permisos ni payloads.
3. Cambiar `.specify/feature.json` → `…/partner-api-onboarding/backend` o `…/frontend` según la capa en curso.

## Dependencias de módulo

- **Requiere:** `autenticacion-y-rbac`, `incorporacion-clientes`, `subscriptions-and-billing`
- **Consumido por:** `api-monitoring-and-billing` (#08), `partner-access-management` (#09)

## Jerarquía de fuentes

| Prioridad | Fuente | Qué aporta |
|---|---|---|
| 1 | `informestacticos/TSI-SRS-Especificacion-de-Requisitos.md` §3.4.1 | **Manda** en toda regla de negocio |
| 2 | `informestacticos/TSI-Catalogo-CU-RF-RNF.md` §5.5 | Numeración canónica CU-O48–O55 y RFs |
| 3 | `../PortalPartnersAPI.md` | Mapeo a tablas Pinot (INSERT/UPDATE por CU) |

> ⚠️ **Numeración legacy obsoleta.** `PortalPartnersAPI.md` usa CU-O71/O72/O80, números que en el catálogo limpio pertenecen a **Emergencias**. Este módulo usa exclusivamente la numeración canónica CU-O48–O50. Ver mapeo en [`backend/spec.md` § Clarifications](./backend/spec.md).

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`partner-api-onboarding.md`), no `README.md`.
