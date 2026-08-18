# Research — OE2 frontend

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z, no extraer `shared/`

**Decision:** módulo `estrategico/oe2/` espejo de `partners/gestion/`: una página parametrizada por definiciones. No se mueve la cáscara a `shared/`. No se importa `PantallaZPage` de Partners.

**Rationale:** AGENTS.md y la spec de Partners D1: extraer ahora toca seis módulos verdes. Importar desde táctico acopla capas.

**Alternatives considered:** tres HTML distintos — descartado en Emergencias. Extraer `shared/informes-z/` — fuera de alcance.

## D2 — Dos guards, nunca una unión

**Decision:**

| Guard | Roles | Pantallas |
|---|---|---|
| `oe2UsoEcosistemaGuard` | `DirectorTecnologico` · `Gerente` | uso, ecosistema |
| `oe2DineroGuard` | esos **más** `DirectorFinanciero` | dinero |

**Rationale:** FR-UI-023/024. Un `canActivate` único le daría al Financiero la latencia de todos (el backend responde 403). El Tecnológico **sí** entra a Dinero (FR-OE2-006); si el HTTP lo negara, se corrige el HTTP, no el menú.

**Alternatives considered:** reusar `partnersGestionGuard` — admite Administrador y no admite Gerente/Financiero. Un guard unión — viola §4.2.

## D3 — Rutas bajo `/estrategico/oe2/`, no bajo `/partners/gestion/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Uso de la API | `/estrategico/oe2/uso` |
| Dinero de la API | `/estrategico/oe2/dinero` |
| Ecosistema | `/estrategico/oe2/ecosistema` |

Grupo de sidebar **Estratégico**, no «Partners y API».

**Rationale:** mezclarlas con Consumo táctico pondría dos p95 en el mismo grupo. El Partner ya ve ese grupo; un ítem gris descubriría la comparativa de todos.

## D4 — Envelope `{ data, meta }`, no `data.resultados` táctico

**Decision:** el cliente tipa `data` como array de filas y lee `meta.cobertura`, `meta.falta`, `meta.alcance`, `meta.objetivo`, `meta.comparacion`. Prohibido buscar `meta.nota_muestras` o `data.resultados` (nombres tácticos).

**Rationale:** OpenAPI OE2. Copiar el tipo de Partners dejaría las zonas vacías con 200 OK.

## D5 — El trío p95 / media / muestras es un widget

**Decision:** la zona de latencia pinta, por endpoint, `latencia_p95_ms`, `latencia_media_ms`, `muestras` y `percentil_fiable`. `percentil_fiable = 0` o p95 `null` → marca **no fiable**; la fila **sigue**. `data: []` → **vacio**, no 0 ms.

**Rationale:** FR-UI-008/009. No hay un p95 global que sumar en cliente.

## D6 — Sin librería de gráficas

**Decision:** número héroe + barras Tailwind. No Chart.js ni D3.

**Rationale:** `package.json` no las tiene. El visual grande es distribución (clase HTTP, versión), no un mapa.

## D7 — Período + granularidad + comparación

**Decision:** controles globales: `desde`, `hasta`, `granularidad` (`mes` | `trimestre` | `anio`) y `comparacion` (`ninguna` | `mom` | `yoy`). No hay editor de `muestra_minima`. Si `meta.comparacion` viene nula con motivo, se pinta **ausente**, no un 400.

**Rationale:** contrato estratégico. El táctico solo tiene fechas; copiar su selector entero omitiría la comparación (FR-UI-005, FR-UI-027).

## D8 — E2-06 no existe en UI

**Decision:** ningún slug `disponibilidad-api` en definiciones, rutas ni OpenAPI de pantalla. Un GET a esa ruta, si alguien lo escribe, no se invoca desde esta capa.

**Rationale:** FR-UI-021. Un recuadro vacío se leería como 100 %.

## D9 — Carga por zona

**Decision:** cada zona dispara su GET. Un 500 en comparativa no borra el héroe. 403 de zona (Financiero en un informe de uso, si se equivocara la definición) se pinta como error de zona, no como pantalla caída.

## D10 — Parcial y alcance salen de `meta`, no se inventan

**Decision:** banner de parcial solo si `meta.cobertura === 'parcial'`. Texto de «no cobrado» solo si `meta.alcance` lo trae (E2-08). Prohibido hardcodear el copy si el backend no lo envía — salvo un fallback idéntico al contrato para no silenciar FR-UI-015 cuando el campo falta por bug.

## D11 — `'v1'` no se colapsa

**Decision:** adopción pinta clave `(servicio, version)`. Prohibido `groupBy(version)` en cliente.

## D12 — Crecimiento = primera 2xx

**Decision:** el héroe de Ecosistema usa el GET `crecimiento-ecosistema` tal cual. Prohibido mezclar con un recuento de credenciales (no hay ese informe en OE2 publicado).

## D13 — Vacío, sin_dato, no fiable, cero de partner

| Señal | Estado |
|---|---|
| `data: []` | **vacio** |
| métrica `null` (p95 bajo muestra) | **sin_dato** en esa cifra; fila visible |
| `percentil_fiable = 0` | **dato** + marca |
| partner con `llamadas = 0` | **dato**: cero real |
| comparación nula con motivo | **ausente**, no error |

## D14 — No hay `acotado_a`

**Decision:** no se pinta zona de alcance territorial. El envelope estratégico no lo envía.

## D15 — Sidebar: tres enlaces nuevos, roles partidos

**Decision:** grupo `Estratégico`. Uso y Ecosistema: roles Tecnológico y Gerente. Dinero: esos más Financiero. PartnerIntegracion **ausente**. Administrador **ausente** (no está en §4.2).

**Rationale:** un ítem gris para el Partner descubriría el ecosistema. Meter Administrador «porque entra a Partners táctico» ampliaría de más.

## D16 — Primera carpeta estratégica: no reusar módulo táctico

**Decision:** `modules/estrategico/oe2/` nace vacío de OE3–OE6. No se crea un `informes-estrategicos/` genérico en esta pasada (evitar un cajón para seis OE).
