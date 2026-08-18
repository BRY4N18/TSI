# Research — Informes compuestos de Cuentas y Clientes (Frontend)

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z, no extraer `shared/`

**Decision:** módulo `cuentas-clientes/gestion/` espejo de `partners/gestion/` y `suscripciones/gestion/`: una página parametrizada por definiciones. No se mueve la cáscara a `shared/`.

**Rationale:** extraer ahora obliga a tocar seis módulos ya verdes. Una spec de refactor, no esta, justifica la extracción.

**Alternatives considered:** tres páginas HTML distintas; importar `PantallaZPage` de Partners (acoplamiento inverso).

## D2 — Dos guards, nunca una unión

**Decision:** `gestionCicloGuard` y `gestionIncorporacionGuard` con **solo** `Administrador`. `gestionAccesoGuard` con `DirectorTecnologico` y `Administrador`. Cliente, Operador y cargos ajenos → access-denied.

**Rationale:** backend `CuentasCompuestosPermission`. Un guard unión le daría al Tecnológico el churn (FR-UI-019). El guard de listados deja al Tecnológico entrar al índice porque desde ahí llega a accesos técnicos; reusarlo en ciclo/incorporación abriría esas materias.

**Alternatives considered:** un solo guard como Partners — viola la autoridad partida. Ampliar el de listados — mezclaría L1–L8 con Z.

## D3 — Rutas bajo `/cuentas-clientes/gestion/`, no bajo `/informes/` ni `/gestion-cuenta`

**Decision:**

| Pantalla | Ruta | Guard |
|---|---|---|
| Ciclo de vida | `/cuentas-clientes/gestion/ciclo` | Administrador |
| Incorporación | `/cuentas-clientes/gestion/incorporacion` | Administrador |
| Acceso | `/cuentas-clientes/gestion/acceso` | Tecnológico + Administrador |

**Rationale:** `/cuentas-clientes/informes` ya es el índice de listados. `/cuentas-clientes/gestion-cuenta` es el perfil del cliente. Los compuestos de los demás departamentos ya usaron `/gestion/`.

## D4 — El envelope es `{ data: { resultados }, meta }`

**Decision:** el cliente extrae `data.resultados`. Las notas van en `meta.nota_cobertura`, `meta.nota_catalogo`, `meta.nota_solape`. Copiar `data: Record[]` de Ventas dejaría las zonas vacías con 200.

**Rationale:** `informe_cuentas` arma el cuerpo con `resultados`, igual que Partners.

## D5 — Ocupación y cobertura son un solo bloque

**Decision:** usuarios, tope y `pct_cobertura_pertenencia` se pintan juntos. Cliente sin plan → «sin dato», no 0 %. `meta.nota_cobertura` junto al visual.

**Rationale:** FR-UI-009. Un héroe de % ocupación solo afirma una cartera que el 9,5 % no representa.

## D6 — El embudo muestra el catálogo, no lo observado

**Decision:** se pintan **todas** las filas que el backend envía, incluidas las de cero clientes. `meta.nota_catalogo` junto al visual. Prohibido filtrar `clientes_que_llegaron = 0` en cliente.

**Rationale:** FR-UI-011. Filtrar ceros afirmaría 100 % de finalización.

## D7 — Duración con sesiones abiertas a la vista

**Decision:** `sesiones_sin_cierre` se pinta junto a la mediana. `concurrencia_maxima` y `sesiones_iniciadas` conviven; no se titula como recuento de logins. `meta.nota_solape` si viene.

**Rationale:** FR-UI-013..015.

## D8 — Pares vacíos = cero filas

**Decision:** el MVP no envía `pares_incompatibles`. Zona vacía. No se pinta «más de un rol». Hallazgo: `idusuario` + ambos roles, nunca el nombre.

**Rationale:** FR-UI-016, FR-UI-017. El multi-rol es el mecanismo previsto.

## D9 — Sin token, sin identidad, sin mapas

**Decision:** no hay ficha de persona ni de sesión. Prohibido resolver `idusuario` contra otra API.

**Rationale:** exclusión constitucional. El token de `Fact_Session` no entra al modelo; la UI no lo reintroduce.

## D10 — Sin librería de gráficas

**Decision:** número héroe + barras Tailwind.

**Rationale:** `package.json` no las tiene. El visual es una distribución (cohorte, etapa, franja).

## D11 — El período es el único filtro

**Decision:** no se editan `dias_inactividad`, `mes_cohorte` ni `pares_incompatibles`. Viajan los defectos del servidor (90 días, pares vacíos).

**Rationale:** FR-UI-005. Un constructor de informes rompería Hick.

## D12 — Carga por zona

**Decision:** cada zona dispara su GET. Un 500 en riesgo no borra el churn.

**Rationale:** igual que Partners D10.

## D13 — Antigüedad en apoyo plegado

**Decision:** Ciclo de vida tiene cuatro informes. Antigüedad va en `apoyo` plegado para no pasar de 8 bloques.

**Rationale:** FR-UI-004, SC-F12.

## D14 — Docker al final de la serie, no ahora

**Decision:** esta pasada no reconstruye contenedores. El usuario pidió terminar la implementación y dejar el rebuild del aplicativo para después.

**Rationale:** el rebuild anterior colgó el daemon. El código se verifica con `ng test` / `ng build` en host.
