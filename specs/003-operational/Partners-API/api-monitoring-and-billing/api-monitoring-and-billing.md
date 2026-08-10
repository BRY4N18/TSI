# Módulo: Monitoreo y Facturación de API

**Ubicación:** `specs/003-operational/Partners-API/api-monitoring-and-billing/`  
**Departamento:** Partners y API  
**CUs:** CU-O51, CU-O52, CU-O53, CU-O54  
**SRS:** §3.4.2 «Módulo: Monitoreo y Facturación de API»

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Dominio, API de datos, medición, límites, tarificación, OpenAPI, Pinot/Kafka | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*.openapi.yaml`, `quickstart.md`, `traceability.md` |
| **Frontend** | [`frontend/`](./frontend/) | Interaction Capability (consola de logs en tiempo real, panel de consumo del partner) | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Specificar e implementar **backend** primero (contrato OpenAPI + servicios).
2. Luego **frontend**, con `Depends-on: ../backend`.
3. Cambiar `.specify/feature.json` → `…/api-monitoring-and-billing/backend` o `…/frontend` según la capa en curso.

## Dependencias de módulo

- **Requiere:** [`partner-api-onboarding`](../partner-api-onboarding/) (#07) — sin partners con credenciales no hay consumo que medir; `autenticacion-y-rbac`; `subscriptions-and-billing` (emisión de `Fact_Factura`)
- **Consumido por:** [`partner-access-management`](../partner-access-management/) (#09) — la mora que dispara la suspensión nace de las facturas de excedente que emite este módulo

## Jerarquía de fuentes

| Prioridad | Fuente | Qué aporta |
|---|---|---|
| 1 | `informestacticos/TSI-SRS-Especificacion-de-Requisitos.md` §3.4.2 | **Manda** en toda regla de negocio |
| 2 | `informestacticos/TSI-Catalogo-CU-RF-RNF.md` §5.5 | Numeración canónica CU-O48–O55 y RFs |
| 3 | `../PortalPartnersAPI.md` | Mapeo a tablas Pinot (INSERT/UPDATE por CU) |

> ⚠️ **Numeración legacy obsoleta.** `PortalPartnersAPI.md` usa CU-O73/O74/O75/O78/O82/O83, números que en el catálogo limpio pertenecen a **Emergencias** y **Soporte al Cliente**. Este módulo usa exclusivamente **CU-O51–CU-O54**. Mapeo en [`backend/spec.md` § Clarifications](./backend/spec.md).

## Frontera con el resto del departamento

| Responsabilidad | Dueño |
|---|---|
| Emitir, rotar y nombrar credenciales | `partner-api-onboarding` (#07) |
| **Validar la credencial en cada llamada, medir, limitar y tarificar** | **este módulo** |
| Revocar por seguridad, avisar de mora, suspender y reactivar | `partner-access-management` (#09) |
| Emitir el documento `Fact_Factura` | `subscriptions-and-billing` |
| Disputar una factura | `gestion-tickets-soporte` (CU-O83 / RF-O83.2) |

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`api-monitoring-and-billing.md`), no `README.md`.
