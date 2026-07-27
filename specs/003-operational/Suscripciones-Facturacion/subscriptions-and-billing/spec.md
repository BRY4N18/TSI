# Especificación: Módulo Suscripciones y Facturación

**Módulo (module-map.md):** Suscripciones-Facturación
**Ruta Spec Kit (esta carpeta):** `specs/003-operational/Suscripciones-Facturacion/subscriptions-and-billing/`
**Nota de naming:** ruta canónica = esta carpeta `subscriptions-and-billing/`. El slug histórico `billing-and-auto-renewal` queda **deprecado**; las demás specs del repo deben referirse a `subscriptions-and-billing`.
**App Django:** `apps/suscripciones/` · **Módulo Angular:** `modules/suscripciones/`
**Fuente narrativa consultada:** `SuscripcionesFacturacion.md`
**Estado:** Implementado (tasks T001–T090; remediation analyze 2026-07-26 aplicada)
**Última actualización:** 2026-07-26

---

## Clarifications

### Session 2026-07-26

- Q: ¿Duración exacta del “ciclo mensual” y zona horaria de cortes? → A: Mes calendario en `America/Guayaquil`; `fecha_fin` = mismo día del mes siguiente (clamp al último día si no existe).
- Q: ¿Formato de `periodo`, `numero_factura`, impuestos y vencimiento? → A: `periodo=YYYY-MM`; `FAC-{YYYYMM}-{seq8}`; `impuestos=0` en v1; `fecha_vencimiento=fecha_emision+7d`.
- Q: ¿Sync de `Dim_Cliente.plan_suscripcion` y primera factura en alta? → A: Sync **obligatorio** del `nombre` del plan; primera factura+cobro **obligatorios** si hay método activo.
- Q: ¿Solicitudes de cambio concurrentes y cambio en `Suspendida`? → A: Máximo una solicitud `Pendiente` por cliente; cambio de plan solo si `estado="Activa"`.
- Q: ¿Quién dispara la reactivación tras actualizar método? → A: Tras RF-SUSF-002, si hay suscripción `Suspendida` con factura `Fallida`, el Sistema **debe** intentar regularización automáticamente.
- Q: ¿Qué pasa con `activo` tras cancelación vencida? → A: Job de mantenimiento pone `activo=false` cuando `Cancelada` y `now > fecha_fin`.
- Q: ¿Ventana de jobs, moneda, simulador y observabilidad? → A: Jobs 02:00–05:00 Guayaquil; USD; simulador éxito salvo fail-rate/env; métricas/logs estructurados de cobros y jobs.
- Q: ¿Forma de `desglose_cargos` y concurrencia de método de pago? → A: JSON `[{concepto,monto}]`; un solo writer lógico por `idcliente` (last-write-wins por `fecha_actualizacion`).
- Q: ¿Clave de idempotencia en reactivación con método nuevo? → A: `{id_factura}-reactivacion-{idmetodopago}` para permitir reintento limpio al cambiar método.
- Q: ¿Cómo se genera el `seq` de `numero_factura` sin BD transaccional? → A: Por `periodo`, `max(seq)+1` leído de Pinot con reintento ante colisión; `id_factura` = UUID.
- Q: ¿Qué es la “factura vigente” para mora/suspensión? → A: La del `periodo` del ciclo actual de la suscripción; si no hay, la más reciente `Fallida` por `fecha_emision`.
- Q: ¿Reintento de cobro sin cambiar método? → A: Sí — acción explícita del Proveedor “Reintentar cobro” (mismo camino RF-SUSF-007).
- Q: ¿Orden del historial de facturas? → A: Obligatorio `fecha_emision` descendente.
- Q: ¿Acceso durante dunning (`Pendiente`)? → A: Sí; solo `Fallida`→`Suspendida` corta acceso (RN-SUSF-017).
- Q: Remediation analyze (C1–C4, I1, A1, B1)? → A: Tasks T086–T090 + ClienteRepository explícito; slug cross-spec → `subscriptions-and-billing`; wrapper Soporte; RN-004↔RNF-001.

---

## 0. Nota de trazabilidad y consistencia (léase antes que el resto del documento)

### 0.1 Numeración de Casos de Uso (CU) — tabla canónica

El identificador estable de requisito en esta spec es `RF-SUSF-###`. Los códigos CU sirven solo para trazabilidad.

| RF | CU canónico (esta spec) | CU narrativo (`SuscripcionesFacturacion.md`) | Notas |
|---|---|---|---|
| RF-SUSF-001 | CU-O106 | CU-O99 | Catálogo de planes |
| RF-SUSF-002 | CU-O101 | CU-O64 | Método de pago |
| RF-SUSF-003 | CU-O104 | CU-O03 | Cambio de plan (no confundir con CU-O03 de `gestion-cuentas` = perfil) |
| RF-SUSF-004 | CU-O107 | CU-O30 | Generación de facturas |
| RF-SUSF-005 | CU-O102 | CU-O65 | Cobro automático |
| RF-SUSF-006 | CU-O108 | CU-O04 | Historial de facturas |
| RF-SUSF-007 | CU-O105 | CU-O66 | Suspensión / reactivación por mora |
| RF-SUSF-008 | CU-O109 | CU-O34 | Renovación automática |
| RF-SUSF-009 | CU-O110 | CU-O67 | Cancelación (sin par en la lista de 8 del module-map; se adopta O110) |
| RF-SUSF-010 | CU-O111 | *(ausente en narrativa)* | Alta / contratación inicial de suscripción |

**Regla:** en títulos, escenarios y trazabilidad de *este* módulo se usa solo la columna **CU canónico**. La columna narrativa queda como equivalencia histórica.

### 0.2 Correcciones de nombres (verificadas contra `data-model.md` / `tablas.json` / `esquemas.json`)

| En la narrativa | Nombre real verificado | Nota |
|---|---|---|
| `Dim_metodopago` | `Dim_MetodoPago` | Solo capitalización |
| `Dim_Plan.severidad_permitida` | `Dim_Plan.nivel` (STRING) | `nivel` ∈ {`Básico`,`Profesional`,`Empresarial`}; la severidad permitida se **deriva** por RN-SUSF-002 |

