# Quickstart — Informes Compuestos de Soporte al Cliente

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md) · **Modelo:** [`data-model.md`](data-model.md)

Guía de validación. **No contiene implementación**: eso vive en `tasks.md`.

---

## 1. Requisitos previos

| | |
|---|---|
| Stack táctico levantado | `docker compose -f docker/docker-compose.tactico.yml up -d` |
| Modelo analítico cargado | Las dimensiones conformadas ya deben existir en `tsi_tactico` |
| `dim_cliente` y `dim_plan` | Las carga **Suscripciones**; sin ellas C2 y C9 salen sin desglose |
| Suites verdes de partida | backend **1 673**, `dags/` **151** |

---

## 2. Cargar el dominio de soporte

```bash
docker compose -f docker/docker-compose.tactico.yml exec airflow-scheduler airflow dags trigger dag_hecho_soporte
```

Un solo flujo carga las tres dimensiones y los dos hechos: comparten fuente y cadencia.

---

## 3. Las cinco comprobaciones que importan

### 3.1 El SLA llegó versionado, no aplanado

```sql
SELECT idslaconfig, valido_desde, valido_hasta, segundos_resolucion_max, es_vigente
FROM dim_sla_config FINAL
WHERE idplan = 1 AND prioridad = 'alta'
ORDER BY valido_desde
```

**Esperado: dos filas** — una cerrada con `86400` y otra abierta con `7200`.

⚠️ **Si sale una sola fila, la carga aplanó la historia** y todo el cumplimiento anterior al cambio
quedará medido contra un SLA de 2 horas que entonces no existía.

### 3.2 El cumplimiento usa el SLA de su época

```sql
SELECT id_reclamo, fechahora_creacion, segundos_resolucion_max, segundos_resolucion, desenlace_sla
FROM hecho_ticket FINAL
WHERE tiene_compromiso = 1
ORDER BY fechahora_creacion
```

**Esperado:** los tickets anteriores al cambio llevan `86400`; los posteriores, `7200`.

⚠️ **Si todos llevan el mismo límite, se está midiendo contra la configuración actual** y un ticket
resuelto en 5 horas antes del cambio aparecerá como incumplido sin que nada haya empeorado.

### 3.3 Los ceros no se colaron como tiempos reales

```sql
SELECT
    countIf(segundos_primera_respuesta = 0) AS ceros_respuesta,
    countIf(segundos_resolucion = 0)        AS ceros_resolucion,
    countIf(segundos_resolucion IS NULL)    AS sin_resolver
FROM hecho_ticket FINAL
```

**Esperado: `ceros_* = 0`** y `sin_resolver` > 0.

⚠️ Un cero significaría «respondido al instante». El origen los guarda así en los tickets abiertos, y
un promedio que los incluyera **mejoraría cuantos más tickets sin atender hubiera**.

### 3.4 El BSC declara su cobertura

```bash
curl "http://localhost:8000/api/v1/informes-tacticos/soporte/cumplimiento-sla?desde=2026-01-01&hasta=2026-12-31&granularidad=mes"
```

**Esperado:** cada fila trae `pct_cumplimiento` **y** `pct_sin_compromiso`, más el desglose por los
tres motivos.

⚠️ **Si `pct_sin_compromiso` faltara, el indicador sería manipulable sin mentir**: bastaría dejar de
clasificar tickets para verlo subir.

**Con los datos de hoy:** 1 cumplido de 9 con compromiso → **11,1 %**, sobre un **35,7 % sin
compromiso**. Ambas cifras son malas y ambas se ven.

### 3.5 El informe de servicio sale vacío, y lo dice

```bash
curl "http://localhost:8000/api/v1/informes-tacticos/soporte/tickets-por-servicio?desde=2026-01-01&hasta=2026-12-31"
```

**Esperado:** una sola fila `sin servicio | 14`, y una declaración `servicio_no_registrado`.

⚠️ **Esto es éxito, no fallo.** El informe es correcto sobre un dato que la operación no rellena;
entregarlo vacío es lo que hace visible el hueco.

---

## 4. Lo que NO debe aparecer nunca

```sql
SELECT name FROM system.columns
WHERE database = 'tsi_tactico' AND table IN ('hecho_ticket','hecho_accion_ticket')
  AND name IN ('asunto','descripcion','mensaje','es_nota_interna','nombre_agente')
```

**Esperado: cero filas.**

⚠️ **`es_nota_interna` es el caso grave.** Las notas internas son comentarios del equipo sobre el
cliente, escritos esperando que el cliente no los lea. En un almacén analítico quedan consultables
por cualquier informe futuro y presentes en cada copia de seguridad.

Y en las respuestas HTTP: **ningún endpoint devuelve nombres de agente ni de cliente**, solo claves.

---

## 5. `FINAL` donde toca, y solo ahí

| Tabla | `FINAL` | Si se equivoca |
|---|---|---|
| Las cinco dimensiones | **Sí** | Filas duplicadas tras una recarga |
| `hecho_ticket` | **Sí** | La cola sale inflada de forma **intermitente** — aparece y desaparece según las fusiones |
| `hecho_accion_ticket` | **No** | `ILLEGAL_FINAL`: es `MergeTree`, no `ReplacingMergeTree` |

---

## 6. Que la carga sea repetible

Ejecuta el DAG **dos veces** sobre el mismo día y vuelve a contar:

```sql
SELECT count() FROM hecho_ticket FINAL;
SELECT count() FROM hecho_accion_ticket;
```

**Esperado: las mismas cifras.** La carga borra la partición y la reescribe; una segunda ejecución no
debe añadir nada.

⚠️ **`hecho_accion_ticket` se cuenta sin `FINAL`.** Si duplicara, `FINAL` lo escondería en las
consultas pero no en el almacén — y ahí es donde importa.

---

## 7. Suites

```bash
docker compose -f docker/docker-compose.tactico.yml exec airflow-scheduler python -m pytest dags/tests -q
```

**Esperado:** las 151 previas siguen verdes, más las nuevas de este módulo.
