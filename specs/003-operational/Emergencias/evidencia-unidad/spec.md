# Especificación: Evidencia en Sitio y Gestión de Disponibilidad de Unidad

## 1. Objetivo

Enriquecer cada caso de accidente con evidencia objetiva (fotografías, notas de campo) capturada en el sitio, gestionar la disponibilidad declarada de las unidades de emergencia para el algoritmo de despacho, y sincronizar la evidencia capturada sin conexión cuando el dispositivo recupere conectividad.

## Clarifications

### Session 2026-07-09

- Q: ¿Cuál es el estado por defecto cuando una unidad no tiene filas en `Fact_HistorialEstadoUnidad`? → A: **Fuera de servicio** — excluida del despacho hasta el primer cambio explícito de estado.
- Q: ¿Qué roles pueden consultar la galería de evidencias de un caso? → A: **Técnico de campo + Unidad de emergencia + Administrador**.
- Q: ¿La evidencia offline es visible para otros usuarios antes de sincronizar? → A: **Solo en dispositivo capturador** — otros usuarios la ven tras sync completa.
- Q: ¿Qué ocurre si falla la subida parcial durante la sincronización? → A: **Reintento automático** — exitosas se persisten en backend; fallidas quedan locales y se reintentan en cada ciclo hasta éxito.
- Q: ¿Quién puede consultar estado e historial de disponibilidad de unidades? → A: **Unidad ve solo la propia; Administrador y despacho ven todas**.

## 2. Contexto

El Técnico de campo documenta cada accidente con evidencia objetiva que enriquece el expediente y sirve como respaldo para aseguradoras y auditorías. La evidencia se captura frecuentemente en zonas sin cobertura móvil, por lo que el sistema debe soportar captura offline y sincronización diferida al recuperar conexión. Simultáneamente, la Unidad de emergencia gestiona su disponibilidad para que el orquestador sepa en tiempo real qué unidades están disponibles.

**Casos de uso incluidos:**
- **CU-O27 — Adjuntar evidencias**: El Técnico de campo o Unidad de emergencia captura y sube evidencia fotográfica y notas de campo asociadas a un accidente. Soporta captura offline (marca `sincronizado=false`). La evidencia se vincula solo por `idaccidente`, sin FK directa a `Fact_Despacho`, permitiendo que múltiples unidades adjunten evidencia al mismo caso de forma independiente.
- **CU-O30 — Gestionar disponibilidad**: La Unidad de emergencia declara su estado de disponibilidad (Activa, Ocupada, Fuera de servicio). Cada cambio se registra como una nueva fila en `Fact_HistorialEstadoUnidad`. El estado actual se deriva consultando la fila con `fechahora` más reciente para esa unidad.
- **CU-O43 — Sincronizar evidencia en diferido**: Un proceso automatizado (comando de gestión o servicio en segundo plano) persiste en backend los registros capturados offline desde el almacenamiento local del dispositivo, con `sincronizado=true` en `Dim_EvidenciaFoto` y `Dim_NotaAccidente`. La `fechahora` original de captura se conserva inalterada.

**Tablas de base de datos utilizadas** (verificadas contra `tablas.json`/`esquemas.json`, ver `data-model.md`):
- `Dim_EvidenciaFoto`: evidencia fotográfica. Campos: `idevidenciafoto`, `idaccidente`, `idusuario`, `urlevidenciafoto`, `sincronizado` (Boolean), `fechahora`.
- `Dim_NotaAccidente`: notas y observaciones. Campos: `idnotaaccidentes`, `idaccidente`, `idusuario`, `nota`, `tipo`, `sincronizado` (Boolean), `fechahora`.
- `Fact_HistorialEstadoUnidad`: trazabilidad de cambios de estado. Campos: `idhistorialestadosunidadesemergencias`, `idunidademergencia`, `idestadounidademergencia` (FK a `Dim_EstadoUnidadEmergencia`), `estadoanterior`, `estadonuevo`, `fechahora`.
- `Dim_EstadoUnidadEmergencia`: catálogo de estados de unidad (Activa, Ocupada, Fuera de servicio).
- `Dim_UnidadEmergencia`: catálogo de unidades externas.


