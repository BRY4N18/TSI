# Especificación: Despacho Inteligente y Asignación de Unidades

## 1. Objetivo

Minimizar el tiempo de respuesta ante un accidente de tránsito mediante la asignación inteligente de unidades de emergencia — automática o manual — con capacidad de re-asignación tras rechazo o timeout, escalamiento a zonas vecinas, y coordinación de despacho múltiple para el mismo caso. El modelo de datos implementa una relación N-N (Caso ↔ Unidad) donde cada caso puede tener múltiples despachos activos simultáneamente y se preserva el historial completo de intentos fallidos.

## Clarifications

### Session 2026-07-09

- Q: ¿El algoritmo O22 debe filtrar unidades geográficamente desde el primer intento o evaluar todas las unidades activas del sistema? → A: Mismo condado primero (vía `idcalle` → `Dim_Ciudad` → `Dim_Condado`); O34 amplía a condados vecinos.
- Q: ¿Qué fuente de ubicación usar para el cálculo Haversine de cada unidad candidata? → A: `Dim_UnidadEmergencia.latitud/longitud` primario; si `Dim_HistorialUbicacionUnidadEmergencia` tiene fila más reciente (por `fechahora`), usar historial.
- Q: ¿Cuándo debe pasar `Fact_Despacho.activo` a `false` tras rechazo o timeout? → A: `activo=false` inmediatamente al Rechazar o Timeout; permanece `activo=true` mientras Pendiente o Confirmado.
- Q: ¿Cómo se dispara O36 tras el timeout O35? → A: Evento asíncrono: O35 publica evento de dominio; un worker O36 independiente consume y re-asigna.
- Q: ¿Qué hacer si push y SMS fallan al notificar despacho (O23)? → A: Tras un reintento fallido en ambos canales, marcar fallo de entrega y disparar O36 inmediatamente (sin esperar timeout).

## 2. Contexto

Cuando un accidente es registrado en TSI, el sistema ejecuta un algoritmo de asignación inteligente que evalúa en tiempo real todas las unidades disponibles, selecciona la óptima según criterios múltiples y notifica a la unidad para que confirme o rechace el despacho. El modelo de datos soporta una relación N-N (Caso ↔ Unidad) donde un caso puede tener múltiples despachos activos (grúa + ambulancia + policía) y se mantiene un historial completo de intentos fallidos (rechazos, timeouts, re-asignaciones).

**Casos de uso incluidos:**

| CU | Nombre | Actor | Tablas principales |
|----|--------|-------|-------------------|
| CU-O22 | Asignación automática de unidad | Sistema | Fact_NotificacionDespacho, Fact_Despacho, Fact_HistorialDespachoUnidad, Fact_AccidenteTipoEstadoAccidente |
| CU-O23 | Notificar despacho | Sistema | Fact_NotificacionDespacho (UPDATE) |
| CU-O24 | Confirmar despacho | Unidad de emergencia | Fact_NotificacionDespacho, Fact_HistorialDespachoUnidad, Fact_HistorialEstadoUnidad, Fact_AccidenteTipoEstadoAccidente |
| CU-O33 | Asignar unidad manualmente | Operador | Igual que O22, idorigendespacho=Manual |
| CU-O34 | Escalar caso a zona | Sistema / Operador | Igual que O22 (zona vecina) o Dim_NotaAccidente (sin unidades) |
| CU-O35 | Timeout de despacho | Sistema (job) | Fact_HistorialDespachoUnidad, evento `DespachoTimeout` |
| CU-O36 | Re-asignación tras rechazo o timeout | Sistema (worker) | Igual que O22 (mismo idaccidente, nueva unidad) |
| CU-O38 | Coordinar despacho múltiple | Operador | Igual que O22 (nueva unidad, mismo caso activo) |
| CU-O45 | Rechazar despacho | Unidad de emergencia | Fact_NotificacionDespacho (UPDATE con motivo), Fact_HistorialDespachoUnidad |

**Tablas de base de datos:**

