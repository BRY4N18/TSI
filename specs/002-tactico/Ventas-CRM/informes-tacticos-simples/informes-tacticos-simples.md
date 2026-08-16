# Informes Tácticos Simples — Ventas y CRM

**Departamento:** 2. Ventas y CRM
**Objetivos tácticos cubiertos:** OT01 (captación digital), OT02 (embudo hasta la conversión),
OT03 (nutrición con demo y alertas)
**Creado:** 2026-08-14

Cuatro listados llanos de solo lectura. Segundo módulo de la serie, después del piloto de
[Cuentas y Clientes](../../Cuentas-Clientes/informes-tacticos-simples/informes-tacticos-simples.md),
cuya capa transversal reutiliza sin volver a decidirla.

**Por qué este departamento fue el segundo.** Es el primero donde el acceso no es uniforme: un
Gerente de Ventas solo ve los prospectos que tiene asignados. El piloto nunca ejerció esa regla
porque el Administrador lo ve todo. Aquí la regla de acotamiento del contrato común tiene
consecuencia observable, y conviene validarla con dos departamentos construidos, no con siete.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| **backend** | Spec redactada | [`backend/spec.md`](backend/spec.md) |
| frontend | **Aplazado deliberadamente** | — |

## Los cuatro listados

| # | Listado | OT | Tipo de filtro | Acotado por |
|---|---|:--:|---|---|
| 1 | Prospectos (canal, tipo, etapa, ejecutivo, estado) | OT01, OT02 | Estado actual | Ejecutivo asignado |
| 2 | Reasignaciones de prospecto | OT02 | Período opcional | — (Administrador) |
| 3 | Demos activas con días restantes | OT03 | Estado actual | Ejecutivo asignado |
| 4 | Notificaciones de señal de interés enviadas | OT03 | Período opcional | Ejecutivo destinatario |

## Cuatro listados, no ocho

El catálogo general enumera ocho informes simples aquí. Al verificarlos:

- **Cuatro filas son el mismo listado con distinto filtro** — prospectos por canal, por tipo de
  organización, por etapa y ejecutivo, y perdidos con motivo. Se resuelven con un endpoint y sus
  filtros. **La cobertura no baja**: las cuatro preguntas se responden.
- **Una no es construible** — «notificaciones con envío fallido». La columna de estado de envío
  existe en el esquema pero **ningún código la escribe**; el fallo solo deja un aviso en el log.

> **Esto va a repetirse.** El catálogo cuenta informes como los nombra el usuario táctico, y varios
> son el mismo listado con otro filtro. Es previsible que los 64 listados pendientes se resuelvan en
> bastantes menos endpoints. Conviene tenerlo presente al estimar el resto.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md)
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §3
- `.specify/docs/actors.md`, `.specify/docs/architecture/api-standards.md`
