# Tasks: Registro de Accidentes — Frontend

**Input**: `frontend/spec.md`, `frontend/plan.md`, Depends-on `../backend/`  
**Prerequisites**: Backend OpenAPI y CA-REG-* disponibles.

## Phase 1: Lista y workpanel (FR-UI-001…004, 007–008)

- [X] T-FE-001 Lista: ID texto plano; Acciones ojo/lápiz en `lista-accidentes.page.*`
- [X] T-FE-002 Detalle: modos Detalles/Editar + Guardar condicional en `detalle-accidente.page.*`
- [X] T-FE-003 Selección de fila + CTA Nuevo registro
- [X] T-FE-004 Jasmine lista/detalle

## Phase 2: Paneles adyacentes view (FR-UI-005/006)

- [X] T-FE-005 Detalle: CTAs condicionados + `queryParams.mode=view`
- [X] T-FE-006 Galería solo lectura si `mode=view`
- [X] T-FE-007 Enriquecimiento solo lectura si `mode=view`

## Phase 3: Borrador local UI (FR-UI-009)

- [X] T-FE-008 Banner + Descartar borrador + confirmación usuario en `registro-accidente.page.*`
- [X] T-FE-009 Jasmine RNF-REG-006 UI

## Phase 4: Polish

- [X] T-FE-010 Rebuild Docker `django` + `frontend`; contenedores Up

**Checkpoint**: FR-UI-001…010 cubiertos en código (piloto 2026-07-30).
