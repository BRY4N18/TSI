# Contrato — Esquema del modelo analítico

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Esquema de la **primera fase**: 2 hechos y 5 dimensiones. Los 11 hechos y 7 dimensiones restantes
están diseñados en el data model y se añaden después sin rehacer esto.

**Base de datos:** `tsi_tactico`.

---

## 1. Convenciones

| Convención | Regla |
|---|---|
| **Prefijos** | `dim_` para dimensiones, `hecho_` para hechos |
| **Motor de hechos de transacción** | `MergeTree`, particionado por mes |
| **Motor de hechos acumulados** | `ReplacingMergeTree(version)`, particionado por mes |
| **Motor de dimensiones** | `ReplacingMergeTree(version)` |
| **Partición** | `toYYYYMM(<fecha del grano>)` en todos los hechos |
| **Ausencia de valor** | `Nullable(...)`. **Prohibido usar 0 o fecha centinela** |
| **Marca de carga** | Toda tabla lleva `cargado_en DateTime` |

> ⚠️ **Regla de consulta sobre tablas con deduplicación.** Las tablas `ReplacingMergeTree` pueden
> contener temporalmente dos versiones de la misma fila hasta que la fusión ocurre en segundo plano.
> **Toda consulta sobre un hecho acumulado o una dimensión debe forzar la versión final** con el
> modificador `FINAL` o equivalente. Omitirlo produce cifras infladas de forma intermitente — el peor
> fallo posible en un informe, porque no es reproducible.

---

## 2. Dimensiones

### `dim_tiempo`

Una fila por día. Se genera, no se extrae.

```sql
CREATE TABLE IF NOT EXISTS dim_tiempo (
    fecha            Date,
    anio             UInt16,
    trimestre        UInt8,
    mes              UInt8,
    nombre_mes       String,
    semana_iso       UInt8,
    dia_del_mes      UInt8,
    dia_semana       UInt8,          -- 1 = lunes
    nombre_dia       String,
    es_fin_de_semana UInt8,
    version          DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY fecha
```

**Franja horaria** no vive aquí: es atributo del hecho, porque depende de la hora del suceso y no
de la fecha.

---

### `dim_geografia`

**Una fila por calle, con todos sus ascendientes aplanados.** Es lo que permite agrupar por condado
sin encadenar tres búsquedas.

```sql
CREATE TABLE IF NOT EXISTS dim_geografia (
    idcalle      Int32,
    calle        String,
    idciudad     Int32,
    ciudad       String,
    idcondado    Int32,
    condado      String,
    idestado     Int32,
    estado       String,
    idpais       Int32,
    pais         String,
    version      DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idcalle
```

**No incluye coordenadas.** Coherente con la exclusión decidida en los listados de Emergencias y
Red Operativa: la ubicación se expresa por nombre.

---

### `dim_severidad`

```sql
CREATE TABLE IF NOT EXISTS dim_severidad (
    idseveridad  Int32,
    severidad    String,
    descripcion  Nullable(String),
    orden        UInt8,          -- para ordenar por gravedad, no alfabéticamente
    version      DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idseveridad
```

---

### `dim_unidad` ⚠️ **versionada**

**Una fila por versión de unidad**, no por unidad. Es la dimensión que resuelve el defecto de
atribución histórica.

```sql
CREATE TABLE IF NOT EXISTS dim_unidad (
    sk_unidad          UInt64,        -- clave de la VERSIÓN, no de la unidad
    idunidademergencia Int32,         -- clave de negocio, se repite entre versiones
    placa              String,
    nombre_unidad      Nullable(String),
    tipo_unidad        Nullable(String),
    capacidad          Nullable(Int32),
    idcliente          Int32,         -- el proveedor DE ESTA VERSIÓN
    proveedor          String,
    idcondado          Nullable(Int32),
    condado            Nullable(String),
    zona_cobertura     Nullable(String),
    valido_desde       DateTime,
    valido_hasta       Nullable(DateTime),   -- NULL = versión vigente
    es_vigente         UInt8,
    inicio_es_real     UInt8,         -- 0 = "desde la primera carga", no una fecha conocida
    version            DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY (idunidademergencia, valido_desde)
```

