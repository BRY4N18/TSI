# Quickstart: Alta de Unidades — Frontend (lista paginada)

**Date**: 2026-07-30

## Prerequisites

Proveedor demo + SMTP (SC-006). Spec/plan/contract con **paginación + filtros** (SC-007…009).

## Scenarios

| # | Check |
|---|--------|
| V1 | Lista sin skeleton infinito; timeout → Reintentar |
| V2 | Nueva → `/nueva` (form) |
| V3 | Ojo → `/detalle/:id` sin Guardar |
| V4 | Lápiz → `/editar/:id` mismo form |
| V5 | Alta + gmail → unidad en flota (`idcliente` OK) |
| V6 | SMTP OK / fail + reenviar |
| V7 | Baja 2 pasos |
| V8 | Filtro estado / texto / tipo reduce filas |
| V9 | Con &gt;20 unidades filtradas, solo ≤20 visibles; Siguiente carga más |
| V10 | Actualizar (warm): resultado &lt;2s o error claro |
| V11 | `GET /api/v1/red-operativa/unidades?limit=20` → `meta.pagination` presente |

## Commands

```text
docker exec -e PYTHONPATH=/app -e DJANGO_SETTINGS_MODULE=config.settings `
  accidentes-django python /app/scripts/seed_demo_proveedor_flota.py

# Contract / perf (tras implementar delta list)
docker exec accidentes-django pytest apps/red_operativa/tests/api/test_list_unidades_contract.py -q
docker exec accidentes-django pytest apps/red_operativa/tests/performance/test_list_unidades_p95.py -q -m slow

npx ng test --include=**/red-operativa/alta-unidades/**/*.spec.ts
docker compose -f docker/accidentes.yml up -d --build django frontend
```

## Network (debug)

DevTools → `unidades` → Timing: si **Waiting (TTFB)** ≈ duración total y body ~KB, el cuello es servidor/Pinot — validar query paginada, no “payload grande”.
