# Especificación: Registro de Accidentes en Tiempo Real

## 1. Objetivo

Capturar de forma rápida, precisa y estructurada toda la información inicial de un accidente de tránsito — geolocalización, tipo, severidad y datos del incidente — para disparar el proceso de despacho de emergencia y alimentar el repositorio de datos de siniestralidad. El módulo también cubre el descarte de casos antes del despacho, la fusión de reportes duplicados y el escalamiento de severidad en sitio.

## 2. Contexto

El registro de accidentes es el punto de entrada al ciclo operativo de TSI. Cada accidente registrado correctamente activa el algoritmo de despacho inteligente, alimenta los reportes de siniestralidad para clientes y nutre los modelos predictivos de IA. La calidad, velocidad y precisión de este registro determinan la efectividad de toda la cadena de respuesta a emergencias.

**Casos de uso incluidos:**
- **CU-O21**: Registrar accidente de tránsito en tiempo real: geolocalización, tipo, severidad y datos del incidente. Nuevos campos: `horainicio`, `descripcion`, `codigopostal`, `numvehiculos`, `numvictimas`, `numheridos`, `numfallecidos`, `horafin`, `duracionminutos`, `idaccidenteorigen`. Estado inicial cambia de "Reportado" a **BORRADOR**.
- **CU-O32**: Descartar caso antes de despacho. Permite al Operador marcar un caso como DESCARTADO cuando la alerta resulta ser falsa o no requiere intervención.
- **CU-O40**: Escalar severidad en sitio. La Unidad de emergencia puede actualizar la severidad, heridos y fallecidos con información real observada en el lugar.
- **CU-O41**: Fusionar reportes duplicados. El Sistema detecta y el Operador confirma la fusión de dos reportes que corresponden al mismo accidente.

El registro utiliza las tablas `Fact_Accidente`, `Dim_Calle`, `Dim_Ciudad`, `Dim_Condado`, `Dim_Estado`, `Dim_Pais`, `Dim_Severidad`, `Dim_PeriodosDias`, `Dim_EstadosClimas`, `Dim_TipoReportado`, `Dim_Elementos_Fisicos`, `Dim_ElementoFisicoAccidente`, `Dim_ReferenciaEstacion`, `Dim_TipoEstadoAccidente`, `Fact_AccidenteTipoEstadoAccidente` y `Dim_NotaAccidente`. Una vez creado, el accidente transiciona por múltiples estados a través de `Fact_AccidenteTipoEstadoAccidente` y `Dim_TipoEstadoAccidente`.

## Clarifications

### Session 2026-07-09

- Q: ¿Cuándo y cómo debe ocurrir la transición BORRADOR → REPORTADO tras el registro inicial (CU-O21)? → A: Condicional: sin advertencias → auto-promoción a REPORTADO en la misma transacción; con advertencias forzadas → queda en BORRADOR hasta confirmación manual.
- Q: ¿Cómo debe definirse el "área de cobertura operativa" para validar coordenadas GPS? → A: GPS dentro de un `Dim_EstadoRegion` vinculado a una `Dim_RegionOperativa` con `estadoregion='Producción'` vía `Dim_RegionOperativaEstadoRegion`.
- Q: ¿Cómo debe modelarse el "registro retrospectivo" cuando `fechahoraaccidente` es anterior a más de 24 horas? → A: Campos explícitos `registroRetrospectivo` (BOOLEAN) y `justificacionRetrospectiva` (STRING, obligatorio si `registroRetrospectivo=true`); solo así se permite fecha >24h.
- Q: ¿En qué estados del accidente puede ejecutarse el escalamiento de severidad en sitio (CU-O40)? → A: En `ASIGNADO` o `EN_ATENCIÓN` con despacho activo confirmado para ese accidente.
- Q: Al fusionar reportes duplicados (CU-O41), ¿cómo debe determinarse el caso "padre" por defecto? → A: Preselección del registro más antiguo (primer `fechahoramodificado` en BORRADOR/REPORTADO); el Operador puede cambiar antes de confirmar.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Operador de emergencias** | Registrador principal | Recibe alertas de accidentes (por llamada, app o integración), ingresa los datos en el sistema, valida la información capturada, descarta casos, fusiona reportes duplicados y dispara el proceso de despacho. |
| **Sistema** | Validador automático y fusionador | Valida coordenadas GPS, completitud de campos obligatorios, coherencia de datos y consistencia cruzada. Detecta automáticamente reportes duplicados y propone fusión (CU-O41). Clasifica inicialmente el incidente. |
| **Unidad de emergencia** | Escalador de severidad | Actualiza la severidad del accidente con información real observada en sitio (CU-O40). |

## 4. Requisitos funcionales

### RF-REG-001: Registro de accidente con datos obligatorios

El sistema debe permitir al Operador de emergencias registrar un nuevo accidente proporcionando los siguientes campos obligatorios:

- **Geolocalización:** `latitudinicio` y `longitudinicio` (DOUBLE, coordenadas GPS en grados decimales, requeridos). El sistema debe validar que las coordenadas estén dentro del área de cobertura operativa (ver RF-REG-003 punto 1).
- **Fecha y hora:** `fechahoraaccidente` (timestamp LONG, requerido, momento exacto del accidente en epoch milliseconds). El sistema debe validar que no sea una fecha futura ni anterior a más de 24 horas, salvo registro retrospectivo (RN-REG-004).
- **Severidad:** `idseveridad` (INT, FK a `Dim_Severidad`, requerido). Valores: 1=Leve, 2=Moderado, 3=Grave, 4=Fatal. El Operador asigna la severidad inicial basada en la información disponible.
- **Descripción:** `descripcion` (STRING, requerido, narrativa del incidente con detalles relevantes: cómo ocurrió, condiciones visibles, vehículos involucrados aparentes).
- **Ubicación:** `idcalle` (INT, FK a `Dim_Calle`, requerido). El sistema debe sugerir automáticamente este valor a partir de las coordenadas GPS mediante geocodificación inversa. **Nota de modelo:** `Fact_Accidente` solo persiste `idcalle`; ciudad, condado, estado y país se resuelven en tiempo de consulta mediante la jerarquía de join `Dim_Calle → Dim_Ciudad → Dim_Condado → Dim_EstadoRegion → Dim_Pais` — no existen columnas `idciudad`/`idcondado`/`idestado`/`idpais` en la tabla de hechos.
- **Operador que registra:** `idusuario` (INT, FK a `Dim_Usuarios`, requerido, obtenido del token JWT).

Al guardar, el sistema debe:
1. Insertar el registro en `Fact_Accidente` con `activo=true`.
2. Insertar el estado **BORRADOR** en `Fact_AccidenteTipoEstadoAccidente` (idtipoestadoincidente correspondiente en `Dim_TipoEstadoAccidente`).
3. Asignar un `idaccidente` único (formato `ACC-{epoch_ms}-{4digitos}`).
4. Registrar `fecha_actualizacion` automáticamente.
5. **Promoción condicional a REPORTADO:** si todas las validaciones de RF-REG-003 pasan sin advertencias, insertar en la misma transacción el estado **REPORTADO** y retornar `estado: "REPORTADO"`. Si el Operador fuerza el registro pese a advertencias (duplicado, fuera de cobertura, discrepancia geográfica u otras no bloqueantes), el caso permanece en **BORRADOR** hasta que el Operador ejecute la acción explícita de confirmar y reportar (ver RF-REG-010).

### RF-REG-002: Registro de datos complementarios del accidente

El sistema debe permitir al Operador agregar los siguientes datos complementarios (no obligatorios en el registro inicial pero importantes para el análisis posterior):

- **Hora de inicio:** `horainicio` (STRING, opcional, HH:mm en hora local).
- **Período del día y condiciones climáticas:** `idperiododia` (INT, FK a `Dim_PeriodosDias`, opcional) e `idestadoclima` (INT, FK a `Dim_EstadosClimas`, opcional). Calculados automáticamente a partir de la hora del accidente, la ubicación geográfica y una estación meteorológica de referencia (`Dim_ReferenciaEstacion`). **Nota de modelo:** ambos campos se registran mediante la tabla puente `Dim_ElementoClimaticosAccidente` (`idaccidente`, `idperiododia`, `idestadoclima`, `idusuario`), siguiendo el mismo patrón que `idelementofisico` vía `Dim_ElementoFisicoAccidente` — no son columnas directas de `Fact_Accidente`.
- **Elementos físicos cercanos:** registrados a través de `Dim_ElementoFisicoAccidente` (INT, FK a `Dim_Elementos_Fisicos`, opcional). Presencia de cruces, semáforos, paradas, estaciones, baches o vías de tren en las cercanías.
- **Tipo de reporte:** `idtiporeportado` (INT, FK a `Dim_TipoReportado`, opcional). Origen de la alerta (llamada telefónica, app móvil, integración API, cámara de tráfico).
- **Código postal:** `codigopostal` (STRING, opcional).
- **Vehículos involucrados:** `numvehiculos` (INT, opcional), número estimado de vehículos.
- **Víctimas:** `numvictimas` (INT, opcional), `numheridos` (INT, opcional), `numfallecidos` (INT, opcional).
- **Distancia estimada:** `distanciamillas` (DOUBLE, opcional).
- **Duración preliminar:** `duracionminutos` (INT, opcional).
- **Hora fin:** `horafin` (STRING, opcional, completada al cerrar el caso).

### RF-REG-003: Validación automática de datos del accidente

El sistema debe ejecutar automáticamente las siguientes validaciones al registrar un accidente:

1. **Coordenadas GPS:** `latitudinicio` y `longitudinicio` deben estar dentro del rango válido global (-90 a 90, -180 a 180) y dentro del **área de cobertura operativa**, definida así: las coordenadas deben geocodificarse a un `Dim_EstadoRegion` que esté vinculado — vía `Dim_RegionOperativaEstadoRegion` — a al menos una `Dim_RegionOperativa` con `estadoregion='Producción'` y `activo=true`. Si las coordenadas no caen en ningún estado/provincia de una región en Producción, el sistema debe emitir advertencia de "fuera de cobertura" (no bloqueante; ver RF-REG-003 párrafo final).
2. **Consistencia temporal:** `fechahoraaccidente` no puede ser una fecha futura. No puede ser anterior a más de 24 horas desde el momento del registro **salvo** registro retrospectivo explícito (`registroRetrospectivo=true` con `justificacionRetrospectiva` no vacía). Sin esos campos, fechas >24h retornan HTTP 422.
3. **Coherencia geográfica:** el `idcalle` sugerido debe ser consistente con las coordenadas GPS (geocodificación inversa) y su jerarquía completa (`Dim_Calle → Dim_Ciudad → Dim_Condado → Dim_EstadoRegion → Dim_Pais`) debe resolver sin ambigüedad. Si hay discrepancia, el sistema debe advertir al Operador.
4. **Duplicados:** no debe existir otro accidente con coordenadas y timestamp idénticos en un radio de 50 metros y 5 minutos (posible duplicado). Si se detecta, el sistema debe advertir, sugerir fusión (O41) y preseleccionar como caso padre el registro más antiguo según RN-REG-010b.
5. **Campos obligatorios:** todos los campos marcados como requeridos deben tener valores no nulos ni vacíos.

