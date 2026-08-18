# Data Model — Informes Compuestos de Cuentas y Clientes

**Fecha:** 2026-08-14 · **Research:** [`research.md`](research.md)

Este módulo **amplía una dimensión existente** y añade **tres dimensiones y dos hechos**.

---

## 1. Los 9 informes

### OT17 — El ciclo de vida *(4 informes, 1 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 1 | **Churn por cohorte de alta**, con motivo | cohorte × período | `dim_cliente` *(ampliada)* |
| 2 | Antigüedad media por tipo y plan | tipo × plan | `dim_cliente` + `dim_plan` |
| 3 | Usuarios por cliente frente al tope del plan | cliente | `dim_usuario_organizacion` + `dim_plan` |
| 4 | Cuentas en riesgo: sin sesión en N días | cliente | `hecho_sesion` + `dim_usuario_organizacion` |

**#1 agrupa por cohorte de alta**, no por mes de baja (research D7). **#2 reutiliza `dim_plan`**, que
creó Suscripciones.

**#3 y #4 declaran su cobertura**: solo el 9,5 % de los usuarios tiene organización conocida.

### OT04 — La incorporación *(3 informes, 1 BSC)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 5 | **Tiempo de onboarding** | período | `hecho_onboarding` |
| 6 | Embudo de abandono | etapa | `hecho_onboarding` + `dim_etapa_onboarding` |
| 7 | Tasa de aprobación frente a rechazo | tipo × período | `dim_cliente` |

**#6 se mide por ausencia** contra el catálogo explícito de etapas (research D2).

### OT18 — El acceso *(2 informes)*

| # | Informe | Grano de salida | Fuente en el modelo |
|--:|---|---|---|
| 8 | Sesiones concurrentes y duración media | día × franja | `hecho_sesion` |
| 9 | Usuarios con roles incompatibles | usuario | `dim_rol` + asignaciones |

**#8 mide concurrencia por solape**, no por conteo de inicios (research D4). **#9 devuelve la clave
del usuario**, nunca su nombre (research D6).

---

## 2. La ampliación de `dim_cliente` ⚠️

```sql
ALTER TABLE dim_cliente ADD COLUMN cohorte_alta          Nullable(String);   -- 'YYYY-MM'
ALTER TABLE dim_cliente ADD COLUMN fecha_baja            Nullable(DateTime);
ALTER TABLE dim_cliente ADD COLUMN motivo_baja           Nullable(String);
ALTER TABLE dim_cliente ADD COLUMN etapa_onboarding_actual Nullable(String);
ALTER TABLE dim_cliente ADD COLUMN onboarding_completo   UInt8;
ALTER TABLE dim_cliente ADD COLUMN resultado_solicitud   Nullable(String);   -- aprobada | rechazada
```

⚠️ **Es una ampliación, no una tabla nueva.** La dimensión la creó Suscripciones; este departamento
es su dueño y llega después. **Las columnas que Suscripciones ya usa no se tocan**, y una prueba
comprueba que sus informes siguen dando las mismas cifras (SC-009).

⚠️ **`etapa_onboarding_actual` se deriva de las etapas registradas**, no de la columna de estado del
sistema operativo, que está **nula en un cliente activo**.

⚠️ **`nit_identificacion` sigue sin copiarse**, como decidió Suscripciones.

---

## 3. Las tablas nuevas

### 3.1 `dim_etapa_onboarding` — el catálogo **explícito** ⚠️

```sql
CREATE TABLE IF NOT EXISTS dim_etapa_onboarding (
    idetapa    Int32,
    etapa      String,
    orden      UInt8,             -- posición en el proceso
    es_obligatoria UInt8,
    version    DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idetapa
```

**Parece excesivo para cinco filas, y es lo que hace correcto el embudo.** Si las etapas se
infirieran de lo observado, **una etapa que nadie ha completado nunca no existiría en el informe** —
y el embudo mostraría 100 % de finalización describiendo un proceso perfecto.

**`orden` es obligatorio**: un embudo sin orden no es un embudo, es un recuento.

### 3.2 `hecho_onboarding` — transacción, grano **una etapa completada**

```sql
CREATE TABLE IF NOT EXISTS hecho_onboarding (
    idonboarding    Int32,
    fecha           Date,              -- del completado; clave de partición
    fechahora       DateTime,

    idcliente       Int32,
    tipo_cliente    Nullable(String),
    idetapa         Nullable(Int32),
    etapa           String,
    orden_etapa     Nullable(UInt8),

    dias_desde_alta Nullable(Int32),

    cargado_en      DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idcliente, idonboarding)
```

