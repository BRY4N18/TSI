# Especificacion: Seguimiento y Cierre de Casos de Emergencia

## 1. Objetivo

Dar visibilidad y trazabilidad completa al ciclo de vida del caso de emergencia desde que la unidad sale en camino hasta su cierre formal, incluyendo rastreo GPS en tiempo real, deteccion de perdida de señal GPS, registro de llegada al sitio, aborto de mision en transito, cancelacion de caso con unidad despachada, cierre con validacion multi-despacho y registro de tiempos efectivos, forzado de cierre desde central, y consulta del historial de expedientes por operadores y clientes.

## Clarifications

### Session 2026-07-09

- Q: ¿Cómo se determina si un caso cerrado pertenece a las zonas geográficas de interés del Cliente (RF-SEG-006)? → A: Por condado (`Dim_Condado`): el cliente selecciona condados en onboarding (`Dim_Preferencias_Cliente.zonas_geograficas`); un caso es visible si `Fact_Accidente.idcalle` → `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado` coincide con uno de esos condados.
- Q: ¿Quién se registra como `idusuario` en los retiros auto-generados al ejecutar O28 con despachos pendientes (RF-SEG-003 paso 2)? → A: El usuario que ejecutó el cierre (operador de central o usuario de la unidad móvil), en cada `Fact_HistorialDespachoUnidad` (Retirado) auto-generado.
- Q: ¿Qué datos son obligatorios al cancelar un caso O42 vs. cierre normal O28 (RF-SEG-004 / RF-SEG-010)? → A: Solo motivo obligatorio en `Dim_NotaAccidente` más `horafin`/`duracionminutos`; sin campos de RF-SEG-004 (resultado, calificación, conteos finales).
- Q: ¿Qué coordenadas GPS se conservan tras la depuración a 90 días (RNF-SEG-004)? → A: Por evento de despacho (`iddespacho`): primer GPS tras `fechahoradespacho` (origen), GPS más cercano a `fechahorallegada` (llegada), último GPS antes de `fechahoraretiro` (cierre).
- Q: ¿Qué mecanismo entrega las actualizaciones del mapa en tiempo real al Operador (RF-SEG-007)? → A: SSE (`text/event-stream`) mediante endpoint dedicado de seguimiento que emite eventos GPS, ETA y cambios de estado, alineado con `despacho-inteligente`.

## 2. Contexto

Una vez que una unidad de emergencia confirmo un despacho, el Operador y el cliente necesitan saber exactamente donde esta la unidad, cuando llegara al sitio y cuando el caso sera cerrado. La trazabilidad completa del caso — desde el despacho hasta el cierre — es fundamental para medir tiempos de respuesta (SLA), auditar la calidad del servicio y generar reportes para aseguradoras.

El modelo de datos sigue una relacion **N-N entre Caso y Unidad**: un accidente (`Fact_Accidente`) puede tener multiples despachos asociados (grua + ambulancia + policia), y cada despacho tiene su propio ciclo de vida registrado en `Fact_HistorialDespachoUnidad` con estados (Confirmado, En_sitio, Retirado, Abortado). El cliente puede consultar el historial de casos atendidos en su jurisdiccion.

**Regla clave de cierre:** el Caso solo pasa a estado **CERRADO** cuando TODOS los `Fact_Despacho` asociados a ese `idaccidente` tienen `fechahoraretiro` no nulo (ultimo estado en `Fact_HistorialDespachoUnidad` = Retirado). No existe cierre parcial.

**Casos de uso incluidos:**
- CU-O25: Rastrear en tiempo real la posicion GPS de la unidad en camino hacia el accidente, almacenando ubicaciones repetidas en `Dim_HistorialUbicacionUnidadEmergencia` y actualizando el snapshot en `Dim_UnidadEmergencia`. Actor: Operador de emergencias / Sistema.
- CU-O26: Registrar llegada de la unidad al sitio del accidente mediante `Fact_HistorialDespachoUnidad` (estado En_sitio) y actualizar `Fact_Despacho.fechahorallegada`. Actor: Unidad de emergencia.
- CU-O28: Cerrar caso de emergencia validando que todos los despachos esten Retirado, registrar `Fact_Accidente.horafin`/`duracionminutos` y liberar unidades. Actor: Operador de emergencias / Unidad de emergencia.
- CU-O29: Consultar historial de emergencias y expedientes de casos atendidos (join extenso con `Fact_HistorialDespachoUnidad`, `Dim_EstadoDespacho`, `Fact_NotificacionDespacho`, `Dim_HistorialUbicacionUnidadEmergencia`). Actor: Operador de emergencias / Cliente.
- CU-O37: Detectar perdida de señal GPS mediante job que compara `MAX(fechahora)` en `Dim_HistorialUbicacionUnidadEmergencia` contra la hora actual e inserta alerta en `Dim_NotaAccidente`. Actor: Sistema / Operador de emergencias.
- CU-O39: Abortar mision en transito registrando `Fact_HistorialDespachoUnidad` (Abortado), retornando la unidad a Activa y disparando re-asignacion O36. Actor: Unidad de emergencia.
- CU-O42: Cancelar caso con unidad despachada (falsa alarma): registrar `fechahoraretiro`, todos los despachos Retirado, caso CERRADO, sin evidencia fotografica. Actor: Operador de emergencias / Unidad de emergencia.
- CU-O44: Forzar cierre desde central: operador establece `fechahoraretiro` para un despacho especifico, inserta `Fact_HistorialDespachoUnidad` (Retirado, forzado por operador) y reevalua condicion de O28. Actor: Operador de emergencias.