Este documento usa siempre los nombres verificados.

### 0.3 Regla de arquitectura Kafka + Pinot (escritura)

Según `infrastructure.md` (§4) y `architectural-patterns.md` (§1):

- Toda escritura publica un **evento completo** en `{NombreTabla}_topic` (no un diff).
- Pinot es de **solo lectura** desde Django; hace upsert `FULL`.
- **Columna de comparación de upsert (todas las tablas de este módulo):** `fecha_actualizacion`. Todo evento **debe** incluir `fecha_actualizacion=now` (más reciente gana).
- **Columna de tiempo Pinot** (segmentación/índice temporal) puede ser otra (`fecha_inicio`, `fecha_emision`, etc.); **no sustituye** a `fecha_actualizacion` para upsert (ver §14.1).
- No hay transacciones atómicas entre tablas (RNF-SUSF-004).

**Convención:** *"Tabla X — escribir (INSERT/UPDATE): …"* = publicar en `X_topic` el registro completo con esos campos y `fecha_actualizacion=now`.

### 0.4 Convención de valores de estado (casing)

Todos los estados persistidos usan **Title Case en español**, exactamente:

- Suscripción: `Activa` | `Suspendida` | `Cancelada`
- Factura (`estado_pago`): `Pendiente` | `Pagada` | `Fallida`
- Solicitud de cambio: `Pendiente` | `Aprobada` | `Rechazada`

`Vencida` **no** es valor persistido (ver RN-SUSF-016).

### 0.5 Regla de acceso al servicio (fuente de verdad)

El acceso del Proveedor a las capacidades de la plataforma **no** se decide solo con `Fact_Suscripcion.estado`. La regla canónica es RN-SUSF-017 (§6).

### 0.6 Tiempo, ciclo de facturación y moneda (canónico)

- **Zona horaria de negocio:** `America/Guayaquil` (UTC−5, sin DST). Todos los crons, “días” de dunning y comparaciones `now` vs `fecha_fin` usan esta zona.
- **Ciclo mensual:** mes calendario. `fecha_fin = add_calendar_months(fecha_inicio, 1)` con *clamp* al último día del mes destino si el día de `fecha_inicio` no existe (ej. 31 ene → 28/29 feb).
- **`periodo` de factura:** string `YYYY-MM` del ciclo que cubre (mes de `fecha_inicio` del ciclo facturado, en Guayaquil).
- **Moneda v1:** USD implícita en todos los montos. Sin multi-moneda.
- **Ventana de jobs batch** (facturación, dunning, renovación, mantenimiento `activo`): **02:00–05:00** America/Guayaquil.

---

## 1. Objetivo

Gestionar el ciclo de vida comercial entre un Proveedor (`Dim_Cliente`) y TSI: alta de suscripción, catálogo de planes, método de pago, cambio de plan, facturación y cobro, mora/suspensión, renovación automática y cancelación — aplicando la regla de acceso RN-SUSF-017 en todo momento.

## 2. Contexto

TSI opera como SaaS B2B. Los clientes (`Dim_Cliente`) son organizaciones que proveen unidades de emergencia y usan la plataforma según el plan contratado (Básico, Profesional, Empresarial). Este módulo sostiene esa relación económica y es dependencia de módulos operativos (Emergencias, Red-Operativa, Partners-API, Soporte).

Orden sugerido de implementación: después de Cuentas-Clientes (`incorporacion-clientes`), porque toda suscripción exige un `Dim_Cliente` existente. La asignación de plan dejó de vivir en Cuentas (O12 retirado / notas en `gestion-cuentas`); la **alta** queda aquí en RF-SUSF-010.

## 3. Actores

| Actor | Rol en este módulo |
|---|---|
| **Proveedor** | Actor operativo de `Dim_Cliente`. Gestiona método de pago, alta/cambio/cancelación de suscripción y consulta su historial. Nunca actúa sobre otro `idcliente`. |
| **Administrador** | Gestiona `Dim_Plan`, aprueba/rechaza downgrades, consulta facturación de cualquier cliente. **No** suspende ni reactiva por mora en v1 (solo el Sistema, RF-SUSF-007). |
| **Sistema** | Jobs: facturación, cobro/dunning, suspensión por mora, renovación, mantenimiento de `activo` post-cancelación. |
| **Pasarela de pago** | Externa. Hoy **simulada** (§13, RN-SUSF-024). |

> `actors.md` llama “Cliente” al mismo actor operativo. Aquí se usa **Proveedor** por consistencia con la narrativa del módulo; ambos apuntan a `Dim_Cliente`.

---

## 4. Requisitos funcionales

### RF-SUSF-010 — Contratar / alta inicial de suscripción *(CU-O111, Proveedor)*

**Descripción:** crea la primera `Fact_Suscripcion` del cliente tras existir `Dim_Cliente`. Cierra el hueco dejado por el retiro de O12 en Cuentas-Clientes.

**Precondiciones:**
- Sesión de Proveedor autorizada sobre su `idcliente`.
- `Dim_Cliente` existe.
- No existe otra `Fact_Suscripcion` del mismo `idcliente` con `activo=true` (RN-SUSF-020).
- Existe `Dim_Plan` con `activo=true` para el `idplan` elegido.

**Flujo principal:**
1. El Proveedor elige `idplan` (solo planes con `activo=true`) y confirma `renovacionautomatica` (default `true`).
2. El sistema valida precondiciones.
3. `Fact_Suscripcion` — escribir (INSERT): `id_suscripcion`, `idcliente`, `idplan`, `precio` (= `Dim_Plan.precio` al momento del alta), `estado="Activa"`, `activo=true`, `renovacionautomatica`, `fecha_inicio=now` (Guayaquil), `fecha_fin=add_calendar_months(fecha_inicio, 1)`, `motivocancelacion=NULL`, `fechacancelacion=NULL`.
4. **Obligatorio:** publicar en `Dim_Cliente_topic` actualizando `plan_suscripcion` = `Dim_Plan.nombre` del plan elegido (campo denormalizado de conveniencia). Fuente de verdad del plan vigente: `Fact_Suscripcion.idplan`.
5. Si existe método de pago `activo=true`: **debe** generar la factura del `periodo` actual (lógica RF-SUSF-004 para esta suscripción) y ejecutar RF-SUSF-005. Si no hay método: no factura; notificar para completar RF-SUSF-002 (RN-SUSF-018); suscripción queda `Activa` y el acceso sigue RN-SUSF-017.

