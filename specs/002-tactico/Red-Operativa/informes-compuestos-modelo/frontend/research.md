# Research — Informes compuestos de Red Operativa (Frontend)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z de Emergencias, no extraer `shared/`

**Decision:** módulo `red-operativa/gestion/` espejo de `emergencias/gestion/`: una página
parametrizada por `pantallas-gestion.definiciones.ts`. No se mueve la cáscara a `shared/` en esta
pasada.

**Rationale:** FR-UI-003 y la asunción de la spec («copia el patrón, no lo reinventa»). Extraer
ahora obliga a tocar Emergencias ya implementada para un ahorro que aún no existe. Un tercer
departamento justifica la extracción; el segundo no.

**Alternatives considered:** tres páginas HTML distintas — descartado en Emergencias (D1) y aquí
igual. Extraer `shared/informes-z/` — aplazado. Reutilizar `PantallaZPage` de Emergencias importando
entre departamentos — acoplamiento inverso.

## D2 — Dos guards, nunca una unión

**Decision:** `gestionCrecimientoGuard` (`DirectorExpansion` | `Administrador`) en `flota` y
`mercados`; `gestionValidacionGuard` (`DirectorTecnologico` | `Administrador`) en `validacion`.

**Rationale:** backend `RedOperativaCompuestosPermission` + `MATERIAS`. El error natural es un
`canActivate` con los tres roles del departamento: cada director entraría a la materia del otro
**sin síntoma**. Las pruebas de esta capa comprueban la **exclusión**, no solo la entrada.

**Alternatives considered:** reusar `informesFlotaGuard` / `informesValidacionesGuard` de los
listados — descartado: flota admite Cliente y Proveedor. Un guard único «Red Operativa gestión» —
descartado por FR-UI-020.

## D3 — Rutas bajo `/red-operativa/gestion/`, no bajo `/informes/`

**Decision:**

| Pantalla | Ruta | Guard |
|---|---|---|
| Flota y cobertura | `/red-operativa/gestion/flota` | crecimiento |
| Mercados y retirada | `/red-operativa/gestion/mercados` | crecimiento |
| Criterios de validación | `/red-operativa/gestion/validacion` | validación |

**Rationale:** `/red-operativa/informes/*` ya es el índice de listados. El mismo corte que
Emergencias (`/emergencias/gestion/` vs `/emergencias/informes/`).

## D4 — Sidebar: tres enlaces, roles distintos, sin ítem gris

**Decision:** tres `NAV_LINKS` en el grupo Red operativa:

| Etiqueta | Roles |
|---|---|
| Flota y cobertura | `DirectorExpansion`, `Administrador` |
| Mercados y retirada | `DirectorExpansion`, `Administrador` |
| Criterios de validación | `DirectorTecnologico`, `Administrador` |

El enlace único «Informes de red» **no se toca** (listados). No se añade un cuarto «Red Operativa
(gestión)» que reúna las dos materias.

**Rationale:** design-system (sidebar por rol; nunca ítems deshabilitados). SC-F03. Un índice
compartido con tarjetas filtradas —como los listados— descubriría al otro cargo.

**Alternatives considered:** un índice de gestión que oculte tarjetas — viola FR-UI-020 y la regla
de sidebar. Fusionar las dos de Expansión en un enlace — perdería el Z (13 informes de crecimiento
en una vista).

## D5 — Agrupar por materia, no por OT11/OT12/OT13

**Decision:** las pantallas siguen `MATERIAS` del backend. Solo `tasa-aprobacion-primer-intento` y
`motivos-rechazo` van a validación. Tiempo de puesta en operación, mercados activos y OT13 entero
van a Expansión.

**Rationale:** el comentario normativo del servicio: «regiones en riesgo suena a validación y no lo
es». Pintar OT11 entero en la pantalla del Tecnológico le daría mercados y plazos que no gobierna.

**Alternatives considered:** una pantalla por objetivo táctico — contradice FR-025 ya implementado.

## D6 — Sin librería de gráficas

**Decision:** número héroe + barras Tailwind, igual que Emergencias. No Chart.js ni D3.

**Rationale:** el visual grande es distribución de estados, motivos o tiempos. No hay mapas
(FR-UI-014).

## D7 — El período es el único filtro; umbrales y objetivos se leen, no se editan

**Decision:** no hay control de `umbral_unidades`, `dias_objetivo` ni `top`. La pantalla muestra lo
que el backend pone en `meta.filtros` y en las notas (`nota_umbral`, `nota_objetivo`, …).

**Rationale:** FR-UI-005. Editar el umbral en cliente convertiría una convención del informe en un
mando que parece política de la empresa, justo lo que las notas existen para evitar.

**Alternatives considered:** un slider de umbral — fuera de alcance; el backend ya parametriza con
defecto.

## D8 — Lecturas derivadas que el contrato ya trae (no inventar columnas)

**Decision:**

| Concepto | Fuente |
|---|---|
| Sin alternativas | columna `sin_alternativas` (no derivar por `vecinos_declarados === 0` en silencio: usarla y mostrarla) |
| Disponibilidad ausente | `pct_disponibilidad === null` (distinto de `0`) |
| Convención de umbral / 30 días | `meta.filtros` + notas del envelope |
| Medida exacta desde | `meta.medida_exacta_desde` **también cuando `data: []`** |
| Grano de intentos | `meta` / texto fijo del contrato UI (como `campos_comprobados` en Emergencias) |
| Cobertura sin región | valor `'Sin región asignada'` + `nota_region` |

**Rationale:** el backend ya emitió estas señales. Re-derivarlas en el cliente duplica y puede
desfasarse. El único texto declarado en definición es el grano de intentos y las advertencias de
convención si `meta` no trae la nota (defensa, no fuente de verdad).

## D9 — Carga por zona; vacío de despublicación no es éxito

**Decision:** cada zona dispara su GET. Un 403/500 en bajas forzadas no borra el héroe de cobertura
crítica. En Mercados, `data: []` en despublicación **sigue mostrando** `medida_exacta_desde`.

**Rationale:** edge cases de la spec. Un histórico vacío sin la fecha se lee como «nunca pasó»
(backend FR-034, SC-011).

## D10 — Apoyo plegado en Flota (cinco) y Mercados (dos)

**Decision:** Flota: cobertura por región, pendientes, rendimiento, rotación, bajas forzadas en un
bloque «Detalle» plegado. Mercados: los dos de despublicación en el mismo patrón. Validación no
tiene apoyo: dos informes caben en héroe + visual + lectura.

**Rationale:** FR-UI-004. Ocho cards en Flota rompen el Z. Vista principal ≤ 8 bloques.

## D11 — No reutilizar la grilla ni el índice de listados

**Decision:** no usar `InformeCardComponent`. No añadir tarjetas al índice de `/red-operativa/informes`.

**Rationale:** FR-UI-001, SC-F12. El índice admite Cliente/Proveedor en flota; estas pantallas no.