- `Fact_Accidente` (`idaccidente`, `latitudinicio`, `longitudinicio`, `idseveridad`, `numheridos`, `numvehiculos`): datos del accidente a atender.
- `Fact_Despacho` (`iddespacho`, `idaccidente`, `idunidademergencia`, `idnotificaciondespacho`, `fechahoradespacho`, `fechahorallegada`, `fechahoraretiro`, `idorigendespacho`, `activo`): tabla intermedia N-N que vincula caso y unidad. Cada fila representa un intento de asignación.
- `Fact_NotificacionDespacho` (`idnotificaciondespacho`, `idaccidente`, `idunidaddemergencia`, `estadonotificaciondespacho`, `motivo`, `numheridos`, `numvehiculos`): registro separado de cada notificación enviada a una unidad. *(Nota: el campo se llama `idunidaddemergencia`, no `idunidademergencia` — así está definido en el esquema real de Pinot; se preserva tal cual para que coincida con la implementación.)*
- `Fact_HistorialDespachoUnidad` (`iddespacho`, `idestadodespacho`, `estadoanterior`, `estadonuevo`, `fechahora`): historial de cambios de estado de cada despacho.
- `Dim_EstadoDespacho` (Pendiente, Confirmado, Rechazado, Timeout, Abortado, En_sitio, Retirado): catálogo de estados de despacho.
- `Dim_OrigenDespacho` (Automático, Manual, Escalado_zona): catálogo de orígenes de despacho.
- `Dim_UnidadEmergencia` (`idunidademergencia`, `tipounidademergencia`, `latitud`, `longitud`, `zonacobertura`): catálogo de unidades de emergencia; `latitud`/`longitud` es el snapshot de última posición conocida.
- `Dim_HistorialUbicacionUnidadEmergencia` (`idunidademergencia`, `latitud`, `longitud`, `fechahora`): trayectoria GPS de la unidad; se usa para distancia Haversine cuando su `fechahora` es más reciente que el snapshot en `Dim_UnidadEmergencia`.
- `Fact_HistorialEstadoUnidad` (`idunidademergencia`, `idestadounidademergencia`, `estadoanterior`, `estadonuevo`, `fechahora`): historial de disponibilidad de cada unidad (estado actual = fila con fechahora más reciente).
- `Dim_EstadoUnidadEmergencia` (Activa, Ocupada, Fuera_de_servicio): catálogo de estados de unidad.
- `Dim_Severidad` (`idseveridad`, `severidad`): nivel de gravedad del accidente.
- `Fact_AccidenteTipoEstadoAccidente` (`idaccidente`, `idtipoestadoincidente`, `idusuario`, `fechahoramodificado`): historial de estados del caso.
- `Dim_TipoEstadoAccidente` (Borrador, Reportado, Buscando_Unidad, Asignado, En_Atención, Cerrado, Descartado, Fusionado): catálogo de estados del caso.
- `Dim_NotaAccidente` (`idnotaaccidentes`, `idaccidente`, `nota`, `tipo`, `activo`): notas y alertas asociadas al caso.


## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Sistema** | Algoritmo de despacho y jobs automáticos | Ejecuta el cálculo de unidad óptima, envía notificaciones, maneja re-asignaciones. Ejecuta job de timeout (O35). |
| **Sistema (job)** | Job programado de timeout | Compara `fechahoradespacho` contra umbral; marca Timeout, publica evento `DespachoTimeout`. |
| **Sistema (worker O36)** | Consumidor de re-asignación | Consume eventos `DespachoTimeout` y ejecuta la lógica de re-asignación (O36). |
| **Unidad de emergencia** | Receptor, confirmador y rechazador | Recibe notificación push/SMS. Confirma (O24) o rechaza con motivo (O45). |
| **Operador de emergencias** | Supervisor humano | Asigna manualmente (O33), escala a zona vecina (O34), coordina despacho múltiple (O38), monitorea el proceso. |

## 4. Requisitos funcionales

### RF-DES-001: Algoritmo de asignación inteligente (O22)

El Sistema debe ejecutar automáticamente el siguiente algoritmo cuando se registra un nuevo accidente (`Fact_Accidente`) en estado "Reportado":

1. **Obtener ubicación del accidente:** `latitudinicio`, `longitudinicio` del `idaccidente`.
2. **Filtrar unidades candidatas:** consultar unidades en `Dim_UnidadEmergencia` que cumplan:
   - `activo = true`.
   - Última fila en `Fact_HistorialEstadoUnidad` tiene `idestadounidademergencia` = "Activa".
   - No tener un despacho activo (`Fact_Despacho.activo=true`) para el mismo accidente.
   - Pertenecer al mismo `Dim_Condado` del accidente: resolver `Fact_Accidente.idcalle` → `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado` y filtrar unidades cuya ubicación (`latitud`, `longitud`) o `zonacobertura` caiga en ese condado.
3. **Calcular distancia:** para cada unidad candidata, resolver su posición efectiva:
   - Tomar `Dim_UnidadEmergencia.latitud`, `Dim_UnidadEmergencia.longitud` como base.
   - Si existe fila en `Dim_HistorialUbicacionUnidadEmergencia` con `fechahora` más reciente que `Dim_UnidadEmergencia.fecha_actualizacion`, usar `latitud`/`longitud` de esa fila.
   - Calcular distancia en línea recta desde la posición efectiva hasta `latitudinicio`/`longitudinicio` del accidente, usando la fórmula de Haversine.
4. **Evaluar concordancia por tipo de emergencia:**
   - Si `idseveridad` corresponde a niveles con víctimas/heridos (Grave, Fatal), priorizar ambulancias.
   - Si el accidente involucra daños materiales sin heridos (Leve, Moderado), priorizar grúas.
   - En todos los casos, las patrullas pueden ser asignadas para gestión de tráfico.
   - El Director Tecnológico puede configurar prioridades por tipo de emergencia vía parámetros del sistema.