**Efecto en el modelo de datos:** `Fact_Suscripcion_topic` + `Dim_Cliente_topic` (+ `Fact_Factura_topic` si aplica paso 5).

### RF-SUSF-001 — Gestionar catálogo de planes *(CU-O106, Administrador)*

**Descripción:** el Administrador crea, edita o desactiva planes.

**Precondiciones:** sesión Administrador autorizada.

**Flujo principal:**
1. Ingresa/edita: `nombre`, `precio` (número ≥ 0, USD), `limites` (objeto JSON, RN-SUSF-019), `nivel` ∈ {`Básico`,`Profesional`,`Empresarial`}.
2. Validación: campos obligatorios; `nivel` del enum; `limites` conforme al esquema. El orden upgrade/downgrade usa solo `nivel` (RN-SUSF-005).
3. `Dim_Plan` — escribir: esos campos + `activo=true`.

**Flujo alternativo — Desactivación:**
- `Dim_Plan` — escribir: `activo=false`. No se elimina la fila. Suscripciones que ya referencian el `idplan` no se alteran (RN-SUSF-001).

**Efecto:** `Dim_Plan_topic`.

### RF-SUSF-002 — Gestionar método de pago *(CU-O101, Proveedor)*

**Descripción:** registra o reemplaza el método principal de cobro.

**Precondiciones:** sesión Proveedor; `Dim_Cliente` existe.

**Flujo principal (alta):**
1. Ingresa `tipo` ∈ {`tarjeta`,`transferencia`,`paypal`} y datos de pasarela.
2. Tokenización externa (simulada en v1) → `tokenpasarela`, `ultimosdigitos` (máx. 4). Nunca se persiste PAN/CVV (RNF-SUSF-001 / RN-SUSF-004).
3. `Dim_MetodoPago` — escribir (INSERT): `idmetodopago`, `idcliente`, `tipo`, `tokenpasarela`, `ultimosdigitos`, `fechaexpiracion`, `activo=true`.
4. Serialización por `idcliente`: la aplicación no permite dos altas concurrentes del mismo cliente; si hubiera carrera, Pinot resuelve por `fecha_actualizacion` más reciente y RN-SUSF-003 se reafirma leyendo y corrigiendo (como máximo un `activo=true`).

**Flujo alternativo — Reemplazo:**
1. Alta del nuevo método como arriba.
2. Sobre el método anterior con `activo=true`: escribir `activo=false` (no delete). Queda exactamente un `activo=true` (RN-SUSF-003).

**Postcondición — reactivación automática (RN-SUSF-021):**
Si el cliente tiene `Fact_Suscripcion` con `activo=true` y `estado="Suspendida"`, y existe factura asociada con `estado_pago="Fallida"`, el Sistema **debe** invocar de inmediato el camino de regularización de RF-SUSF-007 (sin espera a cron).

**Efecto:** `Dim_MetodoPago_topic` (uno o dos eventos) (+ posible RF-SUSF-007).

### RF-SUSF-003 — Solicitar / resolver cambio de plan *(CU-O104, Proveedor; Administrador en downgrade)*

**Descripción:** upgrade o downgrade sobre una suscripción ya existente (creada por RF-SUSF-010).

**Precondiciones:**
- `Fact_Suscripcion` con `activo=true` y `estado="Activa"` (RN-SUSF-022: no se cambia plan si `Suspendida` o `Cancelada`).
- No existe otra `Fact_Solicitud_Cambio_Plan` del mismo `idcliente` con `estado="Pendiente"` (RN-SUSF-023).

**Flujo principal:**
1. Lectura: suscripción actual + planes `activo=true` + uso vs `limites`.
2. Proveedor elige `idplansolicitado` y `motivo`.
3. Clasificación upgrade/downgrade **solo por orden de `nivel`** (RN-SUSF-005): `Básico` < `Profesional` < `Empresarial`. Mismo `nivel` + distinto `idplan` ⇒ downgrade (aprobación). Mismo `idplan` ⇒ error de validación.
4. `Fact_Solicitud_Cambio_Plan` — escribir (INSERT): `estado="Pendiente"`, `idplanactual`, `idplansolicitado`, `motivo`, `fecha_solicitud=now`.

**Flujo A — Upgrade (autoaprobado):**
5. Solicitud → `estado="Aprobada"`, `idadminaprobador=NULL`, `fecha_resolucion=now`.
6. `Fact_Suscripcion` — escribir de inmediato: `idplan=idplansolicitado`, `precio=<Dim_Plan.precio del nuevo plan>`.
7. `Dim_Cliente.plan_suscripcion` — escribir el `nombre` del nuevo plan.
8. **Efecto económico (RN-SUSF-006):** no se modifica ni regenera ninguna `Fact_Factura` del ciclo en curso; la nueva tarifa aplica solo a facturas generadas **después** de esta aprobación. Sin prorrateo.

**Flujo B — Downgrade:**
5. Permanece `Pendiente` hasta resolución administrativa.
6. Aprobación: mismo efecto que A pasos 5–8, con `idadminaprobador` del admin.
7. Rechazo: solicitud → `Rechazada` + `motivo_rechazo`; **no** se toca `Fact_Suscripcion` ni `Dim_Cliente`.

**Efecto:** `Fact_Solicitud_Cambio_Plan_topic` y, si aprueba, `Fact_Suscripcion_topic` + `Dim_Cliente_topic`.

### RF-SUSF-004 — Generar facturas mensuales *(CU-O107, Sistema)*

**Descripción:** batch de cierre de período: crea el documento de factura; **no cobra** (el cobro es RF-SUSF-005).

