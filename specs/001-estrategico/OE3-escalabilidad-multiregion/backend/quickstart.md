# Quickstart — Verificación de OE3

**Fecha:** 2026-08-16 · **Plan:** [`plan.md`](plan.md) · **Contrato:**
[`contracts/informes-estrategicos-oe3.openapi.yaml`](contracts/informes-estrategicos-oe3.openapi.yaml)

Cada comprobación existe porque su fallo sería silencioso.

---

## 1. Prerrequisitos y línea base

```powershell
docker ps --filter name=tactico-clickhouse --filter name=accidentes-django
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SHOW TABLES"
```

**Medido el 2026-08-16.** El contrato de esquema tiene **14 tablas** de modelo (13 +
`dim_condado_vecino`). En disco hay **16** (`SHOW TABLES` con `dim_%`/`hecho_%`): las 14
más residuales `dim_canal`, `dim_prospecto` (y, según carga, hechos de otros módulos).

| Dato | Valor medido |
|---|--:|
| Casos · con primera asignación | 4 252 · 3 638 |
| Registro → primera asignación: mediana / p95 | 38 s / **106 s = 1,77 min** |
| Casos sobre 2 minutos | **58** (1,6 %) |
| Oferta → confirmación de unidad: p95 | 28 s |
| Intentos · por origen | 4 314 · Auto 2 847 · Manual 1 083 · Escalado 384 |
| Manuales tras un intento automático | **1** de 1 083 |
| Completitud de campos críticos | **100 %** → tasa de error 0 % |
| `dim_condado_vecino` FINAL | **3** (2 simétricas + fila desconocida `-1,-1`) |
| `hecho_ping_unidad` | 59 045 posiciones |

**T066 cobertura** de `oe3_service.py`: **95 %** (umbral 80 %). Suite
`apps/informes_estrategicos/tests`: **183 passed**, 1 skipped.

---

## 2. Las comprobaciones

### 2.1 La dimensión nueva se cargó y no movió nada

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SELECT count() FROM dim_condado_vecino FINAL"
```

**Esperado: 2 filas** de adyacencia, simétricas, más la fila desconocida.

✅ **Medido:** 2 pares (`idcondado > 0`) + 1 desconocido = 3 filas FINAL.
`hecho_accidente` = 4 252, `hecho_despacho` = 4 314 — no se movieron.

### 2.2 La latencia de asignación mide lo operativo, no lo técnico

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query @"
SELECT count() AS casos,
       round(median(dateDiff('second', fechahora_accidente, hora_primera_asignacion)),1) AS mediana_seg,
       round(quantile(0.95)(dateDiff('second', fechahora_accidente, hora_primera_asignacion)),1) AS p95_seg,
       countIf(dateDiff('second', fechahora_accidente, hora_primera_asignacion) > 120) AS sobre_2min
FROM hecho_accidente FINAL
WHERE hora_primera_asignacion IS NOT NULL AND fue_descartado=0 AND es_duplicado=0
"@
```

**Esperado:** ≈38 s de mediana, ≈106 s de p95, 58 sobre 2 minutos.

✅ **Medido:** mediana 38 s, p95 106 s, 58 sobre 2 min. El `objetivo` de la API es
`valor: 2`, `unidad: "min"`, `tipo: "NORMATIVO"` — no 100 ms.

### 2.3 El `cumple` es booleano aquí — y solo aquí

Pedir `latencia-asignacion` y `tasa-error-registro`.

**Esperado:** `objetivo.tipo: "NORMATIVO"` y `cumple: true` en ambos.

⚠️ **Si se copió la prueba transversal de OE6 —«ningún `cumple` booleano»—, fallará.** Es lo esperado:
esa prueba no aplica a este módulo. Aquí la comprobación es la inversa.

Y a la vez, `primer-intento` **sí** debe traer `cumple: null`: su meta es `[CALIBRAR]`.

✅ **Medido contra la API (2026-08-16, `DirectorOperaciones`):**
- `tasa-error-registro`: `cumple: true` (0 % < 1 %).
- `primer-intento`: `cumple: null`.
- `latencia-asignacion` con `granularidad=anio`: `cumple: true` (p95 **1,77 min**).
- Con `granularidad=mes` el envelope toma el **máximo** mensual: agosto 2026
  (mes en curso, 54 casos) tiene p95 **3,14 min** → `cumple: false`. Febrero–julio
  están todos entre 1,69 y 1,78 min. El p95 global del año sigue siendo 1,77 min.

### 2.4 La tasa de error publica qué campos comprueba

Pedir `tasa-error-registro`. **Esperado:** `tasa_error: 0.0` **y** `campos_comprobados` presente en la
fila.

⚠️ **El 0 % sin la lista es el fallo, no la cifra.** Un indicador que estructuralmente nunca se mueve
se lee como «el registro es perfecto» cuando dice «los dos campos que miro están completos».

✅ **Medido:** `tasa_error: 0.0`, `campos_comprobados: ["severidad","condado"]`.

### 2.5 La capacidad es la del período, no la de hoy

Pedir `ratio-demanda-capacidad` de un trimestre pasado y comprobar que `unidades_vigentes`
corresponde a las **versiones vigentes entonces**.

**Cómo se detecta el fallo:** si se usara `es_vigente = 1`, todos los períodos devolverían el mismo
número de unidades. **Dos períodos con la misma capacidad y distinta demanda** es la señal.

### 2.6 Un condado sin unidades se declara, no divide por cero