## 3. Actores

| Actor | Rol | Interacción principal |
|---|---|---|
| **Unidad de emergencia** | Operador de campo y gestor de disponibilidad | Cambia su estado de disponibilidad. Consulta su propio estado e historial. Captura evidencia fotográfica y notas. Consulta galería de evidencias del caso. |
| **Técnico de campo** | Documentador en sitio | Captura evidencia fotográfica y registra observaciones cualitativas. Consulta galería de evidencias del caso. |
| **Administrador** | Auditor y gestor del sistema | Consulta estado e historial de todas las unidades. Consulta galería de evidencias de cualquier caso (solo lectura). |
| **Sistema (despacho)** | Orquestador de despacho | Consulta estado de todas las unidades para el algoritmo de despacho (`despacho-inteligente`). |
| **Sistema** | Sincronizador automático | Ejecuta la sincronización diferida de evidencia offline al recuperar conectividad. |

## 4. Requisitos funcionales

### RF-EVI-001: Gestión de disponibilidad de unidad (CU-O30)

La Unidad de emergencia debe poder cambiar su estado de disponibilidad en cualquier momento:

| Estado | Significado |
|---|---|
| **Activa** | Disponible para recibir despachos. |
| **Ocupada** | Atendiendo un caso, no recibe nuevos despachos. |
| **Fuera de servicio** | No operativa (mantenimiento, fin de turno, avería). |

Cada cambio debe:
1. Insertar un nuevo registro en `Fact_HistorialEstadoUnidad` con `idunidademergencia`, `idestadounidademergencia`, `estadoanterior`, `estadonuevo`, `idusuario`, `fechahora`. **`idusuario`** identifica quién declaró el cambio — la propia unidad (autodeclarado, caso de este CU) o un operador declarando a nombre de una unidad sin login (caso cubierto por `CU-O59` en el módulo Red-Operativa, que comparte esta misma tabla).
2. El estado actual no es un campo directo en `Dim_UnidadEmergencia`; se obtiene siempre consultando la fila con `fechahora` más reciente en `Fact_HistorialEstadoUnidad` para esa unidad.
3. El historial de cambios debe ser consultable.

### RF-EVI-002: Registro de evidencia fotográfica (CU-O27)

El Técnico de campo o Unidad debe poder capturar y subir evidencia fotográfica desde la app móvil:
1. Tomar o seleccionar fotos desde el dispositivo.
2. Asociar la evidencia a un `idaccidente` existente.
3. Cada foto se registra en `Dim_EvidenciaFoto` con timestamp automático y campo `sincronizado`:
   - `sincronizado=true` si hay conexión al momento de subir (registro persistido en backend).
   - `sincronizado=false` si se captura sin conexión (registro solo en almacenamiento local del dispositivo capturador hasta completar sync).
4. Soporte para múltiples unidades adjuntando evidencia al mismo caso (solo vinculación por `idaccidente`, no por `Fact_Despacho`).
5. El archivo binario se almacena en Azure Blob Storage (ver `infrastructure.md` sección 3); `Dim_EvidenciaFoto.urlevidenciafoto` guarda solo la URL resultante.

### RF-EVI-003: Registro de observaciones y notas de campo (CU-O27)

Registrar notas textuales asociadas al accidente:
1. Texto libre.
2. Clasificadas por `tipo` (STRING): Observación general, Declaración de testigo, Daños materiales, Condiciones del sitio.
3. Se almacenan en `Dim_NotaAccidente` con `sincronizado` (misma lógica que evidencia fotográfica).
4. Solo vinculación por `idaccidente`.

### RF-EVI-004: Consulta de unidades por estado (CU-O30)