Si alguna validación falla, el sistema debe mostrar una advertencia pero permitir el registro forzado por el Operador bajo su criterio (excepto coordenadas fuera de rango válido global, que bloquean el registro). Un registro forzado con advertencias activas queda en estado **BORRADOR** y no avanza a **REPORTADO** hasta confirmación manual (RF-REG-010).

### RF-REG-004: Estados del accidente

El sistema debe gestionar el ciclo de vida del accidente a través de la tabla `Fact_AccidenteTipoEstadoAccidente` y la dimensión `Dim_TipoEstadoAccidente`. Los estados definidos son:

| Estado | Origen | Significado |
|---|---|---|
| **BORRADOR** | O21 (registro inicial o forzado con advertencias) | El accidente ha sido creado. Pendiente de confirmación manual para pasar a REPORTADO, descarte (O32) o fusión (O41). |
| **REPORTADO** | O21 (post-validación sin advertencias) u O21/RF-REG-010 (confirmación manual desde BORRADOR) | El accidente ha sido validado y está pendiente de asignación de unidad. |
| **BUSCANDO_UNIDAD** | O22 (asignación automática) | El sistema está buscando una unidad disponible para asignar al caso. |
| **ASIGNADO** | O24 (confirmación de despacho) | Una unidad de emergencia ha confirmado el despacho. |
| **EN_ATENCIÓN** | O26 (llegada al sitio) | La unidad llegó al sitio y está atendiendo la emergencia. |
| **CERRADO** | O28/O44 (cierre del caso) | El caso ha sido cerrado. Todos los despachos tienen fechahoraretiro no nulo. |
| **DESCARTADO** | O32 (descarte) | El caso fue descartado antes de cualquier despacho. `activo=false`. |
| **FUSIONADO** | O41 (fusión) | El reporte fue fusionado con otro caso. `idaccidenteorigen` apunta al caso padre. |

Cada cambio de estado debe insertar un nuevo registro en `Fact_AccidenteTipoEstadoAccidente` con `fechahoramodificado` e `idusuario`.

### RF-REG-005: Consulta y edición de accidentes activos

El Operador de emergencias debe poder consultar la lista de accidentes activos (no cerrados, no descartados, no fusionados) y:

1. Filtrar por severidad, ubicación (ciudad, estado), fecha, estado y activo.
2. Ver el detalle completo de un accidente con todos sus datos y estados.
3. Editar datos complementarios de un accidente activo (agregar vehículos, víctimas, condiciones climáticas confirmadas).
4. Corregir errores en datos del registro inicial.

La edición de campos críticos (coordenadas, severidad, fecha) debe requerir confirmación adicional y quedar registrada en los logs del sistema.

### RF-REG-006: Geocodificación inversa automática

Al ingresar las coordenadas GPS (`latitudinicio`, `longitudinicio`), el sistema debe:
1. Ejecutar geocodificación inversa para determinar automáticamente `idcalle` (y resolver, solo para presentación/validación, la jerarquía `Dim_Ciudad`, `Dim_Condado`, `Dim_EstadoRegion`, `Dim_Pais` a la que pertenece).
2. Sugerir los valores al Operador, quien puede confirmarlos o corregirlos manualmente.
3. Si la geocodificación no encuentra resultados precisos, permitir al Operador seleccionar manualmente de las listas de `Dim_Calle`, `Dim_Ciudad`, etc.

### RF-REG-007: Descartar caso antes de despacho (CU-O32)

El Operador debe poder descartar un caso en estado BORRADOR cuando la alerta resulta ser falsa o no requiere intervención.

Al descartar, el sistema debe:
1. Insertar un registro en `Fact_AccidenteTipoEstadoAccidente` con estado **DESCARTADO**.
2. Actualizar `Fact_Accidente` seteando `activo=false`.
3. No modificar `Fact_Despacho` ni `Fact_HistorialEstadoUnidad` (en BORRADOR no existe ningún despacho creado).
4. No se requiere motivo obligatorio, pero el sistema debe ofrecer un campo opcional de nota.

Restricción: solo se puede descartar un caso en estado BORRADOR. Si ya existe algún despacho, el descarte debe hacerse mediante CU-O42 (Cancelar caso con unidad despachada).

### RF-REG-008: Escalar severidad en sitio (CU-O40)

La Unidad de emergencia debe poder escalar la severidad del accidente cuando la información real observada difiere de la severidad inicial registrada (en ruta o en sitio).

**Precondiciones:** el accidente debe estar en estado **ASIGNADO** o **EN_ATENCIÓN**, y el actor debe ser una Unidad de emergencia con un despacho activo y confirmado (`Fact_Despacho`) para ese `idaccidente`. En cualquier otro estado, retornar HTTP 409.

Al escalar severidad, el sistema debe:
1. Actualizar `Fact_Accidente` con los nuevos valores: `idseveridad`, `numheridos`, `numfallecidos`, `descripcion`.
2. Insertar un registro en `Dim_NotaAccidente` con `tipo=escalamiento` y `nota` descriptiva.
3. Registrar el `idusuario` de la Unidad que realizó el escalamiento.
4. Mantener el estado actual del caso (no cambia por el escalamiento).

