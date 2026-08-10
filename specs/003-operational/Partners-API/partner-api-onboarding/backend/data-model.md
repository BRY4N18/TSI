# Data Model — Onboarding de Partners API

> Los cambios de esquema de este documento **ya están aplicados y verificados** contra el Pinot en ejecución (`database/verifica_partners.py`, 16/16). Ver `spec.md` § 15 D1 y D2.

## Nota transversal: Pinot no almacena `NULL`

Ninguna de las 79 tablas habilita `nullHandlingEnabled`, así que **todo valor ausente se materializa como un centinela**. Este módulo los declara explícitamente (`defaultNullValue`) en vez de aceptar los que elige Pinot, porque los suyos rompían reglas de negocio: `planapi` ausente se guardaba como el string `'null'` —dejando **siempre cierta** la guarda de RF-PON-004— y `fecha_expiracion` ausente como `Long.MIN_VALUE`, lo que habría hecho que el job de expiración revocara **todas** las credenciales de producción.

**Regla de diseño para todo este módulo: ninguna consulta usa `IS NULL`.** Las guardas comparan contra el centinela.

## Entidades principales

### 1) `Dim_Partner` (núcleo del módulo)

- **PK:** `idpartner` (INT)
- **FK:** `idcliente` → `Dim_Cliente` (**obligatorio, no nulo** — un partner sin cliente detrás no existe, RN-PON-001)
- **Identidad:** `nombrepartner`, `contacto_tecnico_nombre`, `contacto_tecnico_gmail`
- **Plan y cupo:** `planapi` (STRING), `limitellamadasmes` (INT), `limitellamadasminuto` (INT) — congelados desde `Dim_Plan.limites` al asignar (RN-PON-003)
- **Snapshot de pruebas:** `sandbox_activado`, `sandbox_expiracion` (LONG) — **solo de la primera activación**; la vigencia real vive por credencial
- **Estado operativo:** `activo` (BOOLEAN) — **única fuente de verdad** (RN-PON-009)
- **Snapshot de suspensión:** `fecha_suspension`, `motivo_suspension` — resumen del último evento, **no** historial paralelo. Escritos por CU-O55, no por este módulo
- **Timestamp:** `fecha_actualizacion` (LONG) — `timeColumnName` y `comparisonColumn` del upsert

| Centinela | Columna | Significa |
|---|---|---|
| `""` | `planapi` | sin plan asignado — guarda de RF-PON-004: `planapi <> ''` |
| `-1` | `limitellamadasmes`, `limitellamadasminuto` | sin cupo asignado (`0` sería un cupo válido) |
| `0` | `sandbox_activado`, `sandbox_expiracion` | nunca activó pruebas |
| `""` | `fecha_suspension`, `motivo_suspension` | no suspendido |

**Reglas:**
- Un solo partner por cliente (RN-PON-002), validado a nivel de aplicación.
- Ninguna acción de habilitación procede con `activo=false` (RN-PON-013).
- `fecha_actualizacion` **debe avanzar en cada escritura**: es la columna de comparación del upsert.

### 2) `Dim_CredencialAPI` (una fila por credencial concreta)

- **PK:** `idcredencial` (INT)
- **FKs:** `idpartner` → `Dim_Partner`, `idcliente` → `Dim_Cliente`
- **Identidad:** `nombre_credencial` (STRING, **columna nueva**) — identifica el sistema que la usa (RF-O49.1)
- **Entorno:** `entorno` (STRING: `Sandbox` | `Producción`)
- **Secreto:** `client_secret_hash` (STRING) — **bcrypt, nunca el valor en claro** (RNF-PON-002)
- **Vigencia:** `fecha_expiracion` (LONG, **columna nueva**), `fecha_creacion` (LONG)
- **Control:** `activo` (BOOLEAN)
- **Timestamp:** `fecha_actualizacion` (LONG) — `timeColumnName` y `comparisonColumn`

| Centinela | Columna | Significa |
|---|---|---|
| `253402300799000` (9999-12-31) | `fecha_expiracion` | **no expira nunca** — en el futuro a propósito, para que `fecha_expiracion < ahora` encuentre solo las realmente vencidas sin excluir producción a mano |
| `""` | `nombre_credencial` | — |

**Reglas:**
- Varias credenciales activas por entorno; `nombre_credencial` único **entre las activas** del mismo partner y entorno (RN-PON-014). Un nombre liberado por revocación o expiración se reutiliza.
- Pruebas y producción **coexisten** (RN-PON-008): toda operación va calificada por `entorno`.
- El secreto se entrega una sola vez, en la respuesta de creación (RN-PON-005). **No viaja al topic Kafka**: al evento solo va el hash.
- Producción no expira por tiempo; se corta por revocación o suspensión (CU-O55).