**`sk_unidad`** es a lo que apuntan los hechos. Dos despachos de la misma unidad en épocas distintas
apuntan a **claves distintas**, y por eso cada uno conserva su proveedor correcto.

**`inicio_es_real = 0`** ⚠️ marca las versiones cuya fecha de inicio **no es un cambio observado**,
sino el momento en que el modelo empezó a mirar. Sin esta columna, un informe presentaría «no lo
sabemos» como «siempre fue así».

Para la unidad, **todas las versiones iniciales tendrán `inicio_es_real = 0`**: el origen no
historiza el cambio de proveedor, así que la historia empieza el día de la primera carga.

---

### `dim_origen_despacho`

```sql
CREATE TABLE IF NOT EXISTS dim_origen_despacho (
    idorigendespacho Int32,
    origen           String,      -- Automatico, Manual, Escalado_zona
    version          DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idorigendespacho
```

---

### `dim_condado_vecino`

Adyacencia física entre condados. **Única ampliación de OE3** (E3-08). Es aditiva:
ningún hecho se recarga. No se versiona: si el mapa cambiara, sería otro mapa.

```sql
CREATE TABLE IF NOT EXISTS dim_condado_vecino (
    idcondado        Int32,
    condado          String,
    idcondadovecino  Int32,
    condado_vecino   String,
    version          DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY (idcondado, idcondadovecino)
```

Origen: `Dim_CondadoVecino` (`activo = true`), nombres resueltos contra `Dim_Condado`.
Lleva fila desconocida (`idcondado = -1`): sin ella, un condado sin vecino resuelto
desaparece en la primera unión.

---

## 3. Hechos

### `hecho_accidente` — instantánea acumulada

**Grano: un caso registrado.**

```sql
CREATE TABLE IF NOT EXISTS hecho_accidente (
    idaccidente          String,        -- dimensión degenerada: el número de caso
    fecha                Date,          -- del accidente; clave de partición
    fechahora_accidente  DateTime,
    franja_horaria       String,        -- madrugada / mañana / tarde / noche

    -- dimensiones
    idcalle              Nullable(Int32),
    condado              Nullable(String),      -- desnormalizado (research D4)
    ciudad               Nullable(String),
    idseveridad          Nullable(Int32),
    severidad            Nullable(String),      -- desnormalizado
    tipo_reportado       Nullable(String),

    -- hitos del proceso  ⚠️ NULL = no alcanzado
    hora_confirmacion    Nullable(DateTime),
    hora_primera_asignacion Nullable(DateTime),
    hora_primera_llegada Nullable(DateTime),
    hora_cierre          Nullable(DateTime),

    -- métricas
    num_vehiculos        Nullable(Int32),
    num_heridos          Nullable(Int32),
    num_victimas         Nullable(Int32),
    num_fallecidos       Nullable(Int32),
    duracion_minutos     Nullable(Int32),
    total_intentos_despacho Nullable(Int32),

    -- marcas de proceso
    fue_descartado       UInt8,
    es_duplicado         UInt8,
    duplicado_de         Nullable(String),

    cargado_en           DateTime,
    version              DateTime
) ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idaccidente)
```

**Los tiempos son restas de esta misma fila.** «Reportado a confirmado» es
`hora_confirmacion - fechahora_accidente`; «asignado a cerrado» es
`hora_cierre - hora_primera_asignacion`. Sin uniones, sin ordenar.

⚠️ **Un hito ausente va `NULL`**, nunca cero ni la fecha de carga. Un cierre con fecha de carga
convertiría todos los casos abiertos en cerrados el día que se cargaron.

---

### `hecho_despacho` — instantánea acumulada, **grano intento**