El sistema debe validar que `numheridos` y `numfallecidos` solo puedan incrementarse (nunca decrecer).

### RF-REG-009: Fusionar reportes duplicados (CU-O41)

El sistema debe detectar automáticamente reportes duplicados durante el registro (RF-REG-003 punto 4) y el Operador debe poder fusionar dos reportes que correspondan al mismo accidente.

**Selección de caso padre:** por defecto, el sistema preselecciona como padre el registro existente más antiguo (menor `fechahoramodificado` del primer estado BORRADOR o REPORTADO en `Fact_AccidenteTipoEstadoAccidente`). El registro nuevo en curso se trata como duplicado candidato. El Operador puede invertir la asignación antes de confirmar vía `idaccidenteprincipal` e `idaccidente` (path del duplicado).

Al fusionar, el sistema debe:
1. Validar la asignación padre/duplicado indicada por el Operador (o la preselección por defecto si confirma sin cambios).
2. Actualizar `Fact_Accidente` del reporte duplicado: setear `idaccidenteorigen` = id del caso padre.
3. Insertar un registro en `Fact_AccidenteTipoEstadoAccidente` del duplicado con estado **FUSIONADO**.
4. El caso padre no se modifica; conserva su flujo normal.
5. El duplicado queda con trazabilidad completa vía `idaccidenteorigen`.

La fusión solo procede si ambos casos están en estado BORRADOR o REPORTADO (ninguno ha sido despachado aún).

### RF-REG-010: Confirmar y reportar desde BORRADOR

El Operador debe poder confirmar explícitamente un accidente en estado **BORRADOR** (típicamente tras un registro forzado con advertencias) para transicionarlo a **REPORTADO**.

Al confirmar, el sistema debe:
1. Verificar que el estado actual sea **BORRADOR**.
2. Insertar un nuevo registro en `Fact_AccidenteTipoEstadoAccidente` con estado **REPORTADO**, `fechahoramodificado` e `idusuario`.
3. Retornar HTTP 200 con `estado: "REPORTADO"`.

Restricción: no se puede confirmar un caso ya en **DESCARTADO** o **FUSIONADO**. Si el caso ya está en **REPORTADO**, retornar HTTP 409.

## 5. Requisitos no funcionales

### RNF-REG-001: Velocidad de registro

El formulario de registro de accidente debe completarse en menos de 5 minutos desde el inicio de la captura hasta el guardado exitoso (meta operativa OP-3.2.1).

### RNF-REG-002: Precisión de geocodificación

La geocodificación inversa debe tener una precisión mínima del 95% para coordenadas urbanas (error máximo de 100 metros en la asignación de calle y ciudad).

### RNF-REG-003: Disponibilidad del módulo de registro

El endpoint de registro de accidentes debe tener una disponibilidad del 99.9%, dado que es la puerta de entrada a todo el flujo de emergencia. Una caída en el registro impide la respuesta a nuevos incidentes.

### RNF-REG-004: Trazabilidad

Cada creación, edición, descarte, escalamiento y fusión de un accidente debe registrar en los logs del sistema: `idusuario` del actor que ejecutó, `idaccidente`, timestamp, acción ejecutada, campos modificados, valores anteriores y nuevos.

### RNF-REG-005: Validación en tiempo real

Las validaciones automáticas (RF-REG-003) deben ejecutarse en menos de 2 segundos y no deben bloquear la interfaz del Operador durante la carga del formulario.

### RNF-REG-006: Resiliencia de captura ante interrupción de red

El formulario de registro de accidente (RF-REG-001, RF-REG-002) debe conservar los datos ya ingresados por el Operador ante una interrupción de conectividad, sin descartarlos silenciosamente. El sistema debe:
1. Mantener el contenido del formulario en el cliente (almacenamiento local) mientras no exista confirmación de guardado exitoso en el servidor.
2. Mostrar un indicador de estado de sincronización (ej. "En vivo" / "Reconectando…" / "Sin conexión — guardado localmente") junto al formulario mientras dure la interrupción.
3. Reintentar automáticamente el envío al recuperar conectividad, o permitir reintento manual explícito por parte del Operador.
4. Nunca perder los campos ya diligenciados por timeout o cierre accidental de la sesión de red durante la captura.

Esta regla aplica el principio de "resiliencia de captura en campo" definido en `.specify/docs/design/design-system.md` §2, dado que el registro de accidente es el formulario de entrada más crítico y sensible a interrupciones del camino operativo.

## 6. Reglas de negocio

### RN-REG-001

Solo el Operador de emergencias puede registrar un nuevo accidente. El Cliente no tiene permiso para registrar accidentes desde su portal; solo puede consultar el historial (CU-O29).

### RN-REG-002

La severidad inicial asignada por el Operador en el registro puede ser modificada posteriormente por una Unidad de emergencia tras evaluar el sitio (CU-O40: Escalar severidad en sitio).

### RN-REG-003

Un accidente con coordenadas fuera del rango válido global (-90 a 90, -180 a 180) no puede ser registrado. El sistema debe rechazar el registro con un mensaje de error claro.

### RN-REG-003b (Cobertura operativa)

El área de cobertura operativa se determina por la jerarquía geográfica resuelta desde las coordenadas GPS: el `Dim_EstadoRegion` resultante debe pertenecer a una `Dim_RegionOperativa` en estado `Producción` (tabla puente `Dim_RegionOperativaEstadoRegion`). Coordenadas fuera de esa área generan advertencia no bloqueante; el Operador puede forzar el registro quedando el caso en **BORRADOR** (RN-REG-006, RF-REG-010).

