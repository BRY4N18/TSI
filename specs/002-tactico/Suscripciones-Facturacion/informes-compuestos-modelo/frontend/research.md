# Research — Informes compuestos de Suscripciones y Facturación (Frontend)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z, no extraer `shared/`

**Decision:** módulo `suscripciones/gestion/` espejo de `emergencias/gestion/`,
`red-operativa/gestion/` y `ventas-crm/gestion/`: una página parametrizada por
`pantallas-gestion.definiciones.ts`. No se mueve la cáscara a `shared/` en esta pasada.

**Rationale:** la spec deja fuera de alcance el frontend de los otros departamentos. Extraer ahora
obliga a tocar tres módulos ya verdes para un ahorro que no es de esta capa. Una spec de refactor,
no esta, justifica la extracción.

**Alternatives considered:** tres páginas HTML distintas — descartado en Emergencias (D1). Extraer
`shared/informes-z/` — aplazado: viola el Out of Scope. Importar `PantallaZPage` de Ventas —
acoplamiento inverso entre departamentos.

## D2 — Dos guards, nunca una unión

**Decision:** `gestionFinanzasGuard` (`DirectorFinanciero` | `Administrador`) en `cobro` y
`movimientos`; `gestionCatalogoGuard` (`DirectorEstrategia` | `Administrador`) en `catalogo`.

**Rationale:** backend `SuscripcionesCompuestosPermission` + `MATERIAS`. El error natural es un
`canActivate` con los tres roles del departamento: cada director entraría a la materia del otro
**sin síntoma**. Las pruebas de esta capa comprueban la **exclusión**, no solo la entrada.

**Alternatives considered:** reusar `informesFinanzasGuard` / `informesCatalogoGuard` de los
listados — descartado: esos listados admiten Cliente y Proveedor. Un guard único «Suscripciones
gestión» — descartado por FR-UI-025.

## D3 — Rutas bajo `/suscripciones/gestion/`, no bajo `/informes/`

**Decision:**

| Pantalla | Ruta | Guard |
|---|---|---|
| Cobro e ingreso | `/suscripciones/gestion/cobro` | finanzas |
| Movimientos de cartera | `/suscripciones/gestion/movimientos` | finanzas |
| Catálogo y uso | `/suscripciones/gestion/catalogo` | catálogo |

**Rationale:** `/suscripciones/informes/*` ya es el índice de listados. El mismo corte que
Emergencias, Red Operativa y Ventas (`/…/gestion/` vs `/…/informes/`).

## D4 — Sidebar: tres enlaces, roles distintos, sin ítem gris

**Decision:** tres `NAV_LINKS` en el grupo Suscripciones:

| Etiqueta | Roles |
|---|---|
| Cobro e ingreso | `DirectorFinanciero`, `Administrador` |
| Movimientos de cartera | `DirectorFinanciero`, `Administrador` |
| Catálogo y uso | `DirectorEstrategia`, `Administrador` |

El enlace «Informes de suscripciones» (`/suscripciones/informes`) **no se toca**. No se añade un
cuarto «Suscripciones (gestión)» que reúna las dos materias. Cliente y Proveedor siguen viendo
listados y **no** estos tres.

**Rationale:** design-system (sidebar por rol; nunca ítems deshabilitados). SC-F03. Un índice
compartido con tarjetas filtradas descubriría al otro cargo.

**Alternatives considered:** un índice de gestión que oculte tarjetas — viola FR-UI-025. Fusionar
cobro y movimientos en un enlace — perdería el Z (diez informes de finanzas en una vista).

## D5 — Agrupar por materia, no por OT05/OT06/OT07 en un tablero

**Decision:** las pantallas siguen `MATERIAS` del backend. OT06 entero va a Cobro e ingreso; OT07
entero a Movimientos de cartera; OT05 entero a Catálogo y uso. Las dos primeras comparten
audiencia, **no** pantalla.

**Rationale:** FR-UI-001, FR-UI-025. Pintar OT05 en el menú del Financiero le daría el catálogo que
no gobierna. Pintar las dos de finanzas juntas rompería el tope de 6–8 bloques.

**Alternatives considered:** una pantalla por objetivo táctico con las tres visibles a ambos —
contradice FR-038 / FR-039 ya implementados.

## D6 — Sin librería de gráficas

**Decision:** número héroe + barras de distribución Tailwind. No se añade Chart.js ni D3.

**Rationale:** `package.json` no las tiene. El visual grande del Z es una distribución (ingresos
por plan, movimientos por tipo, utilización usado/contratado), no un mapa (FR-UI-019).

**Alternatives considered:** introducir una librería «porque es un dashboard» — dependencia nueva
sin justificación.

## D7 — El período es el único filtro; escalones y aviso se leen, no se editan

