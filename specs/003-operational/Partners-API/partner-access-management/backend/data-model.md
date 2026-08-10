# Data Model — Gestión de Acceso de Partners

> **Sin cambios de esquema.** Las dos decisiones de diseño (`spec.md` § 15 D1 y D2) se resuelven con tablas y campos que **ya existen**. Este módulo no añade columnas ni tablas.

> **Pinot no almacena `NULL`.** Toda regla se expresa contra centinelas explícitos, nunca con `IS NULL` (RN-PAC-014).

## Entidades que este módulo escribe

### 1) `Dim_Partner` (estado operativo — fuente de verdad única)

- **PK:** `idpartner` (INT)
- **Estado:** `activo` (BOOLEAN) — **la única fuente de verdad** de si el partner está habilitado o suspendido (RN-PAC-012)
- **Snapshot de suspensión:** `fecha_suspension` (STRING), `motivo_suspension` (STRING)
- **Timestamp:** `fecha_actualizacion` (LONG) — `timeColumnName` y `comparisonColumn` del upsert

| Centinela | Columna | Significa |
|---|---|---|
| `""` | `fecha_suspension`, `motivo_suspension` | No suspendido |

**Reglas:**
- `fecha_suspension` y `motivo_suspension` son **un resumen del último evento**, no un historial paralelo que pueda contradecir a `activo` (SRS L442). El historial completo vive en la bitácora.
- Al reactivar, ambos vuelven al centinela vacío.
- `fecha_actualizacion` **debe avanzar en cada escritura**: es la columna de comparación del upsert.
- **Este módulo es el único que escribe `activo`** tras la incorporación. #07 lo pone a `true` al registrar; #08 solo lo lee.

### 2) `Dim_CredencialAPI` (invalidación y restitución)

- **PK:** `idcredencial` (INT)
- **FKs:** `idpartner`, `idcliente`
- **Identidad:** `nombre_credencial` (STRING), `entorno` (STRING)
- **Estado:** `activo` (BOOLEAN)
- **Vigencia:** `fecha_expiracion` (LONG, centinela `253402300799000` = no expira)
- **Timestamp:** `fecha_actualizacion` (LONG)

**Este módulo solo cambia `activo`** (a `false` al revocar o al suspender en cascada; a `true` al restituir). La **creación** del reemplazo la ejecuta el servicio de emisión de #07 (`research.md` Decision 3).

**Las tres razones de `activo=false` son indistinguibles en esta tabla** — de ahí que el conjunto restituible se reconstruya desde la bitácora:

| Razón | Quién la produjo | ¿Se restituye al reactivar? |
|---|---|---|
| Revocada por el partner | este módulo (RF-PAC-001) | **Nunca** |
| Desactivada por cascada | este módulo (RF-PAC-006) | **Sí** |
| Expirada por tiempo | #07 (RF-PON-006) | **No** |

### 3) `Fact_HistorialAccesoPartner` (bitácora inmutable — **y fuente de la reactivación**)

- **PK:** `idhistorial` (INT)
- **FKs:** `idpartner`, `idcredencial` (centinela `-1` cuando el evento es del partner en general)
- **Evento:** `tipo_cambio`, `ejecutado_por`, `motivo`, `estado_anterior`, `estado_nuevo`
- **Timestamp:** `fecha_cambio` (LONG)

**Solo INSERT.** Nunca UPDATE ni DELETE (RN-PAC-013).

**Los seis `tipo_cambio` que escribe este módulo:**

| `tipo_cambio` | `idcredencial` | `ejecutado_por` | Cambia `Dim_Partner.activo` |
|---|---|---|---|
| `revocacion_credencial` | la revocada | `Partner` | No |
| `desactivacion_por_cascada` | **cada** desactivada | `Sistema` / `Administrador` | No (lo hace el evento de suspensión) |
| `aviso_previo_suspension` | `-1` | `Sistema` | **No** — el aviso no cambia el estado |
| `suspension_automatica` | `-1` | `Sistema` | Sí → `false` |
| `suspension_manual` | `-1` | `Administrador` | Sí → `false` |
| `reactivacion` | `-1` | `Administrador` | Sí → `true` |

> **`desactivacion_por_cascada` ≠ `revocacion_credencial`.** El primero se revierte al reactivar; el segundo **nunca**. Son tipos distintos precisamente para que la reactivación no pueda confundirlos (§ 15 D1).

**Esta tabla no es solo auditoría: es la fuente operativa de la reactivación.** Es la única razón por la que la restitución selectiva es posible sin columnas nuevas.

## Dimensiones de lectura (no escritas por este módulo)

| Tabla | Uso | Campo clave |
|---|---|---|
| `Fact_Factura` | Determinar la mora | `tipo='excedente_api'`, `estado_pago`, `fecha_vencimiento` |
| `Fact_Suscripcion` | **No se lee aquí** | La vigencia de suscripción la comprueba #08 (§ 15 D2) |

## Estados

### Estado de acceso del partner

| Estado | `Dim_Partner.activo` | Persistido | Cómo se sale |
|---|---|---|---|
| **Activo** | `true` | Sí | Suspensión automática o manual |
| **En mora, avisado** | `true` | **No — derivado** | Regularizar, o superar el límite |
| **Suspendido** | `false` | Sí | **Solo** reactivación manual (RN-PAC-009) |

«En mora, avisado» se deriva de la existencia de facturas impagadas más los avisos ya registrados en la bitácora. **No hay columna para él**, y no debe crearse: sería una segunda verdad frente a `activo`.

