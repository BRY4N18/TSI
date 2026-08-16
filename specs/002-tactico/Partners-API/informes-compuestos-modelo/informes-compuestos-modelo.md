# Módulo: Informes Compuestos sobre el Modelo — Partners y API

**Ubicación:** `specs/002-tactico/Partners-API/informes-compuestos-modelo/`
**Departamento:** Partners y API
**Feature paraguas:** `002-tactico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../modelo-analitico/)

Índice global del módulo (no es una spec Speckit). La feature activa de Speckit es **una capa**,
apuntada por `.specify/feature.json`.

## Los 14 informes compuestos de OT08 a OT10

**Es el único departamento con supervisión real construida**: OT09 tiene consola de logs, reporte
mensual y métricas de consumo. OT08 y OT10, nada.

**Y es del que dependía Suscripciones**: aquí se modela el hecho de llamadas API que aquel módulo se
abstuvo deliberadamente de construir, para no decidir por este departamento.

## Capas

| Capa | Ruta | Estado |
|------|------|--------|
| **Backend** | [`backend/`](./backend/) | activa |
| **Frontend** | *(pendiente)* | aplazada |

## Lo que hay que saber antes de tocar este departamento

**El motivo de una credencial inactiva no vive en la credencial.** Revocación, cascada y expiración
son **indistinguibles** en `Dim_CredencialAPI`: solo hay un indicador de actividad. El motivo está en
la bitácora de acceso.

**Dos centinelas de fecha.** `fecha_expiracion` del año **9999** significa «nunca expira»;
`fecha_retiro = 0` significa «no retirada». Ninguna de las dos es una fecha.

**La versión del contrato no está en el log**, pero es derivable del endpoint. Y `version` **no es
única**: dos servicios distintos comparten `'v1'`.

⚠️ **Dos fuentes de consumo que no cuadran**: `Fact_APIIntegracion` declara 500 llamadas donde
`Fact_LogLlamadaAPI` tiene 18.

## Relación con los demás módulos del departamento

| Módulo | Qué es |
|---|---|
| [`../informes-tacticos-simples/`](../informes-tacticos-simples/) | Los 9 listados llanos |
| **`informes-compuestos-modelo/`** *(este)* | Los 14 informes agregados |