**Decision:** no hay control de `escalones_dunning` ni de `dias_aviso_caducidad`. La pantalla
muestra lo que el backend pone en `meta.filtros`. Tampoco hay un segundo selector de mes aparte
del período: MRR y NRR se piden con `desde`/`hasta` y **declaran** el mes resuelto.

**Rationale:** FR-UI-005. Editar el escalón en cliente convertiría una convención del informe en un
mando que parece política de cobro. Un selector de mes duplicaría el período y haría creer que se
comparan ventanas arbitrarias.

**Alternatives considered:** un editor de escalones — fuera de alcance; el backend ya parametriza
con defecto `3,5` y `30`.

## D8 — Mes natural se pinta desde `meta`, no se recalcula

**Decision:** en Cobro (MRR) y Movimientos (NRR), junto al período, se muestra `meta.mes` y
`meta.nota_periodo` del envelope. Prohibido derivar el mes en cliente a partir de `desde`/`hasta`.

**Rationale:** backend research D8 y FR-UI-011. Si el cliente «adivina» el mes, un cambio de regla
en el servidor (p. ej. anclar al `desde` en vez del `hasta`) desincronizaría la etiqueta y la
cifra.

**Alternatives considered:** ocultar la nota cuando el rango ya es un mes cerrado — descartado:
sin etiqueta, dos ventanas distintas se discuten como si midieran lo mismo.

## D9 — Carga por zona, no un único spinner de página

**Decision:** cada zona Z dispara su GET. Un 500 en dunning no borra el MRR.

**Rationale:** edge case de la spec. Igual que Emergencias D8 y Red Operativa D9.

## D10 — Apoyo plegado en Cobro (tres) y Movimientos (uno)

**Decision:**

- Cobro e ingreso: cobro al primer intento, dunning y clientes sin método en un bloque «Detalle»
  plegado.
- Movimientos: suspensión / reactivación plegada.
- Catálogo y uso: sin apoyo; tres zonas de dato bastan.

**Rationale:** FR-UI-004, SC-F08. Seis cards iguales en Cobro rompen el Z. Vista principal ≤ 8
bloques (héroe, período+mes, visual, lectura, apoyo como **un** bloque plegado).

## D11 — No reutilizar la grilla ni el índice de listados

**Decision:** no usar `InformeCardComponent`. No añadir tarjetas al índice de
`/suscripciones/informes`. No reutilizar el shell de `catalogo-planes` ni el de `metodos-pago`.

**Rationale:** FR-UI-001, SC-F12. El índice admite Cliente/Proveedor; estas pantallas no. El
catálogo de planes es operación de Estrategia, no esta lectura.

## D12 — Lo que llega se pinta; no se recalcula vigencia ni signo

**Decision:** la pantalla **no** filtra por `activo`, **no** mensualiza precios, **no** cambia el
signo de `notas_credito`. Muestra `sin_periodicidad` aparte, `notas_credito` restando,
`pendientes` fuera de la mediana, `tipo_movimiento` tal cual.

**Rationale:** Depends-on. Recalcular en cliente duplicaría las reglas que el backend ya corrigió
(cancelada con `activo=true`, Empresarial más barato que Profesional, disputa ≠ impago).

## D13 — Utilización: usado y contratado; nunca una columna de llamadas

**Decision:** el visual de Catálogo pinta `unidades_usadas` / `unidades_limite` y
`usuarios_usados` / `usuarios_limite`, más `nota_dimension_pendiente`. Prohibido añadir
`llamadas`, `api` o un hueco titulado consumo, aunque el valor sea `null`.

**Rationale:** backend FR-030, FR-UI-016, SC-F13. Un vacío se lee como «no consume la API».

## D14 — Clientes sin método: comercial, no instrumento

**Decision:** el apoyo de Cobro pinta `nombre_comercial`, `tipo`, `estado_comercial` y
`caduca_en_dias`. Prohibido navegar a `/suscripciones/metodos-pago` desde esa fila, resolver el
token, o mostrar últimos dígitos.

**Rationale:** el informe existe para ver **quién no tiene método**, no cuál es. Un enlace al
listado de métodos (que sí tiene el instrumento, y que admite al Cliente) saltaría la exclusión
constitucional en un clic.

## D15 — Plan de precio cero visible; `idcliente` no es ficha

**Decision:** la distribución muestra `clientes` y `mrr_aportado` por plan, incluido precio cero.
En utilización, la fila se titula por `plan` (y recuento); `idcliente` es clave, no se resuelve a
persona ni fiscal.

**Rationale:** FR-UI-015, FR-UI-018. Omitir el demo haría un éxito falso o una ausencia.
Resolver identidad contra el operativo saltaría Depends-on.