### Flujo de la revocación (RF-PAC-001 + RF-PAC-002)

```
POST /credenciales/{id}/revocar
   │
   ├─ 1. ¿La credencial pertenece a quien la revoca?    no ──► 403
   ├─ 2. ¿Está ya inactiva?                             sí ──► 409 (sin escribir)
   │
   ├─ 3. Dim_CredencialAPI.activo = false
   ├─ 4. Lista de denegación en memoria += client_id     ← cierra la ventana de
   │        (TTL 60 s, research.md Decision 2)             ingesta de 5–15 s
   │
   ├─ 5. Emitir reemplazo (servicio de #07): mismo entorno, MISMO NOMBRE
   │        la unicidad de nombre excluye la recién revocada, conocida EN MEMORIA
   │        (nunca releer Pinot: aún la vería activa y daría colisión falsa)
   │
   ├─ 6. Bitácora: tipo_cambio="revocacion_credencial", idcredencial = la revocada
   │
   └─ 7. Respuesta: la revocada + el reemplazo con su secreto (UNA sola vez)
            Las demás credenciales del partner NO se tocan (RN-PAC-005)
```

### Flujo de suspensión y reactivación (RF-PAC-004 a RF-PAC-006)

```
SUSPENSIÓN (automática por mora, o manual por el Administrador)
   │
   ├─ 1. Leer las credenciales ACTIVAS del partner        ← lectura previa; nada
   │                                                         se ha escrito aún
   ├─ 2. Por CADA una: activo=false
   │        + fila de bitácora `desactivacion_por_cascada` con su idcredencial
   │        (esta lista ES lo que permitirá la reactivación selectiva)
   │
   ├─ 3. Dim_Partner: activo=false, fecha_suspension, motivo_suspension
   └─ 4. Bitácora: `suspension_automatica` | `suspension_manual`, idcredencial=-1

        Las credenciales ya inactivas (revocadas o expiradas) NO generan fila:
        por eso la reactivación no las encontrará.

REACTIVACIÓN (solo Administrador — el sistema nunca reactiva solo)
   │
   ├─ 1. ¿El partner está suspendido?    no ──► 409 (sin escribir)
   ├─ 2. Leer las filas `desactivacion_por_cascada` del ÚLTIMO evento de suspensión
   ├─ 3. Restituir activo=true SOLO en esas credenciales
   ├─ 4. Dim_Partner: activo=true, snapshot de suspensión al centinela vacío
   └─ 5. Bitácora: `reactivacion`, idcredencial=-1
```

## Validaciones de dominio

| Validación | RF / RN | Respuesta |
|---|---|---|
| La credencial pertenece a quien la revoca | RN-PAC-002 | 403 |
| La credencial no está ya inactiva | RN-PAC-003 | 409 |
| `motivo` no vacío al revocar | RF-PAC-001 | 400 |
| `motivo` no vacío al suspender manualmente | RF-PAC-005 | 400 |
| Solo Administrador suspende o reactiva | RF-PAC-005 | 403 |
| El partner está suspendido antes de reactivar | RF-PAC-005 | 409 |
| El partner no está ya suspendido antes de suspender | RF-PAC-005 | 409 |
| El partner consulta su propio estado | RN-PAC-016 | 403 |
| Factura en disputa excluida de la mora | RN-PAC-015 | — (regla del job) |

## Eventos Kafka (escritura)

| Topic | Disparadores | Frecuencia |
|---|---|---|
| `Dim_CredencialAPI_topic` | Revocación, cascada de suspensión, restitución | Baja |
| `Dim_Partner_topic` | Suspensión y reactivación | Muy baja |
| `Fact_HistorialAccesoPartner_topic` | Los seis `tipo_cambio` | Baja; **N filas** en cada cascada |

> **Retraso de ingesta 5–15 s.** Afecta a este módulo de dos formas que el diseño ya resuelve: la **ventana de exposición** tras revocar (lista de denegación, Decision 2) y la **colisión falsa de nombre** al emitir el reemplazo (comprobación en memoria, Decision 4).

## Auditoría

`Fact_HistorialAccesoPartner` cumple aquí **doble función**: es la auditoría exigida por RF-O55.4 (cada acción con motivo, autor y fecha) **y** el mecanismo operativo de la reactivación selectiva. Por eso su inmutabilidad no es solo una buena práctica: si se pudiera editar, se podría alterar qué credenciales se restituyen.

## Mapeo API ↔ persistencia

| Endpoint | Tablas |
|---|---|
| `POST /credenciales/{id}/revocar` | `Dim_CredencialAPI` (×2: revocada + reemplazo), `Fact_HistorialAccesoPartner` |
| `POST /partners/{id}/suspender` | `Dim_Partner`, `Dim_CredencialAPI` (×N), `Fact_HistorialAccesoPartner` (×N+1) |
| `POST /partners/{id}/reactivar` | `Dim_Partner`, `Dim_CredencialAPI` (×N), `Fact_HistorialAccesoPartner` |
| `GET /partners/{id}/estado-acceso` | solo lectura |
| *(job)* evaluación de mora | lee `Fact_Factura`; escribe bitácora y, al suspender, lo del flujo de suspensión |

## Fuera de este modelo

`Dim_Partner` en su alta y su plan, y la **creación** de credenciales, pertenecen a #07. Las tablas de consumo (`Fact_APIIntegracion`, `Fact_LogLlamadaAPI`) y la emisión de facturas pertenecen a #08 y a Suscripciones. `Fact_Suscripcion` la comprueba #08, no este módulo (§ 15 D2).