**Precondiciones:** job dentro de la ventana 02:00–05:00 America/Guayaquil.

**Elegibilidad por suscripción:**
- `estado="Activa"` y `activo=true`.
- Aún no existe `Fact_Factura` para el mismo `id_suscripcion` + `periodo` (RN-SUSF-007).
- Existe al menos un `Dim_MetodoPago` del cliente con `activo=true` (RN-SUSF-018). Si no: **no** crear factura; notificar al Proveedor; no suspender solo por esa causa.

**Cálculo de montos (v1):**
- `monto_base` = `Fact_Suscripcion.precio`
- `impuestos` = `0` (IVA/retenciones fuera de alcance v1; campo presente en esquema pero siempre cero)
- `monto_total` = `monto_base + impuestos`
- `desglose_cargos` = `[{"concepto":"Suscripcion plan <nombre>","monto":<monto_base>}]`
- `id_factura` = UUID v4 (PK).
- `numero_factura` = `FAC-{YYYYMM}-{seq}` donde `YYYYMM` deriva de `periodo` y `seq` es entero decimal de 8 dígitos **único por `periodo`**, monotónico: leer de Pinot el máximo `seq` ya emitido para ese `YYYYMM`, sumar 1; si al publicar se detecta colisión de `numero_factura`, reintentar con `max+1` (RN-SUSF-026).
- `fecha_vencimiento` = `fecha_emision + 7 días` (calendario Guayaquil), alineado al último reintento de dunning

**Flujo:**
1. Leer elegibles.
2. Por cada una: `Fact_Factura` — escribir (INSERT) con los campos anteriores + `id_factura`, `id_cliente`, `id_suscripcion`, `idmetodopago` (método `activo=true`), `periodo` (`YYYY-MM`), `estado_pago="Pendiente"`, `reintentos=0`, `resultado_ultimo_reintento=NULL`, `es_nota_credito=false`, `id_factura_original=NULL`, `motivo_anulacion=NULL`.
3. Tras crear cada factura, invocar RF-SUSF-005 (intento día 0).

**Efecto:** `Fact_Factura_topic` (+ efectos de RF-SUSF-005).

### RF-SUSF-005 — Cobro automático *(CU-O102, Sistema)*

**Descripción:** un intento de cobro contra la pasarela para una factura `Pendiente`. Disparadores: RF-SUSF-004, RF-SUSF-008, reintentos de dunning, o regularización (RF-SUSF-007).

**Precondiciones:** `Fact_Factura.estado_pago="Pendiente"`.

**Flujo:**
1. Leer factura + método: preferir `idmetodopago` de la factura si sigue activo; si no, el `activo=true` actual. Sin método activo ⇒ fallo con motivo `SIN_METODO_PAGO`.
2. Llamada a pasarela con idempotencia `{id_factura}-{reintentos}` (RNF-SUSF-003), usando el `reintentos` **antes** del intento.

**A — Éxito:**
3. Factura → `estado_pago="Pagada"`, `resultado_ultimo_reintento="Exitoso"`.

**B — Fallo:**
3. `reintentos = reintentos + 1`; guardar `resultado_ultimo_reintento`.
4. Si `reintentos < 3`: sigue `Pendiente`; programar reintento (día 3 o día 7 desde `fecha_emision`, RN-SUSF-008).
5. Si `reintentos = 3`: `estado_pago="Fallida"` e invocar RF-SUSF-007 (suspensión).
6. Notificar al Proveedor (revisar método de pago).

**Efecto:** `Fact_Factura_topic` por intento (+ posible RF-SUSF-007).

### RF-SUSF-006 — Consultar historial de facturas *(CU-O108, Proveedor / Administrador)*

**Descripción:** solo lectura.

1. Filtrar `Fact_Factura` por `id_cliente`, orden **obligatorio** `fecha_emision` descendente.
2. Join lectura con `Dim_MetodoPago` para mostrar método usado/intentado.
3. Proveedor: solo su `idcliente`. Administrador: cualquiera (RNF-SUSF-002).

**Estados UX mínimos (RNF-SUSF-006):**
- Vacío: mensaje “No hay facturas aún”; CTA a método de pago si no hay ninguno activo, o a alta de plan si no hay suscripción.
- Carga: indicador de progreso.
- Error de red/autorización: mensaje accionable sin exponer detalles internos.

**Efecto:** ninguno.

### RF-SUSF-007 — Suspensión y reactivación por mora *(CU-O105, Sistema)*

**Descripción:** solo actor **Sistema** en v1.

**Suspensión — entrada:** existe **factura vigente** (RN-SUSF-027) con `estado_pago="Fallida"`.
1. `Fact_Suscripcion` → `estado="Suspendida"` (RN-SUSF-010).
2. Notificar suspensión.

**Nota de acceso durante dunning:** mientras la factura esté `Pendiente` (reintentos < 3), la suscripción permanece `Activa` y el acceso sigue permitido (RN-SUSF-017). Solo `Fallida` corta el acceso vía `Suspendida`.

**Reactivación:**
1. Disparada automáticamente al completar RF-SUSF-002 (RN-SUSF-021), **o** por acción explícita del Proveedor “Reintentar cobro” cuando `estado="Suspendida"` (mismo camino, sin exigir cambio de método) (RN-SUSF-028).
2. Sobre la factura vigente `Fallida`: pasar a `Pendiente` (mismo `id_factura`); cobro con clave `{id_factura}-reactivacion-{idmetodopago}` del método activo actual (RN-SUSF-025). Si falla: vuelve a `Fallida`; suscripción sigue `Suspendida`.
3. Si éxito: factura `Pagada`; suscripción `Activa` (RN-SUSF-011). Notificar reactivación.

**Efecto:** `Fact_Suscripcion_topic`, `Fact_Factura_topic`.

### RF-SUSF-008 — Renovación automática *(CU-O109, Sistema)*

**Descripción:** extiende el ciclo y genera+cobra la factura del nuevo período.

**Precondiciones:** `renovacionautomatica=true`, `estado="Activa"`, `activo=true`, y `fecha_fin <= now` (Guayaquil) al momento del job (RN-SUSF-012).