Consultar unidades con su estado actual (control de acceso por rol):
1. **Unidad de emergencia:** consulta solo su propio estado actual e historial (vinculado a su `idunidademergencia` de sesión). HTTP 403 si intenta consultar otra unidad.
2. **Administrador:** consulta estado e historial de cualquier unidad; puede filtrar por tipo de unidad y estado.
3. **Sistema (despacho):** consulta estado de todas las unidades activas para el algoritmo de despacho (`despacho-inteligente`).
4. **Técnico de campo** y demás roles: sin acceso a consultas de disponibilidad de unidades (HTTP 403).
5. El estado actual se obtiene de la última fila en `Fact_HistorialEstadoUnidad`.
6. Si no existe historial para la unidad, el estado actual se considera **Fuera de servicio** (excluida del despacho hasta el primer cambio explícito).

### RF-EVI-005: Visualización de evidencias por caso (CU-O27)

Ver todas las fotos y notas asociadas a un `idaccidente` (solo roles autorizados: **Técnico de campo**, **Unidad de emergencia**, **Administrador**):
1. Filtrar notas por tipo.
2. Ver fecha/hora y autor de cada evidencia.
3. Indicar visualmente si una evidencia está sincronizada o pendiente de sincronización.
4. Denegar acceso (HTTP 403) a usuarios autenticados sin uno de los roles anteriores.
5. La consulta al backend retorna solo evidencia ya sincronizada (`sincronizado=true`). El dispositivo capturador combina en su galería local las evidencias pendientes (`sincronizado=false`, solo visibles en ese dispositivo) con las ya sincronizadas del servidor.

### RF-EVI-006: Sincronización diferida de evidencia (CU-O43)

El sistema debe proveer un mecanismo para sincronizar evidencia capturada sin conexión:
1. Persistir en `Dim_EvidenciaFoto` y `Dim_NotaAccidente` los registros pendientes del almacenamiento local del dispositivo, con `sincronizado=true` tras subir binarios a Azure Blob Storage. No existen registros con `sincronizado=false` en el backend.
2. La `fechahora` original de captura debe conservarse inalterada (no se reemplaza con el momento de sincronización).
3. Ejecutable como comando de gestión (`sync_diferido`) y/o servicio en segundo plano.
4. Debe poder ejecutarse sin intervención del usuario al detectar conectividad.
5. En caso de fallo parcial (ej. timeout al subir a Azure Blob Storage), los registros exitosos se persisten en backend con `sincronizado=true`; los fallidos permanecen en almacenamiento local (`sincronizado=false`) y se reintentan automáticamente en cada ciclo de sync subsiguiente hasta completar con éxito.

## 5. Requisitos no funcionales

- **RNF-EVI-001:** App móvil offline: capturar fotos/notas sin conexión, sincronización automática al reconectar.
- **RNF-EVI-002:** Cada foto ≤ 10 MB, compresión automática antes de subir.
- **RNF-EVI-003:** Cambio de estado de unidad reflejado en ≤ 5 segundos para el algoritmo de despacho.
- **RNF-EVI-004:** Sincronización offline debe completarse en ≤ 30 segundos tras reconectar (para batch de evidencias pendientes). Los registros fallidos en un ciclo no bloquean la persistencia de los exitosos; se reintentan en ciclos posteriores.
- **RNF-EVI-005:** El proceso de sincronización diferida no debe modificar la `fechahora` original de captura.
- **RNF-EVI-006:** La consulta de estado actual de unidad debe resolverse en ≤ 2 segundos (última fila en historial).

## 6. Reglas de negocio