### RN-REG-004

El `fechahoraaccidente` no puede ser futura ni anterior a más de 24 horas desde el momento del registro, excepto cuando el Operador envía `registroRetrospectivo=true` y `justificacionRetrospectiva` (STRING, obligatoria, no vacía). En registro retrospectivo, la justificación queda registrada en logs (RNF-REG-004). Sin ambos campos, fechas >24h se rechazan con HTTP 422.

### RN-REG-005

Si el sistema detecta un posible duplicado (coordenadas similares en radio de 50m y timestamp en ventana de 5 minutos), debe advertir al Operador y sugerir fusión (O41). El Operador puede optar por crear un registro independiente si confirma que no es duplicado.

### RN-REG-006

Todo accidente recién creado inserta primero el estado **BORRADOR**. Si todas las validaciones de RF-REG-003 pasan sin advertencias, el sistema promueve automáticamente a **REPORTADO** en la misma transacción de guardado. Si el Operador fuerza el registro con advertencias activas, el caso permanece en **BORRADOR** hasta confirmación explícita (RF-REG-010). Los cambios de estado subsecuentes los ejecutan otros módulos (despacho inteligente, operaciones de campo, seguimiento y cierre).

### RN-REG-007

Los campos `numvehiculos`, `numvictimas`, `numheridos` y `numfallecidos` solo pueden incrementarse, nunca decrecer por debajo de un valor previamente registrado, ya que reflejan una situación que no puede revertirse.

### RN-REG-008

El `idperiododia` se calcula automáticamente a partir de `fechahoraaccidente` y la ubicación geográfica. El Operador puede sobrescribirlo si el cálculo automático es incorrecto.

### RN-REG-009 (Descarte)

Solo se puede descartar un caso en estado **BORRADOR**. Si el caso ya tiene despachos asociados, debe usarse el flujo de cancelación (CU-O42).

### RN-REG-010 (Fusión)

La fusión de reportes duplicados solo procede si ambos casos están en estado **BORRADOR** o **REPORTADO**. No se pueden fusionar casos que ya hayan sido despachados o estén en atención.

### RN-REG-010b (Caso padre por defecto)

Ante detección de posible duplicado, el sistema preselecciona como caso padre el `idaccidente` del registro existente más antiguo (primer `fechahoramodificado` en estado BORRADOR o REPORTADO). El Operador puede cambiar padre y duplicado antes de confirmar la fusión (CU-O41).

### RN-REG-011 (Escalamiento)

El escalamiento de severidad en sitio solo puede ser ejecutado por una **Unidad de emergencia** con un despacho activo y confirmado para ese accidente, cuando el caso está en estado **ASIGNADO** o **EN_ATENCIÓN**. No modifica el estado del caso.

## 7. Entradas

### Para registro de accidente (CU-O21)
- `latitudinicio` (DOUBLE, requerido, coordenada GPS latitud).
- `longitudinicio` (DOUBLE, requerido, coordenada GPS longitud).
- `fechahoraaccidente` (LONG, requerido, momento del accidente en epoch ms).
- `registroRetrospectivo` (BOOLEAN, opcional, default `false`; obligatorio `true` si la fecha es anterior a más de 24 horas).
- `justificacionRetrospectiva` (STRING, obligatorio si `registroRetrospectivo=true`, narrativa breve del motivo del registro tardío).
- `idseveridad` (INT, FK a `Dim_Severidad`, requerido: 1=Leve, 2=Moderado, 3=Grave, 4=Fatal).
- `descripcion` (STRING, requerido).
- `idcalle` (INT, FK a `Dim_Calle`, requerido o auto-completado por geocodificación; ciudad/condado/estado/país se resuelven por jerarquía de join, no se envían como campos separados).
- `codigopostal` (STRING, opcional).
- `horainicio` (STRING, opcional, HH:mm).
- `idperiododia` (INT, FK a `Dim_PeriodosDias`, opcional, auto-calculado, se persiste vía `Dim_ElementoClimaticosAccidente`).
- `idestadoclima` (INT, FK a `Dim_EstadosClimas`, opcional, se persiste vía `Dim_ElementoClimaticosAccidente`).
- `idelementofisico` (INT, FK a `Dim_Elementos_Fisicos`, opcional, registrado vía `Dim_ElementoFisicoAccidente`).
- `idtiporeportado` (INT, FK a `Dim_TipoReportado`, opcional).
- `numvehiculos` (INT, opcional).
- `numvictimas` (INT, opcional).
- `numheridos` (INT, opcional).
- `numfallecidos` (INT, opcional).
- `distanciamillas` (DOUBLE, opcional).
- `duracionminutos` (INT, opcional).

### Para descartar caso (CU-O32)
- `idaccidente` (STRING, requerido, path param).
- `motivo` (STRING, opcional, nota de descarte).

### Para escalar severidad (CU-O40)
- `idaccidente` (STRING, requerido, path param).
- `idseveridad` (INT, requerido, nuevo valor de severidad).
- `numheridos` (INT, opcional, solo si incrementa).
- `numfallecidos` (INT, opcional, solo si incrementa).
- `descripcion` (STRING, opcional, actualización de la narrativa).
- `nota` (STRING, requerido, descripción del escalamiento para `Dim_NotaAccidente`).

