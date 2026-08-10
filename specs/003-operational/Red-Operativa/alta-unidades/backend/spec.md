# Especificación: Alta y Configuración de Unidades de Emergencia

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../alta-unidades.md`](../alta-unidades.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — Fase B; no duplicar OpenAPI/data-model en FE.


## 1. Objetivo

Permitir al **Proveedor** (empresa dueña de la flota, `Dim_Cliente` activo) registrar (individualmente o en lote), editar y dar de baja las unidades de emergencia externas (grúas, ambulancias, patrullas) que participan en la red operativa de TSI. TSI no es propietaria de flotas — su valor como orquestador digital depende de un catálogo actualizado. La disponibilidad operativa la declara la propia unidad con login (**CU-O30**, módulo Emergencias).

## Clarifications

### Session 2026-07-21

- Q: ¿Debe existir una relación de integridad referencial (FK) entre `Dim_UnidadEmergencia` (zona de cobertura) y `Dim_RegionOperativa`, o se mantiene como una relación puramente textual sin validación? → A: Se elimina el campo `zonacobertura` de `Dim_UnidadEmergencia` por completo — no tiene un propósito claro definido y no debe vincularse con región operativa.
- Q: Cuando `tipopropiedad = 'Propia'`, ¿es `idcliente` obligatorio, opcional, o debe ser nulo? → A: `idcliente` es obligatorio siempre, independientemente de `tipopropiedad`.
- Q: Al reactivar una unidad (CU-O58) cuya `placa` fue reutilizada mientras tanto por otra unidad activa, ¿qué debe pasar? → A: Bloquear la reactivación con HTTP 409 si ya existe otra unidad activa con la misma `placa` (misma regla de unicidad que CU-O54/O56).
- Q: ¿Puede el Operador declarar "Fuera de servicio" vía CU-O59, o ese estado está reservado al Administrador junto con la baja (CU-O58)? → A: *(Superada por Session 2026-07-24: CU-O59 eliminado.)*
- Q: Si dos Administradores editan la misma unidad simultáneamente (RF-CAM-003), ¿cómo se resuelve el conflicto? → A: Last-write-wins, sin bloqueo optimista. *(Actor actualizado a Proveedor en Session 2026-07-24.)*
- Q: `zonacobertura` resultó ser un fallback geográfico real ya documentado y consumido por `despacho-inteligente`… → A: Reemplazar por `idcondado` (INT, FK real a `Dim_Condado`).

### Session 2026-07-24 (modelo Proveedor)

- Q: ¿Actor de alta/edición/baja/lote? → A: **Proveedor** dueño; el Administrador global **no** tiene override sobre unidades de terceros.
- Q: ¿`idproveedorasistencia`? → A: No existe; ownership = `Dim_UnidadEmergencia.idcliente` del proveedor autenticado (auto-asignado).
- Q: ¿Lote crea logins? → A: Sí — cada fila incluye correo; se crean `Dim_Usuarios` + `Dim_Credencial` + rol unidad. Transacción **todo-o-nada total** (unidades + credenciales).
- Q: ¿Mantener CU-O59 (disponibilidad por Operador sin login)? → A: **Eliminar.** Solo CU-O30 (unidad con login).

### Session 2026-07-29 (mapa borrador Red Operativa)

- Q: El borrador de departamento usa Admin + O59 + `zonacobertura` + `idproveedorasistencia`. ¿Cuál es la fuente de verdad? → A: Este spec (Session 2026-07-24) + `flujoscorreguidos/flujo-red-operativa-canonico.md`. Actor **Proveedor**; O59 → O30; `idcondado`; sin `idproveedorasistencia`.

## 2. Contexto

Antes de que el algoritmo de despacho pueda asignar una unidad, esa unidad debe existir en el catálogo con datos correctos. Este spec cubre el ciclo de vida administrativo (alta → edición → baja). La **disponibilidad** la gestiona la unidad autenticada en `evidencia-unidad` (**CU-O30**).

**Fuente de alineación:** `especificacion-cambios-implementacion.md` + `flujoscorreguidos/flujo-red-operativa-canonico.md`.

**Casos de uso incluidos:**
- **CU-O54: Registrar unidad de emergencia** — El **Proveedor** da de alta una unidad individual; `idcliente` se toma del usuario autenticado.
- **CU-O56: Registrar unidades en lote** — Importación CSV por el Proveedor; valida unidades + credenciales; todo-o-nada; crea login por fila.
- **CU-O57: Editar unidad** — Solo unidades con `idcliente` del Proveedor autenticado.
- **CU-O58: Dar de baja / reactivar unidad** — Misma regla de pertenencia.

**Caso de uso eliminado:**
- **CU-O59: Gestionar disponibilidad de unidad externa** — **Retirado.** No hay unidades sin login en el modelo objetivo; usar **CU-O30**.

**Tablas:**
- `Dim_UnidadEmergencia`: `idunidademergencia`, `idcliente` (FK `Dim_Cliente`, requerido, inmutable, auto del Proveedor), `idcondado`, `tipopropiedad` (en la práctica `'Externa'`), `placa`, `capacidad`, `contactoproveedor`, `unidademergencia`, `tipounidademergencia`, `activo`, `latitud`, `longitud`, `fecha_actualizacion`.
- `Fact_BajaUnidad`: historial de bajas.
- `Fact_HistorialEstadoUnidad` / `Dim_EstadoUnidadEmergencia`: consumidos por O30/despacho; **este spec ya no escribe disponibilidad**.
- `Dim_Usuarios`, `Dim_Credencial`, `Dim_Usuario_Rol`: creados en O56 (y opcionalmente vínculo unidad↔usuario en O54 si se define en plan).
- `Fact_Despacho` (solo lectura): validación de despacho activo en edición/baja.
- `Fact_Suscripcion` (módulo Suscripciones y Facturación, solo lectura vía `SuscripcionActivaReadRepository`): gate `carga_lote_habilitada` en O56 (corrección 2026-08-08, RF-CAM-002 punto 0).

## 3. Actores

| Actor | Rol en este spec | Interacción principal |
|---|---|---|
| **Proveedor** | Dueño del catálogo de su flota | Registra (O54/O56), edita (O57), da de baja/reactiva (O58) **solo** unidades con su `idcliente`. Requiere `Dim_Cliente.estado='Activo'`. |
| **Administrador** | Única excepción — baja forzada con despacho activo (RF-CAM-004, corrección 2026-08-08) | Sin override sobre alta, edición, baja ordinaria ni reactivación de unidades de terceros; su única facultad en este spec es completar `POST .../baja` con `forzar=true` cuando la unidad tiene un despacho activo (RF-O42.4). |
| **Sistema** | Validador | Unicidad de `placa`, pertenencia `idcliente`, bloqueo por despacho activo, todo-o-nada del lote + credenciales. |

**Fuera de actores de este spec:** Operador (ya no declara disponibilidad externa). El Administrador ya no está totalmente fuera de alcance — ver fila arriba.

## 4. Requisitos funcionales

### RF-CAM-001: Registro individual de unidad (CU-O54)

El **Proveedor** autenticado registra una unidad. El sistema:
1. Resuelve `idcliente` **exclusivamente** desde la cuenta del usuario (no se acepta `idcliente` libre en el body para suplantar a otro proveedor).
2. Valida que el cliente esté `Activo`.
3. Valida placa única entre activas (409 si duplicado).
4. Valida `idcondado` existente en `Dim_Condado` (400 si no).
5. Inserta en `Dim_UnidadEmergencia` con los campos: `tipopropiedad` (default/práctico `'Externa'`), `placa`, `idcondado`, `capacidad`, `contactoproveedor`, `unidademergencia`, `tipounidademergencia`, `activo=true`.
6. Si el body incluye **`gmail`** (opcional): crea usuario + credencial + rol `Unidad`, liga `idusuario` e invita por correo (mismo mecanismo O56). Sin `gmail` la unidad no puede declarar disponibilidad vía CU-O30 hasta que se asigne login.
7. **No** inserta fila en `Fact_HistorialEstadoUnidad` aquí — el estado inicial lo declara la unidad vía **CU-O30** tras recibir credenciales.

### RF-CAM-002: Registro en lote (CU-O56)

El **Proveedor** importa CSV:
0. **Gate de plan (RF-O40.6, corrección 2026-08-08):** solo procede si `Fact_Suscripcion.carga_lote_habilitada` (congelado desde `Dim_Plan.carga_lote_habilitada` al alta/cambio de plan — no se lee `Dim_Plan` en vivo, ver `SuscripcionActivaReadRepository`) es `true` para la suscripción activa del Proveedor. Si no hay suscripción activa o el campo es `false`/ausente → `403`, sin leer ni validar el archivo.
1. Cada fila incluye las columnas de O54 **más `gmail`** (correo del usuario-unidad).
2. Validar **todas** las filas: reglas de unidad **y** viabilidad de credencial (gmail válido, gmail no duplicado en `Dim_Usuarios`, etc.).
3. Si **cualquier** fila falla (unidad o login), **no se inserta ninguna** unidad ni ningún usuario (`insertadas: 0`, reporte fila a fila).
4. Si todo pasa: por cada fila, INSERT unidad (`idcliente` del Proveedor) + crear `Dim_Usuarios` + `Dim_Credencial` (temp password, `estadocredencial='Cambio contraseña'`) + rol "Unidad de Emergencia" (o nombre canónico del rol semilla) en `Dim_Usuario_Rol` + envío de invitación por correo (mismo mecanismo que CU-O08).
5. Límite duro: >500 filas → 400 sin procesar.

### RF-CAM-003: Edición (CU-O57)

El Proveedor edita campos: `tipopropiedad`, `capacidad`, `idcondado`, `contactoproveedor`, `unidademergencia`, `tipounidademergencia`, `latitud`, `longitud`. **No** modifica `idunidademergencia` ni `idcliente`.

**Autorización:** la unidad debe tener `idcliente` = cliente del Proveedor; si no → 403/404.

**Concurrencia:** last-write-wins.

**Bloqueo:** despacho activo → bloquear o exigir confirmación para `tipopropiedad` / `tipounidademergencia`.

### RF-CAM-004: Baja / reactivación (CU-O58)

Misma regla de pertenencia `idcliente`. Flujo de baja (`Fact_BajaUnidad`, `activo=false`) y reactivación (409 si placa reutilizada) sin cambio de reglas de negocio previas, salvo el actor.

**Corrección 2026-08-08 (RF-O42.4 del catálogo, SRS §3.5.1):** la baja **sin** despacho activo sigue siendo autoservicio pleno del Proveedor. Pero la baja **con** despacho activo (`forzar=true`) es la única excepción al modelo Proveedor de esta sesión — está reservada exclusivamente al Administrador; el Proveedor recibe 403 aunque envíe `forzar=true`, con sugerencia de esperar el cierre del caso. `UnidadBajaView` acepta tanto Proveedor como Administrador (`IsProveedorFlotaOrAdministrador`); la validación de quién puede completar la baja forzada vive en `BajaUnidadService`, no en el permiso de la vista.

### RF-CAM-005: CU-O59 eliminado

Este requisito **ya no aplica**. La declaración de disponibilidad por Operador sobre unidades sin login se retira del producto. Referencias en OpenAPI, FE, permisos `IsOperadorDisponibilidadExterna` y tests deben eliminarse en la fase de implementación. Consumidores deben usar **CU-O30**.

## 5. Requisitos no funcionales

### RNF-CAM-001: Validación de duplicados
Validación de `placa` (y de `gmail` en lote) &lt; 1 s por fila.

### RNF-CAM-002: Importación en lote
Hasta 500 filas &lt; 30 s, con reporte fila a fila. Todo-o-nada incluye credenciales.

### RNF-CAM-003: Trazabilidad
Registro, edición, baja, reactivación y creación de usuarios-unidad en logs con `idusuario`, timestamp y campos afectados.

### RNF-CAM-004: Seguridad (ISO Security)
Un Proveedor nunca lista ni muta unidades de otro `idcliente`. El Administrador no bypassa esta regla en este módulo.

## 6. Reglas de negocio

### RN-CAM-001
`activo=false` → no candidata de despacho ni cambios de disponibilidad hasta reactivar.

### RN-CAM-002
Solo el **Proveedor dueño** ejecuta O54/O56/O57/O58 sobre sus unidades. Sin override Admin.

### RN-CAM-003
`placa` única entre unidades activas (O54, O56, reactivación O58).

### RN-CAM-004
Baja nunca borra físicamente; `Fact_BajaUnidad` permanece.

### RN-CAM-005
`idcondado` FK lógica a `Dim_Condado`; sin relación directa a `Dim_RegionOperativa`.

### RN-CAM-006
`idcliente` inmutable y siempre el del Proveedor autenticado.

### RN-CAM-007
O56 es atómico: fallo de credencial = fallo de lote completo.

### RN-CAM-008
Solo cuentas `Dim_Cliente.estado='Activo'` pueden gestionar unidades.

## 7. Entradas

### CU-O54
`tipopropiedad`, `placa`, `idcondado`, `capacidad`, `contactoproveedor`, `unidademergencia`, `tipounidademergencia`, `activo` (opcional). **No** `idcliente` en body (o se ignora a favor del token).

### CU-O56
Archivo CSV: columnas O54 + `gmail` por fila.

### CU-O57
`idunidademergencia` + campos editables.

### CU-O58
`idunidademergencia`, `motivo`, `tipobaja` (baja); path para reactivar.

## 8. Salidas

- **201 Created — Unidad:** `{ idunidademergencia, placa, activo: true }`.
- **200 OK — Lote:** `{ insertadas, fallidas: [{ fila, motivo }] }` (`insertadas=0` si alguna falla).
- **200 OK — Actualizada / Baja / Reactivada:** payloads existentes.
- **403** — unidad de otro proveedor o cliente no Activo.
- **409** — placa/gmail duplicados.
- **409** — edición/baja crítica con despacho activo sin confirmación.

## 9. Estados posibles

### `Dim_UnidadEmergencia.activo`
- `true` / `false` (baja O58).

### Disponibilidad
Derivada de `Fact_HistorialEstadoUnidad` vía **CU-O30** (fuera de este spec). Estados: Activa, Ocupada, En Misión (solo sistema), Fuera de servicio.

## 10. Escenarios

### Escenario 1: Alta individual (O54)
Proveedor Activo registra grúa con placa nueva → INSERT con su `idcliente` → `activo=true` → sin fila de historial de estado aún.

### Escenario 2: Placa duplicada (O54)
Placa activa existente → 409.

### Escenario 3: Lote con correo inválido (O56)
50 filas; fila 23 con gmail ya usado → `insertadas=0`, error en fila 23; **ningún** usuario creado.

### Escenario 4: Edición de unidad ajena (O57)
Proveedor A intenta editar unidad de Proveedor B → 403/404.

### Escenario 5: Baja / reactivación (O58)
Igual que reglas previas, actor Proveedor dueño.

### Escenario 6: Intento Admin de alta
Administrador sin rol Proveedor / sin `idcliente` de flota → 403.

## 11. Criterios de aceptación

### CA-CAM-001
Proveedor registra unidad individual; `idcliente` = su cuenta (O54).

### CA-CAM-002
Rechazo por `placa` duplicada entre activas.

### CA-CAM-003
Importación lote: fallo de unidad **o** credencial ⇒ ninguna inserción (O56).

### CA-CAM-004
Lote exitoso crea unidad + usuario + credencial + rol por fila (O56).

### CA-CAM-005
Edición solo sobre unidades propias; no muta `idcliente` (O57).

### CA-CAM-006
Bloqueo/confirmación si despacho activo en campos críticos.

### CA-CAM-007
Baja registra `Fact_BajaUnidad` y `activo=false` (O58).

### CA-CAM-008
Reactivación con historial intacto; 409 si placa reutilizada.

### CA-CAM-009
CU-O59 no forma parte del producto; disponibilidad solo vía CU-O30.

### CA-CAM-010
Administrador no puede CRUD de unidades de proveedores.

## 12. Dependencias

- **`incorporacion-clientes`:** Proveedor con `estado='Activo'` (O14/O16).
- **`autenticacion-y-rbac`:** JWT + rol Proveedor / Unidad de Emergencia.
- **`registro-accidente`:** `Dim_Condado`.
- **`evidencia-unidad`:** CU-O30 (única vía de disponibilidad declarada).
- **`despacho-inteligente`:** consume unidades `activo=true`.
- **`seguimiento-cierre-de-casos`**, **`incorporacion-regional`:** consumidores del catálogo.

## 13. Fuera de alcance

- **CU-O30** autodeclaración de disponibilidad (spec `evidencia-unidad`).
- Tracking GPS, asignación a caso, onboarding regional.
- Filtro de cobertura por severidad de plan de región (⛔ Suscripciones-Facturación).