- **RN-EVI-001:** Solo el Administrador puede registrar unidades. Las unidades solo cambian su propia disponibilidad.
- **RN-EVI-002:** Estado "Ocupada" o "Fuera de servicio" excluye la unidad del algoritmo de despacho.
- **RN-EVI-003:** Cada cambio de estado queda en historial inmutable con `fechahora`. No se permite UPDATE ni DELETE sobre `Fact_HistorialEstadoUnidad`.
- **RN-EVI-004:** Evidencia foto y notas se vinculan a un `idaccidente` existente en `Fact_Accidente`. No requieren FK a `Fact_Despacho`.
- **RN-EVI-005:** Notas de campo son solo lectura una vez registradas en backend (INSERT-only en `Dim_NotaAccidente`). Los registros locales pendientes se persisten en backend al sincronizar (INSERT con `sincronizado=true`).
- **RN-EVI-006:** Solo se puede agregar evidencia a casos activos (estado distinto de Cerrado y Descartado).
- **RN-EVI-007:** Cada unidad tiene usuario asociado en `Dim_Usuarios` con rol "Unidad de Emergencia".
- **RN-EVI-008:** El campo `sincronizado` solo puede cambiar de `false` a `true`. No se permite revertir a `false`.
- **RN-EVI-009:** La `fechahora` de captura original no debe modificarse durante la sincronización diferida.
- **RN-EVI-010:** El estado actual de disponibilidad se deriva exclusivamente de `Fact_HistorialEstadoUnidad` (fila con `fechahora` más reciente). No existe campo redundante en `Dim_UnidadEmergencia`.
- **RN-EVI-011:** Si una unidad no tiene filas en `Fact_HistorialEstadoUnidad`, su estado actual es **Fuera de servicio** por defecto. La unidad queda excluida del algoritmo de despacho hasta registrar su primer cambio de estado.
- **RN-EVI-012:** Solo usuarios con rol **Técnico de campo**, **Unidad de emergencia** o **Administrador** pueden consultar la galería de evidencias de un caso. Otros roles autenticados reciben denegación de acceso.
- **RN-EVI-013:** Evidencia con `sincronizado=false` existe únicamente en el almacenamiento local del dispositivo que la capturó. No es visible para otros usuarios ni en consultas al backend hasta completar la sincronización.
- **RN-EVI-014:** Si la subida de un registro falla durante la sincronización, permanece en almacenamiento local y se reintenta automáticamente en cada ciclo de sync hasta éxito. Los registros ya sincronizados en el mismo batch no se revierten.
- **RN-EVI-015:** La **Unidad de emergencia** solo puede consultar su propio estado e historial. El **Administrador** y el **servicio de despacho** pueden consultar el estado e historial de todas las unidades. Otros roles reciben HTTP 403.

## 7. Entradas

- `idaccidente` (STRING, requerido para adjuntar evidencia/nota) — debe existir y estar activo en `Fact_Accidente`.
- Archivo(s) de imagen (JPEG/PNG, ≤10 MB c/u) — para evidencia fotográfica.
- `nota` (STRING, requerido si se registra observación), `tipo` (STRING: Observación general / Declaración de testigo / Daños materiales / Condiciones del sitio).
- `idunidademergencia` (INT, requerido para cambio de disponibilidad) — implícito por sesión autenticada de la unidad.
- `estadonuevo` (ENUM: Activa / Ocupada / Fuera de servicio) — estado destino del cambio de disponibilidad.
- Señal de reconexión del dispositivo (evento de sistema, no ingresado por el usuario) — dispara la sincronización diferida.

## 8. Salidas

- Registro creado en `Dim_EvidenciaFoto` o `Dim_NotaAccidente`, con `sincronizado` reflejando el estado de conexión al momento de la captura.
- Registro nuevo en `Fact_HistorialEstadoUnidad` tras cada cambio de disponibilidad, con `estadoanterior`/`estadonuevo`.
- Galería de evidencias por `idaccidente` (fotos + notas, ordenadas por `fechahora` descendente, con indicador de sincronización y autor).
- Historial de estados de una unidad, ordenado por `fechahora` descendente.
- Confirmación de sincronización diferida completada (conteo de registros sincronizados y pendientes por reintento).
- Mensajes de error/validación (ej. caso inactivo, foto >10 MB, `idaccidente` inexistente).

## 9. Estados posibles

### Estados de disponibilidad de unidad

| Estado | Significado | Incluido en despacho |
|---|---|---|
| **Activa** | Disponible para recibir despachos. | Sí |
| **Ocupada** | Atendiendo un caso, no recibe nuevos despachos. | No |
| **Fuera de servicio** | No operativa (mantenimiento, fin de turno, avería). | No |

