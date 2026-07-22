# Especificación: Alta y Configuración de Unidades de Emergencia

## 1. Objetivo

Permitir al Administrador registrar (individualmente o en lote), editar, dar de baja y gestionar la disponibilidad declarada de las unidades de emergencia externas (grúas, ambulancias, patrullas) que participan en la red operativa de TSI. TSI no es propietaria de flotas — su valor como orquestador digital depende de mantener un catálogo actualizado y confiable de unidades externas disponibles para el algoritmo de despacho.

## Clarifications

### Session 2026-07-21

- Q: ¿Debe existir una relación de integridad referencial (FK) entre `Dim_UnidadEmergencia` (zona de cobertura) y `Dim_RegionOperativa`, o se mantiene como una relación puramente textual sin validación? → A: Se elimina el campo `zonacobertura` de `Dim_UnidadEmergencia` por completo — no tiene un propósito claro definido y no debe vincularse con región operativa.
- Q: Cuando `tipopropiedad = 'Propia'`, ¿es `idcliente` obligatorio, opcional, o debe ser nulo? → A: `idcliente` es obligatorio siempre, independientemente de `tipopropiedad`.
- Q: Al reactivar una unidad (CU-O58) cuya `placa` fue reutilizada mientras tanto por otra unidad activa, ¿qué debe pasar? → A: Bloquear la reactivación con HTTP 409 si ya existe otra unidad activa con la misma `placa` (misma regla de unicidad que CU-O54/O56).
- Q: ¿Puede el Operador declarar "Fuera de servicio" vía CU-O59, o ese estado está reservado al Administrador junto con la baja (CU-O58)? → A: El Operador puede declarar "Fuera de servicio" vía CU-O59, igual que "Activa"/"Ocupada" — es un estado de disponibilidad, no de alta/baja.
- Q: Si dos Administradores editan la misma unidad simultáneamente (RF-CAM-003), ¿cómo se resuelve el conflicto? → A: Last-write-wins, sin bloqueo optimista.
- Q: `zonacobertura` resultó ser un fallback geográfico real ya documentado y consumido por `despacho-inteligente` (spec, data-model y `unidad_emergencia_repository.py`) para encontrar unidades candidatas por condado cuando `latitud`/`longitud` no basta — no un campo huérfano. ¿Cómo proceder? → A: Reemplazar por `idcondado` (INT, FK real a `Dim_Condado`), eliminando el texto libre casteado a int. `despacho-inteligente` debe actualizarse (spec, data-model, `unidad_emergencia_repository.py`) para usar `idcondado` directamente en vez del fallback de texto — ver dependencia en Sección 12.

## 2. Contexto

Antes de que el algoritmo de despacho inteligente pueda asignar una unidad a un accidente, esa unidad debe existir en el catálogo, con sus datos correctos y su disponibilidad declarada. Este spec cubre todo el ciclo de vida administrativo de la unidad — desde el alta hasta la baja — pero **no** cubre la disponibilidad autodeclarada por una unidad con login propio (eso vive en el módulo Emergencias, spec `evidencia-unidad`).

**Casos de uso incluidos:**
- **CU-O54: Registrar y configurar unidades de emergencia** — El Administrador da de alta una unidad individual en `Dim_UnidadEmergencia`.
- **CU-O56: Registrar unidades de emergencia en lote** — Importación masiva (CSV/Excel) de unidades, misma validación que O54 aplicada fila por fila.
- **CU-O57: Editar/actualizar datos de unidad de emergencia** — Modificación de campos editables de una unidad existente.
- **CU-O58: Dar de baja/desactivar unidad de emergencia** — Baja lógica de una unidad, con trazabilidad completa en `Fact_BajaUnidad`.
- **CU-O59: Gestionar disponibilidad de unidad externa** — El Operador de emergencias declara la disponibilidad de una unidad que no tiene login propio (a diferencia de `CU-O30` en el módulo Emergencias, que es la autodeclaración de una unidad con login).

