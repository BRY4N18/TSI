# Informes Tácticos Simples — Partners y API

**Departamento:** 5. Partners y API
**Objetivos tácticos cubiertos:** OT08 (incorporar partners con contrato estable), OT09 (controlar y
tarificar el consumo), OT10 (entregar datos conforme al alcance contratado)
**Creado:** 2026-08-14

Cinco listados llanos de solo lectura. Sexto módulo de la serie y **el último que acota por
organización**.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| backend | Spec redactada · implementada | [`backend/spec.md`](backend/spec.md) |
| **frontend** | Spec redactada · implementada | [`frontend/spec.md`](frontend/spec.md) |

## Los cinco listados

| # | Listado | OT | Tipo de filtro | Acotado por |
|---|---|:--:|---|---|
| 1 | Partners con su estado, plan y cupos | OT08 | Estado actual | Organización del partner |
| 2 | Credenciales por entorno, vigencia y caducidad | OT08 | Estado actual | Organización del partner |
| 3 | Cambios de acceso con su motivo y ejecutor | OT08, OT09 | Período opcional | Organización del partner |
| 4 | Versiones del contrato de integración | OT08 | Estado actual | — (gestores) |
| 5 | Alcance de datos contratado por cliente | OT10 | Estado actual | — (gestores) |

## Por qué antes que Emergencias

Emergencias introduce un **cuarto eje de acotamiento**: un cliente no ve «sus» expedientes por
titularidad, sino **los casos cerrados de las zonas geográficas que tiene contratadas**. Cerrar aquí
los cinco departamentos que comparten el eje «organización» deja la pieza transversal asentada antes
de volver a tocarla.

## La corrección de fondo: inactiva no dice por qué

Una credencial puede estar inactiva por **tres razones opuestas** —revocada por el partner por
seguridad, desactivada en cascada por impago, o expirada— y **el registro de la credencial no las
distingue**. El propio código lo dice al explicar la reactivación selectiva: *«no podría: las tres
razones son indistinguibles»*.

Por eso:

- El listado de **credenciales** dice **si** está activa, no **por qué** no lo está.
- El listado de **cambios de acceso** sí registra los motivos, cada uno con su tipo propio.
- Unir ambas cosas es **compuesto**.

> Un listado de credenciales inactivas que no distinguiera el motivo pondría en la misma línea una
> decisión de seguridad del partner y un impago administrativo. Reactivar sin mirar la bitácora
> resucitaría una credencial comprometida.

## Nueve filas del catálogo → cinco listados

- **Dos filas son el mismo listado de credenciales** — por entorno/estado y próximas a vencer.
- **Dos filas son el mismo listado de alcance de datos** — zonas habilitadas y entregas programadas.
- **Una ya está cubierta** — «llamadas rechazadas por límite» la resuelve la consola de registros
  existente, que filtra por código de respuesta, acota por partner y pagina. Duplicarla no aportaría
  nada.
- **Y el motivo de una credencial inactiva salió del listado**, por lo explicado arriba.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md)
- [`specs/002-tactico/contrato-informes-simples-frontend.md`](../../contrato-informes-simples-frontend.md)
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §6
- `.specify/docs/actors.md`, `.specify/docs/architecture/api-standards.md`
