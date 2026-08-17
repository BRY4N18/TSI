# Módulo: OE5 — Retención, Satisfacción y Ciclo de Vida del Cliente

**Ubicación:** `specs/001-estrategico/OE5-retencion-ciclo-vida/`
**Objetivo estratégico:** OE5 · **Perspectiva BSC:** Cliente
**Feature paraguas:** `001-estrategico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../002-tactico/modelo-analitico/)

Índice global del módulo (no es una spec Speckit).

## ⚠️ Estado: documentación anticipada — **no ejecutar `/plan` todavía**

| Hecho o dimensión que necesita | Lo diseña | Estado |
|---|---|:--:|
| `hecho_ticket` · `hecho_accion_ticket` · `dim_sla_config` · `dim_servicio` | Soporte al Cliente | **0 / 86 tareas** |
| `hecho_suscripcion` · `hecho_factura` · `hecho_solicitud_cambio_plan` · `dim_plan` · `dim_cliente` | Suscripciones y Facturación | **0 / 71** |
| `hecho_onboarding` · `hecho_sesion` | Cuentas y Clientes | **0 / 67** |
| `hecho_llamada_api` | Partners y API | **0 / 68** *(solo E5-12)* |

**Es el objetivo con más dependencias de los seis**: cuatro módulos tácticos, 292 tareas.

## Los quince informes

| # | Informe | Historia | Estado |
|---|---|:--:|:--:|
| **E5-04** | Cumplimiento consolidado de SLA | US1 | ⏸ sin sustrato |
| **E5-05** | Evolución del incumplimiento de SLA | US1 | ⏸ |
| **E5-07** | SLA desglosado por plan contratado | US1 | ⏸ |
| **E5-02** | Retención neta de ingresos (NRR) | US2 | ⏸ |
| **E5-03** | Movimientos de plan con delta de ingreso | US2 | ⏸ |
| **E5-06** | Rendimiento por agente de soporte | US3 | ⏸ |
| **E5-08** | Reincidencia de soporte | US3 | ⏸ |
| **E5-12** | Cuentas en riesgo de churn | US3 | ⏸ ⚠️ cruza 4 departamentos |
| **E5-15** | Antigüedad media de cuenta | US3 | ⏸ |
| **E5-01** | NPS / índice de satisfacción | US4 | ⛔ sin tabla de encuestas |
| **E5-11** | Reportes entregados sin corrección | US4 | ⛔ sin tabla de entregas |
| **E5-09** | → referencia a **E1-06** | — | dueño: OE1 |
| **E5-10** | → referencia a **E1-11** | — | dueño: OE1 |
| **E5-13** | → referencia a **E1-09** | — | dueño: OE1 |
| **E5-14** | → referencia a **E1-10** | — | dueño: OE1 |

**Cuatro de los quince no se implementan aquí**: son los que OE1 declara primero (§7.1 del contrato).
Quedan **nueve propios construibles** y **dos bloqueados**.

## Capas

| Capa | Ruta | Estado |
|---|---|---|
| **Backend** | [`backend/`](./backend/) | spec redactada · **plan bloqueado** |
| Frontend | *(pendiente)* | aplazada |

## Lo que hay que saber antes de tocar este módulo

**El dato es de escala de demostración**: 14 tickets, 4 suscripciones, 6 facturas, 4 clientes. Un
cumplimiento de SLA sobre 14 tickets se mueve **7 puntos por cada ticket**.

**E5-12 es el único informe de toda la capa sin departamento dueño.** Cruza cuatro señales de cuatro
departamentos, y existe precisamente porque ninguna por separado predice nada. Solo lo ve el
`Gerente` (`acceso-estrategico.md` §6).

## Documentos que lo gobiernan

- [`contrato-informes-estrategicos.md`](../contrato-informes-estrategicos.md) §7.1 y §10
- [`acceso-estrategico.md`](../acceso-estrategico.md) §4.5 y §6
- [`OE1-posicionamiento-captacion/`](../OE1-posicionamiento-captacion/OE1-posicionamiento-captacion.md)
  — dueño de los cuatro compartidos
- `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §5
