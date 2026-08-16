# Contrato — Catálogo de consultas de Emergencias

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/emergencias/`. Este documento
fija sus nombres, sus parámetros y lo que cada uno debe devolver.

---

## 1. Convenciones

| Convención | Regla |
|---|---|
| **Nombre del fichero** | `ot<NN>_<nombre_en_snake_case>.sql` |
| **Parámetros** | Con la sintaxis de parámetros con tipo del almacén: `{desde:Date}`, `{hasta:Date}` |
| **Rango obligatorio** | Toda consulta acepta `desde` y `hasta` y filtra por ellos |
| **Orden** | Toda consulta lleva `ORDER BY` explícito: sin él, el orden de las filas es arbitrario y la comparación entre corridas deja de ser posible |
| **Sin `SELECT *`** | Las columnas se enumeran. Un `*` haría que una columna nueva del hecho apareciera sola en un informe |
| **Encabezado obligatorio** | Un comentario con el número del informe, su OT, su origen del catálogo y qué mide |

### La regla de la versión final, por tabla ⚠️

| Tabla | ¿`FINAL`? |
|---|---|
| `hecho_accidente`, `hecho_despacho` | **Obligatorio** |
| `dim_*` (las cinco) | **Obligatorio** |
| `hecho_estado_unidad`, `hecho_ping_unidad`, `hecho_evidencia` | **Prohibido** — falla con `ILLEGAL_FINAL` |

Se verifica con una prueba sobre el **texto** de las consultas, no sobre su ejecución: una consulta
sin `FINAL` sobre un hecho acumulado **funciona** y devuelve cifras infladas solo a veces.

---

## 2. Parámetros comunes

| Parámetro | Tipo | Por defecto | Notas |
|---|---|---|---|
| `desde` | `Date` | hoy − 30 días | Inclusive |
| `hasta` | `Date` | hoy | Inclusive |
| `granularidad` | `String` | `dia` | `dia` o `mes`, solo en informes con serie temporal |

Parámetros propios de un informe concreto:

| Parámetro | Informe | Por defecto |
|---|---|---|
| `umbral_seg` | #14 pérdida de señal | `60` |
| `ventana_dias` | #16 desviación de llegada | `90` |
| `muestra_minima` | #16 desviación de llegada | `5` |
| `tramos_dias` | #25 envejecimiento | `1, 3, 7, 30` |
| `top` | #5 ranking de ubicaciones | `10` |

---

## 3. Los 26 ficheros

### OT21 — Registro con calidad

| Fichero | Devuelve |
|---|---|
| `ot21_distribucion_severidad.sql` | `periodo, severidad, casos, pct` |
| `ot21_distribucion_zona.sql` | `periodo, condado, casos, pct` |
| `ot21_completitud_campos_criticos.sql` | `periodo, casos, completos, pct_completitud` |
| `ot21_descarte_fusion.sql` | `periodo, casos, descartados, fusionados, pct_descarte, pct_fusion` |
| `ot21_ranking_ubicaciones.sql` | `condado, ciudad, calle, casos` — limitado por `top` |
| `ot21_impacto_humano.sql` | `periodo, condado, heridos, victimas, fallecidos, casos` |

### OT22 — Asignación y despacho

| Fichero | Devuelve |
|---|---|
| `ot22_asignacion_automatica_vs_manual.sql` | `periodo, origen_despacho, intentos, pct` |
| `ot22_tiempo_reportado_a_confirmado.sql` | `periodo, casos_medidos, segundos_mediana, segundos_p90` |
| `ot22_tiempo_respuesta_por_severidad.sql` | `periodo, severidad, intentos_medidos, segundos_mediana` |
| `ot22_rechazo_timeout_por_unidad.sql` | `unidad, intentos, rechazados, vencidos, pct_rechazo, pct_vencido` |
| `ot22_carga_por_unidad.sql` | `periodo, unidad, intentos, confirmados, segundos_atencion_total` |
| `ot22_ratio_demanda_capacidad.sql` | `periodo, condado, casos, unidades_vigentes, ratio` |
| `ot22_primer_intento.sql` | `periodo, casos, resueltos_primer_intento, pct` |

⚠️ **`ot22_ratio_demanda_capacidad.sql`**: `unidades_vigentes` cuenta versiones de unidad cuya
vigencia **cubre el período consultado** y cuyo condado es el del grupo. No cuenta la flota de hoy —
ese es el defecto que corrige.

### OT23 — Misión en tránsito

| Fichero | Devuelve |
|---|---|
| `ot23_perdida_senal.sql` | `periodo, idunidademergencia, idaccidente, inicio_hueco, fin_hueco, duracion_seg, umbral_usado_seg` |
| `ot23_abortos_perdidas.sql` | `periodo, proveedor, intentos, abortados, retirados_forzado, pct_aborto` |
| `ot23_desviacion_llegada.sql` | `periodo, unidad, llegadas_medidas, segundos_referencia, segundos_reales_mediana, desviacion_mediana` |

⚠️ **`ot23_desviacion_llegada.sql`** implementa la referencia derivada. Debe cumplir cuatro cosas, y
las cuatro son verificables:

1. La referencia sale de la **mediana**, no del promedio.
2. Su ventana es **anterior** al despacho medido: `[fecha − ventana_dias, fecha)`.
3. Con menos de `muestra_minima` llegadas comparables, `segundos_referencia` y `desviacion_mediana`
   salen **ausentes**, nunca `0`.
4. Los despachos **sin llegada** quedan fuera del cálculo de la referencia.

La columna `segundos_referencia` se documenta en el contrato HTTP como **valor derivado del
histórico**, y nunca como objetivo ni compromiso.

### OT24 — Evidencia

| Fichero | Devuelve |
|---|---|
| `ot24_cobertura_evidencia.sql` | `severidad, condado, casos_cerrados, con_foto, con_nota, con_ambas, pct_cobertura` |
| `ot24_latencia_sincronizacion.sql` | `periodo, evidencias, sincronizadas, pendientes, segundos_mediana` |
| `ot24_completitud_enriquecimiento.sql` | `periodo, casos, con_clima, con_conductores, con_implicados, pct_enriquecidos` |
| `ot24_volumen_evidencia_por_unidad.sql` | `periodo, unidad, fotos, notas, total` |
| `ot24_escaladas_severidad.sql` | `periodo, casos, escalados, severidad_inicial, severidad_final, pct_escalado` |

### OT25 — Cierre

| Fichero | Devuelve |
|---|---|
| `ot25_tiempo_asignado_a_cierre.sql` | `periodo, casos_medidos, minutos_mediana, minutos_p90` |
| `ot25_cierres_forzados.sql` | `periodo, proveedor, retiros, forzados, pct_forzado` |
| `ot25_distribucion_resultados.sql` | `severidad, condado, casos_cerrados, resultado_atencion, calificacion_media` |
| `ot25_envejecimiento_cartera.sql` | `tramo, casos_abiertos, dias_mediana` |
| `ot25_retiros_forzados_por_proveedor.sql` | `periodo, proveedor, finalizaciones, forzadas, pct` |

---

## 4. Reglas de resultado

| Regla | Detalle |
|---|---|
| **Denominador visible** | Todo porcentaje viene acompañado de su denominador |
| **Sin dato ≠ cero** | Denominador cero ⇒ el porcentaje sale **ausente**. Nunca `0` |
| **Lo desconocido cuenta** | Las filas cuya dimensión no se resolvió aparecen como `Desconocido` y **suman en los totales** |
| **Período vacío** | Cero filas. **No** una fila de ceros: son cosas distintas |
| **Hitos no alcanzados** | Excluidos de medianas y promedios; contados aparte en la columna `*_medidos` |
| **Orden estable** | `ORDER BY` explícito, con desempate por una clave única cuando el criterio principal puede repetirse |

---

## 5. Lo que ninguna consulta puede devolver

Exclusión **constitucional**, sin excepción para ningún rol, ni siquiera la autoridad departamental:

| Excluido | Aunque |
|---|---|
| Latitud, longitud, cualquier coordenada | El origen las tiene en accidentes, unidades y posiciones |
| Identidad de personas: usuario, técnico, conductor, implicado | El catálogo pedía un desglose por técnico (#20) |
| Texto libre: observaciones de cierre, notas, motivos internos | Se cuentan y se clasifican; no se transcriben |
| Secretos de autenticación y medios de cobro | No pertenecen a este departamento |

**No hace falta filtrarlas: no existen en el modelo.** Una prueba comprueba que ninguna consulta del
catálogo nombra una columna excluida.
