# Contrato — Catálogo de consultas de Red Operativa

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/red_operativa/`. Rigen las
mismas convenciones que el
[catálogo de Emergencias](../../../Emergencias/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md) §1,
que **no se repiten aquí**: nombre del fichero, parámetros con tipo, `ORDER BY` explícito, sin
`SELECT *` y encabezado obligatorio.

---

## 1. La regla de la versión final, por tabla ⚠️

| Tabla | ¿`FINAL`? |
|---|---|
| `dim_region`, `dim_unidad`, `dim_geografia` | **Obligatorio** |
| `hecho_despacho` | **Obligatorio** |
| `hecho_estado_unidad`, `hecho_baja_unidad`, `hecho_validacion_region` | **Prohibido** — falla con `ILLEGAL_FINAL` |

---

## 2. Una regla propia de este departamento ⚠️

**Ninguna consulta puede unir con un catálogo de estados de unidad.** No existe en el modelo y no
debe crearse: el del sistema operativo **no define el estado 4** («En Misión»), usado en 6 de sus 45
transiciones. Los estados se agrupan **por el texto que registró la operación**.

Se verifica con una prueba sobre el texto de las consultas.

---

## 3. Parámetros propios

| Parámetro | Informe | Por defecto |
|---|---|---|
| `umbral_unidades` | #6 cobertura crítica, #13 regiones en riesgo | `1` |
| `dias_objetivo` | #9 puesta en operación | `30` — el valor normativo del BSC |
| `top` | #12 motivos de rechazo | `10` |

⚠️ **`umbral_unidades` es una convención de estos informes, no una política de la empresa.** El
sistema operativo no define ningún umbral: `Dim_ParametrosDespacho` tiene 0 filas. El informe debe
decirlo, porque su título sugiere que alguien decidió qué es crítico.

---

## 4. Los 15 ficheros

### OT12 — Flota

| Fichero | Devuelve |
|---|---|
| `ot12_unidades_por_estado.sql` | `periodo, estado, unidades, pct` |
| `ot12_pendientes_primer_acceso.sql` | `unidad, proveedor, fecha_alta, dias_desde_alta` |
| `ot12_rendimiento_proveedor.sql` | `periodo, proveedor, intentos, pct_rechazo, pct_abortos, segundos_llegada_mediana` |
| `ot12_cobertura_flota_por_region.sql` | `region, condado, activas, ocupadas, en_mision, fuera_servicio, total` |
| `ot12_disponibilidad_declarada.sql` | `periodo, unidad, segundos_activa, segundos_medidos, pct_disponibilidad` |
| `ot12_condados_cobertura_critica.sql` | `condado, unidades_disponibles, vecinos, unidades_en_vecinos, sin_alternativas` |
| `ot12_rotacion_flota.sql` | `periodo, proveedor, altas, bajas, saldo` |
| `ot12_bajas_forzadas.sql` | `periodo, proveedor, bajas, forzadas, con_caso_en_curso, pct_forzada` |

⚠️ **`ot12_disponibilidad_declarada.sql`** debe cumplir tres cosas verificables:

1. Mide **tiempo en estado**, no número de transiciones.
2. El estado vigente al final del período cuenta **hasta el fin del período**, no hasta el último
   cambio. Sin esto, una unidad activa todo el mes y sin cambios daría **0 %**.
3. Una unidad **sin ninguna transición conocida** devuelve `pct_disponibilidad` **ausente**, no `0`.

⚠️ **`ot12_condados_cobertura_critica.sql`**: un condado **sin vecinos declarados** aparece con
`sin_alternativas = 1`. Es la situación más grave, no un caso a omitir.

### OT11 — Regiones

| Fichero | Devuelve |
|---|---|
| `ot11_tiempo_puesta_operacion.sql` | `region, fecha_definida, fecha_produccion, dias, cumple_objetivo` |
| `ot11_mercados_activos.sql` | `region, clientes_activos, unidades, es_mercado_activo` |
| `ot11_tasa_aprobacion_primer_intento.sql` | `region, intentos, aprobada_primer_intento, pct` |
| `ot11_motivos_rechazo.sql` | `motivo, rechazos, pct` |

⚠️ **`ot11_tiempo_puesta_operacion.sql`**: las regiones que **no llegaron a producción** devuelven
`dias` **ausente** y `cumple_objetivo` ausente. **Nunca `0` ni `false`**: no incumplieron un plazo,
todavía están dentro de él.

⚠️ **`ot11_motivos_rechazo.sql`** agrupa **solo validaciones rechazadas**. Un motivo ausente no es
una categoría: las aprobadas sin motivo no deben aparecer como un grupo «sin motivo».

### OT13 — Retirada

| Fichero | Devuelve |
|---|---|
| `ot13_regiones_en_riesgo.sql` | `region, estado_ciclo_vida, condados, unidades_disponibles, bajo_umbral` |
| `ot13_casos_activos_al_despublicar.sql` | `region, fecha_despublicacion, casos_activos, medida_exacta_desde` |
| `ot13_tiempo_perdida_a_despublicacion.sql` | `region, fecha_sin_cobertura, fecha_despublicacion, dias, medida_exacta_desde` |

⚠️ **Los dos últimos devuelven `medida_exacta_desde`**, que es la fecha de la primera carga del
modelo. Antes de ella no hay despublicaciones que mostrar **porque nadie las guardó**, no porque no
ocurrieran. Omitir esa columna presentaría un histórico vacío como si significara «nunca pasó».

---

## 5. Reglas de resultado

Las mismas que en Emergencias —denominador visible, sin dato ≠ cero, lo desconocido cuenta, período
vacío devuelve cero filas, orden estable— más una propia:

| Regla | Detalle |
|---|---|
| **Declarar desde cuándo se mide** | Todo informe que dependa del versionado de región devuelve la fecha desde la que su medida es exacta |

---

## 6. Lo que ninguna consulta puede devolver

| Excluido | Aunque |
|---|---|
| Coordenadas | `Dim_UnidadEmergencia` las tiene |
| Identidad de personas: usuario, **validador de región** | El catálogo pedía la tasa de aprobación **por validador** |
| Contacto del proveedor | Está en el origen, junto a los datos de la unidad |
