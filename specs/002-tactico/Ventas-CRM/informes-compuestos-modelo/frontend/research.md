# Research — Informes compuestos de Ventas y CRM (Frontend)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z, no extraer `shared/`

**Decision:** módulo `ventas-crm/gestion/` espejo de `emergencias/gestion/` y
`red-operativa/gestion/`: una página parametrizada por `pantallas-gestion.definiciones.ts`. No se
mueve la cáscara a `shared/` en esta pasada.

**Rationale:** la spec deja fuera de alcance el frontend de Emergencias y Red Operativa. Extraer
ahora obliga a tocar dos módulos ya verdes para un ahorro que no es de esta capa. Un cuarto
departamento, o una spec de refactor, justifica la extracción.

**Alternatives considered:** tres páginas HTML distintas — descartado en Emergencias (D1). Extraer
`shared/informes-z/` — aplazado: viola el Out of Scope. Importar `PantallaZPage` de Emergencias —
acoplamiento inverso entre departamentos.

## D2 — Un guard propio, no el de los listados

**Decision:** `ventasCrmGestionGuard` con `DirectorMarketing`, `GerenteVentas` y `Administrador`.
`GerenteCuentasPublicas`, Operador y Cliente reciben access-denied.

**Rationale:** backend `VentasCrmCompuestosPermission`. El guard de listados
(`informes-ventas-crm.guard`) **admite Cuentas Públicas**. Reusarlo abriría los compuestos a quien
el backend responde 403, y el síntoma sería un enlace que «entra y falla».

**Alternatives considered:** ampliar el guard de listados — mezclaría dos productos. Un guard solo
para el Director — dejaría fuera al ejecutivo, que FR-UI-019 admite acotado.

## D3 — Rutas bajo `/ventas-crm/gestion/`, no bajo `/informes/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Embudo comercial | `/ventas-crm/gestion/embudo` |
| Captación por canal | `/ventas-crm/gestion/captacion` |
| Nutrición del prospecto | `/ventas-crm/gestion/nutricion` |

**Rationale:** `/ventas-crm/informes/*` ya es el índice de listados simples. `/ventas-crm/pipeline`
es el tablero operativo. Los compuestos de Emergencias y Red Operativa ya usaron `/gestion/` por
la misma razón.

## D4 — El alcance se lee de `meta.acotado_a`, no del rol

**Decision:** la etiqueta junto al período pinta `meta.acotado_a` del envelope (`todos` |
`propios`). Si las zonas discrepan, se muestra el valor de la primera zona con dato y las demás
no inventan otro.

**Rationale:** FR-UI-020. Inferir el alcance desde `DirectorMarketing` vs `GerenteVentas` en el
cliente duplicaría la regla del backend y se desincronizaría si el Administrador cambia de
acotamiento. El campo existe precisamente para no adivinar.

**Alternatives considered:** ocultar la etiqueta al Director («es obvio que ve todos») — descartado:
sin etiqueta, ejecutivo y director discuten cifras distintas sin saber por qué.

## D5 — Sin librería de gráficas

**Decision:** número héroe + barras de distribución / por etapa o canal con Tailwind. No se añade
Chart.js ni D3.

**Rationale:** `package.json` no las tiene. El visual grande del Z es una distribución (permanencia,
conversión por canal, uso de demo), no un mapa (FR-UI-018).

**Alternatives considered:** introducir una librería «porque es un dashboard» — dependencia nueva
sin justificación.

## D6 — El CAC no se titula ni se completa en cliente

**Decision:** la lectura de Captación muestra `convertidos` + `nota_indicador` tal como llegan.
Prohibido el título «CAC», una columna de coste y cualquier división local «por si acaso».

**Rationale:** backend FR-021..023. Una columna vacía en pantalla invita a rellenarla a mano. La
nota ya declara qué falta.

## D7 — Los pesos del pipeline se muestran, no se editan

**Decision:** `meta.filtros.nota_pesos` (y `pesos_etapa` si viene) se pintan junto al apoyo de
pipeline. El MVP **no** expone un editor de pesos: el período sigue siendo el único filtro
(FR-UI-005).

**Rationale:** FR-UI-011. Editar pesos en esta capa inventaría una acción que el backend acepta
como query param pero la spec de UI prohíbe. Quien necesite otros pesos lo pide en otra spec.

## D8 — Carga por zona, no un único spinner de página

**Decision:** cada zona Z dispara su GET. Un 500 en motivos de pérdida no borra el embudo.

**Rationale:** edge case de la spec. Igual que Emergencias D8.

## D9 — Apoyo plegado en Embudo y Nutrición

**Decision:**

- Embudo: carga por ejecutivo y pipeline ponderado en un bloque «Detalle» plegado.
- Nutrición: reglas de disparo plegadas. Intensidad y secciones pueden compartir el visual
  grande (dos informes, una zona).
- Captación: sin apoyo; tres zonas de dato bastan.

**Rationale:** FR-UI-004. Cinco cards iguales rompen el Z.

## D10 — Sidebar: tres enlaces nuevos, no reetiquetar listados

**Decision:** tres `NAV_LINKS` en el grupo Ventas CRM, roles del guard, textos «Embudo comercial»,
«Captación por canal», «Nutrición del prospecto». El enlace «Informes comerciales»
(`/ventas-crm/informes`) **no se toca**. Cuentas Públicas sigue viendo listados y **no** estos
tres.

**Rationale:** design-system: el sidebar muestra solo lo que el rol puede abrir. Un ítem gris de
gestión para Cuentas Públicas descubriría la capa.

## D11 — Carga por ejecutivo: clave, nunca nombre

**Decision:** la zona de carga pinta `idejecutivo` como clave. Prohibido resolver nombre, correo o
cargo contra otra API.

**Rationale:** backend FR-028. El modelo no tiene el nombre; ir a buscarlo al operativo saltaría
Depends-on y la exclusión constitucional.

## D12 — OT03 vacío es vacío, no un tablero de ceros

**Decision:** `data: []` en intensidad / efectividad / latencia → estado **vacío** de la zona (y
de la pantalla si todas lo están). Filas con `eventos = 0` solo existen si el backend las
devuelve, y entonces significan «hubo demo y no se usó».

**Rationale:** FR-UI-014, SC-F06. Hoy las fuentes están vacías en el entorno; pintar 0 % afirmaría
que se midió el producto.

## D13 — `idprospecto` en intensidad no es ficha de persona

**Decision:** el visual de intensidad agrega por `empresa` (y recuento de eventos / secciones).
No se titula la fila con el identificador como si fuera un nombre.

**Rationale:** el grano del informe es prospecto × período, y `idprospecto` es clave, no identidad.
Mostrarlo como titular de fila se lee como ficha personal (FR-UI-016).
