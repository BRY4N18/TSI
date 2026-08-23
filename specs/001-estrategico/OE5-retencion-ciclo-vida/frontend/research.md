# Research — OE5 frontend

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md)

## D1 — Copiar la cáscara Z de OE1, no extraer `shared/`

**Decision:** módulo `estrategico/oe5/` espejo de `estrategico/oe1/`: una página parametrizada
por definiciones. No se importa `PantallaZPage` de OE1, OE2 ni Partners. No se mueve la cáscara
a `shared/`.

**Rationale:** la spec y AGENTS.md: extraer ahora acopla tres objetivos. Copiar es el patrón ya
usado de táctico → OE2 → OE1.

**Alternatives considered:** importar OE1 — acopla retención y captación. Extraer `shared/informes-z/`
— fuera de alcance.

## D2 — Cuatro guards, nunca una unión

**Decision:**

| Guard | Roles | Pantalla |
|---|---|---|
| `oe5ServicioGuard` | `GerenteExitoCliente` · `Gerente` | servicio |
| `oe5IngresosGuard` | `DirectorFinanciero` · `Gerente` | ingresos |
| `oe5PlanesGuard` | `DirectorEstrategia` · `Gerente` | planes |
| `oe5RiesgoGuard` | `Gerente` | riesgo |

**Rationale:** FR-UI-017. Un `canActivate` único le daría al Financiero las cuentas en riesgo
(el backend responde 403, pero el menú ya habría descubierto la superficie). El HTTP permite
SLA por plan al Éxito de Cliente; el **menú** de Planes no se lo da (spec US3). Si dirección
exige el desglose en Servicio, se añade el bloque allí — no se abre Planes al CSM «por si acaso».

**Alternatives considered:** reusar guards de OE1 — roles distintos. Un guard unión — viola §4.5.

## D3 — Rutas bajo `/estrategico/oe5/`

**Decision:**

| Pantalla | Ruta |
|---|---|
| Servicio | `/estrategico/oe5/servicio` |
| Ingresos retenidos | `/estrategico/oe5/ingresos` |
| Planes | `/estrategico/oe5/planes` |
| Riesgo | `/estrategico/oe5/riesgo` |

Grupo de sidebar **Estratégico**, no «Soporte» ni «Suscripciones».

**Rationale:** mezclarlas con el SLA táctico pondría dos cumplimientos en el mismo grupo.

## D4 — Envelope `{ data, meta }`

**Decision:** el cliente tipa `data` como array y lee `meta.cobertura`, `meta.falta`,
`meta.alcance`, `meta.objetivo`, `meta.comparacion`. Prohibido `data.resultados` o
`acotado_a`.

## D5 — Recuento y parcial van con el SLA

**Decision:** el héroe de Servicio pinta %, recuento de cerrados con compromiso y `cobertura`
**en el mismo bloque**. `cobertura === 'parcial'` → `zona-parcial`. Prohibido un porcentaje solo.

**Rationale:** FR-UI-007. Con n=14, un 95 % huérfano se lee como KPI de empresa.

## D6 — Vacío de compromiso ≠ 0 %

**Decision:** `data: []` en cumplimiento-sla → zona **vacio**, copy «sin compromisos que
cumplir». Prohibido pintar 0 %.

## D7 — NRR es un GET, tres componentes a la vista

**Decision:** un GET a `retencion-neta-ingresos` alimenta héroe (neto) y visual (expansión,
contracción, churn). El texto de precio congelado sale de `meta.alcance`. Prohibido copiar
ceros de OT07.

## D8 — Sin librería de gráficas

**Decision:** número héroe + barras Tailwind. Señales de riesgo = lista, no heatmap.

## D9 — Período + granularidad + comparación

**Decision:** `desde`, `hasta`, `granularidad` (`mes` | `trimestre` | `anio`), `comparacion`
(`ninguna` | `mom` | `yoy`). Sin editor de umbral de muestra. Comparación nula con motivo →
**ausente**, no 400 de UI.

## D10 — E5-01/11 y refs OE1 no existen en UI

**Decision:** ningún slug `nps-satisfaccion`, `reportes-sin-correccion`, `tasa-renovacion`,
`churn-por-cohorte`, `tiempo-onboarding`, `abandono-onboarding` en definiciones, rutas ni GET.
Ningún recuadro de ciclo de OE1.

**Rationale:** FR-UI-016. Un recuadro vacío de NPS se leería como 0.

## D11 — Carga por zona

**Decision:** cada zona dispara su GET. Un 500 en reincidencia no borra el héroe de SLA.

## D12 — Agente = id + cola, no nombre

**Decision:** rendimiento pinta `idagente` (o equivalente del payload) y cola. Prohibido
agrupar por nombre. Copy de alcance: carga, no desempeño.

## D13 — Riesgo: ≥2 señales; faltantes nombrados

**Decision:** el héroe cuenta filas que el backend ya filtró (≥2). `meta.falta` se pinta si
cobertura parcial. Prohibido marcar en cliente una cuenta con una señal.

## D14 — Reincidencia = cliente × servicio

**Decision:** se pintan las filas tal cual. Prohibido colapsar por cliente solo.

## D15 — Vacío vs cero vs sin_dato

| Señal | Estado |
|---|---|
| `data: []` en SLA / flujo | **vacio** |
| etapa o plan con 0 incumplimientos | **dato**: cero real |
| `pct_churn` no aplica aquí | — |
| NRR con componentes | **dato**, aunque un componente sea 0 |
| comparación nula con motivo | **ausente** |

## D16 — Sidebar: cuatro enlaces, roles partidos

**Decision:** grupo `Estratégico`. PartnerIntegracion **ausente**. Administrador **ausente**.
DirectorMarketing **ausente**.

## D17 — Copiar, no compartir con OE1

**Decision:** duplicar `pantalla-z` y `apoyo-plegable` dentro de `oe5/`. Un cambio de copy de
OE1 no debe romper OE5 en caliente.