ClickHouse 24.8 rechaza claves de ordenación anulables (`allow_nullable_key` desactivado).
`orden_etapa` sigue siendo `Nullable` —una etapa no catalogada no inventa orden— pero **no** entra
en el `ORDER BY`. El grano único es `(fecha, idcliente, idonboarding)`.

⚠️ **Solo contiene etapas completadas**, porque es lo único que el origen registra. **El abandono no
está aquí**: se deduce cruzando con el catálogo (research D2).

### 3.3 `hecho_sesion` — transacción, grano **una sesión** ⚠️

```sql
CREATE TABLE IF NOT EXISTS hecho_sesion (
    idsesion          Int32,
    fecha             Date,              -- del inicio; clave de partición
    fechahora_inicio  DateTime,
    fechahora_cierre  Nullable(DateTime),  -- NULL = sin cierre registrado

    idusuario         Int32,              -- CLAVE, nunca identidad
    idcliente         Nullable(Int32),    -- si su pertenencia es conocida
    pertenencia_conocida UInt8,

    desenlace         String,             -- cerrada | abierta | expulsada
    navegador         Nullable(String),
    franja_horaria    String,
    duracion_segundos Nullable(Int32),    -- NULL si no hubo cierre

    cargado_en        DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(fecha)
ORDER BY (fecha, idusuario, fechahora_inicio)
```

⚠️ **`token` no se copia.** Es una credencial viva: llevarla a un almacén analítico la expone a
cualquier consulta y a cualquier copia de seguridad.

⚠️ **`duracion_segundos` ausente cuando no hubo cierre.** Nunca cero —hundiría la media— y nunca
«hasta ahora» —inventaría una duración para sesiones que quizá cerraron sin registrarse—.

⚠️ **`desenlace` distingue tres finales**, no dos: una sesión **expulsada** terminó, pero no porque
el usuario se fuera.

**`navegador` sí se conserva**: es información de plataforma, no identifica a la persona.

### 3.4 `dim_usuario_organizacion` — la pertenencia, con su cobertura

```sql
CREATE TABLE IF NOT EXISTS dim_usuario_organizacion (
    idusuario   Int32,
    idcliente   Nullable(Int32),
    tiene_pertenencia UInt8,
    es_activo   UInt8,
    version     DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idusuario
```

⚠️ **Contiene a los 21 usuarios, no solo a los 2 con pertenencia declarada.** Los demás llevan
`tiene_pertenencia = 0` y `idcliente` ausente. Cargar solo los declarados haría **imposible calcular
la cobertura**, que es justo lo que los informes deben declarar.

⚠️ **Sin nombre, correo, identificación, teléfono, género ni fecha de nacimiento.**

### 3.5 `dim_rol` y la asignación

```sql
CREATE TABLE IF NOT EXISTS dim_rol (
    idrol       Int32,
    rol         String,
    descripcion Nullable(String),
    es_activo   UInt8,
    version     DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY idrol;

CREATE TABLE IF NOT EXISTS dim_usuario_rol (
    idusuario   Int32,
    idrol       Int32,
    rol         String,
    es_activo   UInt8,
    version     DateTime
) ENGINE = ReplacingMergeTree(version)
ORDER BY (idusuario, idrol)
```

**La política de incompatibilidad no vive aquí**: es un parámetro del informe (research D8). Sin
política declarada, el informe devuelve vacío — preferible a inventar una lista de combinaciones
peligrosas que nadie aprobó.

### 3.6 Lo que NO se añade

| Se pidió | No se añade | Motivo |
|---|---|---|
| Token de sesión | Nada | Credencial viva |
| Identidad del usuario | Nada; solo su clave | Dato personal, incluidos género y fecha de nacimiento |
| Identificador fiscal | Nada | Ya excluido por Suscripciones |
| Una dimensión de cliente propia | **Nada** | `dim_cliente` se amplía |
| Registro de abandono de onboarding | Nada | **No existe**: se deduce por ausencia |

---

## 4. Reglas de consulta

| Regla | Aplicada aquí |
|---|---|
| **Versión final** | Obligatoria en las cinco dimensiones. **Prohibida** en los dos hechos |
| **El abandono es ausencia** | Se cruza con el catálogo de etapas, nunca se cuenta directamente |
| **La duración solo donde hay cierre** | Y las abiertas se declaran aparte |
| **La concurrencia es solape** | No conteo de inicios |
| **Declarar la cobertura** | Los informes de pertenencia dicen qué porcentaje de usuarios la tiene |
| **Ausencia ≠ cero** | Sesión sin cierre, cliente sin plan, cliente sin ninguna sesión |