5. **Seleccionar la unidad óptima:** ordenar candidatas por puntuación ponderada:
   - Proximidad geográfica (mayor peso: 60%).
   - Disponibilidad reciente (unidades que llevan más tiempo en estado "Activa" continuo tienen preferencia: 15%).
   - Concordancia de tipo de unidad con severidad del accidente (25%).
6. **Asignar y persistir:**
   - INSERT en `Fact_NotificacionDespacho`: `idaccidente`, `idunidaddemergencia`, `numheridos`, `numvehiculos`, `estadonotificaciondespacho` = Pendiente.
   - INSERT en `Fact_Despacho`: `idaccidente`, `idunidademergencia`, `idnotificaciondespacho`, `fechahoradespacho=now`, `idorigendespacho` = Automático, `activo=true`.
   - INSERT en `Fact_HistorialDespachoUnidad`: `iddespacho`, `idestadodespacho` = Pendiente, `fechahora`.
   - INSERT en `Fact_AccidenteTipoEstadoAccidente`: estado `idtipoestadoincidente` = BUSCANDO_UNIDAD (solo si es el primer despacho del caso).

### RF-DES-002: Notificar despacho a la unidad (O23)

Tras la inserción de O22/O33/O34, el Sistema debe enviar automáticamente una notificación a la unidad seleccionada (push + SMS de respaldo) que incluya:

- `idaccidente` y `idseveridad` (tipo y gravedad del accidente).
- `descripcion` del accidente (narrativa ingresada por el Operador).
- Dirección aproximada (calle, ciudad obtenidas de `Dim_Calle`, `Dim_Ciudad`).
- Coordenadas exactas (`latitudinicio`, `longitudinicio`).
- Ruta sugerida desde la ubicación actual de la unidad hasta el sitio del accidente (mapa con trazo).
- Tiempo estimado de llegada (ETA).

Ambas notificaciones incluyen un botón/enlace para "Aceptar" (O24) o "Rechazar" (O45) el despacho.

**Entrega exitosa:** UPDATE `Fact_NotificacionDespacho.estadonotificaciondespacho` = "Notificada" cuando al menos un canal (push o SMS) confirma entrega.

**Fallo de entrega:** si push y SMS fallan, el sistema reintenta una vez cada canal. Si tras el reintento ambos canales siguen fallando:
- UPDATE `Fact_NotificacionDespacho.estadonotificaciondespacho` = "No_entregada", `motivo` = detalle del fallo.
- UPDATE `Fact_Despacho`: `activo` = `false` para el `iddespacho` afectado.
- INSERT en `Fact_HistorialDespachoUnidad`: `idestadodespacho` = Rechazado, `estadonuevo` = "No_entregada", `motivo` implícito = fallo de entrega (no es rechazo de la unidad; RN-DES-006 no aplica exclusión).
- Disparar re-asignación O36 de forma **síncrona e inmediata** (sin esperar timeout O35).

### RF-DES-003: Confirmar despacho (O24)

La Unidad de emergencia debe poder responder a la notificación de despacho con "Confirmada". El sistema:

- UPDATE `Fact_NotificacionDespacho.estadonotificaciondespacho` = "Confirmada".
- INSERT en `Fact_HistorialDespachoUnidad`: `iddespacho`, `estadoanterior`="Pendiente", `estadonuevo`="Confirmado", `idestadodespacho` = Confirmado, `fechahora`.
- INSERT en `Fact_HistorialEstadoUnidad`: unidad pasa a estado Ocupada.
- INSERT en `Fact_AccidenteTipoEstadoAccidente`: estado ASIGNADO (solo si es el primer despacho confirmado del caso; si ya hay otro despacho confirmado previamente, no se repite).
- Notifica al Operador que la unidad fue asignada y está en camino.

### RF-DES-004: Rechazar despacho con motivo (O45)

La Unidad de emergencia debe poder responder a la notificación de despacho con "Rechazada", incluyendo un campo `motivo` (texto libre). El sistema:

- UPDATE `Fact_NotificacionDespacho`: `estadonotificaciondespacho` = "Rechazada", `motivo` = texto ingresado por la unidad.
- UPDATE `Fact_Despacho`: `activo` = `false` para el `iddespacho` rechazado.
- INSERT en `Fact_HistorialDespachoUnidad`: `idestadodespacho` = Rechazado.
- Dispara automáticamente re-asignación (RF-DES-006).

### RF-DES-005: Timeout de despacho sin respuesta (O35)

Un job programado debe ejecutarse periódicamente (por defecto cada 30 segundos) y:

1. Consultar `Fact_Despacho` con `activo=true` cuyo `fechahoradespacho` supere el umbral configurable (por defecto 90 segundos).
2. Para cada uno, verificar que su último estado en `Fact_HistorialDespachoUnidad` sea "Pendiente".
3. UPDATE `Fact_Despacho`: `activo` = `false` para el `iddespacho` en timeout.
4. INSERT en `Fact_HistorialDespachoUnidad`: `idestadodespacho` = Timeout.
5. Publicar evento de dominio `DespachoTimeout` (vía Kafka) con `idaccidente`, `iddespacho` y `fechahora`; **no** invocar O36 en el mismo ciclo del job.