**Tablas de base de datos utilizadas:**
- `Fact_Accidente` (`idaccidente`, `horafin`, `duracionminutos`): datos del caso.
- `Fact_AccidenteTipoEstadoAccidente` y `Dim_TipoEstadoAccidente`: trazabilidad de cambios de estado del caso.
- `Fact_Despacho` (`iddespacho`, `idaccidente`, `idunidademergencia`, `fechahoradespacho`, `fechahorallegada`, `fechahoraretiro`): tiempos del despacho.
- `Fact_HistorialDespachoUnidad` y `Dim_EstadoDespacho`: historial de estados del despacho (Pendiente, Confirmado, Rechazado, Timeout, Abortado, En_sitio, Retirado).
- `Fact_NotificacionDespacho`: informacion de notificaciones y motivos de rechazo.
- `Dim_HistorialUbicacionUnidadEmergencia`: trayectoria GPS de la unidad.
- `Dim_UnidadEmergencia` (`latitud`, `longitud`): snapshot de la posicion mas reciente.
- `Fact_HistorialEstadoUnidad`: trazabilidad de cambios de disponibilidad de la unidad.
- `Dim_EvidenciaFoto` y `Dim_NotaAccidente`: evidencias del caso.
- `Dim_Preferencias_Cliente` (`zonas_geograficas`): condados de interes del cliente (onboarding).
- `Dim_Calle`, `Dim_Ciudad`, `Dim_Condado`: resolucion geografica del accidente para filtro de expedientes.


## 3. Actores

| Actor | Rol en este modulo | Interaccion principal |
|---|---|---|
| **Operador de emergencias** | Supervisor del caso | Rastrea en tiempo real la posicion y ETA de la unidad en camino. Puede cerrar el caso registrando tiempos finales. Consulta el historial de emergencias. Fuerza cierre de despachos desde central (O44). Cancela casos con unidad despachada (O42). |
| **Unidad de emergencia** | Ejecutor en campo | Reporta su posicion GPS continua mientras esta en camino. Registra la llegada al sitio (O26). Aborta mision en transito (O39). Puede cerrar el caso desde la app movil. |
| **Cliente** | Consultor de historial | Consulta expedientes de casos cerrados cuyo condado (`Dim_Condado`) esta en sus zonas de interes configuradas en onboarding. No puede ver casos activos en tiempo real. |
| **Sistema** | Rastreador, calculador y monitor | Recibe posiciones GPS de la unidad en camino, recalcula ETA continuamente, almacena en `Dim_HistorialUbicacionUnidadEmergencia` y actualiza snapshot en `Dim_UnidadEmergencia`. Detecta automaticamente la llegada al sitio por geofencing. Ejecuta job de deteccion de perdida de señal GPS (O37). Dispara re-asignacion O36 al abortar mision (O39). |

## 4. Requisitos funcionales

### RF-SEG-001: Rastreo GPS en tiempo real de la unidad en camino (CU-O25)

El Sistema debe recibir y procesar la posicion GPS de la unidad de emergencia mientras esta en camino hacia el sitio del accidente:

1. La app movil de la unidad envia su ubicacion GPS cada 10 segundos mientras esta en estado Confirmado (en camino).
2. El sistema almacena cada actualizacion como una nueva fila en `Dim_HistorialUbicacionUnidadEmergencia` (`idunidademergencia`, `idaccidente`, `latitud`, `longitud`, `fechahora`).
3. El sistema actualiza el snapshot de la posicion mas reciente en `Dim_UnidadEmergencia` (`latitud`, `longitud`).
4. El sistema recalcula el ETA (tiempo estimado de llegada) basado en la distancia lineal remanente y actualiza la estimacion en el mapa.
5. El Operador debe poder ver: posicion actual de la unidad en un mapa, trazado de la ruta recorrida, ETA actualizado, distancia remanente al sitio del accidente.

### RF-SEG-002: Registro de llegada al sitio (CU-O26)

La Unidad de emergencia debe poder registrar su llegada al sitio del accidente de dos formas:

1. **Manual:** la unidad presiona "Registrar llegada" en la app movil. El sistema inserta una fila en `Fact_HistorialDespachoUnidad` con `idestadodespacho` = **En_sitio** y actualiza `Fact_Despacho.fechahorallegada`.
2. **Automatica por geofencing:** cuando las coordenadas GPS de la unidad entran en un radio de 100 metros alrededor de las coordenadas del accidente (`latitudinicio`, `longitudinicio` de `Fact_Accidente`), el sistema registra automaticamente la llegada y notifica a la unidad para confirmar.

