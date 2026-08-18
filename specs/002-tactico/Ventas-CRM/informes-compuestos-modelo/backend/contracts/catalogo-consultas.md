# Contrato — Catálogo de consultas de Ventas y CRM

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/ventas_crm/`. Rigen las
convenciones del
[catálogo de Emergencias](../../../Emergencias/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md) §1,
que no se repiten aquí.

---

## 1. La regla de la versión final, por tabla ⚠️

| Tabla | ¿`FINAL`? |
|---|---|
| `dim_prospecto`, `dim_canal` | **Obligatorio** |
| Los cuatro hechos | **Prohibido** — todos son de transacción |

---

## 2. Dos reglas propias de este departamento ⚠️

**1. Ninguna consulta puede leer `activo` para determinar un desenlace.** Esa columna del origen
cubre a la vez convertido y perdido. El modelo expone `desenlace` con tres valores, y es el único
camino admitido. Se verifica con una prueba sobre el texto de las consultas.

**2. Ninguna consulta puede devolver identidad ni contacto de un prospecto.** No hace falta
filtrarlo: esos campos **no existen en el modelo**. La prueba comprueba que ninguna consulta los
nombra, para que nadie los reintroduzca al ampliar la dimensión.

**3. Un LEFT JOIN de ClickHouse no devuelve NULL.** Sin coincidencia rellena con el valor por
defecto del tipo (`''`, `0`, `1970-01-01`), y `ifNull` / `IS NULL` no disparan. La etapa vigente
sin transiciones, el tramo abierto del estancado y el grupo «sin demo» se resuelven con
`nullIf(..., '')` / `nullIf(..., toDateTime(0))` o con `IN (SELECT …)`, no con `ifNull` a secas.
Una desigualdad de tiempo (`fechahora <=`) va en `WHERE`, no en `ON`: ClickHouse 24.8 la rechaza
en el JOIN.

---

## 3. Parámetros propios

| Parámetro | Informe | Por defecto |
|---|---|---|
| `pesos_etapa` | #4 pipeline ponderado | `Nuevo=0.1, Contactado=0.2, Calificado=0.4, Propuesta=0.6, Negociación=0.8` |
| `top` | #5 motivos de pérdida, #10 secciones | `10` |

⚠️ **`pesos_etapa` es una convención del informe**, no una política de la empresa: el sistema
operativo no define ninguna ponderación. El informe debe declararlo, porque «valor ponderado del
pipeline» suena a cifra corporativa y no lo es.

---

## 4. Los 13 ficheros

### OT02 — Embudo

| Fichero | Devuelve |
|---|---|
| `ot02_embudo_conversion.sql` | `periodo, etapa_anterior, etapa_nueva, transiciones, pct_paso, denominador` |
| `ot02_permanencia_por_etapa.sql` | `periodo, etapa, prospectos_medidos, segundos_mediana, abiertos` |
| `ot02_carga_por_ejecutivo.sql` | `periodo, idejecutivo, activos, valor_pipeline, conversiones` |
| `ot02_pipeline_ponderado.sql` | `periodo, etapa, prospectos, valor_bruto, peso, valor_ponderado` |
| `ot02_motivos_perdida.sql` | `motivo, etapa_abandono, perdidos, pct` |

⚠️ **`ot02_permanencia_por_etapa.sql`** debe incluir el **tramo abierto**: la etapa vigente al final
del período cuenta hasta el fin del período, y se informa aparte en `abiertos`. Sin eso, los
prospectos estancados no aparecen — y son los que el informe existe para encontrar. El inicio del
tramo sin transiciones es `fecha_registro`, resuelto con `nullIf(fechahora_ultima, toDateTime(0))`
porque el LEFT JOIN no deja NULL.

⚠️ **`ot02_embudo_conversion.sql`** calcula el porcentaje **sobre transiciones**, no sobre prospectos
únicos, porque un prospecto puede retroceder de etapa. El campo `denominador` lo hace comprobable.

### OT01 — Captación

| Fichero | Devuelve |
|---|---|
| `ot01_captacion_por_canal.sql` | `periodo, canal, prospectos, pct` |
| `ot01_conversion_por_canal.sql` | `periodo, canal, prospectos, convertidos, pct_conversion` |
| `ot01_convertidos_por_canal.sql` | `periodo, canal, convertidos, prospectos, nota_indicador` |

⚠️ **`ot01_convertidos_por_canal.sql` NO devuelve ninguna columna de coste**, ni vacía. `nota_indicador`
declara que es **la parte medible del CAC** y cuál falta. Una columna `coste: null` invitaría a
rellenarla desde fuera, y el tablero mostraría un CAC que el sistema no sostiene.

### OT03 — Nutrición

| Fichero | Devuelve |
|---|---|
| `ot03_intensidad_demo.sql` | `periodo, idprospecto, empresa, eventos, secciones_distintas` |
| `ot03_secciones_visitadas.sql` | `seccion, visitas, prospectos_distintos` |
| `ot03_efectividad_nutricion.sql` | `grupo, prospectos, convertidos, pct_conversion` |
| `ot03_latencia_reaccion.sql` | `periodo, avisos, con_reaccion, sin_reaccion, segundos_mediana` |
| `ot03_reglas_disparo.sql` | `regla_disparada, avisos, con_reaccion, tasa_acierto` |

⚠️ **`ot03_latencia_reaccion.sql`**: los avisos **sin reacción** se cuentan en `sin_reaccion` y
**quedan fuera de la mediana**. Incluirlos como cero haría que los avisos ignorados **mejoraran** la
latencia media.

⚠️ **`ot03_efectividad_nutricion.sql`** devuelve **dos filas** —con demo y sin demo—, cada una con su
denominador. Un porcentaje sin su base no permite comparar grupos de tamaño distinto.

---

## 5. Reglas de resultado

Las comunes —denominador visible, sin dato ≠ cero, lo desconocido cuenta, período vacío devuelve cero
filas, orden estable— más dos propias:

| Regla | Detalle |
|---|---|
| **Distinguir «no hubo» de «hubo y no se usó»** | Los informes de OT03 devuelven cero filas si no hubo demos, y filas con valores en cero si las hubo y nadie las tocó. Son conclusiones opuestas sobre el producto |
| **Declarar lo que no se mide** | El informe de convertidos por canal dice que es media parte de su indicador |

---

## 6. Lo que ninguna consulta puede devolver

| Excluido | Aunque |
|---|---|
| Nombre, apellidos, correo, teléfono, cargo del prospecto | `Dim_Prospecto` los tiene todos |
| Notas de transición y metadata de demo | Son texto libre |
| Cualquier columna de coste, importe o inversión | El catálogo pide un CAC |
| Identidad del ejecutivo más allá de su clave | El desglose por ejecutivo solo existe en el informe de carga |