**Tablas de base de datos utilizadas** (verificadas contra `tablas.json`/`esquemas.json`):
- `Dim_UnidadEmergencia`: `idunidademergencia` (PK), `idcliente` (FK a `Dim_Cliente`), `idcondado` (FK a `Dim_Condado`), `tipopropiedad` ('Propia'|'Externa'), `placa`, `capacidad`, `contactoproveedor`, `unidademergencia`, `tipounidademergencia`, `activo`, `latitud`, `longitud`, `fecha_actualizacion`. *(Campo `zonacobertura` reemplazado por `idcondado` — ver Clarifications. Requiere migración de `despacho-inteligente`, ver Sección 12.)*
- `Fact_BajaUnidad`: `idbajaunidad` (PK), `idunidademergencia` (FK), `idusuario`, `idaccidente` (FK a `Fact_Accidente`, nullable), `motivo`, `tipobaja`, `fechahora`, `fecha_actualizacion`.
- `Fact_HistorialEstadoUnidad`: `idhistorialestadosunidadesemergencias` (PK), `estadoanterior`, `estadonuevo`, `idestadounidademergencia` (FK), `idunidademergencia` (FK), `idusuario`, `fechahora`, `fecha_actualizacion`.
- `Dim_EstadoUnidadEmergencia`: catálogo de estados (Activa, Ocupada, En Misión, Fuera de servicio). "En Misión" es de asignación exclusiva del sistema (`despacho-inteligente`); el Operador no puede declararla vía CU-O59.
- `Fact_Despacho` (módulo Emergencias, solo lectura): usada para validar si una unidad tiene un despacho activo antes de permitir baja o edición crítica.


## 3. Actores

| Actor | Rol en este spec | Interacción principal |
|---|---|---|
| **Administrador** | Gestor del catálogo de unidades | Registra unidades (individual y en lote), las edita, las da de baja. |
| **Operador de emergencias** | Declarante de disponibilidad externa | Declara la disponibilidad de una unidad sin login propio (CU-O59). |
| **Sistema** | Validador | Valida duplicados por `placa`, bloquea ediciones críticas si hay despacho activo, calcula el estado actual de disponibilidad a partir del historial. |

## 4. Requisitos funcionales

### RF-CAM-001: Registro individual de unidad de emergencia (CU-O54)

El Administrador debe poder registrar una nueva unidad proporcionando:
- `idcliente` (INT, FK a `Dim_Cliente`, **requerido siempre** — para unidades `Propia` referencia al cliente/entidad interna de TSI dueña de la unidad; para `Externa` referencia a la empresa proveedora).
- `tipopropiedad` ('Propia' | 'Externa', requerido).
- `placa` (STRING, requerido, único).
- `idcondado` (INT, FK a `Dim_Condado`, requerido — reemplaza a `zonacobertura`; determina el condado de cobertura de la unidad, usado por `despacho-inteligente` para filtrar candidatas cuando `latitud`/`longitud` no resuelve el condado del accidente).
- `capacidad` (STRING, opcional).
- `contactoproveedor` (STRING, requerido solo si `tipopropiedad = 'Externa'`).
- `unidademergencia` (STRING, requerido, nombre/identificador visible).
- `tipounidademergencia` (Ambulancia/Grúa/Patrulla/Bomberos/Defensa Civil, requerido).
- `activo` (BOOLEAN, default `true`).

Al guardar, el sistema debe:
1. Validar que no exista otra unidad activa con la misma `placa` (rechazo con HTTP 409 si hay duplicado).
2. Validar que `idcondado` exista en `Dim_Condado` (rechazo con HTTP 400 si no existe — Pinot no impone integridad referencial real, la validación es responsabilidad del servicio).
3. Insertar en `Dim_UnidadEmergencia`.
4. **No** insertar ninguna fila en `Fact_HistorialEstadoUnidad` en este paso — el estado inicial de disponibilidad se establece la primera vez que se declara explícitamente, vía `CU-O30` (módulo Emergencias, si la unidad tiene login propio) o `CU-O59` (este spec, si no lo tiene).

### RF-CAM-002: Registro de unidades en lote (CU-O56)

El Administrador debe poder importar un archivo CSV/Excel con múltiples unidades:
1. El sistema valida cada fila con las mismas reglas de `RF-CAM-001` (incluyendo duplicado de `placa`).
2. Si **todo** el archivo pasa validación, se ejecuta el `INSERT` múltiple en `Dim_UnidadEmergencia`.
3. Si alguna fila falla, el sistema debe reportar cuáles filas fallaron y por qué, sin insertar ninguna (todo o nada).
4. No existe tabla propia para el registro de importaciones — es una forma alternativa de poblar `Dim_UnidadEmergencia`, con la misma validación fila por fila que `CU-O54`.

### RF-CAM-003: Edición de unidad existente (CU-O57)