Ambos metodos coexisten: la geovalla sirve como respaldo automatico; la confirmacion manual permite a la unidad validar que efectivamente llego al sitio correcto. Al registrarse la llegada, el estado del caso cambia a EN_ATENCION en `Fact_AccidenteTipoEstadoAccidente`.

### RF-SEG-003: Validacion y cierre del caso de emergencia (CU-O28)

El Operador de emergencias o la Unidad de emergencia debe poder cerrar el caso cuando la atencion ha finalizado:

1. **Validacion previa:** el sistema verifica que TODOS los `Fact_Despacho` asociados al `idaccidente` tengan `fechahoraretiro` no nulo (equivalente a que su ultimo estado en `Fact_HistorialDespachoUnidad` sea Retirado).
2. Si faltan despachos por retirar: para cada despacho pendiente, el sistema establece `Fact_Despacho.fechahoraretiro=now` e inserta `Fact_HistorialDespachoUnidad` con `idestadodespacho` = **Retirado** y `idusuario` = quien ejecutó el cierre (operador de central o usuario de la unidad móvil).
3. El sistema actualiza `Fact_Accidente.horafin` y calcula `duracionminutos` (diferencia entre cierre y hora de inicio).
4. El sistema registra automaticamente los siguientes tiempos metricos:
   - Tiempo de respuesta: diferencia entre `fechahoradespacho` y el registro inicial.
   - Tiempo en transito: diferencia entre `fechahorallegada` y `fechahoradespacho`.
   - Tiempo en sitio: diferencia entre el cierre y `fechahorallegada`.
5. El sistema cambia el estado del accidente a **CERRADO** en `Fact_AccidenteTipoEstadoAccidente`.
6. Cada unidad involucrada se libera: `Fact_HistorialEstadoUnidad` con estado **Activa**.
7. El sistema registra el cierre en los logs del sistema.

### RF-SEG-004: Registro de calificacion y resultados del cierre (CU-O28)

Al cerrar el caso mediante O28 (no aplica a cancelacion O42), el Operador o la Unidad debe poder registrar:

- Resultado de la atencion (string, requerido): resumen de lo ocurrido en el sitio.
- Numero final de vehiculos involucrados (`numvehiculos` actualizado en `Fact_Accidente`).
- Numero final de victimas, heridos y fallecidos (`numvictimas`, `numheridos`, `numfallecidos` actualizados).
- Calificacion de la atencion (opcional): escala de 1 a 5 sobre la efectividad de la respuesta.
- Observaciones finales (string, opcional).

### RF-SEG-005: Consulta de historial de emergencias

El Operador de emergencias debe poder consultar el historial completo de emergencias con filtros por:

- Rango de fechas (fecha desde / fecha hasta).
- Estado del caso (Reportado, En_atencion, Cerrado, etc.).
- Severidad (`idseveridad`).
- Ubicacion geografica (ciudad, estado, pais).
- Unidad de emergencia asignada.

Cada resultado debe mostrar: `idaccidente`, fecha y hora, ubicacion, severidad, estado final, tiempos clave (respuesta, transito, atencion, duracion total) y unidad asignada.

### RF-SEG-006: Consulta de expedientes por el Cliente

El Cliente (aseguradora o municipio) debe poder consultar expedientes de casos cerrados que esten dentro de su jurisdiccion o zona de interes:

1. El Cliente ve solo casos cerrados, no casos activos.
2. El Cliente ve solo casos cuyo condado del accidente coincide con los condados seleccionados en `Dim_Preferencias_Cliente.zonas_geograficas` durante el onboarding. El match se resuelve via `Fact_Accidente.idcalle` → `Dim_Calle` → `Dim_Ciudad` → `Dim_Condado`, alineado con el modelo geografico de `despacho-inteligente`.
3. Cada expediente incluye: datos del accidente, tiempos del caso, unidades despachadas, historial completo de cada despacho (`Fact_HistorialDespachoUnidad` + `Dim_EstadoDespacho`), notificaciones (`Fact_NotificacionDespacho`), trayectoria GPS (`Dim_HistorialUbicacionUnidadEmergencia`), evidencias fotograficas (`Dim_EvidenciaFoto`) y notas de campo (`Dim_NotaAccidente`).
4. El Cliente puede exportar el expediente en formato PDF.

### RF-SEG-007: Mapa de seguimiento en tiempo real

El Operador de emergencias debe disponer de un mapa en tiempo real que muestre:

- Ubicacion de todos los accidentes activos (marcadores por severidad: verde = Leve, amarillo = Moderado, naranja = Grave, rojo = Fatal).
- Ubicacion de todas las unidades de emergencia activas con su estado (Activa = azul, Ocupada = naranja, Fuera de servicio = gris).
- Para unidades en camino: linea de ruta desde su posicion hasta el sitio del accidente, con ETA.
- Al hacer clic en un marcador: detalle resumido del caso o de la unidad.

