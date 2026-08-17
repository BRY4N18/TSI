# Módulo: OE2 — Monetización del Ecosistema de APIs e Integraciones

**Ubicación:** `specs/001-estrategico/OE2-monetizacion-api/`
**Objetivo estratégico:** OE2 · **Perspectiva BSC:** Financiera / Cliente
**Feature paraguas:** `001-estrategico`
**Sustrato:** [`specs/002-tactico/modelo-analitico/`](../../002-tactico/modelo-analitico/)

Índice global del módulo (no es una spec Speckit).

## ⚠️ Estado: documentación anticipada — **no ejecutar `/plan` todavía**

| Hecho o dimensión que necesita | Lo diseña | Estado |
|---|---|:--:|
| `hecho_llamada_api` · `hecho_cambio_acceso` · `dim_partner` · `dim_credencial_api` · `dim_version_contrato` | Partners y API | **0 / 68 tareas** |

**Es el OE con la dependencia más limpia de los tres bloqueados**: un solo departamento, un solo
módulo táctico. Cuando `Partners-API/informes-compuestos-modelo` esté construido, OE2 se desbloquea
entero salvo un informe.

## Los once informes

| # | Informe | Historia | Estado |
|---|---|:--:|:--:|
| **E2-03** | Clientes con integración API activa | US1 | ⏸ sin sustrato |
| **E2-04** | Intensidad de consumo por partner | US1 | ⏸ |
| **E2-05** | Latencia p95 por endpoint | US1 | ⏸ |
| **E2-07** | Taxonomía de errores 4xx / 5xx | US1 | ⏸ |
| **E2-01** | Participación de ingresos por API | US2 | ⏸ ⚠️ sin precio de plan API |
| **E2-02** | MRR por línea: plataforma vs API | US2 | ⏸ ⚠️ ídem |
| **E2-08** | Excedente facturable por partner | US2 | ⏸ ✅ *el precio sí existe* |
| **E2-09** | Adopción de versiones del contrato | US3 | ⏸ |
| **E2-10** | Comparativa entre partners | US3 | ⏸ |
| **E2-11** | Crecimiento del ecosistema | US3 | ⏸ |
| **E2-06** | Disponibilidad de la API pública | US4 | ⛔ fuente externa |

## Capas

| Capa | Ruta | Estado |
|---|---|---|
| **Backend** | [`backend/`](./backend/) | spec redactada · **plan bloqueado** |
| Frontend | *(pendiente)* | aplazada |

## Lo que hay que saber antes de tocar este módulo

**El dato de consumo es de 18 llamadas.** Un p95 de latencia por endpoint sobre 18 registros no es un
percentil: es casi el máximo. Y `Fact_APIIntegracion` declara 40 filas de agregado donde el detalle
tiene 18 — la incoherencia que el táctico ya documentó.

**Y hay una buena noticia que el catálogo no vio:** `Dim_Plan.precio_excedente_llamada` **sí existe**,
así que **E2-08 no está bloqueado** aunque el catálogo lo dé por dependiente del precio de la API.

## Documentos que lo gobiernan

- [`contrato-informes-estrategicos.md`](../contrato-informes-estrategicos.md) §10
- [`acceso-estrategico.md`](../acceso-estrategico.md) §4.2 — `DirectorTecnologico`, con
  `DirectorFinanciero` en los tres de dinero
- `specs/002-tactico/Partners-API/informes-compuestos-modelo/backend/data-model.md`
- `informestacticos/TSI-Informes-Compuestos-Requeridos-por-OE.md` §2