El Administrador debe poder editar los campos: `tipopropiedad`, `capacidad`, `idcondado`, `contactoproveedor`, `unidademergencia`, `tipounidademergencia`, `latitud`, `longitud`. **No** se puede modificar `idunidademergencia` ni `idcliente`.

**Concurrencia:** si dos Administradores editan la misma unidad simultáneamente, aplica last-write-wins — la última escritura en llegar sobrescribe la anterior, sin bloqueo optimista ni control de versión.

**Regla de bloqueo:** si la unidad tiene un despacho activo en curso (`Fact_Despacho` sin `fechahoraretiro`, módulo Emergencias), el sistema debe bloquear la edición de `tipopropiedad` y `tipounidademergencia`, o exigir confirmación explícita del Administrador. Esta validación se ejecuta en tiempo real contra `Fact_Despacho`; no requiere tabla nueva en este spec.

### RF-CAM-004: Dar de baja/desactivar unidad (CU-O58)

El Administrador debe poder dar de baja una unidad:
1. Validación previa: `SELECT` contra `Fact_Despacho` para verificar si la unidad tiene un despacho activo (`fechahoraretiro` nulo).
2. Insertar en `Fact_BajaUnidad`: `idunidademergencia`, `idusuario` (quién ejecuta), `idaccidente` (nullable — solo se llena si la baja fue forzada mientras existía un despacho activo, para trazar qué caso estaba en curso), `motivo`, `tipobaja` ('Normal' | 'Forzada_con_reasignación'), `fechahora`.
3. Actualizar `Dim_UnidadEmergencia.activo = false`.
4. **Reactivación:** si se requiere reactivar una unidad dada de baja, el sistema primero valida que no exista otra unidad activa con la misma `placa` (misma regla de unicidad que CU-O54/O56); si existe, rechaza la reactivación con HTTP 409. Si no hay conflicto, es un `UPDATE` de `Dim_UnidadEmergencia.activo = true`; el registro en `Fact_BajaUnidad` permanece como historial de que hubo una baja previa — no se elimina ni se modifica.

### RF-CAM-005: Gestionar disponibilidad de unidad externa (CU-O59)

El Operador de emergencias debe poder declarar la disponibilidad de una unidad que **no** tiene login propio (a diferencia de `CU-O30` del módulo Emergencias, que es la autodeclaración):
1. Insertar en `Fact_HistorialEstadoUnidad`: `idunidademergencia`, `idestadounidademergencia`, `estadoanterior`, `estadonuevo`, `idusuario` = **el operador** que recibió la información y hace la declaración (no el usuario-sistema de la unidad — esta es la diferencia funcional con `CU-O30`), `fechahora`. El Operador puede declarar cualquiera de los estados de disponibilidad —incluyendo "Fuera de servicio"— excepto "En Misión" (exclusivo del sistema).
2. **Regla de alerta:** si el operador intenta marcar como "Activa" una unidad que tiene un despacho activo sin retirar en `Fact_Despacho`, el sistema debe alertar la inconsistencia antes de aceptar el cambio. Es una validación en tiempo de ejecución, no requiere tabla nueva.

## 5. Requisitos no funcionales

### RNF-CAM-001: Validación de duplicados
La validación de `placa` duplicada (CU-O54, CU-O56) debe ejecutarse en menos de 1 segundo por unidad.

### RNF-CAM-002: Importación en lote
El procesamiento de un archivo de hasta 500 unidades (CU-O56) debe completarse en menos de 30 segundos, con reporte fila por fila de errores. 500 es un límite duro: un archivo con más de 500 filas se rechaza completo con HTTP 400 antes de procesar ninguna fila (no es solo un umbral de rendimiento esperado).

### RNF-CAM-003: Trazabilidad
Todo registro, edición, baja y reactivación de unidad debe quedar en logs del sistema con `idusuario`, timestamp y campos modificados.

## 6. Reglas de negocio

### RN-CAM-001
Unidad con `activo = false` no puede ser candidata del algoritmo de despacho ni cambiar su estado de disponibilidad hasta ser reactivada.

### RN-CAM-002
Solo el Administrador registra, edita, da de baja y reactiva unidades (CU-O54, O56, O57, O58). La declaración de disponibilidad (CU-O59) es exclusiva del Operador de emergencias.

### RN-CAM-003
`placa` debe ser única entre unidades activas — se valida en alta individual (CU-O54), en lote (CU-O56) y también al reactivar una unidad dada de baja (CU-O58).

### RN-CAM-004
La baja de una unidad (CU-O58) nunca elimina físicamente el registro. `Fact_BajaUnidad` conserva historial completo incluso tras una reactivación posterior.

