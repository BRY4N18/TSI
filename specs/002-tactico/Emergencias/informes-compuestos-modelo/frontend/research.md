# Research — Informes compuestos de Emergencias (Frontend)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md)

## D1 — Una cáscara Z, tres definiciones

**Decision:** una sola página parametrizada por un catálogo (`pantallas-gestion.definiciones.ts`).
Añadir un informe a una zona es editar la definición, no clonar el template.

**Rationale:** FR-UI-016 exige el mismo patrón tres veces para que Red Operativa lo copie. Tres
HTML distintos garantizarían que la tercera olvide el vacío o la zona fallida.

**Alternatives considered:** tres páginas independientes (como los workpanels) — descartado: los
workpanels son el anti-patrón que esta spec evita. Un índice + un informe a la vez — descartado por
el usuario: son dashboards Z, no listados.

## D2 — No reutilizar la grilla de tarjetas del workpanel

**Decision:** no usar `InformeCardComponent` como layout. Sí se reutiliza el **selector de período**
(`periodo-selector`), que es un control, no el tablero.

**Rationale:** FR-UI-001 y SC-F09. Meter trece tarjetas en el workpanel, o copiar su grilla, viola el
patrón Z y mezcla roles (el workpanel admite Operador).

**Alternatives considered:** añadir una cuarta fila al workpanel de Registro — rechazado por el
usuario.

## D3 — Rutas bajo `/emergencias/gestion/`, no bajo `/informes/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Calidad del registro | `/emergencias/gestion/calidad` |
| Despacho | `/emergencias/gestion/despacho` |
| Evidencia y cierre | `/emergencias/gestion/cierre` |

**Rationale:** `/emergencias/informes/*` ya es Registro/Despacho/Seguimiento, con guard de Operador.
Los simples cuelgan de `/emergencias/informes-simples` por la misma razón.

## D4 — Guard propio: Director + Administrador, sin Operador

**Decision:** `emergenciasGestionGuard` con `DirectorOperaciones` y `Administrador`. El Operador,
Cliente y Partner reciben access-denied.

**Rationale:** backend `EmergenciasCompuestosPermission`. El guard de workpanels (`Operador` |
`Administrador`) **no sirve**: dejaría entrar al Operador y **dejaría fuera al Director**, que es
quien esta capa existe para servir.

**Alternatives considered:** ampliar el guard de workpanels — mezclaría dos productos.

## D5 — Sin librería de gráficas

**Decision:** número héroe + barras de distribución / por período con Tailwind, igual que
`dashboard-soporte` y los workpanels. No se añade Chart.js ni D3.

**Rationale:** `package.json` no las tiene. El visual grande del Z es una distribución o una serie
corta de agregados, no un mapa (FR-UI-012).

**Alternatives considered:** introducir una librería «porque es un dashboard» — dependencia nueva
sin justificación; se evalúa en otra spec si el negocio pide series ricas.

## D6 — `campos_comprobados` se declara en la definición, no viene en la fila

**Decision:** la lectura de Calidad nombra **severidad** y **condado**, copiados de FR-005 / SQL de
`ot21_completitud_campos_criticos`. Una prueba compara esa lista contra el comentario normativo del
contrato UI.

**Rationale:** la consulta devuelve `casos`, `completos`, `pct_completitud`. No emite la lista. El
backend estratégico de OE3 sí la emite; este no. Inventar un campo en el cliente leyendo otra API
duplicaría. Declararlo en la definición es la misma deuda que los enums de Cuentas (visible, no
silenciosa).

**Alternatives considered:** pedir un cambio de backend en esta spec — fuera de Depends-on. Se anota
como mejora futura, no como bloqueo.

## D7 — `sin_capacidad` se deriva en pantalla

**Decision:** un condado con `casos > 0` y (`unidades_vigentes = 0` o `ratio` nulo) se lee **sin
capacidad**. No se pinta `ratio: 0`.

**Rationale:** el SQL táctico pone `ratio` nulo cuando no hay unidades; no hay columna booleana
(eso lo hace OE3). La pantalla no debe esperar un campo que el contrato no tiene.

## D8 — Carga por zona, no un único spinner de página

**Decision:** cada zona Z dispara su GET. Un 500 en pérdida de señal no borra el primer intento.

**Rationale:** edge case de la spec. Los workpanels ya lo hacen por tarjeta; aquí el aislamiento es
por zona Z (una zona puede agrupar dos informes, p. ej. lectura de cierre).

## D9 — Apoyo de US3 plegado

**Decision:** latencia, enriquecimiento, volumen por unidad y escaladas viven en un bloque
«Detalle» plegado por defecto. La vista principal cuenta: héroe, período, visual grande, lectura,
ratio-equivalente de cierre, y el control de detalle = ≤8.

**Rationale:** FR-UI-004. Ocho cards iguales rompen el Z.

## D10 — Sidebar: tres enlaces nuevos, no reetiquetar los workpanels

**Decision:** tres `NAV_LINKS` en el grupo Emergencias, roles `DirectorOperaciones` y
`Administrador`, textos «Calidad del registro», «Despacho (gestión)», «Evidencia y cierre». Los
tres workpanels del Operador **no se tocan**.

**Rationale:** design-system: el sidebar muestra solo lo que el rol puede abrir. El Director hoy
casi no tiene entradas de Emergencias; esta capa se las da. Reusar «Informes de Registro» metería
al Director en el workpanel del Operador.
