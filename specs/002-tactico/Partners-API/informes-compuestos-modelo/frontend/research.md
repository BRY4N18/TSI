# Research — Informes compuestos de Partners y API (Frontend)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z, no extraer `shared/`

**Decision:** módulo `partners/gestion/` espejo de `emergencias/gestion/`,
`red-operativa/gestion/`, `ventas-crm/gestion/`, `suscripciones/gestion/` y
`soporte-cliente/gestion/`: una página parametrizada por
`pantallas-gestion.definiciones.ts`. No se mueve la cáscara a `shared/` en esta pasada.

**Rationale:** la spec deja fuera de alcance el frontend de los otros departamentos. Extraer
ahora obliga a tocar cinco módulos ya verdes para un ahorro que no es de esta capa. Una spec de
refactor, no esta, justifica la extracción.

**Alternatives considered:** tres páginas HTML distintas — descartado en Emergencias (D1). Extraer
`shared/informes-z/` — aplazado: viola el Out of Scope. Importar `PantallaZPage` de Soporte —
acoplamiento inverso entre departamentos.

## D2 — Un guard propio, no el de listados ni el de la consola

**Decision:** `partnersGestionGuard` con `DirectorTecnologico` y `Administrador`.
`PartnerIntegracion`, `DesarrolladorAPIs`, Cliente y Operador reciben access-denied.

**Rationale:** backend `PartnersCompuestosPermission`. El guard de listados admite
`DesarrolladorAPIs` y `PartnerIntegracion`. La consola admite `DesarrolladorAPIs` y, en parte,
solo Administrador. Reusar cualquiera abriría un enlace que «entra y falla» o dejaría al
Director sin menú / metería al partner en la comparativa de todos.

**Alternatives considered:** ampliar el guard de informes simples — mezclaría listados (el
partner entra acotado) con lectura comparada. Un guard que sume `DesarrolladorAPIs` «porque
opera la API» — el backend responde 403; FR-UI-023 lo prohíbe.

## D3 — Rutas bajo `/partners/gestion/`, no bajo `/informes/`, `/consola/` ni `/portal/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Consumo de la API | `/partners/gestion/consumo` |
| Incorporación | `/partners/gestion/incorporacion` |
| Entrega contratada | `/partners/gestion/entrega` |

**Rationale:** `/partners/informes/*` ya es el índice de listados (el Partner entra).
`/partners/consola/reportes` y `/partners/portal/consumo` son el operativo (solo media). Los
compuestos de los cinco departamentos anteriores ya usaron `/gestion/` por la misma razón.

## D4 — No hay zona de alcance: el partner no entra

**Decision:** esta capa **no** pinta `meta.acotado_a`. El envelope de Partners no lo envía: no
hay cifra «propios». Copiar `zona-alcance` de Soporte afirmaría un acotamiento que no existe.

**Rationale:** FR-UI-023 del spec de Partners es exclusión de menú, no etiqueta de titularidad.
Inferir «todos» desde el rol duplicaría una regla que el backend ya resolvió no emitiendo el
campo.

**Alternatives considered:** pintar «departamento entero» siempre — ruido; el único que entra ya
lo sabe. Reusar el aviso de los listados (`propios`) — mentiría.

## D5 — El envelope lleva `nota_muestras` en `meta`, no `declaraciones` en `data`

**Decision:** el cliente tipa `data` como `{ resultados, periodo? }` y lee
`meta.nota_muestras` cuando viene. Las zonas leen `data.resultados`. La nota se pinta **junto a
la zona** que pidió un informe de `INFORMES_MUESTRAS` (héroe de Consumo, como mínimo).

**Rationale:** `informe_partners` no copia el envelope de Soporte. Copiar
`data.declaraciones` dejaría la nota invisible con 200 OK. Copiar `EnvelopeInforme.data: Record[]`
de Ventas dejaría las zonas vacías — fallo silencioso.

**Alternatives considered:** normalizar a array y tirar `meta` — perdería FR-UI-009 y FR-UI-025.

## D6 — El trío p95 / media / muestras es un widget, no tres

**Decision:** `zona-heroe` de Consumo pinta **todas** las filas de `latencia-p95`:
`endpoint_path`, `latencia_p95_ms`, `latencia_media_ms`, `muestras`, `percentil_fiable`.
`percentil_fiable = 0` → marca **no fiable** en esa fila; la fila **sigue**. `resultados: []` →
**vacio**, no 0 ms. `meta.nota_muestras` se lee en el mismo bloque.

**Rationale:** FR-UI-008, SC-F02. El backend agrupa por endpoint; no hay un p95 global que
sumar en cliente. Elegir «el peor» o «el último» inventaría un héroe. Dos endpoints hoy caben
en un bloque. Tres cards —p95 / media / muestras— romperían el Z y el par inseparable.

**Alternatives considered:** agregar en cliente — viola Depends-on. Héroe = una sola fila
elegida — viola el BSC «por endpoint».

## D7 — Sin librería de gráficas

**Decision:** número héroe + barras de distribución Tailwind. No se añade Chart.js ni D3.

**Rationale:** `package.json` no las tiene. El visual grande del Z es una distribución (clase
de error, canal, versión), no un mapa (FR-UI-021).