**Flujo:**
1. Notificación previa: exactamente **3 días calendario** antes de `fecha_fin` (job diario en la misma ventana), vía `core/notificaciones/`.
2. `Fact_Suscripcion` — escribir: `fecha_inicio` = `fecha_fin` anterior; `fecha_fin` = `add_calendar_months(fecha_inicio, 1)`.
3. **Generar factura** con la lógica de RF-SUSF-004 para el nuevo `periodo`.
4. **Cobrar** con RF-SUSF-005.
5. Si agota reintentos → RF-SUSF-007.

**Efecto:** `Fact_Suscripcion_topic` + `Fact_Factura_topic` (+ RF-SUSF-005/007).

### RF-SUSF-009 — Cancelar suscripción *(CU-O110, Proveedor)*

**Descripción:** el Proveedor finaliza la suscripción.

**Precondiciones:** `Fact_Suscripcion` con `activo=true` y `estado` ∈ {`Activa`,`Suspendida`}.

**Flujo:**
1. Escribir: `estado="Cancelada"`, `motivocancelacion`, `fechacancelacion=now`, `renovacionautomatica=false`. (`activo` permanece `true` mientras `now <= fecha_fin`.)

**Efectos:**
- RF-SUSF-008 deja de seleccionarla (RN-SUSF-013).
- Acceso hasta `fecha_fin` (RN-SUSF-014 / RN-SUSF-017).
- No se generan nuevas facturas.
- Recontratación = RF-SUSF-010 (nueva fila).
- Cuando `now > fecha_fin`, el job de mantenimiento escribe `activo=false` (RN-SUSF-020).

**Efecto:** `Fact_Suscripcion_topic`.

---

## 5. Requisitos no funcionales

Justificación ISO/IEC 25010:2023 (mandato `constitution.md`). Resumen de las 9 características:

| Característica | Tratamiento en este módulo |
|---|---|
| Functional Suitability | RF-SUSF-001…010 + CA-SUSF-* |
| Reliability | RNF-SUSF-003, RNF-SUSF-004, CA-SUSF-002/004/005/008 |
| Performance Efficiency | RNF-SUSF-005, CA-SUSF-006 |
| Interaction Capability | RNF-SUSF-006 |
| Security | RNF-SUSF-001, RNF-SUSF-002, RNF-SUSF-007 |
| Compatibility | RNF-SUSF-008 (adaptador de pasarela) |
| Maintainability | RNF-SUSF-007, RNF-SUSF-008, RNF-SUSF-009 |
| Flexibility | RNF-SUSF-008 (sustitución de proveedor de pago) |
| Safety (física) | **N/A** — este módulo no asigna unidades ni clasifica severidad operativa de despacho; el gating de severidad por plan es regla comercial (RN-SUSF-002), no decisión de Safety en el sentido de la constitución |

| Código | Requisito | ISO/IEC 25010:2023 |
|---|---|---|
| RNF-SUSF-001 | No se transmite ni almacena PAN/CVV; solo `tokenpasarela` y `ultimosdigitos`. (Detalle de negocio también en RN-SUSF-004; no duplicar implementación.) | Security — Confidencialidad |
| RNF-SUSF-002 | Proveedor: solo su `idcliente`. Administrador: lectura amplia + catálogo + aprobaciones de downgrade. | Security — Control de acceso |
| RNF-SUSF-003 | Idempotencia de cobro `{id_factura}-{reintentos}` y `{id_factura}-reactivacion-{idmetodopago}`. | Reliability — Tolerancia a fallos |
| RNF-SUSF-004 | Consistencia eventual entre tablas; diseños reprocesables sin duplicar efectos de negocio. | Reliability |
| RNF-SUSF-005 | Job de generación de facturas: **≤ 30 minutos** para hasta **10 000** suscripciones activas, sin degradar consultas hot-path de otros módulos sobre Pinot. | Performance Efficiency |
| RNF-SUSF-006 | UI muestra estado de suscripción, uso vs límites, último cobro; estados vacío/carga/error definidos en RF-SUSF-006. | Interaction Capability |
| RNF-SUSF-007 | Todo evento Kafka incluye `fecha_actualizacion` precisa. | Maintainability / Security |
| RNF-SUSF-008 | Pasarela detrás de adaptador en `apps/suscripciones/services/`. | Compatibility / Flexibility |
| RNF-SUSF-009 | Observabilidad mínima: log estructurado por intento de cobro (`id_factura`, resultado, clave idempotencia) y métricas de job (elegibles, emitidas, fallos, duración p95). | Maintainability |

---

## 6. Reglas de negocio

