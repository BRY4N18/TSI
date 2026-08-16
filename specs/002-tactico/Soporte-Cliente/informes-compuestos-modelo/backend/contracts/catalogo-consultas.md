# Catálogo de Consultas — Informes Compuestos de Soporte al Cliente

**Fecha:** 2026-08-14 · **Modelo:** [`data-model.md`](../data-model.md)

Nueve consultas, una por informe. Todas de solo lectura sobre `tsi_tactico`.

---

## Reglas que aplican a las nueve

| Regla | Detalle |
|---|---|
| **Versión final** | `FINAL` en las cinco dimensiones y en `hecho_ticket`. ⚠️ **Nunca** en `hecho_accion_ticket` — es de transacción y `FINAL` fallaría |
| **SLA histórico** | Los límites se leen de las columnas copiadas en `hecho_ticket`, **jamás** uniendo con `dim_sla_config` por su vigencia actual |
| **Sin ceros falsos** | Los promedios de tiempo filtran `IS NOT NULL`, y devuelven aparte cuántos se excluyeron |
| **Denominador declarado** | Todo informe de cumplimiento devuelve `con_compromiso`, `sin_compromiso` y `pct_sin_compromiso` |
| **Sin identidad** | Ningún `SELECT` proyecta nombre de agente, asunto, descripción, mensaje ni nota interna |

---

## OT19 — El cumplimiento

### C1 · `ot19_cumplimiento_sla.sql` — **BSC, meta ≥ 95 %**

**Entrada:** `desde`, `hasta`, `granularidad` (`dia|semana|mes`)

```sql
SELECT
    toStartOfInterval(fecha, INTERVAL 1 {granularidad}) AS periodo,

    countIf(tiene_compromiso = 1)                       AS con_compromiso,
    countIf(tiene_compromiso = 0)                       AS sin_compromiso,
    count()                                             AS tickets,

    countIf(desenlace_sla = 'cumplido')                 AS cumplidos,
    countIf(desenlace_sla = 'incumplido')               AS incumplidos,

    -- ⚠️ denominador = solo los que tenían compromiso
    round(100.0 * countIf(desenlace_sla = 'cumplido')
          / nullIf(countIf(tiene_compromiso = 1), 0), 2) AS pct_cumplimiento,

    -- ⚠️ la cobertura, en la MISMA fila (FR-013)
    round(100.0 * countIf(tiene_compromiso = 0)
          / nullIf(count(), 0), 2)                       AS pct_sin_compromiso
FROM hecho_ticket FINAL
WHERE fecha BETWEEN {desde} AND {hasta}
GROUP BY periodo
ORDER BY periodo
```

⚠️ **`nullIf(…, 0)` en los dos denominadores.** Un período sin tickets con compromiso devuelve
**ausente**, no `0 %`: cero cumplimiento y cumplimiento indefinido son cosas distintas, y la segunda
dispararía una alarma BSC falsa.

**Medido hoy:** 8 incumplidos, 1 cumplido, 1 sin compromiso, 4 sin clasificar → **11,1 % de
cumplimiento sobre un 35,7 % sin compromiso.** La cifra es mala y la cobertura peor; ambas se ven.

### C2 · `ot19_cumplimiento_por_plan.sql`

Igual que C1, con `GROUP BY plan, periodo` y unión a `dim_plan FINAL`. Los tickets sin plan se
agrupan bajo `'sin plan'`, nunca se descartan.

### C3 · `ot19_rendimiento_agente.sql`

**Entrada:** `desde`, `hasta`

```sql
SELECT
    idagente,                                    -- ⚠️ CLAVE, jamás nombre
    count()                                      AS asignados,
    countIf(hora_resolucion IS NOT NULL)         AS resueltos,
    countIf(desenlace_sla = 'incumplido')        AS incumplidos,
    countIf(fue_reabierto = 1)                   AS reabiertos,

    round(avg(segundos_resolucion), 0)           AS media_resolucion_s,
    countIf(segundos_resolucion IS NULL)         AS sin_resolver
FROM hecho_ticket FINAL
WHERE fecha BETWEEN {desde} AND {hasta} AND tiene_agente = 1
GROUP BY idagente
ORDER BY incumplidos DESC
```

⚠️ **`avg` ignora los nulos por definición, y `sin_resolver` dice cuántos ignoró.** Sin esa segunda
columna, un agente con 1 ticket resuelto rápido y 20 abiertos parecería el mejor del equipo.

⚠️ **Los tickets sin agente se excluyen aquí y se cuentan en C5.** No pertenecen a nadie.

### C4 · `ot19_tickets_por_servicio.sql`

```sql
SELECT
    coalesce(s.nombre, 'sin servicio')  AS servicio,
    count()                             AS tickets,
    countIf(t.desenlace_sla = 'incumplido') AS incumplidos
FROM hecho_ticket AS t FINAL
LEFT JOIN (SELECT id_servicio, nombre FROM dim_servicio FINAL) AS s
       ON t.idservicio = s.id_servicio
WHERE t.fecha BETWEEN {desde} AND {hasta}
GROUP BY servicio
```

⚠️ **Hoy devuelve una sola fila: `sin servicio | 14`.** Es correcto y es el punto — el informe es la
evidencia de que la asignación de servicio no se registra (research D7). La respuesta lo declara.

---

