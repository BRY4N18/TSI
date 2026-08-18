# Research — Informes compuestos de Soporte al Cliente (Frontend)

**Fecha:** 2026-08-17 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z, no extraer `shared/`

**Decision:** módulo `soporte-cliente/gestion/` espejo de `emergencias/gestion/`,
`red-operativa/gestion/`, `ventas-crm/gestion/` y `suscripciones/gestion/`: una página
parametrizada por `pantallas-gestion.definiciones.ts`. No se mueve la cáscara a `shared/` en
esta pasada.

**Rationale:** la spec deja fuera de alcance el frontend de los otros departamentos. Extraer
ahora obliga a tocar cuatro módulos ya verdes para un ahorro que no es de esta capa. Una spec de
refactor, no esta, justifica la extracción.

**Alternatives considered:** tres páginas HTML distintas — descartado en Emergencias (D1). Extraer
`shared/informes-z/` — aplazado: viola el Out of Scope. Importar `PantallaZPage` de Ventas —
acoplamiento inverso entre departamentos.

## D2 — Un guard propio, no el de listados ni el de la cola

**Decision:** `soporteGestionGuard` con `GerenteExitoCliente`, `Soporte` y `Administrador`.
Cliente, Operador, `DesarrolladorAPIs` y `DirectorTecnologico` reciben access-denied.

**Rationale:** backend `SoporteCompuestosPermission`. El guard de listados
(`informesTicketsGuard`) **admite Cliente**. El de cola/dashboard (`agenteSoporteGuard`) **no
incluye al Gerente** e **incluye** `DesarrolladorAPIs` / `DirectorTecnologico`, que el backend de
compuestos responde 403. Reusar cualquiera abriría un enlace que «entra y falla» o dejaría al
Gerente sin menú.

**Alternatives considered:** ampliar `agenteSoporteGuard` — mezclaría operación diaria con
lectura táctica. Un guard solo para el Gerente — dejaría fuera al agente, que FR-UI-022 admite
acotado.

## D3 — Rutas bajo `/soporte-cliente/gestion/`, no bajo `/informes/` ni `/dashboard`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Cumplimiento de SLA | `/soporte-cliente/gestion/cumplimiento` |
| Cola en curso | `/soporte-cliente/gestion/cola` |
| Tendencias | `/soporte-cliente/gestion/tendencias` |

**Rationale:** `/soporte-cliente/informes/*` ya es el índice de listados (el Cliente entra y ve
asunto). `/soporte-cliente/dashboard` es el tablero operativo sin período. Los compuestos de los
cuatro departamentos anteriores ya usaron `/gestion/` por la misma razón.

## D4 — El alcance se lee de `meta.acotado_a`, no del rol

**Decision:** la etiqueta junto al período pinta `meta.acotado_a` del envelope (`todos` |
`propios`). Si las zonas discrepan, se muestra el valor de la primera zona con dato y las demás
no inventan otro.

**Rationale:** FR-UI-023. Inferir el alcance desde `GerenteExitoCliente` vs `Soporte` en el
cliente duplicaría la regla del backend y se desincronizaría si el Administrador cambia de
acotamiento. El campo existe precisamente para no adivinar.

**Alternatives considered:** ocultar la etiqueta al Gerente («es obvio que ve todos») — descartado:
sin etiqueta, agente y gerente discuten cifras distintas sin saber por qué.

## D5 — El envelope no es el de Ventas

**Decision:** el cliente tipa `data` como objeto `{ resultados, declaraciones, periodo? }`, no
como array. Las zonas leen `data.resultados`. Las advertencias se pintan desde
`data.declaraciones[].mensaje` (códigos incluidos `eje_servicio_sustituido` y
`periodo_acotado_difiere_del_tablero`), sin filtrar por el enum del OpenAPI.

**Rationale:** `informe_soporte` envuelve el cuerpo OpenAPI en `data`. Copiar
`EnvelopeInforme.data: Record[]` de Ventas dejaría las zonas vacías con 200 OK — fallo silencioso.

**Alternatives considered:** normalizar a array en el servicio y tirar `declaraciones` — perdería
FR-UI-025.

## D6 — Slug `cumplimiento-sla-por-plan` → ruta `cumplimiento-sla/por-plan`

**Decision:** el servicio mapea el id publicado a la ruta HTTP del contrato (la misma tabla que
`RUTAS` en las pruebas de OpenAPI del backend). El resto de slugs coinciden con el segmento.

**Rationale:** hay una vista dedicada registrada **antes** del `<str:informe>`. Pedir el id con
guiones funciona hoy en la vista genérica, pero el contrato y las pruebas usan la ruta anidada.
El cliente sigue el contrato.

**Alternatives considered:** un único `${base}/${informe}` — frágil si la vista genérica deja de
aceptar el id con guiones.

## D7 — El par cumplimiento/cobertura es un widget, no dos

**Decision:** `zona-heroe` de Cumplimiento pinta, del **último** `periodo` de `resultados`,
`pct_cumplimiento` y `pct_sin_compromiso` juntos, con `con_compromiso` / `tickets` a la vista y
la meta ≥95 %. `pct_cumplimiento === null` → estado **sin_dato**, nunca 0 %. Los tres motivos
(`sin_compromiso_por_motivo`) van en el mismo bloque, tamaño menor.