| Código | Regla |
|---|---|
| RN-SUSF-001 | Un plan solo se desactiva (`activo=false`); nunca delete físico. |
| RN-SUSF-002 | `Dim_Plan.nivel` → severidad: `Básico`→Baja; `Profesional`→Baja+Media; `Empresarial`→Baja+Media+Alta. |
| RN-SUSF-003 | Como máximo un `Dim_MetodoPago.activo=true` por `idcliente`. |
| RN-SUSF-004 | Sin PAN/CVV en modelo TSI; solo token + últimos 4 dígitos. *(Normativa de negocio; el RNF equivalente es RNF-SUSF-001.)* |
| RN-SUSF-005 | Upgrade/downgrade **solo por `nivel`**: `Básico` < `Profesional` < `Empresarial`. Mayor = upgrade (auto). Menor o mismo nivel con otro `idplan` = downgrade (admin). |
| RN-SUSF-006 | Tras aprobar cambio: `idplan`/`precio` inmediatos; tarifa nueva solo en próximas facturas; sin prorrateo. |
| RN-SUSF-007 | Una sola `Fact_Factura` por `id_suscripcion` + `periodo` (`YYYY-MM`). |
| RN-SUSF-008 | Dunning desde `fecha_emision`: día 0, día 3, día 7 (Guayaquil). Máx. 3 intentos. |
| RN-SUSF-009 | `reintentos` inicia en 0; cada fallo suma 1; éxito no incrementa. |
| RN-SUSF-010 | `Fallida` ⇒ suspensión automática `Suspendida`. |
| RN-SUSF-011 | Reactivación a `Activa` solo tras cobro exitoso de la factura en mora. |
| RN-SUSF-012 | Renovación solo si `renovacionautomatica=true` y `estado="Activa"`. |
| RN-SUSF-013 | Cancelación fija `renovacionautomatica=false`. Recontratación = RF-SUSF-010. |
| RN-SUSF-014 | Tras `Cancelada`, acceso hasta `fecha_fin`. |
| RN-SUSF-015 | Sin historial de transiciones más allá de `reintentos` + `resultado_ultimo_reintento`. |
| RN-SUSF-016 | `Vencida` solo etiqueta derivada en lectura; nunca persistida. |
| RN-SUSF-017 | Acceso permitido sii `activo=true` y (`estado="Activa"` **o** (`estado="Cancelada"` y `now <= fecha_fin`)). `Suspendida` deniega. |
| RN-SUSF-018 | Sin método activo: no emitir factura en RF-004/008; notificar; no suspender solo por eso. |
| RN-SUSF-019 | `limites` JSON mínimo: `unidades_max`, `usuarios_max`, `api_calls_mes` (ints ≥ 0). |
| RN-SUSF-020 | Como máximo una `Fact_Suscripcion` con `activo=true` por `idcliente`. Al vencer acceso de `Cancelada` (`now > fecha_fin`), el job de mantenimiento escribe `activo=false`. |
| RN-SUSF-021 | Tras RF-SUSF-002, si hay `Suspendida` + factura `Fallida`, el Sistema intenta regularización de inmediato. |
| RN-SUSF-022 | Cambio de plan (RF-SUSF-003) solo con `estado="Activa"`. |
| RN-SUSF-023 | Como máximo una `Fact_Solicitud_Cambio_Plan` en `Pendiente` por `idcliente`; nueva solicitud se rechaza con error de validación. |
| RN-SUSF-024 | Simulador de pasarela v1: éxito por defecto; fallo controlado por `BILLING_SIMULATOR_FAIL_RATE` (0.0–1.0, default `0`) o flag de prueba `force_fail`. |
| RN-SUSF-025 | Idempotencia de regularización: `{id_factura}-reactivacion-{idmetodopago}`. |
| RN-SUSF-026 | `numero_factura`: `seq` de 8 dígitos por `periodo` vía `max(seq en Pinot)+1` con reintento si colisión; `id_factura` = UUID v4. |
| RN-SUSF-027 | **Factura vigente** de una suscripción = la `Fact_Factura` con mismo `id_suscripcion` y `periodo` del ciclo actual (`fecha_inicio`..`fecha_fin` en Guayaquil). Si no existe, la más reciente del mismo `id_suscripcion` por `fecha_emision` con `estado_pago="Fallida"`. |
| RN-SUSF-028 | El Proveedor puede invocar “Reintentar cobro” estando `Suspendida`, sin cambiar método; dispara el mismo camino de regularización que RN-SUSF-021. |

---

## 7. Entradas

- Alta suscripción (Proveedor): `idplan`, `renovacionautomatica`.
- Alta/edición plan (Admin): `nombre`, `precio`, `limites`, `nivel`, `activo`.
- Método de pago: `tipo` + datos a tokenizar.
- Cambio de plan: `idplansolicitado`, `motivo`.
- Resolución admin: `Aprobada`\|`Rechazada`, `motivo_rechazo`.
- Resultado pasarela: éxito/fallo + código.
- Cron de jobs: facturación, dunning, renovación, mantenimiento `activo`.
- Cancelación: `motivocancelacion`.
- Acción Proveedor: “Reintentar cobro” (solo si `Suspendida`).

## 8. Salidas

- Confirmaciones de alta, método de pago, solicitud/resolución de plan, cancelación.
- `Fact_Factura` con desglose.
- Notificaciones: fallo de cobro, aviso renovación (−3 días), suspensión, reactivación, falta de método de pago.
- Historial RF-SUSF-006.
- Errores de validación.
- Logs/métricas de cobro y jobs (RNF-SUSF-009).

## 9. Estados posibles

### 9.1 `Fact_Suscripcion.estado` (persistido)

```
Activa ──(RF-SUSF-007: factura Fallida)──► Suspendida
  │                                            │
  │◄──(RF-SUSF-007: cobro exitoso)─────────────┘
  │
  └──(RF-SUSF-009)──► Cancelada ──(acceso hasta fecha_fin; luego activo=false)
```

Alta inicial (RF-SUSF-010) entra en `Activa`. Cambio de plan solo desde `Activa`.

`Vencida`: solo UI/consulta derivada (RN-SUSF-016).

### 9.2 `Fact_Factura.estado_pago`

```
Pendiente ──(éxito RF-SUSF-005)──► Pagada
    │
    └──(3 fallos)──► Fallida ──► RF-SUSF-007
         │
         └──(regularización)──► Pendiente ──► Pagada | Fallida
```

### 9.3 `Fact_Solicitud_Cambio_Plan.estado`

```
Pendiente ──(upgrade auto)──► Aprobada
    ├──(downgrade admin OK)──► Aprobada
    └──(downgrade rechazo)──► Rechazada
```

### 9.4 Flags `activo`

`Dim_MetodoPago.activo` / `Dim_Plan.activo` / `Fact_Suscripcion.activo`: booleanos; `false` = histórico / no disponible para nuevas altas; sin delete físico.

---

## 10. Escenarios

### Escenario 0 — Alta inicial de suscripción
Dado un Proveedor con `Dim_Cliente` y sin suscripción `activo=true`
Cuando elige un plan activo y confirma
Entonces se crea `Fact_Suscripcion` `Activa` con ciclo de un mes calendario (Guayaquil)
Y se actualiza `Dim_Cliente.plan_suscripcion`
Y si tiene método activo se genera y cobra la primera factura; si no, se notifica para registrar método.

### Escenario 1 — Alta exitosa de método de pago
Dado un Proveedor sin método registrado
Cuando registra datos válidos
Entonces queda un `Dim_MetodoPago` con `activo=true` (token + últimos dígitos, sin PAN/CVV).

