# Quickstart — Verificación de OE4

**Fecha:** 2026-08-16 · **Plan:** [`plan.md`](plan.md) · **Contrato:**
[`contracts/informes-estrategicos-oe4.openapi.yaml`](contracts/informes-estrategicos-oe4.openapi.yaml)

---

## 1. Prerrequisitos y línea base

```powershell
docker ps --filter name=tactico-clickhouse --filter name=accidentes-django
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SHOW TABLES"
```

**El recuento de tablas no cambia con este módulo.** Las dos ampliaciones son columnas de
`hecho_accidente`, no tablas. Si aparece una tabla nueva, algo se hizo mal.

**Medido el 2026-08-16:**

| Dato | Valor |
|---|--:|
| Casos | 4 252 |
| Descartados · duplicados | 220 · 141 |
| Completitud de campos críticos | **100 %** |
| Casos con fotografía · fotografías totales | **2** · **3** |
| Casos con nota | 51 |
| Casos con condición climática | **3** (0,07 %) |
| Casos con `distanciamillas > 0` en el origen | **4 200** (98,8 %) |
| `resultado_atencion` · `calificacion` | 1 · **0** |
| Filas de `indice_calidad_historico` | 182 |
| Condados: Cuauhtemoc · Benito Juarez | 2 158 · 2 094 |

---

## 2. Las comprobaciones

### 2.1 Las dos ampliaciones se cargaron y no movieron nada

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query @"
SELECT count() AS casos,
       countIf(distancia_millas IS NOT NULL) AS con_distancia,
       countIf(condicion_clima  IS NOT NULL) AS con_clima
FROM hecho_accidente FINAL
"@
```

**Esperado:** 4 252 casos, **≈4 200 con distancia**, **3 con clima**.

Y el resto de cifras de `hecho_accidente` —casos, descartados, duplicados, hitos— **idénticas a antes
de la ampliación**. Es la garantía de crecimiento aditivo que el §4.bis exige.

### 2.2 ⚠️ La cardinalidad del clima sigue siendo 1:0..1

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query "SELECT max(num_elementos_clima) FROM hecho_accidente FINAL"
```

**Esperado: 1.**

Si algún día devuelve 2, la carga está **eligiendo una condición en silencio** y hay que rediseñar
con un puente. La prueba automatizada de esta comprobación es la que convierte ese cambio en un fallo
visible en vez de en una cifra plausible.

### 2.3 La fórmula del índice reproduce el legado

```powershell
docker exec tactico-clickhouse clickhouse-client --database tsi_tactico --query @"
SELECT periodo, indice_consolidado,
       round((pct_completitud + (1-pct_descarte) + (1-pct_fusion) + pct_cobertura_evidencia)/4, 4) AS formula
FROM indice_calidad_historico ORDER BY periodo DESC LIMIT 6
"@
```

**Esperado:** las dos columnas **idénticas** en las seis filas. Es la fórmula que E4-01 conserva.

### 2.4 ⚠️ La cobertura de evidencia diverge, y se declara

Pedir `indice-calidad-historico` y compararlo con el legado.

**Esperado:** que **diverja** en `pct_cobertura_evidencia`, y que la prueba de contraste **declare la
divergencia con su causa** en vez de tolerarla o de fallar.

Se probaron tres definiciones y ninguna reproduce el legado:

| Fecha | Legado | Solo foto | Solo nota | Foto o nota |
|---|--:|--:|--:|--:|
| 2026-08-13 | 0,50 | 0,00 | 0,25 | 0,25 |
| 2026-08-12 | 1,00 | 0,25 | 0,75 | 0,75 |

✅ **La comprobación es que el endpoint nuevo publique `con_foto`, `con_nota` y `con_ambas` por
separado**, que es lo que el legado no permite saber.

### 2.5 Un campo que nunca falta sigue en el ranking

Pedir `campos-mas-ausentes`. **Esperado:** severidad y calle aparecen con **cero ausencias**, no
desaparecen.

Un campo fuera de la lista se confunde con un campo que nadie revisó, y son conclusiones opuestas.

### 2.6 La completitud publica qué campos comprueba

Pedir `completitud-campos-criticos`. **Esperado:** `pct_completitud: 1.0` **y** `campos_comprobados`
presente.

⚠️ El 100 % sin la lista es el fallo, no la cifra.

### 2.7 ⚠️ El patrón climático declara su escasez

