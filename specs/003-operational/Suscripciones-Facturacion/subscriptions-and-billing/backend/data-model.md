# Data Model — Suscripciones y Facturación

Esquemas alineados a la spec v1 clarificada y a campos ya presentes en fixtures (`backend/conftest.py`). Donde el fixture legacy difiere (p. ej. `estado: "activa"`), **gana el canon Title Case** de la spec; actualizar fixtures en implementación.

## Convención temporal Kafka → Pinot (canónica)

Todas las columnas de tiempo / upsert de este módulo (`fecha_actualizacion`, `fecha_inicio`, `fecha_fin`, `fecha_emision`, `fecha_vencimiento`, `fecha_solicitud`, `fecha_resolucion`, `fechacancelacion`, `fechaexpiracion`) se publican a Kafka como **LONG epoch milliseconds** (`1:MILLISECONDS:EPOCH`), alineado a los schemas Pinot REALTIME. **No** usar ISO-8601 string en esos campos.

---

## Entidades principales (escritura vía Kafka)

### 1) `Dim_Plan`

- **PK:** `idplan`
- **Campos:** `nombre` (STRING), `precio` (DOUBLE, USD), `limites` (STRING JSON — ver RN-SUSF-019), `nivel` (STRING: `Básico` \| `Profesional` \| `Empresarial`), `periodicidad` (STRING: `Mensual` \| `Anual` — RN-SUSF-029, obligatorio), `severidades_desbloqueadas` (STRING JSON — lista no vacía de `idseveridad` de `Dim_Severidad`; independiente de `nivel`, RN-SUSF-002), `carga_lote_habilitada` (BOOLEAN — habilita CU-O40 de Red Operativa para proveedores en este plan; dato independiente y configurable, default `false`, RF-O26.5/RF-O40.6, corrección 2026-08-08), `activo` (BOOLEAN)
  - **`precio_excedente_llamada` (DOUBLE, añadido 2026-08-08, RN-SUSF-030):** precio unitario de cada llamada que supera el cupo de API. Distinto de `precio`, que es el importe de la suscripción. Configurable por el Director de Estrategia (CU-O26 / RF-O26.1); alimenta el cálculo de excedente de CU-O54 en `api-monitoring-and-billing`. Centinela `-1.0` = sin tarifa configurada (nunca `0.0`, que significaría excedente gratis).
- **Upsert / time column:** `fecha_actualizacion` (LONG ms)
- **Topic:** `Dim_Plan_topic`
- **Reglas:** nunca delete físico; desactivar con `activo=false` (RN-SUSF-001). `severidades_desbloqueadas` es un campo **independiente**, configurable libremente por el Director de Estrategia — no se deriva de `nivel` (corrección 2026-08-08, RN-SUSF-002). Guarda **ids de `Dim_Severidad`** desde la migración del 2026-08-11 (`database/migra_severidades_plan_a_idseveridad.py`); antes guardaba nombres de una escala paralela que no existía en el catálogo.
- **Actor de mutación (Session 2026-07-30):** solo Director de Estrategia (`DirectorEstrategia`). El esquema y topic **no cambian**.
- **Listado (RF-SUSF-001 / RNF-SUSF-005a):**
  - Orden estable: `idplan ASC`.
  - Página: `idplan > cursor` + `LIMIT limit` (default 20); `next_cursor` = último `idplan` de la página si hay más.
  - Filtros: `nombre` (~ `q`), `activo`, `nivel`.
  - **Prohibido** cargar todas las filas a memoria de aplicación para paginar (RN-SUSF-001a).
  - Detalle puntual: lectura por `idplan` (no es listado).

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
- **Campos:** `estado` (`Activa` \| `Suspendida` \| `Cancelada`), `activo` (BOOLEAN), `renovacionautomatica` (BOOLEAN), `precio` (DOUBLE), `periodicidad` (STRING: `Mensual` \| `Anual` — copiada de `Dim_Plan.periodicidad` al alta/cambio de plan, determina `fecha_fin`), `nivel` (STRING — copiado de `Dim_Plan.nivel` al alta/cambio de plan, congelado, RN-SUSF-006), `severidades_desbloqueadas` (STRING JSON — copiado de `Dim_Plan.severidades_desbloqueadas` al alta/cambio de plan, congelado, RN-SUSF-006), `carga_lote_habilitada` (BOOLEAN — copiado de `Dim_Plan.carga_lote_habilitada` al alta/cambio de plan, congelado, RN-SUSF-006; leído por Red Operativa `alta-unidades` para gatear CU-O40), `motivocancelacion`, `fechacancelacion` (LONG ms \| null), `fecha_inicio` (LONG ms), `fecha_fin` (LONG ms)
- **Upsert:** `fecha_actualizacion` (LONG ms; columna tiempo Pinot puede ser `fecha_inicio`)
- **Topic:** `Fact_Suscripcion_topic`
- **Reglas:**
  - Máx. una fila `activo=true` por cliente (RN-SUSF-020).
  - Acceso = RN-SUSF-017.
  - `Vencida` no se persiste (RN-SUSF-016).
  - Post-`Cancelada` y `now > fecha_fin` → job escribe `activo=false`.

### 4) `Fact_Factura`

- **PK:** `id_factura` (UUID STRING) — **corrección 2026-08-08:** `database/esquemas.json` declaraba esta columna como `INT`, desalineado con este documento y con el código (`FacturaRepository` siempre generó UUID). Corregido a `STRING` en el esquema; un clúster Pinot ya desplegado con el tipo viejo requiere recrear la tabla.
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

- `limites` JSON mínimo: `unidades_max`, `usuarios_max`, `api_calls_mes`, `api_calls_minuto` ≥ 0. `api_calls_minuto` añadido 2026-08-08 (RN-SUSF-019): lo exige el SRS §3.4.1 y alimenta `Dim_Partner.limitellamadasminuto` en `partner-api-onboarding`.
- Ciclo: `fecha_fin = add_calendar_months(fecha_inicio, 1)` en `America/Guayaquil`.
- Montos: `monto_total = monto_base + impuestos` con `impuestos=0`.