### Para fusionar reportes (CU-O41)
- `idaccidente` (STRING, requerido, path param — el duplicado a fusionar).
- `idaccidenteprincipal` (STRING, requerido, ID del caso padre).
- `confirmacion` (BOOLEAN, requerido, confirmación explícita del Operador).

### Para confirmar y reportar desde BORRADOR (RF-REG-010)
- `idaccidente` (STRING, requerido, path param).
- `confirmacion` (BOOLEAN, requerido, confirmación explícita del Operador).

## 8. Salidas

### Respuestas exitosas
- **201 Created — Accidente registrado:** `{ "message": "Accidente registrado exitosamente", "idaccidente": "ACC-...", "estado": "REPORTADO" | "BORRADOR", "advertencias": [...], "fechahoramodificado": ... }` — `estado` es `"REPORTADO"` si no hubo advertencias; `"BORRADOR"` si el Operador forzó el registro con advertencias activas.
- **200 OK — Caso confirmado y reportado (RF-REG-010):** `{ "message": "Caso confirmado y reportado", "idaccidente": "ACC-...", "estado": "REPORTADO" }`
- **200 OK — Accidente actualizado:** `{ "message": "Accidente actualizado", "idaccidente": "ACC-...", "campos_modificados": ["numvehiculos", "numheridos"] }`
- **200 OK — Detalle de accidente:** `{ "idaccidente": "ACC-...", "latitudinicio": 19.4326, "longitudinicio": -99.1332, "idseveridad": 3, "descripcion": "...", "estado_actual": "BORRADOR", "historial_estados": [...], ... }`
- **200 OK — Lista de accidentes activos:** `{ "data": [...], "total": 25, "pagina": 1 }`
- **200 OK — Caso descartado (O32):** `{ "message": "Caso descartado exitosamente", "idaccidente": "ACC-...", "estado": "DESCARTADO" }`
- **200 OK — Severidad escalada (O40):** `{ "message": "Severidad escalada exitosamente", "idaccidente": "ACC-...", "idseveridad": 4, "estado": "ASIGNADO" | "EN_ATENCIÓN" }` — refleja el estado actual sin cambiarlo.
- **200 OK — Reportes fusionados (O41):** `{ "message": "Reportes fusionados exitosamente", "idaccidente_duplicado": "ACC-...", "idaccidente_principal": "ACC-...", "estado_duplicado": "FUSIONADO" }`

### Respuestas de error
- **400 Bad Request** — Campos obligatorios faltantes o coordenadas fuera de rango global.
- **401 Unauthorized** — Token no proporcionado, inválido o expirado.
- **403 Forbidden** — Usuario sin rol de Operador de emergencias (O21, O32, O41) o Unidad de emergencia (O40).
- **409 Conflict** — Posible duplicado detectado: incluye `idaccidente_similar`, `idaccidente_principal_sugerido` (registro más antiguo, RN-REG-010b) y `idaccidente_duplicado_sugerido`; el sistema advierte pero permite forzar registro independiente o fusionar (O41).
- **409 Conflict** — Intento de escalamiento (O40) con caso no en ASIGNADO/EN_ATENCIÓN o sin despacho activo confirmado (RN-REG-011).
- **409 Conflict** — Intento de fusión con caso ya despachado (RN-REG-010).
- **409 Conflict** — Intento de descarte con caso no en BORRADOR (RN-REG-009).
- **422 Unprocessable Entity** — `fechahoraaccidente` anterior a más de 24 horas sin `registroRetrospectivo=true` y `justificacionRetrospectiva` (RN-REG-004).
- **422 Unprocessable Entity** — Discrepancia entre coordenadas GPS y ubicación geográfica declarada.
- **409 Conflict** — Intento de confirmar caso no en BORRADOR (RF-REG-010).
- **422 Unprocessable Entity** — Intento de decrecer `numheridos` o `numfallecidos` (RN-REG-007).

## 9. Estados posibles

### Estados del accidente

| Estado | Significado |
|---|---|
| BORRADOR | Registro inicial creado por el Operador. Pendiente de confirmación manual (RF-REG-010), descarte o fusión si hubo advertencias forzadas. |
| REPORTADO | Caso validado, pendiente de asignación de unidad. |
| BUSCANDO_UNIDAD | El sistema está buscando una unidad disponible para asignar. |
| ASIGNADO | Una unidad confirmó el despacho. |
| EN_ATENCIÓN | La unidad llegó al sitio y está atendiendo. |
| CERRADO | Caso finalizado. Todos los despachos tienen estado "Retirado". |
| DESCARTADO | Caso descartado antes de despacho (O32). `activo=false`. |
| FUSIONADO | Reporte fusionado con otro caso (O41). `idaccidenteorigen` poblado. |

### Transiciones
```
BORRADOR → REPORTADO (auto-promoción en guardado sin advertencias, o confirmación manual RF-REG-010)
BORRADOR → DESCARTADO (O32 — descarte antes de despacho)
BORRADOR → FUSIONADO (O41 — fusión de duplicados)
REPORTADO → FUSIONADO (O41 — fusión de duplicados)
REPORTADO → BUSCANDO_UNIDAD (O22 — asignación automática)
BUSCANDO_UNIDAD → ASIGNADO (O24 — unidad confirmó despacho)
ASIGNADO → EN_ATENCIÓN (O26 — unidad llegó al sitio)
EN_ATENCIÓN → CERRADO (O28 — cierre normal cuando todos los despachos están retirados)
Cualquier estado con despacho activo → CERRADO (O42/O44 — cancelación o cierre forzado)
```

## 10. Escenarios

### Escenario 1: Registro exitoso de accidente