El frontend del Operador consume actualizaciones via **SSE** (`text/event-stream`) desde un endpoint dedicado de seguimiento. El stream emite eventos de posicion GPS, ETA recalculado y cambios de estado de casos/unidades, sin polling REST. Patron alineado con RF-DES-011 de `despacho-inteligente`.

### RF-SEG-008: Deteccion de perdida de señal GPS (CU-O37)

El Sistema debe ejecutar un job periodico que monitoree la recepcion de senal GPS de las unidades en camino:

1. El job compara `MAX(fechahora)` en `Dim_HistorialUbicacionUnidadEmergencia` para cada unidad contra la hora actual.
2. Si la diferencia supera un umbral configurable (ej. 60 segundos sin actualizacion), el sistema considera que hay perdida de senal.
3. El sistema inserta una alerta en `Dim_NotaAccidente` (`idaccidente`, `idusuario`="Sistema", `nota`="Perdida de senal GPS detectada", `tipo`="alerta").
4. No se modifica `Fact_Despacho` — la unidad sigue asignada, solo se pierde visibilidad de su posicion.
5. Si la senal se recupera antes de que se complete el cierre del caso, se reanuda el rastreo normal.

### RF-SEG-009: Abortar mision en transito (CU-O39)

La Unidad de emergencia debe poder abortar una mision mientras esta en camino hacia el sitio:

1. La unidad selecciona "Abortar mision" en la app movil.
2. El sistema inserta una fila en `Fact_HistorialDespachoUnidad` con `idestadodespacho` = **Abortado**.
3. El sistema inserta una fila en `Fact_HistorialEstadoUnidad` para que la unidad retorne a estado **Activa** (queda disponible).
4. El sistema dispara automaticamente el flujo de re-asignacion CU-O36 (nuevo `Fact_Despacho` para el mismo `idaccidente` con nueva unidad).
5. El despacho abortado permanece en la tabla como historial de intentos.

### RF-SEG-010: Cancelar caso con unidad despachada (CU-O42)

El Operador de emergencias o la Unidad debe poder cancelar un caso cuando ya hay una unidad despachada (falsa alarma, abandono):

1. El usuario confirma la cancelacion con un motivo.
2. El sistema actualiza `Fact_Despacho.fechahoraretiro=now` para todos los despachos del caso.
3. El sistema inserta `Fact_HistorialDespachoUnidad` con `idestadodespacho` = **Retirado** para cada despacho.
4. El sistema inserta `Fact_HistorialEstadoUnidad` para que cada unidad retorne a **Activa**.
5. El sistema registra el motivo en `Dim_NotaAccidente`.
6. El sistema actualiza `Fact_Accidente.horafin` y calcula `duracionminutos` (diferencia entre cancelacion y hora de inicio).
7. El sistema cambia el estado del caso a **CERRADO** en `Fact_AccidenteTipoEstadoAccidente`.
8. **No se solicitan ni registran** los campos de RF-SEG-004 (resultado, calificacion, conteos finales).
9. **No se crea ninguna fila en `Dim_EvidenciaFoto`** para este caso — a diferencia del cierre normal.

### RF-SEG-011: Forzar cierre desde central (CU-O44)

El Operador de emergencias debe poder forzar el cierre de un despacho especifico cuando el tecnico en campo olvido cerrarlo:

1. El Operador selecciona un despacho especifico y ejecuta "Forzar retiro".
2. El sistema actualiza `Fact_Despacho.fechahoraretiro=now` para ese despacho.
3. El sistema inserta `Fact_HistorialDespachoUnidad` con `idestadodespacho` = **Retirado**, registrando al operador como responsable (`idusuario` = operador de central).
4. El sistema reevalua la condicion de CU-O28:
   - Si con este cierre se completan todos los despachos del caso: el caso pasa a **CERRADO** (mismo flujo que O28).
   - Si quedan otras unidades activas: el caso permanece en **EN_ATENCION**.

## 5. Requisitos no funcionales

### RNF-SEG-001: Frecuencia de actualizacion GPS
La posicion GPS de la unidad en camino debe actualizarse en el mapa del Operador cada 10 segundos, con una latencia maxima de 5 segundos desde que la unidad envia su ubicacion. Las actualizaciones se entregan al frontend via SSE (`text/event-stream`), no mediante polling REST.

### RNF-SEG-002: Precision del geofencing
El geofencing para deteccion de llegada debe tener una precision minima de 100 metros. No debe registrar falsas llegadas por fluctuaciones GPS (histeresis minima de 30 segundos dentro del radio).

### RNF-SEG-003: Disponibilidad del mapa de seguimiento
El mapa de seguimiento en tiempo real debe estar disponible 24/7 con una disponibilidad del 99.9%, dado que es la herramienta principal del Operador durante emergencias activas.