### RF-DES-006: Re-asignación tras rechazo o timeout (O36)

Tras un rechazo (O45) o timeout (O35), el Sistema debe crear un nuevo intento de despacho:

- **Timeout (O35):** un worker O36 independiente consume el evento `DespachoTimeout` y ejecuta la lógica de re-asignación de forma asíncrona.
- **Rechazo (O45):** dispara re-asignación de forma síncrona (invocación directa a la misma lógica O36).
- **Fallo de entrega (O23):** dispara re-asignación de forma síncrona e inmediata (invocación directa a la misma lógica O36).

- INSERT en `Fact_NotificacionDespacho` + `Fact_Despacho` (mismo `idaccidente`, nueva `idunidademergencia`).
- `idorigendespacho` = Automático (o Escalado_zona si aplicó O34).
- El despacho anterior queda con `activo=false` y permanece en `Fact_HistorialDespachoUnidad` como historial del intento fallido.
- El proceso continúa hasta que una unidad confirme o se agoten todas las candidatas.

Si se agotan las candidatas, escalar al Operador para intervención manual y generar alerta crítica.

### RF-DES-007: Asignación manual de unidad (O33)

El Operador debe poder seleccionar manualmente una unidad desde la interfaz de monitoreo. El sistema ejecuta el mismo patrón de persistencia que O22, con la única diferencia:

- `Fact_Despacho.idorigendespacho` = Manual.
- El registro de auditoría del despacho refleja al operador que decidió, no al algoritmo.

### RF-DES-008: Escalamiento a zona vecina (O34)

Si el algoritmo no encuentra unidades disponibles en el condado del accidente (o si el Operador lo solicita explícitamente), el sistema debe:

1. Ampliar la consulta de `Dim_UnidadEmergencia` a **condados vecinos** del condado del accidente (misma jerarquía `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado`; vecindad definida por condados adyacentes en la misma `Dim_Ciudad` o condados limítrofes según catálogo geográfico).
2. Si encuentra unidad(es): mismo patrón O22 con `idorigendespacho` = Escalado_zona.
3. Si no encuentra ninguna: INSERT en `Dim_NotaAccidente` (`idaccidente`, `idusuario`, `nota`="Sin unidades disponibles en condado ni condados vecinos", `tipo`=alerta, `activo=true`).

### RF-DES-009: Coordinar despacho múltiple (O38)

Para un caso que ya tiene uno o más despachos activos, el Operador debe poder asignar una nueva unidad adicional (ej. ambulancia sumándose a una grúa ya asignada). El sistema:

- Ejecuta el mismo patrón que O22/O33 para el **mismo `idaccidente`** con una **nueva `idunidademergencia`**.
- `idorigendespacho` = Manual.
- Valida que la nueva unidad no tenga ya un despacho activo (`Fact_Despacho.activo=true`) para el mismo caso.
- INSERT en `Fact_NotificacionDespacho` + `Fact_Despacho` + `Fact_HistorialDespachoUnidad`.

### RF-DES-010: Parámetros configurables del algoritmo

El Director Tecnológico y el Administrador deben poder configurar los siguientes parámetros del algoritmo de despacho:

- **Timeout de respuesta:** tiempo máximo que una unidad tiene para aceptar/rechazar (por defecto: 90 segundos, rango: 30-300 segundos).
- **Peso de distancia:** porcentaje de peso del factor proximidad en la puntuación (por defecto: 60%, rango: 40-80%).
- **Peso de concordancia de tipo:** porcentaje del factor tipo de unidad vs severidad (por defecto: 25%).
- **Peso de disponibilidad:** porcentaje del factor tiempo continuo en estado Activa (por defecto: 15%).
- **Prioridades por tipo de emergencia:** mapping de `idseveridad` a `tipounidademergencia` preferido (ej. idseveridad=4 (Fatal) → prioridad: Ambulancia, luego Patrulla, luego Grúa).

Estos parámetros afectan a todos los despachos subsecuentes. Los cambios se registran en los logs del sistema.

### RF-DES-011: Monitoreo del proceso de despacho

El Operador de emergencias debe poder ver en tiempo real el estado del proceso de despacho para cada accidente activo:

- Unidad(es) asignada(s) actualmente (o "Buscando unidad...").
- Historial de intentos (unidades notificadas y su respuesta: Confirmado / Rechazado con motivo / Timeout / Pendiente).
- Tiempo transcurrido desde el registro del accidente.
- Mapa con ubicación del accidente y posición de unidades candidatas.

## 5. Requisitos no funcionales

### RNF-DES-001: Tiempo de despacho

El proceso completo desde el registro del accidente hasta la confirmación de unidad asignada debe completarse en menos de 2 minutos en el percentil 95 (meta operativa del BSC). Para accidentes en zonas urbanas con al menos 3 unidades activas en radio de 10 km, el tiempo objetivo es menos de 60 segundos.

