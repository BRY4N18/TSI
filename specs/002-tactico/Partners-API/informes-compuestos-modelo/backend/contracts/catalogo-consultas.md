# Contrato — Catálogo de consultas de Partners y API

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/partners/`. Rigen las
convenciones del
[catálogo de Emergencias](../../../Emergencias/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md) §1.

---

## 1. La regla de la versión final, por tabla ⚠️

| Tabla | ¿`FINAL`? |
|---|---|
| `dim_partner`, `dim_credencial_api`, `dim_version_contrato`, `dim_cliente` | **Obligatorio** |
| `hecho_factura`, `hecho_accidente` | Ver el catálogo de su módulo — `hecho_accidente` **sí** lo exige |
| `hecho_llamada_api`, `hecho_cambio_acceso` | **Prohibido** — transacción |

---

## 2. Cuatro reglas propias del departamento ⚠️

1. **Ninguna consulta usa métricas de consumo preagregadas.** No existen en el modelo, y no deben
   añadirse: difieren del detalle en un orden de magnitud.
2. **Toda medida declara sobre cuántas llamadas se calculó.** Sin eso, «poco consumo» y «poco
   registrado» se ven igual.
3. **429, 403 y 5xx no se suman entre sí.** Son tres problemas con tres responsables distintos.
4. **Ninguna consulta devuelve secreto, contacto técnico, IP de origen ni ejecutor de un cambio.**

Las cuatro se verifican con pruebas sobre el **texto** de las consultas.

---

## 3. Parámetros propios

| Parámetro | Informe | Por defecto |
|---|---|---|
| `percentil` | #4 latencia | `95` |
| `muestra_minima` | #4 latencia | `20` — por debajo, el percentil se marca como no fiable |
| `mes` | #2 reporte mensual | mes natural en curso |
| `dias_aviso_expiracion` | #8 credenciales | `30` |

⚠️ **`muestra_minima` no filtra: marca.** Con 18 llamadas registradas hoy, filtrar dejaría el informe
vacío; marcar deja ver la cifra **y** que no es fiable todavía.

---

## 4. Los 13 ficheros

### OT09 — Consumo

| Fichero | Devuelve |
|---|---|
| `ot09_metricas_consumo.sql` | `periodo, partner, llamadas, errores, latencia_media_ms, latencia_p95_ms, muestras, cupo, pct_consumido` |
| `ot09_reporte_mensual.sql` | `mes, partner, llamadas, errores, excedente, muestras` |
| `ot09_consumo_por_endpoint.sql` | `endpoint_path, metodo_http, llamadas, pct, muestras` |
| `ot09_latencia_p95.sql` | `endpoint_path, latencia_media_ms, latencia_p95_ms, muestras, percentil_fiable` |
| `ot09_taxonomia_errores.sql` | `periodo, clase_resultado, codigo_http, llamadas, pct` |
| `ot09_comparativa_partners.sql` | `partner, llamadas, pct_error, latencia_p95_ms, desviacion_vs_mediana` |
| `ot09_participacion_ingresos_api.sql` | `mes, partner, ingreso_base, excedente, pct_excedente` |

⚠️ **`ot09_latencia_p95.sql`** debe cumplir tres cosas verificables: devuelve **p95 y media** juntas
—si la p95 supera mucho a la media, hay una cola que la media esconde—; devuelve **`muestras`**; y
marca `percentil_fiable = 0` por debajo de `muestra_minima`, **sin ocultar la fila**.

⚠️ **`ot09_metricas_consumo.sql`** es el equivalente del endpoint ya construido, **y sus cifras
diferirán**: aquel da solo media. La diferencia **es el arreglo**.

⚠️ **`ot09_taxonomia_errores.sql`** agrupa por `clase_resultado` **antes** que por código: un informe
que solo liste códigos deja al lector decidir cuál es culpa de quién.

### OT08 — Incorporación

| Fichero | Devuelve |
|---|---|
| `ot08_motivo_credencial_inactiva.sql` | `partner, motivo_inactividad, credenciales, pct` |
| `ot08_tiempo_incorporacion.sql` | `partner, etapa, dias, en_proceso` |
| `ot08_adopcion_versiones.sql` | `servicio, version, llamadas, pct, version_es_derivada` |
| `ot08_tasa_rechazo_produccion.sql` | `periodo, motivo, solicitudes, rechazadas, pct_rechazo` |

⚠️ **`ot08_motivo_credencial_inactiva.sql`** distingue **revocada, cascada, expirada y suspensión
manual**. En el sistema operativo las cuatro son el mismo `activo = false`.

⚠️ **`ot08_tiempo_incorporacion.sql`**: los partners **aún en proceso** se cuentan en `en_proceso` y
**quedan fuera de la media**. No tardaron cero: siguen tardando.

⚠️ **`ot08_adopcion_versiones.sql`** agrupa por **(servicio, versión)** y devuelve
`version_es_derivada` — el log no registra la versión, se extrae del path, y **el día que el path
cambie de forma la derivación no fallará: devolverá otra cosa**.

⚠️ **`ot08_tasa_rechazo_produccion.sql`** agrupa **por motivo, nunca por la persona que resolvió**.

### OT10 — Entrega

| Fichero | Devuelve |
|---|---|
| `ot10_clientes_integracion_activa.sql` | `periodo, clientes_totales, con_integracion, pct, meta` |
| `ot10_volumen_expedientes.sql` | `cliente, canal, expedientes` |

⚠️ **`ot10_clientes_integracion_activa.sql`**: el denominador son **todos los clientes**, no solo los
que tienen partner. Con el denominador equivocado el indicador daría **siempre 100 %** y parecería
cumplido.

---

## 5. Reglas de resultado

Las comunes, más dos propias:

| Regla | Detalle |
|---|---|
| **Declarar las muestras** | Toda medida estadística viene con el número de llamadas sobre el que se calculó |
| **Declarar lo derivado** | La versión de contrato se marca como derivada del endpoint |

---

## 6. Lo que ninguna consulta puede devolver

| Excluido | Aunque |
|---|---|
| `client_secret_hash` | Está en la credencial, al lado de todo lo demás |
| Contacto técnico del partner | El informe de incorporación lo tiene cerca |
| **IP de origen** | El informe de patrones anómalos parecería quererla |
| Ejecutor de un cambio de acceso | El catálogo pide la tasa de rechazo «y sus motivos» |
| Zona consultada | No existe en el log, y **no se infiere** |