### RN-CAM-005
`Dim_UnidadEmergencia.idcondado` es una FK real a `Dim_Condado` (catálogo geográfico del módulo Emergencias/registro-accidente), no a `Dim_RegionOperativa`. No existe relación directa entre `Dim_UnidadEmergencia` y `Dim_RegionOperativa` — la cobertura de una unidad se expresa a nivel de condado, no de región operativa. Este campo reemplaza al anterior `zonacobertura` (texto libre), que ya era consumido como fallback geográfico por `despacho-inteligente` (ver Sección 12, dependencia de migración).

## 7. Entradas

### Para registro individual (CU-O54)
`idcliente`, `tipopropiedad`, `placa`, `idcondado`, `capacidad`, `contactoproveedor` (si Externa), `unidademergencia`, `tipounidademergencia`, `activo`.

### Para registro en lote (CU-O56)
Archivo CSV/Excel con las mismas columnas de `CU-O54`, una fila por unidad.

### Para edición (CU-O57)
`idunidademergencia` (path param), campos editables a modificar.

### Para baja (CU-O58)
`idunidademergencia` (path param), `motivo`, `tipobaja`.

### Para disponibilidad externa (CU-O59)
`idunidademergencia`, `idestadounidademergencia` (nuevo estado), `idusuario` (operador que declara).

## 8. Salidas

- **201 Created — Unidad registrada:** `{ idunidademergencia, placa, activo: true }`.
- **200 OK — Importación en lote:** `{ insertadas, fallidas: [{ fila, motivo }] }`.
- **200 OK — Unidad actualizada:** `{ idunidademergencia, campos_modificados }`.
- **200 OK — Unidad dada de baja:** `{ idunidademergencia, activo: false }`.
- **200 OK — Disponibilidad actualizada:** `{ idunidademergencia, estadonuevo }`.
- **409 Conflict** — `placa` duplicada.
- **409 Conflict** — Baja o edición crítica con despacho activo sin confirmación explícita.
- **422 Unprocessable Entity** — Alerta de inconsistencia al marcar "Activa" con despacho sin retirar (CU-O59).

## 9. Estados posibles

### Estados de `Dim_UnidadEmergencia.activo`
- **true**: unidad operativa, candidata para despacho.
- **false**: unidad dada de baja (CU-O58), excluida del algoritmo de despacho.

### Estados de disponibilidad (`Fact_HistorialEstadoUnidad`, vía `Dim_EstadoUnidadEmergencia`)
- **Activa**: disponible para despacho.
- **Ocupada**: no disponible por otra razón operativa, declarado manualmente (no ligada a un caso activo).
- **En Misión**: atendiendo un caso activo — asignación automática del sistema (`despacho-inteligente`), no declarable vía CU-O59.
- **Fuera de servicio**: no operativa.

El estado *actual* nunca es un campo directo — se obtiene siempre consultando la fila con `fechahora` más reciente en `Fact_HistorialEstadoUnidad` para esa unidad.

## 10. Escenarios

### Escenario 1: Registro exitoso de unidad individual (CU-O54)
Dado que el Administrador registra una grúa nueva con `placa` no existente
Cuando envía el formulario
Entonces el sistema debe insertar en `Dim_UnidadEmergencia` con `activo=true`
Y no debe crear ninguna fila en `Fact_HistorialEstadoUnidad` todavía.

### Escenario 2: Rechazo por placa duplicada (CU-O54)
Dado que ya existe una unidad activa con `placa = "ABC-123"`
Cuando el Administrador intenta registrar otra unidad con la misma placa
Entonces el sistema debe rechazar con HTTP 409.

### Escenario 3: Importación en lote con una fila inválida (CU-O56)
Dado que el Administrador sube un archivo con 50 unidades
Y la fila 23 tiene una placa duplicada
Cuando se procesa el archivo
Entonces el sistema no debe insertar ninguna unidad
Y debe reportar el error específico de la fila 23.

### Escenario 4: Edición bloqueada por despacho activo (CU-O57)
Dado que una unidad tiene un despacho activo (`Fact_Despacho` sin `fechahoraretiro`)
Cuando el Administrador intenta editar `tipounidademergencia`
Entonces el sistema debe bloquear la edición o exigir confirmación explícita.