### Diagrama de transiciones
```
Activa ←→ Ocupada
Activa ←→ Fuera de servicio
Ocupada → Activa  (al cerrar caso o retirarse)
Ocupada → Fuera de servicio  (excepción: avería durante atención)
Fuera de servicio → Activa  (al volver a estar operativa)
```

### Estados de sincronización de evidencia

| Estado (`sincronizado`) | Significado | Transición permitida |
|---|---|---|
| `false` | Capturado sin conexión, pendiente de subir (solo almacenamiento local del dispositivo capturador) | → `true` al sincronizar (persistencia en backend) |
| `true` | Sincronizado con el backend (visible para todos los roles autorizados) | Estado terminal, no revierte a `false` |

## 10. Escenarios

### Escenario 1: Cambio de estado exitoso
Dado que la Unidad de emergencia está en estado "Activa"
Cuando selecciona "Ocupada" en la app móvil
Y envía el cambio
Entonces el sistema debe insertar una fila en `Fact_HistorialEstadoUnidad`
Y debe registrar `estadoanterior="Activa"` y `estadonuevo="Ocupada"`
Y la consulta posterior de estado actual debe retornar "Ocupada".

### Escenario 2: Captura de evidencia con conexión
Dado que el Técnico de campo tiene conexión a internet
Y está en el sitio de un accidente con `idaccidente` existente
Cuando toma 3 fotos y las envía
Entonces el sistema debe crear registros en `Dim_EvidenciaFoto` con `sincronizado=true`
Y debe almacenar las imágenes en Azure Blob Storage
Y debe registrar `fechahora` con el timestamp de captura.

### Escenario 3: Captura de evidencia sin conexión
Dado que el Técnico de campo no tiene conexión a internet
Y captura 2 fotos y 1 nota
Cuando las fotos se almacenan localmente en el dispositivo
Entonces los registros locales deben marcarse como `sincronizado=false`
Y deben incluir `fechahora` con el timestamp real de captura
Y deben estar visibles en la galería local del caso en ese dispositivo
Y no deben ser visibles para otros usuarios ni en consultas al backend hasta completar la sincronización.

### Escenario 4: Sincronización diferida al reconectar
Dado que existen registros de evidencia con `sincronizado=false` en el almacenamiento local del dispositivo
Y el dispositivo recupera conectividad
Cuando se ejecuta el comando `sync_diferido` (automática o manualmente)
Entonces el sistema debe persistir los registros en `Dim_EvidenciaFoto` y `Dim_NotaAccidente` con `sincronizado=true`
Y debe conservar la `fechahora` original de captura sin modificar
Y debe subir los archivos pendientes a Azure Blob Storage.

### Escenario 4b: Fallo parcial en sincronización
Dado que existen 3 registros de evidencia con `sincronizado=false` en el almacenamiento local
Y el dispositivo recupera conectividad
Cuando se ejecuta `sync_diferido` y la subida de 1 registro falla por timeout
Entonces los 2 registros exitosos deben persistirse en backend con `sincronizado=true`
Y el registro fallido debe permanecer local con `sincronizado=false`
Y en el siguiente ciclo de sync el registro fallido debe reintentarse automáticamente hasta completar con éxito.

### Escenario 5: Consulta de galería de evidencias
Dado que un caso tiene 5 fotos y 2 notas sincronizadas en el backend
Y el dispositivo capturador tiene 1 foto pendiente local con `sincronizado=false`
Cuando el Técnico consulta la galería del caso en su dispositivo
Entonces el sistema debe mostrar las 8 evidencias (7 del servidor + 1 local pendiente) ordenadas por fecha descendente
Y debe indicar cuáles están sincronizadas y cuáles pendientes
Cuando otro usuario autorizado consulta la galería del mismo caso
Entonces solo debe ver las 7 evidencias sincronizadas del backend.

### Escenario 6: Consulta de historial de estado de unidad
Dado que una unidad ha cambiado de estado 5 veces en el día
Cuando se consulta el historial de esa unidad
Entonces el sistema debe retornar los 5 registros ordenados por `fechahora` descendente
Y el primer registro debe corresponder al estado actual.

## 11. Criterios de aceptación