### RNF-SEG-004: Retencion de expedientes
Los expedientes de casos cerrados deben conservarse permanentemente. Los datos de rastreo GPS (`Dim_HistorialUbicacionUnidadEmergencia`) pueden depurarse despues de 90 dias, conservando por cada `iddespacho` solo tres puntos clave:
- **Origen:** primer registro GPS con `fechahora` >= `Fact_Despacho.fechahoradespacho`.
- **Llegada:** registro GPS con `fechahora` mas cercana a `Fact_Despacho.fechahorallegada`.
- **Cierre:** ultimo registro GPS con `fechahora` <= `Fact_Despacho.fechahoraretiro`.
La trayectoria completa permanece disponible durante los 90 dias posteriores al cierre del caso.

### RNF-SEG-005: Umbral de perdida de señal GPS
El umbral de deteccion de perdida de señal GPS debe ser configurable (por defecto 60 segundos). El job de monitoreo debe ejecutarse cada 30 segundos como maximo.

### RNF-SEG-006: Inmutabilidad del historial de despacho
Una vez insertado un registro en `Fact_HistorialDespachoUnidad`, no puede ser modificado ni eliminado. Solo se agregan nuevas filas con `fechahora` creciente.

## 6. Reglas de negocio

### RN-SEG-001
El registro de llegada al sitio puede ser manual (la unidad presiona el boton) o automatico (geofencing). Si ocurre la deteccion automatica primero, el sistema notifica a la unidad para que confirme. Si la unidad confirma manualmente antes de que se active la geovalla, la deteccion automatica se ignora.

### RN-SEG-002
El cierre del caso puede ser ejecutado tanto por el Operador de emergencias desde el centro de control como por la Unidad de emergencia desde la app movil. Ambos tienen igual autoridad para cerrar.

### RN-SEG-003
Al cerrar un caso (O28, O42), cada unidad involucrada se libera (estado Activa en `Fact_HistorialEstadoUnidad`). Si la unidad estaba "Fuera de servicio" antes del despacho, vuelve a "Fuera de servicio" en lugar de "Activa".

### RN-SEG-004
Los campos `numvehiculos`, `numvictimas`, `numheridos` y `numfallecidos` en `Fact_Accidente` se actualizan con los valores definitivos al cierre normal O28. Los valores registrados durante la atencion son preliminares. En cancelacion O42 no se actualizan estos campos.

### RN-SEG-005
El Cliente solo puede consultar expedientes de casos cerrados. No tiene acceso al mapa de seguimiento en tiempo real ni a casos activos. El Cliente solo ve casos cuyo `Dim_Condado` del accidente esta incluido en `Dim_Preferencias_Cliente.zonas_geograficas`.

### RN-SEG-006
El Operador de emergencias puede consultar todo el historial, incluyendo casos activos y cerrados, sin restriccion de zona geografica.

### RN-SEG-007
Los tiempos registrados al cierre (`duracionminutos`, tiempos de respuesta, transito y sitio) son inmutables. No pueden ser modificados despues del cierre del caso, garantizando la integridad de los datos para auditorias de SLA.

### RN-SEG-008 (Regla de cierre multi-despacho)
El Caso solo pasa a estado CERRADO cuando TODOS los `Fact_Despacho` asociados a ese `idaccidente` tienen `fechahoraretiro` no nulo. No existe cierre parcial. El estado del Caso es una funcion del conjunto de estados de sus Despachos (relacion N-N), no de un solo despacho aislado.

### RN-SEG-009
Al abortar mision (O39), la unidad retorna a Activa inmediatamente y se dispara la re-asignacion O36. El despacho abortado permanece como historial de intentos en `Fact_HistorialDespachoUnidad`.

### RN-SEG-010
En la cancelacion de caso con unidad despachada (O42), solo se requiere motivo en `Dim_NotaAccidente` mas `horafin`/`duracionminutos`. No se solicitan campos de RF-SEG-004 ni se crean registros en `Dim_EvidenciaFoto`.

### RN-SEG-011
El forzado de cierre desde central (O44) registra al operador como responsable del retiro en `Fact_HistorialDespachoUnidad`. Si quedan otros despachos activos, el caso permanece en EN_ATENCION hasta que todos se retiren.

### RN-SEG-012
En el cierre de caso O28, los retiros auto-generados de despachos pendientes registran `idusuario` = quien ejecutó el cierre (operador o unidad). En O44, el retiro forzado de un despacho específico registra `idusuario` = operador de central que ejecutó el forzado. Ambos flujos son distinguibles en auditoría por el contexto de la acción (cierre global vs. forzado unitario).

### RN-SEG-013
Tras 90 dias del cierre del caso, el job de depuracion GPS elimina registros intermedios de `Dim_HistorialUbicacionUnidadEmergencia` y conserva exactamente tres puntos por `iddespacho` segun RNF-SEG-004 (origen, llegada, cierre vinculados a tiempos de `Fact_Despacho`).

## 7. Entradas

### Para rastreo (CU-O25)
- Coordenadas GPS de la unidad (latitud, longitud) enviadas cada 10 segundos.
- `idunidademergencia` y `idaccidente` asociado.