### Escenario 5: Baja forzada con despacho activo (CU-O58)
Dado que una unidad tiene un despacho activo
Cuando el Administrador fuerza la baja
Entonces el sistema debe insertar `Fact_BajaUnidad` con `tipobaja='Forzada_con_reasignación'` e `idaccidente` poblado
Y debe actualizar `Dim_UnidadEmergencia.activo=false`.

### Escenario 6: Reactivación de unidad dada de baja (CU-O58)
Dado que una unidad tiene `activo=false` con un registro histórico en `Fact_BajaUnidad`
Cuando el Administrador la reactiva
Entonces el sistema debe actualizar `Dim_UnidadEmergencia.activo=true`
Y el registro en `Fact_BajaUnidad` debe permanecer sin modificarse.

### Escenario 6b: Reactivación bloqueada por placa duplicada (CU-O58)
Dado que una unidad dada de baja tiene `placa = "ABC-123"`
Y otra unidad activa ya usa esa misma `placa`
Cuando el Administrador intenta reactivar la unidad dada de baja
Entonces el sistema debe rechazar la reactivación con HTTP 409.

### Escenario 7: Declaración de disponibilidad externa con alerta (CU-O59)
Dado que una unidad externa tiene un despacho activo sin retirar
Cuando el Operador intenta marcarla como "Activa"
Entonces el sistema debe alertar la inconsistencia antes de aceptar el cambio.

## 11. Criterios de aceptación

### CA-CAM-001
El Administrador puede registrar una unidad individual con todos los campos reales de `Dim_UnidadEmergencia` (CU-O54).

### CA-CAM-002
El sistema rechaza el registro de una unidad con `placa` duplicada entre unidades activas.

### CA-CAM-003
El Administrador puede importar un archivo con múltiples unidades; si alguna fila falla, no se inserta ninguna (CU-O56).

### CA-CAM-004
El Administrador puede editar los campos editables de una unidad, sin poder modificar `idunidademergencia` ni `idcliente` (CU-O57).

### CA-CAM-005
El sistema bloquea o exige confirmación para editar campos críticos si la unidad tiene un despacho activo.

### CA-CAM-006
El Administrador puede dar de baja una unidad; el sistema registra `Fact_BajaUnidad` y actualiza `activo=false` (CU-O58).

### CA-CAM-007
Una unidad dada de baja puede reactivarse; el historial de baja permanece intacto.

### CA-CAM-008
El Operador puede declarar disponibilidad de una unidad sin login propio, registrando `idusuario` como el operador, no la unidad (CU-O59).

### CA-CAM-009
El sistema alerta si se intenta marcar "Activa" una unidad con despacho activo sin retirar.

## 12. Dependencias

- **`autenticacion-y-rbac`:** requiere autenticación JWT y roles "Administrador" y "Operador de emergencias".
- **`registro-accidente`** (módulo Emergencias): `idcondado` referencia `Dim_Condado`, catálogo geográfico propiedad de ese spec.
- Es requerido por:
  - **`evidencia-unidad`** (módulo Emergencias): consume el catálogo de unidades y su disponibilidad.
  - **`despacho-inteligente`** (módulo Emergencias): el algoritmo de despacho solo considera unidades con `activo=true`. **Migración requerida:** hoy este spec (ya implementado) documenta y consume `zonacobertura` como texto libre casteado a int (`unidad_emergencia_repository.py::list_candidatas_por_condado`) para el filtro por condado. Al introducir `idcondado` como FK real, `despacho-inteligente` (spec, `data-model.md` y `unidad_emergencia_repository.py`) debe actualizarse para usar `idcondado` directamente y eliminar el fallback de texto. Este trabajo debe ejecutarse como parte de la implementación de `alta-unidades` o inmediatamente después, antes de que ambos specs queden desincronizados.
  - **`seguimiento-cierre-de-casos`** (módulo Emergencias): las unidades gestionadas aquí son las que se rastrean y liberan.
  - **`incorporacion-regional`** (este módulo): la disponibilidad de unidades activas en una región influye en su despublicación automática (CU-O62).

## 13. Fuera de alcance

- **Autodeclaración de disponibilidad por una unidad con login propio:** eso corresponde a `CU-O30`, spec `evidencia-unidad` (módulo Emergencias).
- **Tracking GPS en tiempo real:** eso corresponde a `seguimiento-cierre-de-casos` (módulo Emergencias).
- **Asignación de unidad a un caso:** eso corresponde a `despacho-inteligente` (módulo Emergencias).
- **Onboarding y validación de regiones operativas:** eso corresponde a `incorporacion-regional` (este módulo, spec separado).