### CA-EVI-001: Cambio de estado de unidad
La Unidad de emergencia cambia su estado a "Ocupada". El sistema inserta un registro en `Fact_HistorialEstadoUnidad` con `estadoanterior`, `estadonuevo` y `fechahora`. La consulta de estado actual refleja "Ocupada" inmediatamente.

### CA-EVI-002: Consulta de estado actual
La consulta de estado de una unidad retorna el estado de la fila con `fechahora` más reciente en `Fact_HistorialEstadoUnidad`. Si no hay registros, retorna **Fuera de servicio** (unidad excluida del despacho).

### CA-EVI-003: Subida de evidencia fotográfica en línea
El Técnico sube 3 fotos asociadas a un `idaccidente`. El sistema crea 3 registros en `Dim_EvidenciaFoto` con `sincronizado=true`, URLs válidas de Azure Blob Storage y `fechahora` correcta.

### CA-EVI-004: Captura de evidencia sin conexión
El Técnico captura 2 fotos sin conexión. Los registros se crean en almacenamiento local del dispositivo con `sincronizado=false` y no son visibles para otros usuarios. Al reconectar, el proceso de sync persiste los registros en backend con `sincronizado=true` sin alterar `fechahora`.

### CA-EVI-005: Registro de notas de campo
El Técnico registra una nota tipo "Declaración de testigo" para un `idaccidente`. El sistema crea un registro en `Dim_NotaAccidente` con los datos ingresados y `sincronizado=true` (si hay conexión).

### CA-EVI-006: Sincronización diferida (CU-O43)
Se ejecuta el comando `sync_diferido`. Los registros pendientes del almacenamiento local se persisten en `Dim_EvidenciaFoto` y `Dim_NotaAccidente` con `sincronizado=true`. La `fechahora` de cada registro no se modifica. Los fallidos permanecen locales y se reintentan en ciclos posteriores.

### CA-EVI-007: Galería de evidencias por caso
La consulta GET de evidencias para un `idaccidente` retorna todas las fotos y notas asociadas, ordenadas por `fechahora` descendente, con indicador de sincronización y autor. Solo accesible para roles **Técnico de campo**, **Unidad de emergencia** y **Administrador**; otros roles reciben HTTP 403.

### CA-EVI-008: Multi-unidad
Dos unidades diferentes (ej. grúa y ambulancia) adjuntan evidencia al mismo `idaccidente`. Ambas evidencias aparecen en la galería del caso sin relación con `Fact_Despacho`.

### CA-EVI-009: Historial de cambios de unidad
Se consulta el historial de estado de una unidad. El sistema retorna todas las filas de `Fact_HistorialEstadoUnidad` para esa unidad ordenadas por `fechahora` descendente. La Unidad de emergencia solo puede consultar su propio historial; el Administrador y el servicio de despacho pueden consultar cualquier unidad; otros roles reciben HTTP 403.

## 12. Dependencias

- **`autenticacion-y-rbac`:** Autenticación JWT y roles definidos (Técnico de campo, Unidad de Emergencia, Administrador).
- **`registro-accidente`:** Evidencia se vincula a `idaccidente` en `Fact_Accidente`. Requiere que el caso exista y esté activo.
- **`despacho-inteligente`:** Consume el estado actual de disponibilidad de todas las unidades para el algoritmo de despacho (acceso de servicio con permisos de consulta de flota completa).
- **`seguimiento-cierre-de-casos`:** Al cerrar un caso, las unidades asociadas deben regresar a estado Activa. Durante atención, las unidades pueden adjuntar evidencia.

## 13. Fuera de alcance

- Registro de unidades externas (**CU-O54**) → spec `alta-unidades`.
- Geolocalización GPS continua (**CU-O25**) → spec `seguimiento-cierre-de-casos`.
- Confirmación/rechazo de despachos (**CU-O24, CU-O45**) → spec `despacho-inteligente`.
- Análisis de imágenes por IA.
- Almacenamiento de video (solo fotografía fija en esta versión).
- Sincronización bidireccional de notas (solo subida, no edición remota).
