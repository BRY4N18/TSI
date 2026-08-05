# Módulo: Informes Tácticos Simples

**Ubicación:** `specs/002-tactico/Emergencias/informes-tacticos-simples/`
**Feature paraguas:** `002-tactico` (ver también `specs/002-tactico/infraestructura/` — infraestructura ClickHouse+Airflow, hermana de este módulo)
**Departamento:** Emergencias
**Base:** `informestacticos/auditoria-esquemas-informes-v2.md` (informes ✅ Cubiertos, consulta directa a Pinot)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa** (`backend` o `frontend`), apuntada por `.specify/feature.json`.

**Estado (2026-08-02):** **backend y frontend completos y verificados contra el sistema real.** Backend: 16 endpoints (93 tests del módulo, suite completa del backend: 1007 passed). Frontend: módulo `modules/emergencias/` con 3 workpanels (Registro/Despacho/Seguimiento), `ng build` sin errores, recorrido real en navegador confirmando las 16 tarjetas con datos reales de Pinot.

## Capas

| Capa | Ruta Speckit | Autoridad | Artefactos |
|------|--------------|-----------|------------|
| **Backend** | [`backend/`](./backend/) | Consultas SQL a Pinot, endpoints de agregación, RF/RN/CA | `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, `contracts/*.openapi.yaml`, `quickstart.md` |
| **Frontend** | [`frontend/`](./frontend/) | 3 workpanels (Registro, Despacho, Seguimiento) — tarjetas/gráficas de informe | `spec.md`, `plan.md`, `tasks.md`, `contracts/*.ui-contract.md`, `quickstart.md` |

## Orden de trabajo

1. Especificar e implementar **backend** primero (endpoints de agregación sobre Pinot, uno por informe).
2. Luego **frontend**, con `Depends-on: ../backend` — los 3 workpanels consumen esos endpoints, sin redefinir cálculos.
3. Cambiar `.specify/feature.json` → `…/informes-tacticos-simples/backend` o `…/frontend` según la capa en curso.

## Dependencias de módulo

- Requiere (solo lectura, sin cambios): `registro-accidente`, `despacho-inteligente`, `seguimiento-cierre-de-casos` (mismas tablas Pinot que ya pueblan esos módulos)
- No depende de `002-tactico` (ClickHouse/Airflow) — este módulo es 100% Pinot directo
- Hermano de: la futura spec de "Informes Tácticos Compuestos" (ClickHouse + Airflow), que sí depende de `002-tactico`

## Convención de nombres

El archivo de índice del módulo se llama **igual que la carpeta del módulo** (`informes-tacticos-simples.md`), no `README.md`.