### RNF-DES-002: Precisión del cálculo de distancia

El cálculo de distancia Haversine debe tener una precisión de al menos 99% para distancias de hasta 100 km, utilizando la posición efectiva de la unidad (snapshot en `Dim_UnidadEmergencia` o historial GPS más reciente en `Dim_HistorialUbicacionUnidadEmergencia`, según RF-DES-001) y las coordenadas GPS almacenadas en `Fact_Accidente`.

### RNF-DES-003: Disponibilidad del servicio de despacho

El algoritmo de despacho debe ejecutarse de forma síncrona e inmediata al registrarse un accidente. No debe haber demora perceptible entre el registro del accidente y el inicio del algoritmo de asignación.

### RNF-DES-004: Notificaciones push

Las notificaciones push a la app móvil de la unidad deben entregarse en menos de 5 segundos desde la selección de la unidad óptima. El SMS de respaldo debe entregarse en menos de 30 segundos.

## 6. Reglas de negocio

### RN-DES-001

Solo las unidades con estado "Activa" (última fila en `Fact_HistorialEstadoUnidad`) y `activo = true` en `Dim_UnidadEmergencia` son consideradas candidatas para despacho. Una unidad en estado "Ocupada" o "Fuera_de_servicio" no puede recibir notificaciones de despacho. En el intento inicial (O22), las candidatas deben pertenecer al mismo `Dim_Condado` del accidente; el escalamiento (O34) amplía a condados vecinos.

### RN-DES-002

La relación entre Caso (`Fact_Accidente`) y Unidad (`Dim_UnidadEmergencia`) es N-N, materializada en `Fact_Despacho`. Un caso puede tener múltiples despachos activos simultáneamente (ej. grúa + ambulancia + policía). Una unidad puede tener solo un despacho `activo=true` a la vez (no puede estar asignada a dos casos simultáneamente). `Fact_Despacho.activo` permanece `true` mientras el despacho esté Pendiente o Confirmado; pasa a `false` al registrar Rechazado o Timeout.

### RN-DES-003

El timeout de respuesta es configurable pero no puede ser menor a 30 segundos ni mayor a 300 segundos, para balancear rapidez de respuesta con tiempo razonable para que la unidad evalúe el despacho.

### RN-DES-004

La concordancia de tipo de unidad con severidad usa las siguientes reglas por defecto:
- Severidad "Fatal" o "Grave" → prioridad: Ambulancia.
- Severidad "Moderada" → prioridad: Ambulancia o Grúa (según descripción del accidente).
- Severidad "Leve" → prioridad: Grúa o Patrulla.

El Director Tecnológico puede modificar estas prioridades.

### RN-DES-005

El algoritmo no tiene un número máximo de reintentos predefinido. El sistema sigue intentando con nuevas unidades (vía O36) hasta que una confirme o se agoten las candidatas disponibles. Cada intento fallido queda registrado como una fila en `Fact_HistorialDespachoUnidad`.

### RN-DES-006

Una unidad que rechaza un despacho debe permanecer en estado "Activa" y puede ser candidata para otros accidentes, excepto para el mismo accidente que rechazó (para evitar bucles de reasignación a la misma unidad).

### RN-DES-007

El tiempo transcurrido desde el registro del accidente hasta la confirmación del primer despacho (`fechahoradespacho` en `Fact_Despacho` con estado Confirmado) se utiliza como métrica de tiempo de respuesta (KPI del BSC).

### RN-DES-008

El caso pasa a estado ASIGNADO solo cuando al menos un `Fact_Despacho` alcanza estado Confirmado (vía O24). Mientras tanto, permanece en BUSCANDO_UNIDAD aunque haya despachos Pendientes, Rechazados o Timeout. El estado del Caso es una función del conjunto de estados de sus despachos.

### RN-DES-009

Múltiples intentos fallidos para el mismo caso quedan registrados en `Fact_HistorialDespachoUnidad` (con estados Rechazado o Timeout) y en `Fact_Despacho` (cada intento es una fila independiente). No se sobrescribe historial: solo se agregan filas con `fechahora` creciente.

### RN-DES-010

La posición efectiva de una unidad para despacho se resuelve así: `Dim_UnidadEmergencia.latitud/longitud` por defecto; si `MAX(fechahora)` en `Dim_HistorialUbicacionUnidadEmergencia` para esa unidad es posterior a `Dim_UnidadEmergencia.fecha_actualizacion`, prevalece la coordenada del historial.

### RN-DES-011

Si push y SMS fallan tras un reintento en O23, el despacho no permanece en espera de timeout: se marca `No_entregada`, se desactiva el `Fact_Despacho` (`activo=false`) y se ejecuta O36 de inmediato. El fallo de entrega **no** excluye a la unidad de futuros despachos para el mismo accidente (a diferencia de un rechazo explícito en RN-DES-006).

## 7. Entradas

### Disparador automático (CU-O22, CU-O23)
- `idaccidente` recién creado en `Fact_Accidente` con estado "Reportado".
- Coordenadas GPS del accidente: `latitudinicio`, `longitudinicio`.
- `idseveridad` para evaluar concordancia de tipo de unidad.