### 3) `Fact_HistorialAccesoPartner` (bitácora inmutable)

- **PK:** `idhistorial` (INT)
- **FKs:** `idpartner`, `idcredencial` (opcional)
- **Evento:** `tipo_cambio`, `ejecutado_por`, `motivo`, `estado_anterior`, `estado_nuevo`
- **Timestamp:** `fecha_cambio` (LONG)

| Centinela | Columna | Significa |
|---|---|---|
| `-1` | `idcredencial` | evento sobre el partner en general, no sobre una credencial |
| `""` | `motivo`, `estado_anterior` | sin motivo / sin estado previo (registro inicial) |

**Reglas:**
- **Solo INSERT.** Nunca UPDATE ni DELETE (RN-PON-010). Cada evento es una fila nueva con `fecha_cambio` creciente.
- Valores de `tipo_cambio` que **este módulo** escribe:

  | `tipo_cambio` | Origen | `idcredencial` |
  |---|---|---|
  | `registro` | RF-PON-001 | `-1` |
  | `asignacion_plan` | RF-PON-003 | `-1` |
  | `activacion_sandbox` | RF-PON-004 | la emitida |
  | `expiracion_sandbox` | RF-PON-006 | la vencida |
  | `solicitud_promocion_produccion` | RF-PON-007 | `-1` |
  | `activacion_produccion` | RF-PON-008 (aprobar) | la emitida |
  | `rechazo_promocion_produccion` | RF-PON-008 (rechazar) | `-1` |

  `revocacion_credencial`, `aviso_previo_suspension`, `suspension_automatica`, `suspension_manual` y `reactivacion` pertenecen a **CU-O55** (`partner-access-management`).

### 4) `Dim_VersionContratoAPI` (catálogo de versiones — tabla nueva, CU-O50)

- **PK:** `idversion` (INT)
- **FK:** `id_servicio` → `Dim_Servicio` (**obligatorio**)
- **Versión:** `version` (STRING), `estado` (STRING: `vigente` | `soportada` | `retirada`), `spec_url` (STRING)
- **Fechas:** `fecha_publicacion`, `fecha_retiro` (LONG)
- **Control:** `activo` (BOOLEAN), `fecha_actualizacion` (LONG)

| Centinela | Columna | Significa |
|---|---|---|
| `""` | `spec_url` | sin URL explícita (se deriva del path) |
| `0` | `fecha_retiro` | sin fecha de retiro planificada |

**Reglas:**
- **El versionado es por servicio, no global.** `Dim_Servicio` contiene hoy tres entradas (*API Despacho*, *API Registro de accidentes*, *Portal Cliente*): sin la FK, las tres colapsarían en una sola línea temporal.
- Clave natural (`id_servicio`, `version`) única entre filas con `activo=true`.
- **Máximo una versión `vigente` por servicio.** Publicar una nueva pasa la anterior a `soportada` en la misma operación.
- Ninguna versión pasa a `retirada` sin `fecha_retiro` publicada previamente (RN-PON-012).
- `activo` y `estado` **no son redundantes**: `activo` es la baja lógica de la fila (RNF-14); `estado` es el ciclo de vida de la versión. Una versión `retirada` conserva `activo=true` para que su historial siga consultable.

## Dimensiones de lectura (join, no escritas por este módulo)

| Dimensión | Uso en el módulo |
|---|---|
| `Dim_Cliente` | Existencia del cliente antes de registrar (RF-PON-001) |
| `Fact_Suscripcion` | Vigencia de la suscripción (RN-PON-011) y resolución de `idplan` |
| `Dim_Plan` | Origen del cupo: `limites.api_calls_mes` / `api_calls_minuto` (RN-PON-003) |
| `Dim_Servicio` | Catálogo referenciado por `Dim_VersionContratoAPI` |

## Estados del partner (derivados, no persistidos)

El estado **no es una columna**: se deriva de `Dim_Partner` (`activo`, `planapi`) y del último evento de `Fact_HistorialAccesoPartner`.

```text
Registrado ──RF-PON-003──► Plan asignado ──RF-PON-004──► Pruebas activo
                                                              │  ▲
                                                RF-PON-007────┘  │
                                                              ▼  │
                                                Pendiente de aprobación
                                                     │            │
                                     RF-PON-008 aprobar           │ RF-PON-008 rechazar
                                                     ▼            │  (motivo obligatorio,
                                              Producción activa ──┘   sin tope de reintentos)
```