**Alternatives considered:** introducir una librería «porque es un dashboard» — dependencia
nueva sin justificación.

## D8 — `percentil`, `muestra_minima`, `mes` y `dias_aviso` no se editan

**Decision:** el período refresca todas las zonas. Los demás parámetros viajan con el defecto
del servidor. No hay segundo filtro global.

**Rationale:** FR-UI-005. Un constructor de informes rompería Hick. El backend ya marca
fiabilidad con `muestra_minima = 20`.

**Alternatives considered:** exponer el mínimo de muestras — la spec reserva el período como
única acción de la capa.

## D9 — Un GET de Entrega alimenta héroe y lectura

**Decision:** `clientes-integracion-activa` se pide **una vez**. El héroe muestra `pct`,
`con_integracion`, `clientes_totales` y `meta`. La lectura usa **la misma fila** para decir qué
implicaría un 100 % (contar solo a quienes ya tienen partner). El visual es otro GET
(`volumen-expedientes`).

**Rationale:** son el mismo informe. Dos GET idénticos no añaden verdad. Restar o porcentuar en
cliente a partir de `con_integracion / clientes_totales` duplicaría `pct`; se muestra `pct` tal
cual.

**Alternatives considered:** dos informes ficticios para la lectura — no existen.

## D10 — Carga por zona, no un único spinner de página

**Decision:** cada zona Z dispara su GET (salvo D9). Un 500 en comparativa no borra el héroe.

**Rationale:** edge case de la spec. Igual que Emergencias D8 / Ventas D8 / Soporte D11.

## D11 — Apoyo plegado en Consumo e Incorporación

**Decision:**

- Consumo: métricas, reporte mensual, consumo por endpoint y participación de ingresos en
  **un** bloque «Detalle» plegado (cuatro GET al abrir, o al cargar en paralelo con la zona
  plegada sin competir en peso visual).
- Incorporación: tasa de rechazo en apoyo plegado.
- Entrega: sin apoyo; héroe + canales + lectura bastan.

**Rationale:** FR-UI-004. Siete cards iguales en Consumo romperían el Z (SC-F14).

## D12 — 429, 403 y 5xx no se suman en cliente

**Decision:** la taxonomía agrupa visualmente por `clase_resultado` (cupo, autorización,
servicio). Prohibido un total «errores HTTP» aunque sea la suma de las tres. El recuento
`errores` de métricas/reporte, si se muestra en apoyo, se etiqueta como **no éxito**, no como
«fallos del servicio».

**Rationale:** FR-UI-010, SC-F04. El backend ya no las suma en la taxonomía; el cliente no debe
«ayudar».

## D13 — `'v1'` no se colapsa entre servicios

**Decision:** adopción pinta la clave `(servicio, version)`. Prohibido agrupar solo por
`version` en cliente.

**Rationale:** FR-UI-014, SC-F07. Dos APIs que comparten la etiqueta son dos contratos.

## D14 — Sidebar: tres enlaces nuevos, no reetiquetar consola ni portal

**Decision:** tres `NAV_LINKS` en el grupo Partners, roles del guard, textos «Consumo de la
API», «Incorporación», «Entrega contratada». No se tocan «Informes de partners», «Estado de mi
acceso», «Registros de API», «Reporte de consumo», «Mi consumo» ni la consola.

**Rationale:** design-system: el sidebar muestra solo lo que el rol puede abrir. Un ítem gris
de gestión para el Partner descubriría la comparativa de todos. Reetiquetar el reporte
operativo anularía FR-UI-013 y FR-UI-026.

## D15 — Sin ficha de llamada, sin IP, sin ir a la consola desde una fila

**Decision:** comparativa y métricas pintan `partner` (etiqueta comercial). Motivos pintan
`motivo_inactividad`, no persona. Prohibido resolver contacto contra otra API. Prohibido
enlazar una fila a `/partners/consola/logs` (la consola muestra IP).

**Rationale:** backend SC-008. Abrir el detalle operativo desde esta lectura reintroduciría IP
y convertiría «ver» en «diagnosticar una llamada».

## D16 — Vacío, sin_dato, no fiable y ceros de partner no se confunden

**Decision:**

| Señal | Estado de zona |
|---|---|
| `resultados: []` | **vacio** — no héroe en 0 ms / 0 % |
| fila con `pct` / `latencia_p95_ms` / `dias` = `null` | **sin_dato** para esa métrica |
| `percentil_fiable = 0` con fila presente | **dato** + marca no fiable |
| partner con `llamadas = 0` | **dato**: el cero es real (SC-F05) |
| `en_proceso = 1` y `dias` nulo | **dato**: en proceso, no cero días |

**Rationale:** FR-UI-006, FR-UI-007, FR-UI-009, FR-UI-011, FR-UI-017.

## D17 — La latencia de esta lectura se declara distinta del operativo

**Decision:** Consumo muestra, junto al héroe, que **esta** p95 no es la media de
`/partners/consola/reportes` ni de «Mi consumo». No se reutiliza el layout de esas pantallas.

**Rationale:** FR-UI-013, SC-F06. Sin la declaración, el mismo partner tendrá dos latencias y
nadie sabrá cuál creer — el defecto documentado del operativo.
