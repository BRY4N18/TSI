# Informes Tácticos Simples — Soporte al Cliente

**Departamento:** 7. Soporte al Cliente
**Objetivos tácticos cubiertos:** OT19 (resolver dentro del SLA comprometido), OT20 (vigilar y
escalar el cumplimiento)
**Creado:** 2026-08-14

Dos listados llanos de solo lectura. Quinto módulo de la serie, y el más pequeño — pero aporta dos
cosas que ningún anterior validó.

## Capas

| Capa | Estado | Ruta |
|---|---|---|
| **backend** | Spec redactada | [`backend/spec.md`](backend/spec.md) |
| frontend | **Aplazado deliberadamente** | — |

## Los dos listados

| # | Listado | OT | Tipo de filtro | Acotado por |
|---|---|:--:|---|---|
| 1 | Tickets (estado, compromiso, prioridad, agente, factura) | OT19 | Estado actual | Cuenta del reportador |
| 2 | Escalados con su autor | OT20 | Período opcional | — (solo roles de atención) |

## Por qué este departamento fue el quinto

**Es el que usa el criterio de pertenencia amplio.** Red Operativa y Suscripciones resuelven la
cuenta de un usuario por ser su administrador local; Soporte lo hace por **estar vinculado** a ella.
Al parametrizar ese criterio en el módulo anterior quedó una hipótesis pendiente de comprobar: que
la parametrización sirviera para ambos. **Este módulo es esa comprobación.**

**Y el acotamiento no se decide por el rol que se tiene, sino por el que no se tiene.** Cliente y
Partner de integración son ambos reportadores, y decidir el acotamiento por «ser Cliente» dejaría al
Partner viendo tickets ajenos y contenido interno. Fue un fallo real que casi se cuela en la
revisión anterior; aquí queda como requisito explícito.

## Seis filas del catálogo → dos listados

- **Cuatro filas son el mismo listado de tickets con distinto filtro** — sin clasificar, sin
  compromiso de tiempo, cola por agente, y ligados a una factura en disputa.
- **Una es el listado de escalados.**
- **Una ya estaba construida** — la configuración de SLA.

## Una exclusión deliberada, no un olvido

**El listado de escalados no expone el texto de los mensajes.**

El registro de acciones guarda, junto a cada entrada, el mensaje escrito y una marca de si es una
**nota interna**. Las notas internas no pueden llegar al cliente — regla ya verificada, aplicada hoy
filtrando la lista después de leerla.

Un listado táctico necesita saber **qué pasó, cuándo y quién lo hizo**, no la prosa. Al no exponer el
mensaje, el problema de filtrar notas internas **no llega a plantearse**, en lugar de resolverse con
un filtro que alguien podría olvidar al añadir un campo más adelante.

## Documentos que lo gobiernan

- [`specs/002-tactico/contrato-informes-simples.md`](../../contrato-informes-simples.md)
- `informestacticos/TSI-Informes-Tacticos-Requeridos-por-OT.md` §8
- `.specify/docs/actors.md`, `.specify/docs/architecture/api-standards.md`