### Escenario 1b — Método actualizado en mora
Dado `Suspendida` con factura `Fallida`
Cuando el Proveedor registra/reemplaza método de pago
Entonces el Sistema intenta cobro de regularización de inmediato
Y si tiene éxito la suscripción vuelve a `Activa`.

### Escenario 2 — Reemplazo del método principal
Dado un método `activo=true`
Cuando registra otro
Entonces el anterior pasa a `activo=false` y solo el nuevo queda activo.

### Escenario 3 — Upgrade
Dado plan `Básico` `Activa` y solicitud a `Profesional`
Cuando envía la solicitud
Entonces se autoaprueba
Y `idplan`/`precio` y `plan_suscripcion` se actualizan de inmediato
Y no se regenera la factura del ciclo en curso.

### Escenario 4 — Downgrade pendiente
Dado plan `Empresarial` y solicitud a `Profesional`
Cuando envía
Entonces la solicitud queda `Pendiente` y no cambia la suscripción hasta resolución admin.

### Escenario 4b — Segunda solicitud mientras hay Pendiente
Dado ya una solicitud `Pendiente`
Cuando el Proveedor envía otra
Entonces el sistema rechaza con error de validación (RN-SUSF-023).

### Escenario 4c — Cambio de plan en Suspendida
Dado `estado="Suspendida"`
Cuando intenta cambiar de plan
Entonces se rechaza (RN-SUSF-022).

### Escenario 5 — Downgrade rechazado
Dado downgrade `Pendiente`
Cuando el Admin rechaza con motivo
Entonces solicitud `Rechazada` y suscripción intacta.

### Escenario 6 — Generación mensual
Dado suscripciones `Activa` con método y sin factura del `periodo`
Cuando corre el batch (02:00–05:00 Guayaquil)
Entonces se crea exactamente una `Fact_Factura` `Pendiente` con `impuestos=0` y `numero_factura` FAC-…
Y se invoca cobro día 0.

### Escenario 6b — Sin método de pago en facturación
Dado suscripción `Activa` sin método activo
Cuando corre el batch
Entonces no se crea factura y se notifica al Proveedor
Y no se suspende solo por esa causa.

### Escenario 7 — Cobro exitoso
Dado factura `Pendiente` y pasarela OK
Entonces `Pagada` y `resultado_ultimo_reintento="Exitoso"`.

### Escenario 8 — Cobro fallido con reintento
Dado fallo y `reintentos` resultará < 3
Entonces permanece `Pendiente` y se agenda dunning (día 3 o 7).

### Escenario 9 — Agotamiento de reintentos
Dado tercer fallo
Entonces `Fallida` y se dispara suspensión.

### Escenario 10 — Suspensión por mora
Dado `Fallida`
Entonces suscripción `Suspendida` sin acción de Administrador.

### Escenario 11 — Reactivación
Dado `Suspendida` y cobro de regularización exitoso
Entonces factura `Pagada` y suscripción `Activa`.

### Escenario 11b — Reintentar cobro sin cambiar método
Dado `Suspendida` con factura vigente `Fallida` y método activo válido
Cuando el Proveedor elige “Reintentar cobro”
Entonces se ejecuta la regularización (RF-SUSF-007)
Y si la pasarela responde éxito vuelve a `Activa`.

### Escenario 12 — Renovación automática
Dado elegible (`fecha_fin <= now`, renovación on, `Activa`)
Cuando corre el job
Entonces se recorren fechas un mes calendario, se crea factura (RF-SUSF-004) y se cobra (RF-SUSF-005).

### Escenario 13 — Cancelación
Dado `Activa` o `Suspendida`
Cuando cancela con motivo
Entonces `Cancelada`, `renovacionautomatica=false`, sin más facturas
Y acceso hasta `fecha_fin`
Y tras `fecha_fin` el mantenimiento pone `activo=false`.

### Escenario 14 — Historial
Dado facturas propias
Cuando consulta
Entonces ve solo las de su `idcliente`; si no hay, estado vacío definido.

### Escenario 15 — Desactivación de plan
Dado plan con suscriptores
Cuando Admin pone `activo=false`
Entonces no aparece para altas/cambios y suscripciones existentes no se rompen.

---

## 11. Criterios de aceptación

| Código | Criterio | ISO/IEC 25010:2023 |
|---|---|---|
| CA-SUSF-001 | Plan desactivado: 0% de suscripciones vigentes rotas; no aparece en altas/cambios. | Functional Suitability |
| CA-SUSF-002 | 100% de reemplazos de método dejan exactamente un `activo=true` por cliente. | Reliability |
| CA-SUSF-003 | 100% upgrades autoaprobados; 100% downgrades quedan `Pendiente` hasta admin. | Functional Suitability |
| CA-SUSF-004 | Exactamente una factura por suscripción elegible y `periodo`, sin duplicados. | Reliability |
| CA-SUSF-005 | ≤ 3 intentos de cobro por factura en dunning; 0 cobros duplicados verificables por idempotencia. | Reliability / Security |
| CA-SUSF-006 | Historial de facturas ≤ 3 s en condiciones normales. | Performance Efficiency |
| CA-SUSF-007 | 100% de facturas `Fallida` provocan suspensión en el mismo ciclo de procesamiento. | Functional Suitability / Reliability |
| CA-SUSF-008 | 100% de elegibles de renovación procesados por ejecución del job. | Reliability |
| CA-SUSF-009 | 0 renovaciones sobre `Cancelada`. | Functional Suitability |
| CA-SUSF-010 | 100% de altas iniciales dejan exactamente una suscripción `activo=true` `Activa` cuando no existía vigente, con `plan_suscripcion` sincronizado. | Functional Suitability |
| CA-SUSF-011 | Acceso cumple RN-SUSF-017 en 100% de la matriz Activa/Suspendida/Cancelada × antes/después de `fecha_fin`. | Functional Suitability |
| CA-SUSF-012 | 100% de actualizaciones de método en mora disparan intento de regularización (RN-SUSF-021). | Reliability |
| CA-SUSF-013 | 100% de segundas solicitudes con otra `Pendiente` son rechazadas (RN-SUSF-023). | Functional Suitability |
| CA-SUSF-014 | 100% de `numero_factura` emitidos son únicos por `periodo` (RN-SUSF-026). | Reliability |
| CA-SUSF-015 | Durante dunning (`Pendiente`), 100% de suscripciones siguen con acceso permitido hasta `Fallida`. | Functional Suitability |

