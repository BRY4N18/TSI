# Módulo: Informes Compuestos sobre el Modelo — Ventas y CRM

**Ubicación:** `specs/002-tactico/Ventas-CRM/informes-compuestos-modelo/`
**Departamento:** Ventas y CRM
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 13 informes compuestos de OT01 a OT03

El **backend de los 13 informes ya está publicado**. Esta capa pinta tres historias (embudo,
captación, nutrición) sobre esas cifras; no las recalcula.

**Cubre los dos casos de uso tácticos ausentes del proyecto**, CU-T03 y CU-T04, que hasta ahora no
satisfacía ningún informe.

## Capas

| Capa | Ruta | Estado |
|------|------|--------|
| **Backend** | [`backend/`](./backend/) | hecha |
| **Frontend** | [`frontend/`](./frontend/) | hecha |

## Lo que hay que saber antes de tocar este departamento

**`Dim_Prospecto.activo` no dice el desenlace.** Cubre a la vez **convertido y perdido**, que son
resultados opuestos. El desenlace se deriva de `motivo_inactividad` y de `etapa_actual`, que sí los
distinguen.

**Todo OT03 opera hoy sobre tablas vacías**, pero sus repositorios sí publican a Kafka: el vacío es
de entorno, no de diseño.

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 7 listados llanos |
| **`informes-compuestos-modelo/`** *(este)* | Los 13 informes agregados |
