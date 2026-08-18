# Research — OE5, Retención y Ciclo de Vida

**Fecha:** 2026-08-18 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Los compuestos tácticos de Soporte, Suscripciones, Cuentas y Partners **ya están en código**
(2026-08-18). OE1 ya publicó E1-06/09/10/11. Este plan verifica el DDL (`dags/lib/ddl.py`), no
lo espera.

**Resultado neto: nueve informes publicables, dos sin endpoint, cuatro 404 hacia OE1.**

---

## D1 — Cero tablas nuevas; no recrear `dim_cliente`

**Decision:** OE5 no hace ALTER ni CREATE. Lee `hecho_ticket` (`FINAL`), `hecho_accion_ticket`,
`dim_sla_config` (`FINAL`), `dim_servicio` (`FINAL`), `hecho_suscripcion` (`FINAL`),
`hecho_factura`, `hecho_solicitud_cambio_plan`, `dim_plan` (`FINAL`), `dim_cliente` (`FINAL`),
`hecho_sesion`, `hecho_llamada_api`.

**Rationale:** constitución VII. Cuentas ya conformó `dim_cliente`.

**Alternatives considered:** una tabla de encuestas para E5-01 — es el prerrequisito, no se
inventa aquí.

---

## D2 — Denominador de SLA = cerrados con compromiso

**Decision:** E5-04/05/07 cuentan `desenlace_sla` solo donde `tiene_compromiso = 1`. Los
tickets `tiene_compromiso = 0` salen en una cifra aparte (`sin_compromiso`). Un período sin
cerrados-con-compromiso es `data: []`, no 0 %.

**Rationale:** OT19 ya lo midió. Incluirlos como cumplidos infla; como incumplidos, hunde.
`motivo_sin_compromiso` viaja para no premiar dejar tickets sin clasificar.

**Tie-break:** Fiabilidad sobre completitud aparente.

---

## D3 — NRR descompone; no copiar OT07 a ciegas

**Decision:** E5-02 publica **expansión, contracción y churn por separado**, más el neto.
OT07 deja `expansion` y `contraccion` en **0** (stub). El estratégico **no** hereda ese 0:
la expansión/contracción salen de `hecho_solicitud_cambio_plan` con `estado` en
`aprobada`/`aplicada` y `delta_precio` (congelado). El churn sale de bajas de
`hecho_suscripcion` en la ventana. El denominador es el MRR de la cohorte existente al
inicio (`precio_mensualizado`, `FINAL`).

**Rationale:** FR-OE5-013. Un NRR del 100 % puede ser estable o un empate de altas y bajas.

---

## D4 — Movimientos: precio congelado, solo aprobados

**Decision:** E5-03 lee `delta_precio` y `tipo_movimiento` del hecho de solicitud. No une
`dim_plan.precio`. Pendientes no cuentan.

**Rationale:** FR-OE5-014/015. Cambiar la tarifa del catálogo no debe reescribir el histórico.

---

## D5 — E5-01 y E5-11 no tienen ruta

**Decision:** no hay SQL ni path. GET a `nps-satisfaccion` o `reportes-sin-correccion` →
**404**. `Fact_CierreAccidente.calificacion` **no se lee**.

**Rationale:** no hay encuestas ni tabla de entregas. Usar la calificación de un caso de
emergencia sería medir otra cosa con el nombre del KPI de Cliente.

---

## D6 — Las cuatro de OE1 no existen aquí

**Decision:** GET a `tasa-renovacion`, `churn-por-cohorte`, `tiempo-onboarding`,
`abandono-onboarding` bajo `/oe5/` → **404**. El cuerpo apunta a `/oe1/…`. Cero ficheros
`e5_09_*` / `e5_10_*` / `e5_13_*` / `e5_14_*`.

**Rationale:** contrato §7.1. Dos SQL para la misma tasa de renovación es el fallo que
Mantenibilidad prohíbe.

---

## D7 — E5-12 exige ≥2 señales y nombra la que falta

**Decision:** cuatro señales, ninguna suficiente sola:

| Señal | Fuente |
|---|---|
| Caída de consumo API | `hecho_llamada_api` |
| Alza de tickets | `hecho_ticket` |
| Fallos de cobro | `hecho_factura.estado_pago` / `pagada_primer_intento` / `dias_mora` |
| Ausencia de sesiones | `hecho_sesion` (patrón OT17: `sin_actividad_conocida`, no 0 días) |

Una cuenta se marca si **dos o más** están activas. Si una fuente no está cargada, `cobertura:
parcial` y `falta` nombra la señal. No se lee medio de cobro.

**Rationale:** FR-OE5-016/017. Una sola señal es ruido.

---

## D8 — Agente = carga, no desempeño; reincidencia = cliente × servicio

**Decision:** E5-06 identifica `idagente` (clave, jamás nombre) y declara `alcance` de carga
de trabajo. E5-08 agrupa por `idcliente` y `servicio`. Tres tickets de tres servicios no son
reincidencia.

**Rationale:** FR-OE5-018/019. OT19 ya prohibió el nombre.

---

## D9 — Antigüedad solo de activas

**Decision:** E5-15 promedia `dim_cliente` con `fecha_baja IS NULL`. Las cerradas salen en
cifra aparte. El `alcance` declara el criterio de reactivación (continúa vs reinicia).

**Rationale:** FR-OE5-020. Mezclar activas y cerradas mezcla fidelidad con rotación.

---

## D10 — Permiso por informe, no por módulo

**Decision:**

| Informes | Quién (JWT) |
|---|---|
| E5-04, E5-05, E5-06, E5-08 | `GerenteExitoCliente` · `Gerente` |
| E5-07 | esos **más** `DirectorEstrategia` |
| E5-02 | `DirectorFinanciero` · `Gerente` |
| E5-03 | `DirectorEstrategia` · `DirectorFinanciero` · `Gerente` |
| E5-12 | **solo** `Gerente` |
| E5-15 | `DirectorEstrategia` · `Gerente` |

**Rationale:** `acceso-estrategico.md` §4.5 y §6. El JWT usa `GerenteExitoCliente` (no el
alias de la spec). Cuentas no tiene autoridad de negocio.

---

## D11 — Lista blanca: sin prosa, sin cobro, sin NPS de emergencia

**Decision:** prohibido `asunto`, `descripcion`, `mensaje`, `es_nota_interna`,
`idmetodopago`, `calificacion` de cierre de accidente. `hecho_accion_ticket` no trae texto
(DDL). El informe no lo reintroduce.

---

## D12 — Armazón HTTP de OE6–OE1

**Decision:** `Oe5Service` + `Oe5View` + permiso por informe. Metas `[CALIBRAR]`: `cumple`
siempre `null`. Umbral de muestra heredado de OE6 (defecto 20). Con 14 tickets, los nueve
salen `parcial`.
