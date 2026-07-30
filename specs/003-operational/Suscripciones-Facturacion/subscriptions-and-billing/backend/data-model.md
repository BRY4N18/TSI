# Data Model — Suscripciones y Facturación

Esquemas alineados a la spec v1 clarificada y a campos ya presentes en fixtures (`backend/conftest.py`). Donde el fixture legacy difiere (p. ej. `estado: "activa"`), **gana el canon Title Case** de la spec; actualizar fixtures en implementación.

## Convención temporal Kafka → Pinot (canónica)

Todas las columnas de tiempo / upsert de este módulo (`fecha_actualizacion`, `fecha_inicio`, `fecha_fin`, `fecha_emision`, `fecha_vencimiento`, `fecha_solicitud`, `fecha_resolucion`, `fechacancelacion`, `fechaexpiracion`) se publican a Kafka como **LONG epoch milliseconds** (`1:MILLISECONDS:EPOCH`), alineado a los schemas Pinot REALTIME. **No** usar ISO-8601 string en esos campos.

---

## Entidades principales (escritura vía Kafka)

### 1) `Dim_Plan`

- **PK:** `idplan`
- **Campos:** `nombre` (STRING), `precio` (DOUBLE, USD), `limites` (STRING JSON — ver RN-SUSF-019), `nivel` (STRING: `Básico` \| `Profesional` \| `Empresarial`), `activo` (BOOLEAN)
- **Upsert / time column:** `fecha_actualizacion` (LONG ms)
- **Topic:** `Dim_Plan_topic`
- **Reglas:** nunca delete físico; desactivar con `activo=false` (RN-SUSF-001). Severidad operativa se **deriva** de `nivel` (RN-SUSF-002), no hay columna `severidad_permitida`.
- **Actor de mutación (Session 2026-07-30):** solo Director de Estrategia (`DirectorEstrategia`). El esquema y topic **no cambian**.

### 2) `Dim_MetodoPago`

- **PK:** `idmetodopago`
- **FK:** `idcliente` → `Dim_Cliente`
- **Campos:** `tipo` (`tarjeta` \| `transferencia` \| `paypal`), `tokenpasarela` (STRING opaco), `ultimosdigitos` (STRING ≤4), `fechaexpiracion` (LONG ms), `activo` (BOOLEAN)
- **Upsert:** `fecha_actualizacion` (LONG ms)
- **Topic:** `Dim_MetodoPago_topic`
- **Reglas:** máx. un `activo=true` por `idcliente` (RN-SUSF-003); nunca PAN/CVV (RN-SUSF-004).

### 3) `Fact_Suscripcion`

- **PK:** `id_suscripcion`
- **FKs:** `idcliente` → `Dim_Cliente`, `idplan` → `Dim_Plan`
- **Campos:** `estado` (`Activa` \| `Suspendida` \| `Cancelada`), `activo` (BOOLEAN), `renovacionautomatica` (BOOLEAN), `precio` (DOUBLE), `motivocancelacion`, `fechacancelacion` (LONG ms \| null), `fecha_inicio` (LONG ms), `fecha_fin` (LONG ms)
- **Upsert:** `fecha_actualizacion` (LONG ms; columna tiempo Pinot puede ser `fecha_inicio`)
- **Topic:** `Fact_Suscripcion_topic`
- **Reglas:**
  - Máx. una fila `activo=true` por cliente (RN-SUSF-020).
  - Acceso = RN-SUSF-017.
  - `Vencida` no se persiste (RN-SUSF-016).
  - Post-`Cancelada` y `now > fecha_fin` → job escribe `activo=false`.

### 4) `Fact_Factura`

- **PK:** `id_factura` (UUID STRING)
- **FKs:** `id_cliente`, `id_suscripcion`, `idmetodopago`
- **Campos:** `numero_factura` (`FAC-{YYYYMM}-{seq8}`), `periodo` (`YYYY-MM`), `estado_pago` (`Pendiente` \| `Pagada` \| `Fallida`), `desglose_cargos` (JSON STRING), `monto_base`, `impuestos` (siempre `0` en v1), `monto_total`, `fecha_emision` (LONG ms), `fecha_vencimiento` (LONG ms), `reintentos` (INT), `resultado_ultimo_reintento`
- **NC (fuera de alcance v1):** `es_nota_credito=false`, `id_factura_original=NULL`, `motivo_anulacion=NULL`
- **Upsert:** `fecha_actualizacion` (LONG ms; tiempo Pinot: `fecha_emision`)
- **Topic:** `Fact_Factura_topic`
- **Reglas:** una por (`id_suscripcion`,`periodo`) (RN-SUSF-007); dunning RN-SUSF-008/009; factura vigente RN-SUSF-027.

### 5) `Fact_Solicitud_Cambio_Plan`

- **PK:** `idsolicitud`
- **FKs:** `idcliente`, `idplanactual`, `idplansolicitado`, `idadminaprobador` (nullable)
- **Campos:** `estado` (`Pendiente` \| `Aprobada` \| `Rechazada`), `motivo`, `motivo_rechazo`, `fecha_solicitud` (LONG ms), `fecha_resolucion` (LONG ms \| null)
- **Upsert:** `fecha_actualizacion` (LONG ms; tiempo Pinot: `fecha_solicitud`)
- **Topic:** `Fact_Solicitud_Cambio_Plan_topic`
- **Reglas:** máx. una `Pendiente` por cliente (RN-SUSF-023); upgrade/downgrade por `nivel` (RN-SUSF-005).

## Entidades tocadas (otros módulos)

| Entidad | Uso |
|---------|-----|
| `Dim_Cliente` | Precondición de alta; escritura denormalizada `plan_suscripcion` = `Dim_Plan.nombre` |
| `Dim_Usuarios` / `Dim_Rol` | JWT claims → Proveedor vs Administrador vs `DirectorEstrategia` |

## Transiciones de estado

### `Fact_Suscripcion.estado`

```text
(alta RF-010) → Activa
Activa → Suspendida     (factura vigente Fallida)
Suspendida → Activa     (cobro regularización OK)
Activa|Suspendida → Cancelada  (RF-009)
Cancelada + now>fecha_fin → activo=false (mantenimiento)
```

### `Fact_Factura.estado_pago`

```text
Pendiente → Pagada
Pendiente → Fallida     (reintentos=3)
Fallida → Pendiente     (regularización) → Pagada|Fallida
```

### `Fact_Solicitud_Cambio_Plan.estado`

```text
Pendiente → Aprobada    (upgrade auto o admin)
Pendiente → Rechazada   (admin)
```

## Eventos Kafka

| Topic | Productor | Disparador |
|-------|-----------|------------|
| `Dim_Plan_topic` | `PlanRepository` | RF-001 |
| `Dim_MetodoPago_topic` | `MetodoPagoRepository` | RF-002 |
| `Fact_Suscripcion_topic` | `SuscripcionRepository` | RF-010, 003, 007, 008, 009, job mantenimiento |
| `Fact_Factura_topic` | `FacturaRepository` | RF-004, 005, 007, 008 |
| `Fact_Solicitud_Cambio_Plan_topic` | `SolicitudCambioPlanRepository` | RF-003 |
| `Dim_Cliente_topic` | `ClienteRepository` (patch) | RF-010, RF-003 aprobado |

## Validaciones cruzadas

- `limites` JSON mínimo: `unidades_max`, `usuarios_max`, `api_calls_mes` ≥ 0.
- Ciclo: `fecha_fin = add_calendar_months(fecha_inicio, 1)` en `America/Guayaquil`.
- Montos: `monto_total = monto_base + impuestos` con `impuestos=0`.