---

## 12. Dependencias

- **Cuentas-Clientes** (`incorporacion-clientes`, `autenticacion-y-rbac`): `Dim_Cliente` previo.
- **`core/notificaciones/`**: fallos, renovación (−3 días), suspensión, reactivación, falta de método.
- **Kafka + Pinot** (`infrastructure.md`).
- **Partners-API** (`api-monitoring-and-billing`): comparte `Dim_Plan` / patrón de mora; coordinar cambios.
- **Pasarela:** simulada en v1 (RN-SUSF-024).

## 13. Fuera de alcance (v1 definitivo)

- Integración real con Stripe/PayPal/etc. (solo simulador).
- Prorrateo a mitad de ciclo.
- Cálculo de IVA/retenciones (`impuestos` siempre 0).
- Historial de transiciones / intentos individuales más allá de `reintentos` + `resultado_ultimo_reintento`.
- Cancelación automática por mora persistente sin reactivación.
- **Notas de crédito / anulación de facturas:** campos presentes con defaults; sin CU en v1.
- Múltiples métodos de pago activos a la vez.
- Multi-moneda.
- Suspensión/reactivación manual por Administrador.
- i18n más allá de español (UI v1 en español).

## 14. Apéndice — Mapeo a modelo de datos

### 14.1 Tablas

| Tabla | PK | Tópico Kafka | Columna upsert (obligatoria en evento) | Columna tiempo Pinot (índice) |
|---|---|---|---|---|
| `Dim_Plan` | `idplan` | `Dim_Plan_topic` | `fecha_actualizacion` | `fecha_actualizacion` |
| `Dim_MetodoPago` | `idmetodopago` | `Dim_MetodoPago_topic` | `fecha_actualizacion` | `fecha_actualizacion` |
| `Fact_Suscripcion` | `id_suscripcion` | `Fact_Suscripcion_topic` | `fecha_actualizacion` | `fecha_inicio` |
| `Fact_Factura` | `id_factura` | `Fact_Factura_topic` | `fecha_actualizacion` | `fecha_emision` |
| `Fact_Solicitud_Cambio_Plan` | `idsolicitud` | `Fact_Solicitud_Cambio_Plan_topic` | `fecha_actualizacion` | `fecha_solicitud` |

### 14.2 RF → escrituras

| RF | CU canónico | Escribe |
|---|---|---|
| RF-SUSF-010 | CU-O111 | `Fact_Suscripcion`, `Dim_Cliente` (+ `Fact_Factura` si hay método) |
| RF-SUSF-001 | CU-O106 | `Dim_Plan` |
| RF-SUSF-002 | CU-O101 | `Dim_MetodoPago` (+ RF-SUSF-007 si mora) |
| RF-SUSF-003 | CU-O104 | `Fact_Solicitud_Cambio_Plan`, `Fact_Suscripcion`, `Dim_Cliente` (si aprueba) |
| RF-SUSF-004 | CU-O107 | `Fact_Factura` |
| RF-SUSF-005 | CU-O102 | `Fact_Factura` |
| RF-SUSF-006 | CU-O108 | (solo lectura) |
| RF-SUSF-007 | CU-O105 | `Fact_Suscripcion`, `Fact_Factura` |
| RF-SUSF-008 | CU-O109 | `Fact_Suscripcion` + factura vía RF-SUSF-004 + cobro RF-SUSF-005 |
| RF-SUSF-009 | CU-O110 | `Fact_Suscripcion` (+ mantenimiento posterior `activo=false`) |

---

## 15. Decisiones de diseño v1 (normativas)

1. Upgrade auto / downgrade admin: **sí** (RN-SUSF-005).
2. Dunning 0/3/7, máx. 3: **sí**.
3. Un método activo: **sí**.
4. `Vencida` solo derivada: **sí**.
5. Post-cancelación = nueva alta: **sí**.
6. Idempotencia cobro + reactivación por método: **sí**.
7. `nivel` enum + severidad derivada: **sí**.
8. Cambio de plan: escritura inmediata; cobro en próxima factura: **sí**.
9. Acceso = RN-SUSF-017: **sí**.
10. Alta = RF-SUSF-010: **sí**.
11. Notas de crédito fuera de v1: **sí**.
12. Sin admin en mora: **sí**.
13. Job facturación ≤ 30 min / 10k: **sí**.
14. Ruta canónica `subscriptions-and-billing/` (slug `billing-and-auto-renewal` deprecado; referencias Soporte/Ventas alineadas): **sí**.
15. Ciclo = mes calendario Guayaquil; jobs 02:00–05:00: **sí**.
16. `impuestos=0`, `periodo=YYYY-MM`, `FAC-{YYYYMM}-{seq8}`, vencimiento +7d: **sí**.
17. Sync obligatorio `plan_suscripcion` vía `ClienteRepository`; primera factura obligatoria si hay método: **sí**.
18. Una `Pendiente` de cambio; solo cambiar plan en `Activa`: **sí**.
19. Reactivación auto tras RF-002; `activo=false` post-`fecha_fin` en canceladas: **sí**.
20. USD; simulador con fail-rate; observabilidad RNF-009: **sí**.
21. `numero_factura` por max+1 Pinot + UUID PK: **sí** (RN-SUSF-026).
22. Factura vigente = RN-SUSF-027; acceso durante dunning = sí: **sí**.
23. Acción “Reintentar cobro” sin cambiar método: **sí** (RN-SUSF-028).
24. Historial ordenado por `fecha_emision` desc: **sí**.
25. Idempotency-Key HTTP + throttles DRF en tasks T086–T089: **sí**.
26. Smoke latency CA-006 (T090); RNF-005 load a escala = post-MVP: **sí**.
