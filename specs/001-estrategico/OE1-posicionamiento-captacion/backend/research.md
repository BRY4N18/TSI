# Research — OE1, Posicionamiento y Captación Digital

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Los compuestos tácticos de Suscripciones, Ventas y Cuentas **ya están en código** (2026-08-18).
Este plan verifica el DDL, no lo espera. Los nombres de columna salen de `dags/lib/ddl.py`.

**Resultado neto: diez informes publicables, tres sin endpoint.** E1-05, E1-07 y E1-08 no se
publican. Los diez salen con `cobertura: parcial` mientras la muestra de demostración no
alcance el umbral heredado de OE6.

---

## D1 — Cero tablas nuevas; no recrear `dim_cliente`

**Decision:** OE1 no hace ALTER ni CREATE. Lee `hecho_suscripcion`, `hecho_factura`,
`dim_plan`, `dim_cliente` (conformada), `hecho_transicion_embudo`,
`hecho_asignacion_prospecto`, `dim_prospecto`, `hecho_onboarding`, `dim_etapa_onboarding`.

**Rationale:** constitución VII y contrato §10. Cuentas ya creó `dim_cliente`; recrearla
rompería la dimensión conformada.

**Alternatives considered:** una `dim_mercado` para desbloquear E1-07 — inventaría geografía
que el origen no tiene.

---

## D2 — MRR usa `precio_mensualizado`, no divide en el servicio

**Decision:** E1-01/02/03 suman `hecho_suscripcion.precio_mensualizado` de filas vigentes al
cierre del período (`estado_derivado` / vigencia). Una anual ya viene mensualizada en el
hecho táctico.

**Rationale:** OT06 ya lo midió. Volver a dividir el precio anual por 12 **duplicaría** la
corrección.

**Criterion declared in `alcance`:** vigente **al cierre** del mes. Cancelada a mitad de mes
no entra en el MRR de ese mes.

---

## D3 — ARR es extrapolación, no compromiso

**Decision:** E1-02 = MRR × 12 con escenarios. `alcance` dice que no es ingreso firmado.
Optimista y conservador se etiquetan; no se inventa un modelo de churn.

**Rationale:** FR-OE1-010. Un ARR sin esa etiqueta se lee como contrato.

---

## D4 — E1-05, E1-07, E1-08 no tienen ruta

**Decision:** no hay SQL ni path. GET a `cac-por-canal`, `mercados-activos` o
`cartera-mrr-por-mercado` → **404**.

**Rationale:** no hay costos de marketing; `dim_cliente` no tiene país ni estado (14 columnas
verificadas). Publicar CAC = 0 o «1 mercado» mentiría el BSC internacional.

**Tie-break:** Fiabilidad sobre completitud aparente (regla 2; no hay Safety).

---

## D5 — Todo informe declara `cobertura: parcial` bajo muestra mínima

**Decision:** umbral heredado de OE6 (defecto 20 unidades del denominador). Con 4 suscripciones,
6 facturas, 4 clientes, 3 onboardings y 10 prospectos, **los diez** salen parciales.

**Rationale:** FR-OE1-005. Un 25 % de churn sobre 4 clientes es una anécdota.

---

## D6 — Embudo por transiciones; etapas en cero visibles

**Decision:** E1-04 agrupa `hecho_transicion_embudo`, no prospectos únicos. Las etapas del
catálogo con cero pasos **aparecen**. El volumen no crece entre etapas consecutivas (si el
dato lo viola, se declara; no se «arregla» en cliente).

**Rationale:** OT02: un retroceso desaparecería si se contaran prospectos.

---

## D7 — Onboarding contra catálogo, no contra lo observado

**Decision:** E1-10 parte de `dim_etapa_onboarding` (explícita) y mide ausencia en
`hecho_onboarding` (solo completadas). Un 100 % de finalización **sin** el catálogo sería el
defecto que el táctico ya documentó.

---

## D8 — Renovación: denominador = vencidas en el período

**Decision:** E1-06 no usa el stock de activas. Denominador = suscripciones cuya
`fecha_fin_prevista` cae en la ventana.

**Rationale:** FR-OE1-019. Activas como denominador mejora sola cuando nadie vence.

---

## D9 — Permiso por informe, no por módulo

**Decision:**

| Informes | Quién |
|---|---|
| E1-01, E1-02, E1-06 | `DirectorFinanciero` · `Gerente` |
| E1-03 | esos **más** `DirectorEstrategia` |
| E1-12 | `DirectorEstrategia` · `Gerente` |
| E1-04, E1-13 | `DirectorMarketing` · `Gerente` |
| E1-09, E1-10, E1-11 | **solo** `Gerente` |

**Rationale:** `acceso-estrategico.md` §4.1 y §5. Cuentas no tiene autoridad de negocio. No se
concede al Administrador.

---

## D10 — Lista blanca: sin cobro, sin persona, sin país

**Decision:** prohibido `tiene_metodo_pago`, `metodo_pago_caduca`, identidad de prospecto,
contacto, `idpais`. Segmento = `dim_cliente.tipo`. Ejecutivo = `idejecutivo` de asignación,
nunca ficha personal.

---

## D11 — Dueño de los cuatro compartidos con OE5

**Decision:** E1-06, E1-09, E1-10, E1-11 se implementan **solo aquí**. OE5 los referenciará.
No hay segunda SQL.

---

## D12 — Armazón HTTP de OE6/OE3/OE4/OE2

**Decision:** `Oe1Service` + `Oe1View` + permiso por informe en `informes_estrategicos`. Sin
app nueva. Metas `[CALIBRAR]`: `cumple` siempre `null` (SC-008).
