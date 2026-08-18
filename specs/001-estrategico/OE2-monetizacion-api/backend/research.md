# Research — OE2, Monetización del Ecosistema de APIs

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

El sustrato táctico de Partners **ya está en código** (compuestos OT08–OT10, 2026-08-18). Este
plan verifica el modelo, no lo espera. Donde hay un nombre de columna, sale de `dags/lib/ddl.py`.

**Resultado neto: diez informes publicables, uno sin endpoint.** E2-08 se construye. E2-01 y E2-02
salen **parciales** (volumen sí, precio de plan API no). E2-06 no se publica.

---

## D1 — Una sola fuente de consumo: `hecho_llamada_api`

**Decisión:** ningún informe de OE2 lee un agregado de consumo. Solo `hecho_llamada_api`
(transacción, grano una llamada, partición mensual, **sin IP**).

**Por qué:** el táctico ya documentó que el agregado operativo y el detalle no cuadran (40 vs 18).
Sobre estas cifras se factura. Recalcular desde el agregado reintroduciría la discrepancia.

**Alternativa rechazada:** cruzar `Fact_APIIntegracion` «para el denominador de adopción». El
denominador de E2-03 es `dim_partner` con acceso concedido, no el agregado.

---

## D2 — E2-08 es construible

**Decisión:** el excedente sale de llamadas del mes menos `dim_partner.limite_llamadas_mes`, por
`dim_plan.precio_excedente_llamada` (join `dim_partner.plan_api` → `dim_plan.nombre`).

**Por qué:** la spec lo adelantó y el DDL lo confirma. El táctico ya separa `hecho_factura.tipo =
'excedente_api'` para lo **cobrado**; E2-08 calcula lo **facturable** y declara que no afirma cobro.

**Alternativa rechazada:** usar solo `hecho_factura` de excedente. Eso mediría caja, no cupo.

---

## D3 — E2-01 y E2-02 se publican parciales, no se ocultan

**Decisión:** entregan volumen (llamadas / partners) y, si hay `hecho_factura`, el excedente
cobrado. `cobertura: "parcial"` y `falta: ["precio del plan de API"]` mientras `plan_api` sea
texto sin `precio_lista` de plan API.

**Por qué:** FR-OE2-015. Un 200 sin la etiqueta «parcial» afirmaría un mix de ingresos que el
modelo no puede partir.

---

## D4 — E2-06 no tiene ruta

**Decisión:** no hay SQL ni path. Un GET a `disponibilidad-api` responde **404**.

**Por qué:** el log solo ve llamadas que ocurrieron. Ausencia de filas = nadie llamó o el servicio
estaba caído; no se distinguen. Publicar 100 % sería mentir. Mismo prerrequisito que E3-01
(monitoreo de infraestructura).

**Regla 2 del desempate (sin Safety):** fiabilidad gana a completitud aparente del catálogo.

---

## D5 — Versión del contrato: derivada, agrupada por (servicio, versión)

**Decisión:** E2-09 usa `hecho_llamada_api.servicio` + `version_contrato` y declara
`version_es_derivada`. Nunca agrupa solo por `version` (`'v1'` no es único).

**Por qué:** el táctico OT08 ya lo midió. El log no trae la versión; se deriva del path.

---

## D6 — Permiso partido y exclusión de partners

**Decisión:**

| Informes | Quién entra |
|---|---|
| Los siete de consumo / ecosistema | `DirectorTecnologico` · `Gerente` |
| E2-01, E2-02, E2-08 (dinero) | esos **más** `DirectorFinanciero` |
| Cualquier rol de partner | **403 en los diez** |

**Por qué:** `acceso-estrategico.md` §4.2. El portal del partner ya tiene consumo acotado a sí
mismo. El agregado del ecosistema es ventaja competitiva.

---

## D7 — p95 ausente bajo muestra mínima

**Decisión:** heredar el umbral del táctico (`muestra_minima`, defecto 20). Con 18 llamadas en el
origen, casi todos los endpoints devolverán p95 `null` y `percentil_fiable = 0`.

**Por qué:** un p95 de 2 observaciones es el máximo. FR-OE2-009.

---

## D8 — Cero tablas nuevas

**Decisión:** OE2 no altera el DDL. Lee `hecho_llamada_api`, `hecho_cambio_acceso` (solo si hace
falta para altas), `dim_partner`, `dim_credencial_api`, `dim_version_contrato`, `dim_plan`,
`hecho_factura`.

**Por qué:** constitución VII y contrato §10. El táctico ya creó el modelo.

---

## D9 — E2-11 cuenta primera llamada 2xx, no el alta de credencial

**Decisión:** primera fila de `hecho_llamada_api` con `clase_resultado` de éxito por partner.
Una credencial emitida y nunca usada no es adopción.

**Por qué:** FR-OE2-018 y el mismo criterio de E2-03.

---

## D10 — Armazón HTTP de OE6/OE3/OE4

**Decisión:** un `Oe2Service` + `Oe2View` + permiso por informe en `informes_estrategicos`.
Sin app nueva.

**Por qué:** ya probado. Las metas de consumo son `[CALIBRAR]` salvo lo normativo de latencia
si el contrato de API fija un p95; la spec marca E2-05 `[NORMATIVO]` — **se publica el p95 y
`cumple` solo si hay muestra suficiente**; si no, `cumple: null` y p95 ausente (no un rojo
falso por muestra de 2).