| Estado | Se deriva de |
|---|---|
| Registrado | `activo=true` y `planapi = ''` |
| Plan asignado | `planapi <> ''` y sin evento `activacion_sandbox` |
| Pruebas activo | existe o existió una credencial `Sandbox`; último evento ≠ solicitud pendiente |
| Pendiente de aprobación | último evento = `solicitud_promocion_produccion` |
| Producción activa | existe credencial `Producción` con `activo=true` |
| Suspendido | `activo=false` — **lo escribe CU-O55**, aquí solo se lee para bloquear (RN-PON-013) |

La expiración de una credencial de pruebas (RF-PON-006) **no** es una transición del partner: desactiva la credencial y lo deja en «Plan asignado» efectivo, desde donde puede volver a emitir.

## Validaciones de dominio

| Validación | RF / RN | Bloqueante | Respuesta |
|---|---|---|---|
| Cliente existe en `Dim_Cliente` | RF-PON-001 | Sí | 404 |
| Cliente tiene suscripción vigente | RN-PON-011 | Sí | 422 |
| Cliente sin partner previo | RN-PON-002 | Sí | 409 (+ `idpartner` existente) |
| `contacto_tecnico_gmail` con formato válido | RF-PON-001 | Sí | 400 |
| `limites` declara `api_calls_mes` y `api_calls_minuto` | RF-PON-003 | Sí | 422 |
| Partner con `activo=true` | RN-PON-013 | Sí | 409 |
| `planapi <> ''` antes de emitir | RF-PON-004 | Sí | 409 |
| `nombre_credencial` no vacío y no duplicado entre activas | RN-PON-014 | Sí | 400 / 409 |
| Estado «Pruebas activo» antes de solicitar producción | RN-PON-004 | Sí | 409 |
| Estado «Pendiente de aprobación» antes de resolver | RF-PON-008 | Sí | 409 |
| `motivo` no vacío al rechazar | RN-PON-007 | Sí | 422 |
| Propiedad: el partner opera sobre su propio perfil | Decision 4 | Sí | 403 |

Ninguna validación de este módulo es «advertencia no bloqueante»: a diferencia de `registro-accidente`, aquí no hay urgencia operativa que justifique forzar. El partner puede reintentar.

## Eventos Kafka (escritura)

| Topic | Disparadores |
|---|---|
| `Dim_Partner_topic` | Registro (RF-PON-001), asignación de plan (RF-PON-003), snapshot de primera activación (RF-PON-004) |
| `Dim_CredencialAPI_topic` | Emisión de credencial (RF-PON-004, RF-PON-008), expiración (RF-PON-006) |
| `Fact_HistorialAccesoPartner_topic` | Los siete `tipo_cambio` de la tabla de arriba |
| `Dim_VersionContratoAPI_topic` | Alta y cambio de estado de una versión (CU-O50) |

> **El secreto en claro nunca viaja en un evento.** Al topic solo va `client_secret_hash`.

> **Retraso de ingesta 5–15 s.** Ningún servicio relee de Pinot lo que acaba de escribir; la respuesta se construye con los valores en memoria (`research.md` Decision 3).

Lecturas: queries Pinot vía repositorios en `core/repositories/partners/`.

## Auditoría (RNF-PON-004)

El 100 % de las acciones deja rastro en `Fact_HistorialAccesoPartner` con autor, acción, motivo y fecha. Además, log estructurado por acción con `idpartner`, `idusuario`, timestamp y campos modificados.

**Nunca se registra:** el secreto en claro, ni siquiera parcialmente o en mensajes de error.

## Mapeo API ↔ persistencia

| Endpoint | Tablas afectadas |
|---|---|
| `POST /partners` | `Dim_Partner`, `Fact_HistorialAccesoPartner` |
| `POST /partners/{id}/plan-acceso` | `Dim_Partner`, `Fact_HistorialAccesoPartner` |
| `POST /partners/{id}/credenciales` | `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner`, `Dim_Partner` (solo 1ª activación) |
| `POST /partners/{id}/solicitud-produccion` | `Fact_HistorialAccesoPartner` |
| `POST /partners/{id}/solicitud-produccion/resolucion` | `Dim_CredencialAPI` (si aprueba), `Fact_HistorialAccesoPartner` |
| `GET /partners`, `GET /partners/{id}` | solo lectura |
| `GET /contrato-integracion` | solo lectura (`Dim_VersionContratoAPI` ⋈ `Dim_Servicio`) |

## Fuera de este modelo

`Fact_APIIntegracion`, `Fact_LogLlamadaAPI` y `Dim_EstadoIntegracion` pertenecen a `api-monitoring-and-billing`. `Fact_Factura` (incluida la columna `tipo`, ya añadida) se escribe en `subscriptions-and-billing`. `Fact_Reclamo` (disputas, con `idfactura` ya migrado a STRING) pertenece a `gestion-tickets-soporte`.