### Para registro de llegada (CU-O26)
- Confirmacion manual de la unidad o deteccion automatica por geofencing.
- `idunidademergencia`, `iddespacho`.

### Para cierre de caso (CU-O28)
- `idaccidente` a cerrar.
- `idusuario` de quien ejecuta el cierre (operador o unidad).
- Resultado de la atencion (string, requerido).
- Numeros finales de vehiculos, victimas, heridos, fallecidos (INT, opcionales, actualizan `Fact_Accidente`).
- Calificacion de la atencion (INT, 1-5, opcional).
- Observaciones finales (string, opcional).

### Para consulta de historial (CU-O29)
- Filtros: fecha desde/hasta, estado, severidad, ubicacion geografica, unidad.
- Para Cliente: automaticamente filtrado por condados en `Dim_Preferencias_Cliente.zonas_geograficas` (match via `idcalle` → `Dim_Condado`).

### Para deteccion de perdida de señal (CU-O37)
- `idunidademergencia` (evaluada por el job).
- Umbral de tiempo sin actualizacion GPS (configurable).

### Para abortar mision (CU-O39)
- `iddespacho` a abortar.
- Motivo del aborto (string, opcional).

### Para cancelar caso con unidad despachada (CU-O42)
- `idaccidente` a cancelar.
- Motivo de cancelacion (string, requerido) — unico campo de entrada del usuario; no aplica RF-SEG-004.

### Para forzar cierre desde central (CU-O44)
- `iddespacho` a forzar retiro.
- `idusuario` del operador que forza.

## 8. Salidas

- Mapa de seguimiento en tiempo real con posiciones de unidades y accidentes activos (actualizado via SSE).
- Stream SSE de seguimiento con eventos GPS, ETA y cambios de estado.
- ETA actualizado continuamente para cada unidad en camino.
- `fechahorallegada` y estado En_sitio registrados en `Fact_HistorialDespachoUnidad`.
- `fechahoraretiro` registrado en `Fact_Despacho`.
- `horafin` y `duracionminutos` calculados y almacenados en `Fact_Accidente`.
- Estado **CERRADO** en `Fact_AccidenteTipoEstadoAccidente` (solo cuando todos los despachos estan retirados).
- Cambio de disponibilidad de unidades a **Activa** en `Fact_HistorialEstadoUnidad`.
- Alerta de perdida de señal GPS en `Dim_NotaAccidente`.
- Lista paginada de casos historicos con filtros.
- Expediente completo en PDF (para cliente).

## 9. Estados posibles

### Estados del caso (ciclo completo)
Los estados del caso a nivel de `Fact_AccidenteTipoEstadoAccidente` manejados total o parcialmente en este spec son:

- **EN_ATENCION:** al menos una unidad llego al sitio y se esta atendiendo la emergencia. Transiciona desde ASIGNADO (spec despacho-inteligente).
- **CERRADO:** caso finalizado. Todos los despachos asociados tienen `fechahoraretiro` no nulo.

Estados previos (Reportado, Buscando_Unidad, Asignado) son gestionados por los specs registro-accidente e despacho-inteligente.

### Estados del despacho (Fact_HistorialDespachoUnidad)
Gestionados en este spec mediante `Dim_EstadoDespacho`:

| Estado | Significado | Transicion desde |
|---|---|---|
| **Confirmado** | Unidad acepto el despacho y esta en camino (heredado de despacho-inteligente). | Pendiente (O24) |
| **En_sitio** | Unidad llego al sitio del accidente. | Confirmado (O26) |
| **Retirado** | Unidad se retiro del sitio. | En_sitio (O28, O42, O44) |
| **Abortado** | Mision abortada en transito. | Confirmado (O39) |

### Transiciones en este spec
```
                CU-O26 (llegada)
Confirmado ──────────────────► En_sitio ──────────► Retirado (O28/O42/O44)
     │                                                  │
     │                                                  │
     └── Abortado (O39) ──► (dispara re-asignacion O36) │
                                                         │
                    Cuando TODOS los despachos            │
                    del caso son Retirado ────────────────┘
                              │
                              ▼
                         CERRADO
```

## 10. Escenarios

### Escenario 1: Rastreo en tiempo real de unidad en camino

Dado que la "Ambulancia 05" confirmo un despacho y esta en camino al sitio
Y su app movil envia coordenadas GPS cada 10 segundos
Cuando el Operador de emergencias abre el mapa de seguimiento
Entonces debe ver la posicion actual de la ambulancia en el mapa
Y el trazado de la ruta recorrida desde que salio
Y el ETA actualizado (ej. "3.2 km restantes — ETA: 4 min")
Y cada posicion GPS se almacena en `Dim_HistorialUbicacionUnidadEmergencia`
Y la posicion snapshot se actualiza en `Dim_UnidadEmergencia`.

### Escenario 2: Llegada al sitio — confirmacion manual