### Asignación manual (CU-O33)
- `idaccidente` existente en estado BUSCANDO_UNIDAD o ASIGNADO.
- `idunidademergencia` seleccionada manualmente por el Operador.

### Escalamiento a zona (CU-O34)
- `idaccidente` sin unidades disponibles en zona actual.

### Timeout (CU-O35)
- Job programado: compara fechahoradespacho contra umbral configurable.

### Re-asignación (CU-O36)
- Disparado síncronamente tras O45 (rechazo) o fallo de entrega O23.
- Disparado asíncronamente por worker O36 al consumir evento `DespachoTimeout` publicado por O35.

### Coordinación múltiple (CU-O38)
- `idaccidente` con al menos un despacho activo.
- `idunidademergencia` nueva para asignar al mismo caso.

### Confirmación / Rechazo (CU-O24 / CU-O45)
- `idunidademergencia` que responde.
- `idaccidente` del despacho.
- Respuesta: "Confirmada" o "Rechazada".
- Para rechazo: `motivo` (texto libre).

### Parámetros configurables
- Timeout de respuesta (segundos, 30-300).
- Pesos del algoritmo (distancia, concordancia, disponibilidad).
- Prioridades por tipo de emergencia (mapping severidad → tipo de unidad).

## 8. Salidas

### Respuestas del sistema
- **Notificación push/SMS a la unidad:** datos del accidente, coordenadas, ruta sugerida, botones Aceptar/Rechazar.
- **Confirmación al Operador:** `{ "idaccidente": 12345, "idunidademergencia": 42, "unidademergencia": "Ambulancia 05", "fechahoradespacho": "...", "estado_caso": "ASIGNADO" }`
- **Alerta de escalamiento:** cuando se agotan las unidades candidatas: `{ "tipo": "CRITICA", "idaccidente": 12345, "mensaje": "Sin unidades disponibles. Requiere intervención manual." }`
- **Nota de alerta (O34):** cuando no hay unidades en condado ni condados vecinos: `{ "tipo": "alerta", "idaccidente": 12345, "nota": "Sin unidades disponibles en condado ni condados vecinos" }`

### Registro en base de datos
- Nuevos registros en `Fact_NotificacionDespacho`, `Fact_Despacho`, `Fact_HistorialDespachoUnidad`, `Fact_HistorialEstadoUnidad`, `Fact_AccidenteTipoEstadoAccidente`.
- Actualizaciones en `Fact_NotificacionDespacho` (estado + motivo).

## 9. Estados posibles

### Estado del Caso (Fact_AccidenteTipoEstadoAccidente + Dim_TipoEstadoAccidente)
- **BUSCANDO_UNIDAD:** el caso tiene despachos Pendientes, Rechazados o Timeout; aún no hay confirmación.
- **ASIGNADO:** al menos un despacho fue confirmado; hay unidad(es) en camino.

### Estado del Despacho (Fact_HistorialDespachoUnidad + Dim_EstadoDespacho)
- **Pendiente:** notificación enviada, esperando respuesta de la unidad.
- **Confirmado:** la unidad aceptó el despacho.
- **Rechazado:** la unidad rechazó (con motivo registrado).
- **Timeout:** la unidad no respondió en el tiempo configurado.
- **Abortado:** la unidad abortó la misión en tránsito (CU-O39, fuera de este spec).
- **En_sitio:** la unidad llegó al lugar del accidente (CU-O26, fuera de este spec).
- **Retirado:** la unidad se retiró del sitio (CU-O28, fuera de este spec).

### Estado de la Unidad (Fact_HistorialEstadoUnidad + Dim_EstadoUnidadEmergencia)
- **Activa:** disponible para recibir despachos.
- **Ocupada:** asignada a un caso activo.
- **Fuera_de_servicio:** no disponible (mantenimiento, descanso, etc.).

### Transiciones del proceso de despacho
```
Reportado → BUSCANDO_UNIDAD (primer despacho creado)
BUSCANDO_UNIDAD → Pendiente (notificación enviada)
Pendiente → Confirmado (unidad acepta) → ASIGNADO (primer despacho confirmado del caso)
Pendiente → Rechazado (unidad rechaza) → BUSCANDO_UNIDAD (se reinicia búsqueda vía O36)
Pendiente → Timeout (no responde) → evento DespachoTimeout → BUSCANDO_UNIDAD (worker O36 reinicia búsqueda)
BUSCANDO_UNIDAD → Sin unidades disponibles → Alerta crítica, escalar a Operador
```

## 10. Escenarios

### Escenario 1: Despacho exitoso en primer intento (O22 + O23 + O24)

