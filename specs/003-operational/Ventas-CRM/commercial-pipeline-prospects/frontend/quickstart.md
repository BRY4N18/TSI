# Quickstart: Pipeline Comercial — Frontend

## Prerrequisitos

- Docker: `accidentes-frontend` (:4200), `accidentes-django` (:8000), Pinot/Kafka up.
- Seed Admin (si aún no puedes entrar):

```powershell
docker exec accidentes-django python /app/scripts/seed_demo_usuarios_roles.py
```

Espera ~5–15 s a Pinot realtime.

## Seed de prospectos demo (lista / pipeline)

```powershell
docker exec accidentes-django python /app/scripts/seed_demo_usuarios_roles.py
docker exec accidentes-django python /app/scripts/seed_demo_prospectos.py
```

Espera ~5–15 s. Login GerenteVentas → `/ventas-crm/prospectos` y `/ventas-crm/pipeline`.

## Credenciales demo

| Rol | Usuario | Contraseña | Para qué |
|-----|---------|------------|----------|
| **GerenteVentas** | `lucia.ramos.ventas@demo.tsi.com` | `password123` | Prospectos/Pipeline (día a día); sin Entrada directa |
| **Administrador** | `carlos.mendoza.admin@demo.tsi.com` | `password123` | Listado completo, CTA Entrada directa, asignación huérfano |
| Operador | `sofia.castro.operador@demo.tsi.com` | `password123` | **No** es CRM (Accidentes) |
| Director Estrategia | `elena.nunez.estrategia@demo.tsi.com` | `password123` | Planes Suscripciones — **no** Prospectos |

**Rutas públicas (sin login):**

- http://localhost:4200/ventas-crm/planes  
- http://localhost:4200/ventas-crm/registro  

**CRUD autenticado (stub actual → delta workpanel):**

- http://localhost:4200/ventas-crm/prospectos  
- http://localhost:4200/ventas-crm/pipeline  
- http://localhost:4200/ventas-crm/entrada-directa (Admin)

## Humo — estado actual (antes del delta)

1. Login Admin → `/ventas-crm/prospectos` → verás listado **stub** (`<ul>` + links por nombre).
2. Click nombre → detalle stub con botones crudos avance/Perdido/convertir.
3. `/ventas-crm/pipeline` → columnas stub.

## Humo — tras implementar delta (V-CRM) ✅

| ID | Check | Estado |
|----|-------|--------|
| V-CRM-1 | Listado = tabla; ojo abre Detalles **sin** Guardar ficha | Implementado |
| V-CRM-2 | Cero ícono lápiz; nombre no es el único enlace | Implementado |
| V-CRM-3 | Admin: CTA Entrada directa en header; Gerente (cuando exista): sin CTA | Implementado |
| V-CRM-4 | Filtros activo/etapa reinician página y reducen filas | Implementado |
| V-CRM-5 | Board: botones adyacentes + ojo; sin drag | Implementado |
| V-CRM-6 | 409 en transición → mensaje + Refrescar | Implementado |

## Humo — Phase 13 workpanel Accidente + combobox (UX) ✅

| ID | Check | Estado |
|----|-------|--------|
| V-CRM-7 | Detalles: shell Accidente (`← Volver`, eyebrow Detalles, `dl` RO, sin inputs disabled de ficha) | Implementado |
| V-CRM-8 | Asignar huérfano: motivo + **Tu usuario** (sesión); sin campo ID gerente numérico | Implementado |
| V-CRM-9 | Entrada directa: Volver + card + focus ring; sin IDs técnicos en UI | Implementado |
| UX-UN-1 | Nueva/Editar unidad: País→Estado→Condado por **nombre**; dueño = gmail sesión; sin inputs idcondado/idcliente | Implementado |
| UX-UN-2 | Detalle unidad: `dl` RO; Condado por nombre (no solo id) | Implementado |

## Tests

```powershell
cd frontend
npx ng test --no-watch --browsers=ChromeHeadless --include=**/ventas-crm/pages/listado-prospectos/**/*.spec.ts --include=**/ventas-crm/pages/detalle-prospecto/**/*.spec.ts --include=**/ventas-crm/pages/pipeline-board/**/*.spec.ts --include=**/ventas-crm/pages/entrada-directa/**/*.spec.ts --include=**/red-operativa/alta-unidades/pages/formulario/**/*.spec.ts
```

## Rebuild

```powershell
docker compose -f docker/accidentes.yml up -d --build frontend
```
