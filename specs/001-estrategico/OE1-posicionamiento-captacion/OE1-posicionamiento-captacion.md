# Módulo: OE1 — Posicionamiento y Captación Digital Internacional

**Ubicación:** `specs/001-estrategico/OE1-posicionamiento-captacion/`
**Objetivo estratégico:** OE1 · **Perspectiva BSC:** Financiera
**Feature paraguas:** `001-estrategico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../002-tactico/modelo-analitico/)

Índice global del módulo (no es una spec Speckit).

## Estado: backend **implementado** · frontend **implementado**

Sus trece informes consumen hechos que cargan los compuestos tácticos de tres departamentos:

| Hecho o dimensión que necesita | Lo diseña | Estado del módulo |
|---|---|:--:|
| `hecho_suscripcion` · `hecho_factura` · `dim_plan` · `dim_cliente` | Suscripciones y Facturación | ✅ compuestos tácticos (2026-08-18) |
| `hecho_transicion_embudo` · `dim_prospecto` · `dim_canal` | Ventas y CRM | ✅ compuestos tácticos (2026-08-18) |
| `hecho_onboarding` · `dim_etapa_onboarding` | Cuentas y Clientes | ✅ compuestos tácticos (2026-08-18) |

**Actualizado 2026-08-18:** el sustrato táctico **ya está**. El backend tiene plan y
[`tasks.md`](backend/tasks.md) (53). Siguen ⛔ E1-05 (sin costos de marketing) y E1-07/E1-08
(sin geografía comercial en `dim_cliente`). El dato de demostración sigue siendo anecdótico.

## Los trece informes

| # | Informe | Historia | Estado |
|---|---|:--:|:--:|
| **E1-01** | MRR mensual y variación MoM | US1 | 📐 plan · parcial por n |
| **E1-02** | ARR y proyección anual | US1 | 📐 |
| **E1-03** | MRR y ARPU por segmento | US1 | 📐 |
| **E1-12** | Distribución de la cartera por plan | US1 | 📐 |
| **E1-04** | Embudo de conversión digital | US2 | 📐 |
| **E1-13** | Velocidad del ciclo de venta | US2 | 📐 |
| **E1-06** | Tasa de renovación *(dueño de E5-09)* | US3 | 📐 |
| **E1-09** | Tiempo de onboarding *(dueño de E5-13)* | US3 | 📐 Gerente only |
| **E1-10** | Embudo de abandono en onboarding *(dueño de E5-14)* | US3 | 📐 Gerente only |
| **E1-11** | Churn de cliente por cohorte *(dueño de E5-10)* | US3 | 📐 Gerente only |
| **E1-05** | CAC por canal | US4 | ⛔ sin fuente de costos |
| **E1-07** | Mercados activos | US4 | ⛔ sin geografía comercial |
| **E1-08** | Cartera y MRR por mercado | US4 | ⛔ ídem |

**OE1 es dueño de los cuatro informes compartidos con OE5**, que los referencia sin reimplementarlos.

## Capas

| Capa | Ruta | Estado |
|---|---|---|
| **Backend** | [`backend/`](./backend/) | **implementado** (10 GET, 3 → 404) |
| **Frontend** | [`frontend/`](./frontend/) | **implementado** — 4 pantallas Z, sin CAC/mercados |

## Lo que hay que saber antes de tocar este módulo

**La dependencia es doble.** No basta con que los tácticos carguen los hechos: **el dato de origen es
de escala de demostración**. Medido el 2026-08-16: 4 suscripciones, 6 facturas, 4 clientes,
3 onboardings, 10 prospectos, y **0 filas** en las dos fuentes de nutrición comercial.

Un MRR sobre 4 suscripciones y un churn por cohorte sobre 4 clientes **son cifras anecdóticas con
forma de indicador**, y este objetivo es el de la perspectiva Financiera del tablero.

**Tres informes están bloqueados por algo que ningún módulo táctico resuelve**: no hay fuente de
costos de marketing, y `Dim_Cliente` **no tiene país ni estado**.

## Documentos que lo gobiernan

- [`contrato-informes-estrategicos.md`](../contrato-informes-estrategicos.md) §10 — el orden de
  construcción y por qué este módulo espera
- [`acceso-estrategico.md`](../acceso-estrategico.md) §4.1 — autoridad **repartida** entre cuatro
  cargos, y cuatro informes **sin autoridad**
- Los `data-model.md` de los tres tácticos, que definen los hechos que este módulo consumirá
- `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §1