Dado que se registra un accidente grave (`idseveridad = 4`, Fatal) en `Fact_Accidente`
Y hay 5 ambulancias activas en la región
Cuando el Sistema ejecuta el algoritmo de asignación
Entonces debe calcular la distancia Haversine desde cada ambulancia al sitio
Y debe priorizar ambulancias por concordancia de tipo (Fatal → Ambulancia)
Y debe seleccionar la de mayor puntuación ponderada
Y debe INSERT en Fact_NotificacionDespacho (Pendiente), Fact_Despacho (Automático), Fact_HistorialDespachoUnidad (Pendiente), Fact_AccidenteTipoEstadoAccidente (BUSCANDO_UNIDAD)
Y debe notificar push y SMS a la unidad seleccionada
Y si la unidad confirma (O24), debe UPDATE Fact_NotificacionDespacho → Confirmada, INSERT en Fact_HistorialDespachoUnidad → Confirmado, Fact_HistorialEstadoUnidad → Ocupada, Fact_AccidenteTipoEstadoAccidente → ASIGNADO.

### Escenario 2: Primera unidad rechaza, re-asignación a segunda (O45 + O36)

Dado que la unidad "Ambulancia 05" recibe una notificación de despacho
Y evalúa que está demasiado lejos (ETA > 15 min)
Cuando rechaza el despacho con motivo "Muy lejos"
Entonces el sistema debe UPDATE Fact_NotificacionDespacho.estadonotificaciondespacho = "Rechazada", motivo = "Muy lejos"
Y debe UPDATE Fact_Despacho.activo = false
Y debe INSERT en Fact_HistorialDespachoUnidad con idestadodespacho = Rechazado
Y debe ejecutar O36: nuevo Fact_NotificacionDespacho + Fact_Despacho (mismo idaccidente, nueva unidad)
Y debe notificar a la siguiente unidad óptima.

### Escenario 3: Timeout sin respuesta (O35)

Dado que la unidad "Grúa 08" recibe una notificación de despacho
Y no responde en 90 segundos (timeout por defecto)
Cuando el job de timeout (O35) ejecuta su ciclo
Entonces debe verificar que el último estado en Fact_HistorialDespachoUnidad siga siendo "Pendiente"
Y debe UPDATE Fact_Despacho.activo = false
Y debe INSERT en Fact_HistorialDespachoUnidad con idestadodespacho = Timeout
Y debe publicar evento DespachoTimeout en Kafka
Y el worker O36 debe consumir el evento y ejecutar re-asignación a la siguiente unidad.

### Escenario 4: Sin unidades disponibles

Dado que un accidente ocurre en una zona con solo 2 unidades activas
Y ambas rechazan el despacho
Cuando el sistema agota las candidatas
Entonces debe generar una alerta crítica: "Sin unidades disponibles para accidente #12345"
Y debe notificar al Operador de emergencias para intervención manual.

### Escenario 5: Configuración de parámetros del algoritmo (RF-DES-010)

Dado que el Director Tecnológico quiere ajustar el peso de proximidad de 60% a 70%
Y reducir el timeout de 90s a 60s
Cuando modifica los parámetros desde el panel de configuración
Entonces el sistema debe guardar los nuevos valores
Y los despachos subsecuentes deben usar los nuevos parámetros
Y el cambio debe registrarse en los logs del sistema.

### Escenario 6: Asignación manual por el Operador (O33)

Dado que un accidente está en estado BUSCANDO_UNIDAD
Y el Operador decide asignar manualmente una unidad específica
Cuando selecciona la unidad desde la interfaz de monitoreo
Entonces el sistema debe ejecutar el patrón O22 con idorigendespacho = Manual
Y el auditoría del despacho debe reflejar al operador que lo asignó.

### Escenario 7: Escalamiento a zona vecina (O34)

Dado que un accidente ocurre en un condado sin unidades activas disponibles
Cuando el Sistema (u Operador) solicita escalar la búsqueda
Entonces el sistema debe ampliar la consulta a condados vecinos (Dim_Calle → Dim_Ciudad → Dim_Condado)
Y si encuentra unidad en condado vecino, ejecutar O22 con idorigendespacho = Escalado_zona
Y si no encuentra ninguna, INSERT en Dim_NotaAccidente con alerta de "Sin unidades disponibles en condado ni condados vecinos".

### Escenario 8: Coordinación de despacho múltiple (O38)

Dado que un caso ya tiene una grúa confirmada (Fact_Despacho activo)
Y el Operador decide asignar también una ambulancia
Cuando selecciona una ambulancia disponible desde la interfaz
Entonces el sistema debe INSERT nueva Fact_NotificacionDespacho + Fact_Despacho (mismo idaccidente, nueva unidad)
Y la nueva unidad recibe su propia notificación de despacho.

### Escenario 9: Rechazo con motivo completo (O45)

Dado que la unidad "Patrulla 03" recibe una notificación de despacho
Y está en medio de otra intervención
Cuando rechaza el despacho ingresando motivo "Ya estoy atendiendo otro incidente"
Entonces el sistema debe registrar el motivo completo en Fact_NotificacionDespacho.motivo
Y debe INSERT Rechazado en Fact_HistorialDespachoUnidad
Y debe disparar O36 para re-asignación.