## OT20 — La cola

### C5 · `ot20_tablero_cola.sql` — **sustituye al tablero actual**

**Entrada:** `desde`, `hasta` *(opcionales)*, `agrupar_por` (`estado|prioridad|tipo|agente`)

```sql
SELECT
    estado, prioridad, tipo,
    count()                                        AS tickets,
    countIf(tiene_agente = 0)                      AS sin_agente,
    countIf(hora_primera_respuesta IS NULL)        AS sin_primera_respuesta,
    countIf(desenlace_sla = 'incumplido')          AS incumplidos
FROM hecho_ticket FINAL
WHERE fecha BETWEEN {desde} AND {hasta}
GROUP BY estado, prioridad, tipo
ORDER BY tickets DESC
```

⚠️ **Sus cifras diferirán del tablero actual en cuanto se pida un período** (research D8): el actual
devuelve toda la cola. La respuesta declara el período aplicado para que la diferencia se explique
sola.

### C6 · `ot20_evolucion_incumplimiento.sql`

Serie temporal de `incumplidos` y `pct_incumplimiento` por período, con **la misma pareja
denominador/cobertura de C1**. Los períodos sin tickets se rellenan con `WITH FILL` a **cero
tickets**, no se omiten: un hueco en la serie se leería como un buen período.

### C7 · `ot20_tasa_escalado_automatico.sql`

```sql
SELECT
    t.tipo_incidencia, t.prioridad,
    uniqExact(t.id_reclamo)                                AS tickets,
    uniqExactIf(a.id_reclamo, a.es_escalado_automatico = 1) AS con_escalado_automatico,
    uniqExactIf(a.id_reclamo, a.es_escalado = 1
                              AND a.es_escalado_automatico = 0) AS con_escalado_humano
FROM hecho_ticket AS t FINAL
LEFT JOIN hecho_accion_ticket AS a           -- ⚠️ SIN FINAL: es de transacción
       ON a.id_reclamo = t.id_reclamo
WHERE t.fecha BETWEEN {desde} AND {hasta}
GROUP BY t.tipo_incidencia, t.prioridad
```

⚠️ **Las dos columnas de escalado nunca se suman.** Un escalado automático por SLA es el sistema
avisando de que un compromiso se está rompiendo; uno humano es una decisión. Sumarlos borra
precisamente el dato que hace útil el informe.

⚠️ **`uniqExact` sobre el ticket, no `count()` sobre acciones.** Un ticket escalado tres veces es un
ticket escalado.

**Medido hoy:** 13 de 34 acciones son escalado automático; 7 tickets en estado `Escalado`.

---

## OT20 — Las tendencias

### C8 · `ot20_carga_entrante_vs_resuelta.sql`

Dos series por día: tickets creados (`fecha`) y tickets resueltos (`toDate(hora_resolucion)`), unidas
por día con `WITH FILL`. La diferencia acumulada es el crecimiento neto de la cola.

⚠️ **Los días sin actividad aparecen con cero.** Sin `WITH FILL` la línea uniría dos días distantes y
la pendiente mentiría.

### C9 · `ot20_reincidencia_clientes.sql`

**Entrada:** `desde`, `hasta`, `eje` (`tipo_incidencia|tipo`), `minimo` *(por defecto 2)*

```sql
SELECT
    t.idcliente,                                 -- ⚠️ CLAVE, jamás nombre
    c.tipo_cliente,
    count()                        AS tickets,
    uniqExact(t.tipo_incidencia)   AS tipos_distintos,
    countIf(t.fue_reabierto = 1)   AS reaperturas
FROM hecho_ticket AS t FINAL
LEFT JOIN (SELECT id_cliente, tipo_cliente FROM dim_cliente FINAL) AS c
       ON t.idcliente = c.id_cliente
WHERE t.fecha BETWEEN {desde} AND {hasta}
GROUP BY t.idcliente, c.tipo_cliente
HAVING tickets >= {minimo}
ORDER BY tickets DESC
```

⚠️ **El eje es `tipo_incidencia`, no servicio.** El agrupamiento por servicio sería el natural y
**hoy no existe**: `idservicio` es nulo en los 14 tickets. La respuesta lo declara en vez de dejar
que el analista crea que nadie repite en un mismo servicio.

---

## Tabla de trazabilidad

| Consulta | Informe | OT | FR principales |
|---|---|---|---|
| C1 | Cumplimiento de SLA **(BSC)** | OT19 | FR-006 … FR-014, FR-027 |
| C2 | Cumplimiento por plan | OT19 | FR-015, FR-016 |
| C3 | Rendimiento por agente | OT19 | FR-010, FR-020, FR-025 |
| C4 | Tickets por servicio | OT19 | FR-001, FR-028 |
| C5 | Tablero de cola | OT20 | FR-017, FR-018, FR-020 |
| C6 | Evolución del incumplimiento | OT20 | FR-005, FR-022 |
| C7 | Escalado automático | OT20 | FR-019 |
| C8 | Carga entrante vs. resuelta | OT20 | FR-021, FR-022 |
| C9 | Reincidencia de clientes | OT20 | FR-023, FR-026 |

**Transversales a las nueve:** FR-002 … FR-004 (modelo y versión final), FR-024 (sin texto de
ticket), FR-029 … FR-033 (solo lectura y acceso).
