# Módulo: Informes Compuestos sobre el Modelo — Soporte al Cliente

**Ubicación:** `specs/002-tactico/Soporte-Cliente/informes-compuestos-modelo/`
**Departamento:** Soporte al Cliente
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 9 informes compuestos de OT19 y OT20

**Uno ya existe**: el tablero de cola, con dos defectos documentados —lee 100 000 tickets a memoria y
no admite corte temporal ni desglose por agente—. Los otros ocho son construcción nueva, incluido el
**indicador BSC de cumplimiento de SLA**, que hoy no tiene fuente.

## Capas

| Capa | Ruta | Estado |
|------|------|--------|
| **Backend** | [`backend/`](./backend/) | activa |
| **Frontend** | *(pendiente)* | aplazada |

## Lo que hay que saber antes de tocar este departamento

**✅ El SLA está versionado en el origen, y correctamente.** Es el **primer caso del proyecto** en que
el sistema operativo guarda la vigencia de algo que cambia. El modelo solo tiene que respetarlo: medir
un ticket contra el SLA vigente **cuando ocurrió**, no contra el actual.

**Los tiempos valen `0` mientras el ticket no llega al hito** — son centinelas, no medidas.

⚠️ **`idservicio` es nulo en los 14 tickets**: el informe por servicio queda materialmente vacío.

**Solo 8 de 14 tickets tienen SLA asignado**, lo que abre la pregunta de qué denominador usa el
indicador BSC.

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 6 listados llanos |
| **`informes-compuestos-modelo/`** *(este)* | Los 9 informes agregados |