### Escenario 10: Fallo de entrega de notificación (O23 + O36)

Dado que el sistema selecciona una unidad y ejecuta O23
Y push y SMS fallan en el primer intento
Y ambos canales fallan nuevamente en el reintento
Cuando se confirma el fallo de entrega
Entonces debe UPDATE Fact_NotificacionDespacho.estadonotificaciondespacho = "No_entregada"
Y debe UPDATE Fact_Despacho.activo = false
Y debe INSERT Rechazado (No_entregada) en Fact_HistorialDespachoUnidad
Y debe ejecutar O36 de forma síncrona e inmediata hacia la siguiente unidad candidata.

## 11. Criterios de aceptación

### CA-DES-001
Al registrarse un accidente, el sistema ejecuta automáticamente el algoritmo de asignación en menos de 5 segundos.

### CA-DES-002
El algoritmo considera tres factores: proximidad geográfica (Haversine), disponibilidad desde Fact_HistorialEstadoUnidad, y concordancia de tipo de unidad con severidad.

### CA-DES-003
La unidad seleccionada recibe notificación push y SMS con datos del accidente, coordenadas, ruta sugerida y botones Aceptar/Rechazar. Si ambos canales fallan tras reintento, se marca No_entregada y se re-asigna de inmediato (CA-DES-013).

### CA-DES-004
Si la unidad confirma, se actualiza Fact_NotificacionDespacho a Confirmada, se inserta Fact_HistorialDespachoUnidad con estado Confirmado, la unidad pasa a Ocupada, y el caso pasa a ASIGNADO (si era el primer despacho confirmado).

### CA-DES-005
Si la unidad rechaza (con motivo), se actualiza Fact_NotificacionDespacho a Rechazada con motivo, Fact_Despacho.activo pasa a false, se inserta Rechazado en Fact_HistorialDespachoUnidad, y se dispara re-asignación.

### CA-DES-006
Si la unidad no responde en el timeout configurado (por defecto 90s), el job O35 marca Fact_Despacho.activo=false, inserta Timeout, publica evento DespachoTimeout y el worker O36 re-asigna de forma asíncrona.

### CA-DES-007
Si se agotan las unidades candidatas, se genera alerta crítica y se escala al Operador para intervención manual.

### CA-DES-008
El Director Tecnológico puede configurar: timeout de respuesta, pesos del algoritmo y prioridades por tipo de emergencia.

### CA-DES-009
El proceso completo desde registro hasta confirmación se completa en menos de 2 minutos (P95).

### CA-DES-010
La asignación manual (O33) persiste con idorigendespacho = Manual.

### CA-DES-011
El escalamiento a zona vecina (O34) amplía la búsqueda desde el condado del accidente a condados vecinos (Dim_Calle → Dim_Ciudad → Dim_Condado); si no encuentra, inserta alerta en Dim_NotaAccidente.

### CA-DES-012
El despacho múltiple (O38) permite asignar una nueva unidad a un caso que ya tiene despacho(s) activo(s).

### CA-DES-013
Si push y SMS fallan tras reintento en O23, el sistema marca No_entregada, desactiva el despacho y ejecuta O36 inmediatamente sin esperar timeout.

## 12. Dependencias

- **`autenticacion-y-rbac`:** Requiere autenticación JWT y roles "Sistema", "Unidad de Emergencia" y "Operador de emergencias".
- **`registrar-accidente` (registro-accidente):** necesita un `idaccidente` válido en `Fact_Accidente` con estado "Reportado".
- **`field-operations`:** necesita que las unidades estén registradas en `Dim_UnidadEmergencia` y que su estado de disponibilidad esté actualizado en `Fact_HistorialEstadoUnidad`.
- Es requerido por:
  - **`seguimiento-cierre-de-casos`:** el despacho confirmado es el punto de partida para el rastreo en tiempo real y el cierre del caso.

## 13. Fuera de alcance

- **Rastreo GPS en tiempo real de la unidad en tránsito:** eso corresponde al spec seguimiento-cierre-de-casos (CU-O25).
- **Registro de llegada al sitio:** eso corresponde al spec seguimiento-cierre-de-casos (CU-O26).
- **Cierre del caso y liberación de unidad:** eso corresponde al spec seguimiento-cierre-de-casos (CU-O28).
- **Aborto de misión en tránsito:** eso corresponde a CU-O39.
- **Pérdida de señal GPS:** eso corresponde a CU-O37.
- **Cálculo de rutas óptimas con tráfico en tiempo real:** la ruta sugerida es una línea recta o ruta básica. La integración con servicios de navegación (Google Maps, Waze) para rutas con tráfico está fuera del alcance.
- **Escalamiento de severidad en sitio:** eso corresponde a CU-O40.
- **Fusión de reportes duplicados:** eso corresponde a CU-O41.
- **Cancelación de caso con unidad despachada:** eso corresponde a CU-O42.
- **Sincronización de evidencia en diferido:** eso corresponde a CU-O43.
- **Forzar cierre desde central:** eso corresponde a CU-O44.
