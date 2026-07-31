# UI Contract: Listado + Workpanel Prospectos

**Module**: `ventas-crm` — delta piloto CRUD + Phase 13 chrome Accidente  
**Depends-on API**: [`../backend/contracts/commercial-pipeline-prospects.openapi.yaml`](../backend/contracts/commercial-pipeline-prospects.openapi.yaml)  
**Golden sample UI**: `frontend/src/app/modules/accidentes/pages/detalle-accidente/detalle-accidente.page.html` (+ lista-accidentes para listados).

## Surfaces

| Surface | Route | Roles |
|---------|-------|-------|
| Listado | `/ventas-crm/prospectos` | Admin, GerenteVentas, GerenteCuentasPublicas |
| Workpanel Ver | `/ventas-crm/prospectos/:idprospecto` | Dueño o Admin |
| Board | `/ventas-crm/pipeline` | Admin / Gerentes CRM |
| Entrada directa | `/ventas-crm/entrada-directa` | Admin only |
| Registro público | `/ventas-crm/registro` | anónimo |

## Principio UX (usuario, no técnico)

1. El usuario **elige** opciones por **nombre legible** (combobox / select / typeahead), nunca escribe un PK (`idcondado`, `idcliente`, `idusuario`, `idprospecto` como campo de entrada).
2. En pantallas Ver/Detalles, **no** se muestran IDs técnicos como dato principal (salvo el identificador de negocio del caso si aplica, p. ej. placa). Dueño/cliente se muestran como **nombre / email / razón social**.
3. Los IDs viajan solo en el payload API (ocultos al usuario).

## Listado — must

1. Tabla (patrón Accidente): `md:table` + cards mobile; shared `list-states`.
2. Filtros: activo (Todas/Activo/Inactivo), etapa (Todos + enum). Cambio → página 1.
3. Pager Anterior/Siguiente según `meta.pagination.next_cursor`; Actualizar con ícono refresh.
4. Acción fila: solo `eye` `aria-label="Ver detalles"` ≥44×44. **No** lápiz.
5. Nombre/empresa: texto plano, no único enlace de apertura.
6. Header: si Admin → CTA «Entrada directa»; si Gerente → sin CTA alta.
7. Estados: skeleton / vacío+ícono / error+Reintentar; timeout ~10s.

## Workpanel Ver — must (chrome = Accidente Detalles)

1. Shell `mx-auto max-w-6xl p-8`.
2. **Volver**: link izquierdo `← Volver a la lista` + `app-tabler-icon name="arrow-left"` (no botón outline a la derecha como único chrome).
3. Eyebrow «Detalles» (`text-sm text-text-secondary`) + `h1` nombre completo + **badge(s) etapa/estado en la misma fila** del título.
4. **Modo Ver = proyección tipográfica**: `<dl>` con `dt` uppercase `text-xs tracking-wide text-text-secondary` + `dd` valor texto. **MUST NOT** usar `<input disabled>` para simular solo lectura.
5. Grid responsive: columna principal (datos + acciones de dominio) + opcional columna lateral (historial pipeline / asignación) como Accidente Historial.
6. Secciones en cards `rounded-lg border border-border-default bg-bg-surface p-6` con `h2` de sección.
7. Acciones de dominio: botones con ícono Tabler cuando aplique (avance, Perdido, convertir, asignar); sin Guardar de ficha.
8. Loading/error: shared `list-loading-skeleton` / `list-error-state` (ícono + Reintentar).
9. Perdido: modal/motivo obligatorio (FR-UI-007).
10. 409: mensaje + Refrescar (re-fetch).
11. Asignación (si UI pide gerente): **select por nombre/email**, no campo numérico `idusuario`.

## Entrada directa — must

1. Mismo shell y Volver link que workpanel.
2. Formulario en card(s) sección; labels 14px; inputs `bg-bg-surface` + focus ring Accidente (design-system Formularios).
3. Submit primario con estado carga (gerundio + spinner in-button).
4. Error: alert visible con ícono, no solo `<p>` suelto.
5. Sin campos de ID técnico.

## Board — must

1. Columnas etapas activas; botones avance adyacente + Perdido.
2. Sin drag.
3. Ojo por card → workpanel; empresa texto plano.
4. Empty/error/skeleton shared list-states.

## Forbidden

- Modal de alta de prospecto autenticado.
- PATCH inventado de ficha.
- Abrir detalle clickeando solo el nombre.
- Split-view obligatorio.
- Inputs disabled como “modo Ver”.
- Pedir al usuario que teclee IDs de catálogo / cliente / usuario.
- Mostrar `idcliente` / `idusuario` / `idcondado` como labels visibles de formularios.

## Cross-module note (alta-unidades)

El mismo principio UX aplica a `frontend/.../alta-unidades/pages/formulario/formulario.page.ts`: Condado = combobox de nombres; Cliente dueño = etiqueta legible o oculto (sesión), **nunca** input “Cliente (dueño)” = `1` ni “Condado (ID)” numérico libre. Ver tasks Phase 13 / alta-unidades polish.