Dado que la "Ambulancia 05" llega al sitio del accidente
Cuando el conductor presiona "Registrar llegada" en la app movil
Entonces el sistema debe insertar `Fact_HistorialDespachoUnidad` con estado **En_sitio**
Y debe actualizar `Fact_Despacho.fechahorallegada`
Y debe cambiar el estado del caso a **EN_ATENCION** en `Fact_AccidenteTipoEstadoAccidente`
Y debe notificar al Operador que la unidad llego al sitio.

### Escenario 3: Llegada detectada automaticamente por geofencing

Dado que la "Ambulancia 05" esta en camino
Y sus coordenadas GPS entran en un radio de 100 metros del sitio del accidente
Y permanece dentro de ese radio por mas de 30 segundos
Cuando el sistema detecta la condicion de geovalla
Entonces debe registrar la llegada automaticamente
Y debe enviar una notificacion a la app movil: "Se ha detectado su llegada al sitio. Confirme."
Y mientras la unidad confirma, el estado ya se actualiza a **EN_ATENCION**.

### Escenario 4: Cierre del caso con validacion multi-despacho

Dado que el caso tiene dos despachos activos (grua y ambulancia)
Y la ambulancia ya se retiro (fechahoraretiro registrado)
Pero la grua aun no se retira
Cuando el Operador ejecuta el cierre del caso
Entonces el sistema debe validar que todos los despachos tengan fechahoraretiro
Y al detectar que la grua aun no se retira, debe registrar automaticamente su retiro con `idusuario` = operador que ejecutó el cierre
Y debe actualizar `Fact_Accidente.horafin` y calcular `duracionminutos`
Y debe cambiar el estado a **CERRADO** en `Fact_AccidenteTipoEstadoAccidente`
Y debe liberar ambas unidades a estado **Activa** en `Fact_HistorialEstadoUnidad`.

### Escenario 5: Cliente consulta expediente de caso cerrado

Dado que un cliente (aseguradora) desea revisar un accidente ocurrido en un condado de su cobertura
Cuando accede a la seccion de historial y busca por fecha y ubicacion
Entonces el sistema debe mostrar solo los casos cerrados cuyo `Dim_Condado` esta en `Dim_Preferencias_Cliente.zonas_geograficas`
Y al seleccionar un caso, debe mostrar el expediente completo con datos del accidente, tiempos, historial de despachos (incluyendo rechazados y abortados), notificaciones, trayectoria GPS, fotos y notas
Y debe permitir descargar el expediente en formato PDF.

### Escenario 6: Operador monitorea multiples casos activos en el mapa

Dado que hay 4 accidentes activos en la ciudad con unidades en camino
Cuando el Operador abre el mapa de seguimiento
Entonces debe ver los 4 accidentes como marcadores de colores segun severidad
Y debe ver las 4 unidades en camino con sus rutas y ETAs actualizados via SSE
Y debe poder hacer clic en cualquier marcador para ver el detalle del caso.

### Escenario 7: Deteccion de perdida de señal GPS (CU-O37)

Dado que la "Ambulancia 05" esta en camino y su GPS dejo de enviar datos
Y el job de monitoreo detecta que `MAX(fechahora)` en `Dim_HistorialUbicacionUnidadEmergencia` supera el umbral de 60 segundos
Cuando se ejecuta el job
Entonces el sistema debe insertar una alerta en `Dim_NotaAccidente` con `tipo`="alerta"
Y debe notificar al Operador sobre la perdida de señal
Y la unidad sigue asignada al caso (no se modifica `Fact_Despacho`).

### Escenario 8: Abortar mision en transito (CU-O39)

Dado que la "Ambulancia 05" esta en camino hacia el accidente
Cuando el conductor selecciona "Abortar mision" en la app movil
Entonces el sistema debe insertar `Fact_HistorialDespachoUnidad` con estado **Abortado**
Y debe insertar `Fact_HistorialEstadoUnidad` con estado **Activa** para la unidad
Y debe disparar la re-asignacion O36 para encontrar una nueva unidad
Y el Operador debe ser notificado del aborto y la re-asignacion.

### Escenario 9: Cancelar caso con unidad despachada (CU-O42)

Dado que se reporto un accidente como falso alarmo y ya hay una unidad despachada
Cuando el Operador ejecuta la cancelacion del caso con motivo "Falsa alarma"
Entonces el sistema debe actualizar `Fact_Despacho.fechahoraretiro=now`
Y debe insertar `Fact_HistorialDespachoUnidad` con estado **Retirado**
Y debe insertar `Fact_HistorialEstadoUnidad` para retornar la unidad a **Activa**
Y debe actualizar `Fact_Accidente.horafin` y calcular `duracionminutos`
Y debe cambiar el estado del caso a **CERRADO** en `Fact_AccidenteTipoEstadoAccidente`
Y **no debe** solicitar ni registrar campos de RF-SEG-004 (resultado, calificacion, conteos)
Y **no debe** crear ningun registro en `Dim_EvidenciaFoto`.