**Grano: un intento de asignación a una unidad.**

```sql
CREATE TABLE IF NOT EXISTS hecho_despacho (
    iddespacho           Int32,
    idaccidente          String,
    fecha                Date,          -- del despacho; clave de partición
    fechahora_despacho   DateTime,

    -- dimensiones
    sk_unidad            UInt64,        -- ⚠️ la VERSIÓN de unidad vigente al despachar
    idunidademergencia   Int32,
    unidad               String,             -- desnormalizado
    proveedor            String,             -- ⚠️ el DE ESE MOMENTO, no el actual
    idorigendespacho     Int32,
    origen_despacho      String,             -- desnormalizado
    idseveridad          Nullable(Int32),
    severidad            Nullable(String),
    condado              Nullable(String),

    -- hitos  ⚠️ NULL = no alcanzado
    hora_confirmacion    Nullable(DateTime),
    hora_rechazo         Nullable(DateTime),
    hora_llegada         Nullable(DateTime),
    hora_retiro          Nullable(DateTime),

    -- métricas derivadas de los hitos
    segundos_respuesta   Nullable(Int32),
    segundos_transito    Nullable(Int32),
    segundos_atencion    Nullable(Int32),

    -- marcas
    numero_intento       UInt8,         -- 1 = primer intento sobre este caso
    resultado            String,        -- confirmado / rechazado / vencido / en_curso
    motivo_rechazo       Nullable(String),
    retiro_forzado       UInt8,

    cargado_en           DateTime,
    version              DateTime
) ENGINE = ReplacingMergeTree(version)
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idaccidente, iddespacho)
```

**`numero_intento`** es lo que hace calculable el KPI «despachos resueltos al primer intento»
(≥90 % en el tablero): son los intentos con `numero_intento = 1 AND resultado = 'confirmado'`.

⚠️ **`proveedor` es el de la versión vigente al despachar.** Copiar el actual reintroduciría el
defecto que este modelo existe para corregir.

---

### `hecho_estado_unidad` — **transacción**

**Grano: un cambio de estado registrado.** Añadido al implementar US3, siguiendo el procedimiento de
§4.bis. Es el primero que **no** es una instantánea acumulada, y por eso usa `MergeTree`: una fila de
transacción no se actualiza nunca, así que **no se consulta con `FINAL`** — pedirlo falla.

```sql
CREATE TABLE IF NOT EXISTS hecho_estado_unidad (
    idhistorial                 Int32,
    fecha                       Date,
    fechahora                   DateTime,
    sk_unidad                   UInt64,       -- la VERSIÓN vigente al cambiar
    idunidademergencia          Int32,
    unidad                      String,
    proveedor                   String,       -- el DE ESE MOMENTO
    idestadounidademergencia    Nullable(Int32),
    estado_nuevo                Nullable(String),
    estado_anterior             Nullable(String),
    es_cambio_efectivo          UInt8,        -- 0 = el estado no cambió realmente
    segundos_en_estado_anterior Nullable(Int32),
    cargado_en                  DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idunidademergencia, idhistorial)
```

⚠️ **`es_cambio_efectivo`** existe porque el origen registra filas con `Activa → Activa`: hubo una
escritura, no una transición. No se descartan —el registro existió— pero contarlas como cambios
inflaría cualquier métrica de rotación de flota.

**`idusuario` no se copia**, aunque el origen lo trae: analizar la disponibilidad de la flota no
requiere saber quién movió cada estado.

---

## 4. Reglas de carga

| Regla | Detalle |
|---|---|
| **Orden** | Dimensiones **antes** que hechos, siempre |
| **Idempotencia** | `ALTER TABLE … DROP PARTITION` del período, luego insertar. **No** `DELETE WHERE` |
| **Dimensión desconocida** | El hecho se carga con la referencia a la fila «desconocida» de la dimensión. **Nunca se descarta el hecho** |
| **Versionado** | Al cargar una dimensión versionada: si el atributo cambió, cerrar la versión vigente y abrir una nueva. Si no cambió, no tocar nada |
| **Fecha de inicio real** | La primera versión de cada entidad lleva `inicio_es_real = 0` salvo que se haya reconstruido desde una tabla de historial del origen |

