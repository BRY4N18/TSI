# Informes Tácticos Simples — Cuentas y Clientes

**Departamento:** 1. Cuentas y Clientes
**Objetivos tácticos cubiertos:** OT04 (incorporación), OT17 (ciclo de vida de la cuenta),
OT18 (acceso seguro por rol)
**Creado:** 2026-08-14

Ocho listados llanos de solo lectura que permiten al nivel táctico mirar el dato operativo de
Cuentas y Clientes sin transformarlo. Es el **módulo piloto** de los 66 listados del catálogo: fija
el patrón que replicarán los siete departamentos restantes.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| **backend** | Spec redactada | [`backend/spec.md`](backend/spec.md) |
| frontend | **Aplazado deliberadamente** | — |

**Por qué el frontend está aplazado.** Hoy existe un solo tablero para todo, y varios de estos
listados podrían tener que verse desde más de un sitio. Esa decisión de ubicación no condiciona el
contrato HTTP, así que el backend avanza primero y la pantalla se define después, cuando esté claro
el mapa de tableros.

## Los ocho listados

| # | Listado | OT | Tipo de filtro | Origen |
|---|---|:--:|---|:--:|
| 1 | Solicitudes de alta pendientes de aprobación | OT04 | Estado actual | OP04 |
| 2 | Clientes con incorporación incompleta | OT04 | Estado actual | OP05 |
| 3 | Cuentas cliente por estado | OT17 | Estado actual | OP07 |
| 4 | Transferencias de propiedad | OT17 | Período opcional | CU-O15 |
| 5 | Usuarios y sus roles asignados | OT18 | Estado actual | OP02 |
| 6 | Sesiones actualmente abiertas | OT18 | Estado actual | CU-O05 |
| 7 | Credenciales temporales pendientes de cambio | OT18 | Estado actual | CU-O04 |
| 8 | Accesos técnicos de infraestructura | OT18 | Estado actual | CU-O08 |

Siete de los ocho se trazan a un objetivo operativo o a un caso de uso del marco. Ninguno es
criterio propio.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md) — contrato
  común de los 66 listados. Lo allí definido no se repite en la spec.
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §2 — catálogo y trazabilidad.
- `.specify/docs/architecture/api-standards.md`, `.specify/docs/actors.md`.

## Dos exclusiones que salieron al redactar

El catálogo listaba **diez** listados para este departamento. Al verificarlos contra el código y el
modelo de datos, dos no proceden:

- **Invitaciones de onboarding reenviadas** — no hay dato. `audit_service.log_reenvio_invitacion`
  escribe con el logger de aplicación; ninguna tabla registra el evento.
- **Usuarios por cliente frente al tope de su plan** — es compuesto: exige contar usuarios por
  cliente y cruzar con los límites del plan.

Ambas quedan anotadas en el catálogo general.