Dado que el Operador de emergencias ha iniciado sesión
Y recibe una alerta de accidente en una intersección
Cuando ingresa latitud y longitud del sitio
Y el sistema ejecuta geocodificación inversa sugiriendo calle y ciudad
Y el Operador completa severidad, descripción y confirma los datos
Y envía el formulario
Entonces el sistema debe validar coordenadas, campos obligatorios y consistencia
Y debe crear el registro en `Fact_Accidente`
Y debe insertar el estado "BORRADOR" en `Fact_AccidenteTipoEstadoAccidente`
Y debe promover automáticamente a "REPORTADO" en la misma transacción (sin advertencias)
Y debe retornar HTTP 201 con el `idaccidente` y estado "REPORTADO".

### Escenario 2: Coordenadas GPS fuera de área operativa

Dado que el Operador ingresa coordenadas cuyo `Dim_EstadoRegion` resuelto no pertenece a ninguna `Dim_RegionOperativa` con `estadoregion='Producción'`
Cuando envía el formulario
Entonces el sistema debe advertir que las coordenadas están fuera del área operativa
Y debe preguntar al Operador si desea registrar de todas formas
Y si el Operador confirma, registrar en estado **BORRADOR** con advertencia de fuera de cobertura (sin auto-promoción a REPORTADO).

### Escenario 3: Posible duplicado detectado (con fusión)

Dado que el Operador registra un accidente
Y el sistema detecta que ya existe un accidente con coordenadas y timestamp casi idénticos (radio 50m, ventana 5 min)
Cuando el Operador envía el formulario
Entonces el sistema debe advertir del posible duplicado
Y debe mostrar el `idaccidente` del registro similar
Y debe preseleccionar como caso padre el registro más antiguo (`idaccidente_principal_sugerido`) y el nuevo como duplicado candidato
Y debe ofrecer al Operador las opciones: (a) fusionar con el reporte existente (puede cambiar padre/duplicado antes de confirmar), (b) registrar como accidente independiente, (c) cancelar el registro.
Si el Operador elige fusionar, el sistema ejecuta O41 con la asignación confirmada (por defecto o modificada).

### Escenario 4: Edición de datos complementarios

Dado que un accidente está en estado "EN_ATENCIÓN"
Y el Operador recibe información adicional sobre más vehículos involucrados
Cuando edita los campos `numvehiculos` y `descripcion` del accidente
Entonces el sistema debe actualizar los datos en `Fact_Accidente`
Y debe registrar la edición en los logs del sistema con los valores anteriores y nuevos.

### Escenario 5: Registro con geocodificación fallida

Dado que el Operador ingresa coordenadas en una zona sin cobertura de geocodificación
Cuando el sistema intenta la geocodificación inversa y no obtiene resultados
Entonces el sistema debe informar que no pudo determinar la ubicación automáticamente
Y debe habilitar la selección manual de `idcalle` desde una lista desplegable (con búsqueda en cascada por ciudad/condado/estado/país para facilitar la ubicación)
Y debe permitir al Operador continuar con el registro.

### Escenario 6: Descarte de caso antes de despacho (O32)

Dado que un accidente está en estado BORRADOR
Y el Operador determina que la alerta es falsa o no requiere intervención
Cuando ejecuta la acción de descartar caso
Entonces el sistema debe insertar el estado DESCARTADO en `Fact_AccidenteTipoEstadoAccidente`
Y debe actualizar `activo=false` en `Fact_Accidente`
Y no debe modificar `Fact_Despacho` (no existe ningún despacho)
Y debe retornar HTTP 200 con estado "DESCARTADO".

### Escenario 7: Escalamiento de severidad en sitio (O40)

Dado que una Unidad de emergencia tiene un despacho activo confirmado para el accidente
Y el caso está en estado ASIGNADO o EN_ATENCIÓN
Y observa que la severidad real es mayor que la registrada inicialmente (ej. de Moderado a Grave)
Cuando la Unidad envía la actualización con `idseveridad=3`, `numheridos=4`, `descripcion` actualizada
Entonces el sistema debe actualizar `Fact_Accidente` con los nuevos valores
Y debe insertar un registro en `Dim_NotaAccidente` con `tipo=escalamiento`
Y debe mantener el estado actual del caso (ASIGNADO o EN_ATENCIÓN)
Y debe retornar HTTP 200 confirmando el escalamiento.

### Escenario 8: Fusión de reportes duplicados (O41)

Dado que existen dos reportes en estado BORRADOR con coordenadas casi idénticas
Y el Operador confirma que corresponden al mismo accidente
Cuando ejecuta la fusión indicando el caso padre y el duplicado
Entonces el sistema debe actualizar `idaccidenteorigen` del duplicado con el ID del caso padre
Y debe insertar el estado FUSIONADO en `Fact_AccidenteTipoEstadoAccidente` del duplicado
Y el caso padre no debe modificarse
Y debe retornar HTTP 200 confirmando la fusión.

### Escenario 9: Registro retrospectivo (>24 horas)

Dado que el Operador necesita registrar un accidente ocurrido hace más de 24 horas
Cuando envía el formulario con `registroRetrospectivo=true` y `justificacionRetrospectiva` no vacía
Entonces el sistema debe aceptar la fecha histórica
Y debe registrar la justificación en logs del sistema
Y debe aplicar las validaciones restantes de RF-REG-003 (promoción condicional a REPORTADO según advertencias).

