# Informes Tácticos Simples — Suscripciones y Facturación

**Departamento:** 3. Suscripciones y Facturación
**Objetivos tácticos cubiertos:** OT05 (catálogo diferenciado), OT06 (ciclo de suscripción,
facturación y cobro), OT07 (cambios de plan y estado comercial)
**Creado:** 2026-08-14

Cuatro listados llanos de solo lectura. Tercer módulo de la serie, tras
[Cuentas y Clientes](../../Cuentas-Clientes/informes-tacticos-simples/informes-tacticos-simples.md)
(capa transversal) y [Ventas y CRM](../../Ventas-CRM/informes-tacticos-simples/informes-tacticos-simples.md)
(acotamiento por titularidad), cuyas piezas reutiliza sin volver a decidirlas.

**Por qué este departamento fue el tercero.** Aporta tres cosas que ningún módulo anterior validó:

1. **Acotamiento por organización, no por persona.** En Ventas el titular era el propio solicitante;
   aquí un usuario pregunta y el resultado se acota a la cuenta a la que pertenece.
2. **Primer departamento mayoritariamente de hechos del período.**
3. **El dato más delicado del sistema.** El método de pago guarda el identificador con el que se
   cobra: no es una credencial que haya que romper, es la capacidad de cobrar.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| **backend** | Spec redactada · **implementada** | [`backend/spec.md`](backend/spec.md) · `backend/apps/suscripciones/views/informes_*.py` |
| **frontend** | **Implementada** (sin carpeta `frontend/` de Speckit; el índice mentía el aplazamiento) | `/suscripciones/informes` · `frontend/src/app/modules/suscripciones/informes/` |

## Los cuatro listados

| # | Listado | OT | Tipo de filtro | Acotado por |
|---|---|:--:|---|---|
| 1 | Suscripciones (estado, plan, vencimiento, cambio programado, cancelación) | OT05, OT07 | Estado actual | Cuenta cliente |
| 2 | Facturas con su estado de pago y mora | OT06 | Período opcional | Cuenta cliente |
| 3 | Solicitudes de cambio de plan | OT07 | Estado actual | Cuenta cliente |
| 4 | Métodos de pago vigentes y próximos a caducar | OT06 | Estado actual | Cuenta cliente |

## Cuatro listados a partir de diez filas del catálogo

- **Cinco filas son el mismo listado de suscripciones con distinto filtro** — clientes por plan,
  vencimientos próximos, suspendidas por impago, reducciones pendientes de aplicar y cancelaciones
  con motivo.
- **Dos filas son el mismo listado de facturas** — del período con estado, y vencidas con mora.
- **Una fila se reclasificó a compuesta** — «clientes sin método de pago activo» exige una
  diferencia de conjuntos entre dos tablas.
- **Una ya estaba construida** — el catálogo de planes.

**Se añade un listado no previsto**: métodos de pago vigentes con los próximos a caducar. Es la
mitad simple de la fila que resultó compuesta y responde la misma preocupación de forma preventiva:
una tarjeta que caduca la semana que viene es un cobro que va a fallar. Marcado como **criterio
propio**.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md)
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §4
- `.specify/docs/actors.md`, `.specify/docs/architecture/api-standards.md`