**Rationale:** FR-UI-008, SC-F02. Dos cards —un héroe al 11 % y la cobertura al pie— son
exactamente el incentivo que el backend ya impide. Tomar la última fila evita agregar en cliente
una serie que el backend entrega por granularidad (defecto: mes). La evolución temporal del
incumplimiento vive en **Cola**, no aquí.

**Alternatives considered:** sumar la serie en cliente — viola Depends-on. Dos zonas para las dos
cifras — viola FR-UI-008.

## D8 — Sin librería de gráficas

**Decision:** número héroe + barras de distribución / serie de barras Tailwind. No se añade
Chart.js ni D3.

**Rationale:** `package.json` no las tiene. El visual grande del Z es una distribución (por plan,
por día, por tipo), no un mapa (FR-UI-021).

**Alternatives considered:** introducir una librería «porque es un dashboard» — dependencia nueva
sin justificación.

## D9 — `agrupar_por` es de la zona, no un segundo filtro global

**Decision:** el período refresca las tres zonas de Cola. Un control de agrupación
(`estado|prioridad|tipo|agente`) vive **dentro** de `zona-heroe` y solo re-pide `tablero-cola`.
No hay editor de `granularidad`, `eje` ni `minimo`: viajan los defectos del servidor.

**Rationale:** FR-UI-004, FR-UI-005. Un segundo filtro global convertiría Cola en un constructor
de informes y rompería Hick. El tablero es el único informe que el backend parametriza así.

**Alternatives considered:** exponer granularidad en Cumplimiento — la spec reserva el período
como única acción de la capa.

## D10 — Un GET de carga alimenta héroe y visual

**Decision:** `carga-entrante-resuelta` se pide **una vez**. El héroe muestra la **última** fila
(saldo del día = `creados - resueltos`, más `neto_acumulado`). El visual pinta la serie completa.
Los días con `creados = 0` y `resueltos = 0` se dejan en la serie: el backend ya rellena; omitirlos
en cliente recrearía el hueco.

**Rationale:** son el mismo informe. Dos GET idénticos no añaden verdad. Restar `creados - resueltos`
en la última fila es presentación de campos ya entregados, no una métrica nueva.

**Alternatives considered:** dos informes ficticios — no existen. Recalcular el acumulado en
cliente — el backend ya lo envía.

## D11 — Carga por zona, no un único spinner de página

**Decision:** cada zona Z dispara su GET (salvo D10). Un 500 en rendimiento no borra el
cumplimiento.

**Rationale:** edge case de la spec. Igual que Emergencias D8 / Ventas D8.

## D12 — Apoyo plegado solo en Cumplimiento

**Decision:**

- Cumplimiento: tickets por servicio en un bloque «Detalle» plegado. La declaración
  `servicio_no_registrado` se lee **al abrir** el detalle (y un extracto corto puede ir junto al
  visual si el backend la manda en ese GET).
- Cola: sin apoyo; tablero + evolución + escalado bastan. Agrupar es control de zona, no bloque
  extra del mismo peso.
- Tendencias: sin apoyo; reincidencia es la lectura.

**Rationale:** FR-UI-004. Cuatro cards iguales en Cumplimiento romperían el Z. El informe por
servicio está materialmente vacío: no puede competir con el BSC.

## D13 — Sidebar: tres enlaces nuevos, no reetiquetar el dashboard

**Decision:** tres `NAV_LINKS` en el grupo Soporte, roles del guard, textos «Cumplimiento de SLA»,
«Cola en curso», «Tendencias». El enlace «Informes de soporte» (`/soporte-cliente/informes`) y
«Dashboard de soporte» (`/soporte-cliente/dashboard`) **no se tocan**. Cliente sigue viendo
listados y **no** estos tres. `DesarrolladorAPIs` / `DirectorTecnologico` siguen viendo el
dashboard operativo y **no** estas tres.

**Rationale:** design-system: el sidebar muestra solo lo que el rol puede abrir. Un ítem gris de
gestión para el Cliente descubriría la capa. Reetiquetar el dashboard anularía FR-UI-026.

## D14 — Clave, nunca nombre; sin ficha de ticket

**Decision:** rendimiento y tablero-por-agente pintan `id_agente`. Reincidencia pinta `id_cliente`
y `tipo_cliente`. Prohibido resolver nombre contra otra API. Prohibido enlazar una fila a
`/soporte-cliente/tickets/:id`.

**Rationale:** backend FR-024..026. Abrir el detalle operativo desde esta lectura reintroduciría
asunto y mensajes, y convertiría «ver» en «decidir».

## D15 — Vacío, sin_dato y ceros de serie no se confunden

**Decision:**

| Señal | Estado de zona |
|---|---|
| `resultados: []` | **vacio** — no héroe en 0 % |
| fila con `pct_cumplimiento` / `pct_escalado_automatico` / `media_resolucion_s` = `null` | **sin_dato** para esa métrica |
| fila de evolución o carga con `tickets = 0` o `creados = 0` | **dato**: el cero es real |

**Rationale:** FR-UI-006, FR-UI-007, FR-UI-015. Pintar 0 % de cumplimiento sin denominador dispara
una alarma BSC falsa. Omitir un día en cero se lee como un buen día.

## D16 — Automático y humano no se suman en cliente

**Decision:** la lectura de Cola muestra `con_escalado_automatico` y `con_escalado_humano` en
columnas distintas. Prohibido un total «escalados» aunque sea la suma de las dos.

**Rationale:** FR-UI-016, SC-F08. El backend ya no las suma; el cliente no debe «ayudar».