Dado que el Operador envía `fechahoraaccidente` con más de 24 horas de antigüedad
Y no incluye `registroRetrospectivo=true` con justificación
Cuando envía el formulario
Entonces el sistema debe rechazar el registro con HTTP 422.

## 11. Criterios de aceptación

### CA-REG-001
El Operador puede registrar un accidente con coordenadas GPS, severidad, descripción y ubicación, y el sistema lo almacena en `Fact_Accidente` insertando "BORRADOR" y promoviendo a "REPORTADO" automáticamente si no hay advertencias de validación.

### CA-REG-013
Un accidente registrado con advertencias forzadas permanece en "BORRADOR". El Operador puede confirmarlo explícitamente (RF-REG-010) para transicionar a "REPORTADO".

### CA-REG-002
El sistema valida que las coordenadas estén en rango global (-90 a 90, -180 a 180) y rechaza el registro si están fuera de rango.

### CA-REG-003
La geocodificación inversa sugiere automáticamente calle, ciudad, condado, estado y país basándose en las coordenadas GPS.

### CA-REG-004
El sistema detecta posibles duplicados (mismas coordenadas en radio de 50m y misma ventana de 5 minutos) y ofrece fusión (O41).

### CA-REG-005
El Operador puede editar datos complementarios de un accidente activo (vehículos, víctimas, descripción), y la edición queda registrada en logs.

### CA-REG-006
El sistema rechaza fechas futuras como `fechahoraaccidente`. Rechaza fechas anteriores a más de 24 horas salvo que el payload incluya `registroRetrospectivo=true` y `justificacionRetrospectiva` no vacía; de lo contrario retorna HTTP 422.

### CA-REG-007
Cada cambio de estado del accidente genera automáticamente un nuevo registro en `Fact_AccidenteTipoEstadoAccidente` con `fechahoramodificado`.

### CA-REG-008
Solo el Operador de emergencias puede registrar accidentes. Otros roles reciben HTTP 403.

### CA-REG-009 (O32)
El Operador puede descartar un caso en estado BORRADOR. El sistema marca `activo=false` y registra estado DESCARTADO. Si el caso no está en BORRADOR, retorna HTTP 409.

### CA-REG-010 (O40)
La Unidad de emergencia puede escalar la severidad de un accidente en estado ASIGNADO o EN_ATENCIÓN con despacho activo confirmado. El sistema actualiza `Fact_Accidente` e inserta nota en `Dim_NotaAccidente` con `tipo=escalamiento`. Si el estado no es ASIGNADO/EN_ATENCIÓN o no hay despacho confirmado, retorna HTTP 409.

### CA-REG-011 (O41)
El Operador puede fusionar dos reportes duplicados. El sistema preselecciona como padre el registro más antiguo (RN-REG-010b), permite cambiar la asignación, setea `idaccidenteorigen` en el duplicado y registra estado FUSIONADO. Si algún caso ya fue despachado, retorna HTTP 409.

### CA-REG-012
Los campos `numheridos` y `numfallecidos` solo pueden incrementarse. Intentar decrecerlos retorna HTTP 422.

### CA-REG-014
El sistema valida cobertura operativa resolviendo el `Dim_EstadoRegion` de las coordenadas GPS y verificando su pertenencia a una `Dim_RegionOperativa` en `Producción` vía `Dim_RegionOperativaEstadoRegion`. Coordenadas fuera de cobertura generan advertencia y, si se fuerza el registro, el caso queda en BORRADOR.

## 12. Dependencias

- **`autenticacion-y-rbac`:** Requiere autenticación JWT y los roles "Operador de emergencias" y "Unidad de emergencia" definidos.
- **`incorporacion-regional`:** Define qué regiones están en `Producción` y qué `Dim_EstadoRegion` cubren (`Dim_RegionOperativa`, `Dim_RegionOperativaEstadoRegion`); el módulo de registro consulta esta configuración para validar cobertura operativa.
- Es requerido por los siguientes specs:
  - **`despacho-inteligente` (despacho-inteligente):** necesita un accidente registrado con estado REPORTADO para ejecutar la asignación de unidad.
  - **`seguimiento-y-cierre-caso` (seguimiento-cierre-de-casos):** necesita un accidente con estados para rastrear y cerrar.
  - **`ia-predictiva-siniestralidad` (predictive-ai):** necesita histórico de accidentes para entrenar modelos.
  - **`calidad-de-datos-analiticos` (data-quality-analytics):** necesita datos de accidentes para validar calidad.

## 13. Fuera de alcance

- **Registro de conductores y vehículos involucrados:** eso se maneja a través de `Dim_Conductor`, `Dim_Vehiculo` y `Fact_Conductor_Accidente`, que son parte del enriquecimiento posterior del caso (puede hacerlo el Técnico de campo en spec field-operations).
- **Asignación de unidad de emergencia:** eso corresponde al spec despacho-inteligente (CU-O22, O33, O34).
- **Captura de evidencia fotográfica:** eso corresponde al spec field-operations (Técnico de campo, CU-O27).
- **Cálculo de tiempos de respuesta y SLAs:** eso corresponde al spec seguimiento-cierre-de-casos.
- **Consulta de historial por parte del cliente:** el cliente consulta expedientes cerrados a través del spec seguimiento-cierre-de-casos (CU-O29).
- **Coordinación de despacho múltiple:** corresponde al spec despacho-inteligente (CU-O38).
- **Cancelación de caso con unidad ya despachada:** corresponde al spec seguimiento-y-cierre (CU-O42).
- **Forzar cierre desde central:** corresponde al spec seguimiento-y-cierre (CU-O44).