---

## 4.bis Cómo se hace crecer el modelo

Procedimiento verificado ejecutándolo: `hecho_estado_unidad` se añadió siguiéndolo, y las cifras de
los dos hechos anteriores **no se movieron** (`dags/tests/test_crecimiento_aditivo.py`).

### Añadir un hecho

1. **Fijar el grano en una frase.** «Una fila por *X*». Si la frase necesita un «y», son dos hechos.
2. **Elegir el tipo**, que determina el motor y las reglas de consulta:

   | Tipo | Cuándo | Motor | ¿`FINAL` al consultar? |
   |---|---|---|---|
   | Transacción | El suceso ocurrió y no se actualiza | `MergeTree` | **No** — y pedirlo falla con `ILLEGAL_FINAL` |
   | Instantánea acumulada | Un proceso con hitos que avanza | `ReplacingMergeTree(version)` | **Sí, obligatorio** |

3. **Particionar por `toYYYYMM(<fecha del grano>)`**, siempre. Es lo que hace idempotente la recarga.
4. **Reutilizar las dimensiones que existan.** Un hecho nuevo que cree su propia copia de una entidad
   ya modelada introduce una segunda verdad sobre la misma cosa.
5. **Escribir su módulo en `dags/lib/hechos/`** con la lógica pura separada de la extracción, y sus
   tareas en `dags/lib/<hecho>_tasks.py` siguiendo el patrón de los tres existentes.
6. **Declarar la dependencia de las dimensiones con un sensor**, no con el horario.

**Garantías que debe preservar:** las cifras de los hechos existentes no cambian; no hace falta una
dimensión nueva; y el hecho nuevo no comparte particiones con ningún otro, de modo que retirarlo no
toca a los demás.

### Añadir una dimensión

Solo si ninguna existente sirve. Si el atributo pertenece a una entidad ya modelada, **es una columna
de esa dimensión**, no una tabla nueva.

Si sus atributos cambian con el tiempo y algún informe histórico los usa, va **versionada**: fila por
versión, `valido_desde` / `valido_hasta` y `inicio_es_real`. Si no, basta con `ReplacingMergeTree`
por su clave.

Toda dimensión resoluble necesita su **fila desconocida** en `dags/lib/dimensiones/desconocido.py`, o
los hechos que no la resuelvan se perderán en la primera unión.

### Añadir una métrica a un hecho existente

`ALTER TABLE … ADD COLUMN <nombre> Nullable(<tipo>)`.

⚠️ **Nullable, nunca con valor por defecto.** Las filas anteriores no tienen ese dato, y rellenarlas
con `0` hunde cualquier promedio y presenta «no lo medíamos» como una medición de cero. Con la
columna ausente, el promedio las excluye solo y el informe puede decir desde cuándo existe el dato
(`test_metrica_nueva.py`).

### Ampliar una dimensión compartida

`ALTER TABLE … ADD COLUMN`, también `Nullable`. **No hace falta recargar los hechos**: apuntan a la
clave de la versión, no a sus atributos, así que añadir columnas no mueve esas claves
(`test_dimension_ampliada.py`).

---

## 5. Lo que este esquema NO contiene, deliberadamente

| Excluido | Por qué |
|---|---|
| Coordenadas geográficas | Dato sensible; la ubicación va por nombre |
| Identidad de conductores, implicados y víctimas | Dato sensible bajo control y auditoría propios |
| Contacto de proveedores y clientes | Dato personal, innecesario para analizar |
| Texto libre de notas y mensajes | Puede contener material interno; el análisis no lo requiere |
| Una tabla por informe | Es el diseño que este modelo sustituye |