Pedir `patron-horario-climatico`.

**Esperado:** la parte horaria con los 4 252 casos y `cobertura: "parcial"` con `falta` nombrando la
condición climática — **3 casos de 4 252**.

Un reparto por condición climática sobre tres casos tiene la forma de un patrón y el significado de
una anécdota, y este informe alimenta un modelo predictivo.

### 2.8 El impacto vial entrega las dos mitades

Pedir `impacto-vial-por-zona`. **Esperado:** `duracion_media_min` y `distancia_media_millas`, con
`casos_con_duracion` y `casos_con_distancia` **distintos entre sí** (4 252 frente a ≈4 200).

Si fueran iguales, la distancia estaría entrando como cero en los casos sin dato.

### 2.9 Cero y no registrado son distintos

Pedir `impacto-humano-por-zona` con un caso de cero heridos y otro sin heridos registrados.

**Esperado:** resultados distintos, y `casos_con_dato` menor que `casos`.

⚠️ El síntoma del fallo es sutil y grave: el impacto humano total **baja cuando empeora la calidad del
registro**. En un informe que se vende, el comprador no tiene forma de notarlo.

### 2.10 Ninguna ubicación por coordenadas

Recorrer los nueve. **Esperado:** ninguna respuesta con latitud, longitud ni identidad de personas.

⚠️ **Con `DirectorDatos`, que es la máxima autoridad del módulo**, no solo con un rol acotado. Y con
más motivo aquí: estos informes se venden a terceros.

### 2.11 Ningún `cumple` booleano

Recorrer los nueve. **Esperado:** todo `meta.objetivo.cumple` es `null`.

✅ **Aquí sí aplica la prueba transversal de OE6**, al contrario que en OE3. Todas las metas de OE4
son `[CALIBRAR]`.

### 2.12 El umbral de masa crítica se publica

Pedir `cobertura-del-historico`. **Esperado:** `umbral: 500` en la fila, y **ninguna zona marcada**
—los dos condados tienen 2 158 y 2 094 casos—.

Repetir con `umbral_casos=3000`: **ambas zonas se marcan**. Es la comprobación de que el parámetro
funciona.

### 2.13 Los seis bloqueados no existen

Pedir las rutas de E4-07 a E4-11 y E4-14. **Esperado: `404`.**

⚠️ **E4-14 es el que más fácil se cuela**, porque `cargado_en` existe y la resta no falla. Devolvería
una mediana de **1 971 horas** que parece una latencia de ingesta y es la antigüedad del accidente
respecto de la carga.

### 2.14 El acceso excluye

| Rol | `completitud-campos-criticos` | `concentracion-siniestralidad` |
|---|:--:|:--:|
| `DirectorDatos` | `200` | `200` |
| `DirectorOperaciones` | `200` | **`403`** |
| `Gerente` | `200` | `200` |
| `Operador`, `Analista` | `403` | `403` |

⚠️ El `403` de `DirectorOperaciones` en los de analítica pura es la comprobación.

### 2.15 Un período sin datos no es una fila de ceros

Los nueve devuelven `data: []` con `cobertura: "completa"`.

---

## 3. Lo que este quickstart NO comprueba

- **Los cinco informes del modelo predictivo**, más allá del `404`. No hay modelo del que hablar.
- **Un usuario demo con rol `Gerente`.** El rol (id 23) está en `Dim_Rol` / `ROLES_DEMO`; este
  quickstart no comprueba que haya una cuenta asignada en el entorno.
- **La agrupación por región.** No existe.
- **El frontend.** Implementado: [`../frontend/quickstart.md`](../frontend/quickstart.md).

---

## 4. Dos lecturas que van a aparecer

**Casi todo lo que este objetivo mide sale cercano a cero, y es correcto.** Tres fotografías, un
resultado de atención, cero calificaciones, tres condiciones climáticas. El trabajo del módulo es que
esas cifras se lean como **«esto no se registra»** y no como **«esto no ocurre»** — la primera se
arregla con formación y la segunda con nada.

**Y OE4 solo cubre la mitad de su propio tablero.** Tres de sus indicadores BSC —precisión del
modelo, unidades preposicionadas y productos de inteligencia— no tienen fuente, porque las tres
tablas que los sostienen no existen en ninguna parte del sistema. Es lo primero que hay que saber al
leer el tablero de este objetivo.