Construir un período donde un condado tenga casos y ninguna unidad vigente.

**Esperado:** `sin_capacidad: true` y `ratio: null`. **No** un infinito, un cero ni un `500`.

Es el hallazgo más valioso del informe: una zona donde una emergencia no tiene quién la atienda.

### 2.7 El respaldo mide disponibilidad, no existencia

Pedir `cobertura-de-respaldo` con todas las unidades del condado vecino en estado `Ocupada` o
`Fuera de servicio`.

**Esperado:** `vecinos_con_unidad_disponible: 0` aunque el vecino tenga unidades dadas de alta.

⚠️ Si devuelve el vecino como respaldo, se está leyendo la existencia de la unidad y no su último
estado — el error que Red Operativa documentó como el más caro de su departamento.

### 2.8 La pérdida de señal ve todas las posiciones

Pedir `perdida-de-senal` y comparar con las cifras del módulo táctico, que ya corrigió el
truncamiento.

**Esperado:** del orden de **3 942 huecos sobre 59 045 posiciones**, no los 714 del flujo legado.

✅ **Medido:** **3 942** huecos (`granularidad=anio`, 59 045 posiciones).

### 2.9 Los siete bloqueados no existen

Pedir las rutas de E3-01, E3-04, E3-05, E3-06, E3-09, E3-12 y E3-14.

**Esperado: `404`.** No un `200` con `data: []`, y desde luego no un `200` con ceros.

⚠️ **E3-04 es el que más importa.** Publicado, compararía contra `1970-01-01` y devolvería más de
veinte mil días en rojo contra una meta `[NORMATIVO]`, sin un solo error.

✅ **Medido:** los siete nombres bloqueados responden **404** con JWT de Operaciones.

### 2.10 La autoridad repartida excluye, no solo concede

Es la comprobación propia de este módulo, y la más fácil de dejarse.

| Rol | `latencia-asignacion` | `ratio-demanda-capacidad` |
|---|:--:|:--:|
| `DirectorOperaciones` | `200` | `200` |
| `DirectorExpansion` | **`403`** | `200` |
| `Gerente` | `200` | `200` |
| `Operador`, `Despacho`, `Unidad` | `403` | `403` |

⚠️ **El `403` de `DirectorExpansion` en los informes de despacho es la comprobación**, no un efecto
colateral. Un permiso de módulo en vez de por informe concedería de más justo donde el SRS pide lo
contrario.

✅ **Medido por login real** (`director.operaciones@demo.tsi.com` /
`director.expansion@demo.tsi.com`): Operaciones 200 en los siete; Expansión **403** en
`latencia-asignacion` y 200 en `ratio-demanda-capacidad`, `cobertura-de-respaldo` y
`perdida-de-senal`.

### 2.11 La comparación declara sus dos ventanas

Con `comparacion=mom`, dos ventanas de igual longitud. Con `yoy`, `ventana_anterior: null` y
`motivo_ausencia` — **no un `400`**.

✅ **Medido:** `yoy` sobre 2026-01-01..2026-03-31 → **200**, `ventana_anterior: null`,
motivo «el histórico arranca en 2026-02-03».

### 2.12 Las dos capas coinciden

Para los que existen en ambas, con granularidad `mes` y sin comparación:

| Estratégico | Táctico |
|---|---|
| `primer-intento` | `/informes-tacticos/emergencias/primer-intento` |
| `ratio-demanda-capacidad` | `/informes-tacticos/emergencias/ratio-demanda-capacidad` |
| `perdida-de-senal` | `/informes-tacticos/emergencias/perdida-senal` |
| `tasa-error-registro` | complemento de `completitud-campos-criticos` |

⚠️ Si diverge alguno, **la salida no es ampliar la tolerancia**: es promover la medida a fichero
compartido.

### 2.13 Nada sensible sale, con la autoridad

Recorrer los siete con `DirectorOperaciones` y con `DirectorExpansion`: ninguna respuesta con
coordenadas ni identidad de personas.

### 2.14 Un período sin datos no es una fila de ceros

Los siete devuelven `data: []` con `cobertura: "completa"`.

✅ **Medido:** `latencia-asignacion` 2019-01-01..2019-03-31 → `data: []`, `cobertura: "completa"`.
El resto de comprobaciones 2.5–2.7, 2.12 y 2.13 las cubre la suite pytest (183 passed).

---

## 3. Lo que este quickstart NO comprueba

- **La agrupación por región.** No existe. Comprobar que `por_region` **no es un parámetro aceptado**
  forma parte de 2.10.
- **El rol `Gerente`.** No está sembrado todavía.
- **Los siete informes bloqueados**, más allá de que devuelvan `404`.
- **El frontend.** Aplazado.

---

## 4. Dos lecturas que van a aparecer

**El objetivo cumple sus dos metas medibles.** Latencia 1,77 min contra 2, y error de registro 0 %
contra 1 %. Es una buena noticia con una advertencia: **son dos metas de las cinco `[NORMATIVO]` que
el tablero promete para OE3**. Las otras tres —uptime, puesta en operación regional y reasignación
manual— no tienen fuente.

**Y la mitad del objetivo sigue sin medirse.** OE3 se llama *escalabilidad sin degradación*. Con este
módulo se puede afirmar lo segundo. Lo primero necesita que el sistema operativo historice el estado
de las regiones — y con dos regiones declaradas, una llamada «Region Prueba Norte», y todos los
accidentes en un solo estado, **el objetivo todavía no tiene el fenómeno que quiere medir**.
