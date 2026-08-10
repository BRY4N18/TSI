# Módulo: Gestión de Acceso de Partners

**Ubicación:** `specs/003-operational/Partners-API/partner-access-management/`  
**Departamento:** Partners y API  
**CU:** CU-O55  
**SRS:** §3.4.3 «Módulo: Gestión de Acceso de Partners»

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API, RF/RN/CA, OpenAPI, Pinot/Kafka | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*.openapi.yaml`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | Interaction Capability (revocación de autoservicio, panel de suspensiones del Administrador) | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Specificar e implementar **backend** primero (contrato OpenAPI + servicios).
2. Luego **frontend**, con `Depends-on: ../backend`.
3. Cambiar `.specify/feature.json` → `…/partner-access-management/backend` o `…/frontend` según la capa en curso.

## Dependencias de módulo

- **Requiere:** [`partner-api-onboarding`](../partner-api-onboarding/) (#07) — emite las credenciales que este módulo invalida; [`api-monitoring-and-billing`](../api-monitoring-and-billing/) (#08) — emite las facturas de excedente cuya mora dispara la suspensión; `subscriptions-and-billing`; `autenticacion-y-rbac`
- **Cierra el departamento:** ningún módulo depende de este.

## Jerarquía de fuentes

| Prioridad | Fuente | Qué aporta |
|---|---|---|
| 1 | `informestacticos/TSI-SRS-Especificacion-de-Requisitos.md` §3.4.3 | **Manda** en toda regla de negocio |
| 2 | `informestacticos/TSI-Catalogo-CU-RF-RNF.md` §5.5 | Numeración canónica y RF-O55.1–4 |
| 3 | `../PortalPartnersAPI.md` | Mapeo a tablas Pinot (INSERT/UPDATE por CU) |

> ⚠️ **Numeración legacy obsoleta.** `PortalPartnersAPI.md` reparte este módulo en CU-O84 (revocar), CU-O81 (aviso de mora), CU-O79 (suspensión automática) y CU-O76 (suspensión/reactivación manual). En el catálogo limpio **los cuatro son un solo CU: CU-O55**. Mapeo en [`backend/spec.md` § Clarifications](./backend/spec.md).

## Frontera con el resto del departamento

| Responsabilidad | Dueño |
|---|---|
| Emitir, nombrar y rotar credenciales | `partner-api-onboarding` (#07) |
| Medir el consumo y emitir la factura de excedente | `api-monitoring-and-billing` (#08) |
| **Invalidar credenciales, avisar de mora, suspender y reactivar** | **este módulo** |
| Suspender la **suscripción** por mora (distinto de suspender al partner) | `subscriptions-and-billing` (RF-SUSF-007) |

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`partner-access-management.md`), no `README.md`.