### Escenario 10: Forzar cierre desde central (CU-O44)

Dado que un tecnico en campo olvido registrar el retiro de su unidad
Cuando el Operador selecciona el despacho y ejecuta "Forzar retiro"
Entonces el sistema debe actualizar `Fact_Despacho.fechahoraretiro=now` para ese despacho
Y debe insertar `Fact_HistorialDespachoUnidad` con estado **Retirado** y `idusuario` = operador
Y debe reevaluar la condicion de cierre O28
Y si todos los despachos estan ahora retirados, debe cerrar el caso a **CERRADO**
Y si quedan mas unidades activas, el caso permanece en **EN_ATENCION**.

## 11. Criterios de aceptación

### CA-SEG-001
El Operador puede ver en tiempo real la posicion GPS de las unidades en camino, actualizada cada 10 segundos, almacenada en `Dim_HistorialUbicacionUnidadEmergencia`.

### CA-SEG-002
El sistema calcula y muestra el ETA actualizado basado en la distancia remanente, entregado al mapa del Operador via SSE.

### CA-SEG-003
La llegada al sitio puede registrarse manualmente (boton en app) o automaticamente (geofencing a 100m).

### CA-SEG-004
Al registrarse la llegada, se inserta una fila en `Fact_HistorialDespachoUnidad` (estado En_sitio), se actualiza `Fact_Despacho.fechahorallegada` y el caso cambia a EN_ATENCION.

### CA-SEG-005
El cierre del caso valida que todos los despachos tengan `fechahoraretiro`, actualiza `Fact_Accidente.horafin`/`duracionminutos`, libera las unidades y registra `idusuario` del ejecutor en retiros auto-generados.

### CA-SEG-006
Al cerrar el caso, todas las unidades involucradas regresan a estado Activa en `Fact_HistorialEstadoUnidad`.

### CA-SEG-007
Los tiempos registrados al cierre son inmutables y no pueden modificarse despues del cierre.

### CA-SEG-008
El Operador puede consultar el historial completo de emergencias con filtros, incluyendo historial de despachos y trayectoria GPS.

### CA-SEG-009
El Cliente puede consultar expedientes de casos cerrados en sus zonas de interes y descargarlos en PDF.

### CA-SEG-010
El Cliente no puede ver casos activos ni el mapa de seguimiento en tiempo real.

### CA-SEG-011 (CU-O37)
El job de monitoreo detecta perdida de señal GPS cuando `MAX(fechahora)` supera el umbral configurado e inserta alerta en `Dim_NotaAccidente`.

### CA-SEG-012 (CU-O39)
Al abortar mision, se inserta estado Abortado en `Fact_HistorialDespachoUnidad`, la unidad retorna a Activa y se dispara O36.

### CA-SEG-013 (CU-O42)
Al cancelar caso con unidad despachada, todos los despachos se marcan Retirado, el caso pasa a CERRADO con `horafin`/`duracionminutos`, solo motivo en `Dim_NotaAccidente`, sin campos RF-SEG-004 ni registros en `Dim_EvidenciaFoto`.

### CA-SEG-014 (CU-O44)
Al forzar cierre desde central, el despacho se marca Retirado con `idusuario` del operador y se reevalua O28.

## 12. Dependencias

- **despacho-inteligente:** requiere un despacho confirmado (`Fact_Despacho` con `fechahoradespacho` y estado Confirmado) para iniciar el rastreo. Al abortar mision, dispara re-asignacion O36. Reutiliza patron SSE (RF-DES-011) para monitoreo en tiempo real del mapa de seguimiento (RF-SEG-007).
- **evidencia-unidad:** al cerrar el caso (O28, O42), las unidades se liberan usando `Fact_HistorialEstadoUnidad`. Las evidencias fotograficas y notas de campo se consultan en `Dim_EvidenciaFoto` y `Dim_NotaAccidente`.
- **registro-accidente:** los datos del accidente (`Fact_Accidente`) y los cambios de estado (`Fact_AccidenteTipoEstadoAccidente`) se almacenan en las tablas de este spec.
- **autenticacion-y-rbac:** requiere autenticacion JWT y roles "Operador de emergencias", "Unidad de emergencia" y "Cliente".
- **incorporacion-clientes:** `Dim_Preferencias_Cliente.zonas_geograficas` define los condados de interes del Cliente para filtrar expedientes (RF-SEG-006).

## 13. Fuera de alcance

- Asignacion y despacho de unidades: eso esta en despacho-inteligente.
- Captura de evidencia fotografica y notas de campo: eso esta en evidencia-unidad.
- Calculo de rutas optimas con trafico en tiempo real (Google Maps, Waze): este spec usa distancia lineal. La integracion con servicios de navegacion no esta incluida.
- Re-asignacion automatica tras aborto (O39): la re-asignacion O36 se dispara pero su implementacion esta en despacho-inteligente.
- Fusion de reportes duplicados (CU-O41): spec registro-accidente.
- Coordinacion de despacho multiple (CU-O38): spec despacho-inteligente.
