# Feature Specification: Informes Tácticos Simples de Emergencias (Backend)

**Feature Branch**: `informes-tacticos-agregados`

**Created**: 2026-08-01

**Status**: Draft

**Input**: User description: "Informes tácticos simples de Emergencias — consulta directa a Pinot, sin ClickHouse/Airflow, para los 3 módulos operativos: Registro de Accidente, Despacho Inteligente y Seguimiento y Cierre de Casos. Basado en informestacticos/auditoria-esquemas-informes-v2.md (informes ya marcados ✅ Cubierto)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar informes de Registro de Accidente (Priority: P1)

Como Operador o Supervisor de Emergencias, quiero consultar un conjunto de indicadores agregados sobre los accidentes registrados (volumen, severidad, zona, calidad del registro, ranking de ubicaciones, impacto humano), filtrables por período, para entender el volumen y la calidad del trabajo de registro sin tener que revisar caso por caso.

**Why this priority**: Es el módulo con más informes ya viables (✅ Cubierto) y el que alimenta datos de mayor valor comercial (impacto humano, calidad del histórico) según la auditoría — el mejor punto de entrada para demostrar valor con el menor esfuerzo.

**Independent Test**: Se puede solicitar cada uno de los 7 indicadores de este módulo de forma aislada (con un rango de período dado) y obtener una respuesta agregada correcta, sin necesidad de que los otros dos módulos existan todavía.

**Acceptance Scenarios**:

1. **Given** existen accidentes registrados en el período solicitado, **When** se solicita el volumen total de casos por período, **Then** el sistema devuelve el conteo agrupado por el período pedido (día/semana/mes).
2. **Given** existen accidentes con distintos niveles de severidad, **When** se solicita la distribución por severidad, **Then** el sistema devuelve el conteo agrupado por cada nivel de severidad.
3. **Given** existen accidentes en distintas zonas/regiones, **When** se solicita la distribución por zona, **Then** el sistema devuelve el conteo agrupado por el nivel geográfico solicitado (calle, ciudad, condado, estado).
4. **Given** existen accidentes con y sin campos críticos completos, **When** se solicita el % de completitud, **Then** el sistema devuelve el porcentaje de registros con severidad y calle no nulos sobre el total del período.
5. **Given** existen accidentes descartados y fusionados, **When** se solicita el % de descarte y fusión, **Then** el sistema devuelve ambos porcentajes sobre el total de reportes del período.
6. **Given** existen accidentes concentrados en ciertas ubicaciones, **When** se solicita el ranking de ubicaciones, **Then** el sistema devuelve las ubicaciones ordenadas por frecuencia descendente, limitadas a un tope configurable.
7. **Given** existen accidentes con datos de víctimas/heridos/fallecidos, **When** se solicita el impacto humano por región, **Then** el sistema devuelve la suma de cada campo agrupada por región y período.

---

### User Story 2 - Consultar informes de Despacho Inteligente (Priority: P1)

Como Operador o Supervisor de Emergencias, quiero consultar indicadores sobre cómo se están despachando las unidades (automatización, tiempos de respuesta, rechazos, carga por unidad, relación entre demanda y capacidad por condado), para detectar cuellos de botella operativos antes de que degraden el servicio.

**Why this priority**: Junto con Registro, es el otro módulo con más informes viables; además incluye el informe "ratio demanda/capacidad por condado", que la auditoría señala como la métrica central del objetivo estratégico de "escalar sin degradar el servicio".

**Independent Test**: Se puede solicitar cada uno de los 6 indicadores de este módulo de forma aislada y obtener una respuesta agregada correcta, sin depender de que User Story 1 o 3 estén implementadas.

**Acceptance Scenarios**:

1. **Given** existen despachos con distinto origen (automático/manual/escalado), **When** se solicita el % de asignaciones por origen, **Then** el sistema devuelve el porcentaje agrupado por tipo de origen, con opción de cortar por condado.
2. **Given** un accidente pasó de reportado a confirmado, **When** se solicita el tiempo promedio entre ambos estados, **Then** el sistema devuelve el promedio de la diferencia de tiempos del período.
3. **Given** existen despachos con distinta severidad de accidente asociada, **When** se solicita la distribución del tiempo de respuesta por severidad, **Then** el sistema devuelve el tiempo agrupado por nivel de severidad (y opcionalmente por condado).
4. **Given** existen despachos rechazados o con timeout, **When** se solicita el % de rechazo/timeout por unidad, **Then** el sistema devuelve el porcentaje agrupado por unidad para el período.
5. **Given** existen despachos atendidos por distintas unidades, **When** se solicita la carga de despachos por unidad, **Then** el sistema devuelve el conteo agrupado por unidad para el período.
6. **Given** existen accidentes y unidades activas en un condado, **When** se solicita el ratio demanda/capacidad, **Then** el sistema devuelve, por condado, el conteo de accidentes dividido entre el conteo de unidades activas.

---

### User Story 3 - Consultar informes de Seguimiento y Cierre de Casos (Priority: P2)

Como Operador o Supervisor de Emergencias, quiero consultar indicadores sobre cómo se cierran los casos (tiempos hasta el cierre, cierres forzados, abortos/pérdidas de misión), para verificar que el ciclo completo del caso se está resolviendo dentro de lo esperado.

**Why this priority**: Completa el ciclo de vida del caso (registro → despacho → cierre), pero tiene menos informes que los otros dos módulos y depende de datos que ya se generan en las etapas anteriores — es la prioridad más baja de las tres sin dejar de ser necesaria para el objetivo de los 3 workpanels.

**Independent Test**: Se puede solicitar cada uno de los 3 indicadores de este módulo de forma aislada y obtener una respuesta agregada correcta, sin depender de que User Story 1 o 2 estén implementadas.

**Acceptance Scenarios**:

1. **Given** un caso pasó de asignado a cerrado, **When** se solicita el tiempo promedio entre ambos estados, **Then** el sistema devuelve el promedio agrupado por unidad, zona o período, según el corte solicitado.
2. **Given** existen cierres forzados desde central y cierres normales, **When** se solicita el % de cierres forzados, **Then** el sistema devuelve el porcentaje sobre el total de cierres del período.
3. **Given** existen despachos abortados o con pérdida de señal, **When** se solicita el % de abortos/pérdidas, **Then** el sistema devuelve el porcentaje sobre el total de despachos del período, agrupado por unidad.

---

### Edge Cases

- ¿Qué pasa si el período solicitado no tiene ningún dato? → El indicador correspondiente devuelve cero/vacío explícito, no un error, y el workpanel lo muestra como "sin datos en este período" en vez de dejar la tarjeta en blanco.
- ¿Qué pasa si se solicita un rango de período excesivamente amplio (ej. varios años)? → Cada consulta declara un `LIMIT` explícito (regla vinculante ya documentada en `infrastructure.md`); si el resultado agregado excede ese límite, el sistema indica que el rango debe acotarse, en vez de truncar el resultado en silencio.
- ¿Qué pasa si el usuario no tiene permiso para ver informes de un condado/zona fuera de su alcance? → Queda fuera de esta spec definir un modelo de permisos por zona nuevo; se asume el mismo control de acceso por rol (Operador/Supervisor) ya vigente para el resto del sistema, sin recorte adicional por geografía en esta primera versión (ver Assumptions).
- ¿Qué pasa si dos informes del mismo workpanel se solicitan simultáneamente? → Cada informe es un endpoint y una consulta independientes; no hay dependencia de orden entre ellos dentro de un mismo workpanel.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE exponer un endpoint de agregación por cada uno de los 16 informes descritos en las 3 historias de usuario (7 de Registro, 6 de Despacho, 3 de Seguimiento), cada uno con su propio contrato de entrada/salida.
- **FR-002**: Cada endpoint DEBE aceptar un filtro de período (rango de fechas) como parámetro obligatorio, y filtros adicionales opcionales según el informe (zona/condado/unidad/severidad), documentados en su contrato.
- **FR-003**: Cada endpoint DEBE calcular su resultado con una única consulta a Pinot que incluya `GROUP BY`, filtro y `LIMIT` explícitos — sin traer un conjunto sin acotar para recortarlo o agregarlo en Python.
- **FR-004**: El sistema DEBE mantener a Pinot como fuente de solo lectura para estos informes — ningún endpoint de esta feature escribe en Pinot ni publica eventos en Kafka.
- **FR-005**: El sistema DEBE devolver, para cada informe, una respuesta agregada estructurada (no filas crudas de detalle) lista para representarse como tarjeta o gráfica.
- **FR-006**: El sistema DEBE responder con un resultado vacío explícito (no error) cuando el período solicitado no tiene datos.
- **FR-007**: El acceso a estos endpoints DEBE quedar restringido a los roles Operador y Supervisor de Emergencias, siguiendo el mecanismo de autenticación/autorización ya vigente en el sistema (`Dim_Credencial`, RBAC existente) — sin introducir un mecanismo nuevo.
- **FR-008**: El sistema DEBE registrar (log) cada solicitud a estos endpoints con el rol solicitante y el rango de período consultado, para trazabilidad de uso — sin registrar aquí el detalle de los resultados devueltos.
- **FR-009**: Los 16 informes de esta spec DEBEN corresponder exactamente a los ya marcados ✅ Cubierto en `informestacticos/auditoria-esquemas-informes-v2.md` para los módulos Registro de Accidente, Despacho Inteligente y Seguimiento y Cierre de Casos — ningún informe nuevo fuera de esa lista se agrega sin actualizar primero la auditoría.

### Key Entities

- **Informe agregado**: Resultado de una consulta de agregación sobre una o más tablas Pinot (`Fact_Accidente`, `Fact_Despacho`, `Fact_HistorialDespachoUnidad`, `Fact_AccidenteTipoEstadoAccidente`, `Dim_UnidadEmergencia`, dimensiones geográficas), parametrizado por período y filtros opcionales. No se persiste — se calcula en cada solicitud.
- **Workpanel**: Agrupación de varios informes agregados de un mismo módulo (Registro, Despacho o Seguimiento), consumida por el frontend en una sola pantalla. Se define formalmente en la capa `frontend/` de este módulo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Operador o Supervisor puede obtener cualquiera de los 16 informes de este módulo en menos de 3 segundos, para un rango de período de hasta 90 días.
- **SC-002**: El 100% de los 16 informes coinciden, en su fórmula de cálculo, con lo descrito en `informestacticos/auditoria-esquemas-informes-v2.md` para cada uno (sin desviación de criterio de agregación).
- **SC-003**: El 100% de las consultas generadas por estos endpoints declaran `LIMIT` explícito, verificable por revisión de código/consulta antes de cada despliegue.
- **SC-004**: Un Supervisor que use los 3 workpanels (una vez exista el frontend) puede identificar, sin ayuda externa, al menos un cuello de botella operativo (ej. una zona con alto volumen y baja capacidad) usando solo estos informes.

## Assumptions

- El control de acceso de esta primera versión es por rol (Operador/Supervisor), no por zona/condado asignado — un recorte de datos por área de responsabilidad del usuario queda fuera de alcance hasta que exista un requisito explícito que lo pida.
- El agrupamiento de "período" soporta al menos día, semana y mes; una granularidad más fina (hora) no se requiere para ningún informe de esta lista según la auditoría.
- Los 16 informes elegidos ya están marcados ✅ Cubierto en la auditoría — no se requiere ningún cambio de esquema de Pinot para implementarlos.
- El frontend consumirá estos endpoints vía los 3 workpanels definidos en la capa `frontend/` de este mismo módulo (uno por módulo operativo); esta spec de backend no define la disposición visual de las tarjetas/gráficas.
- No se requiere ClickHouse ni Airflow para ningún informe de esta spec — toda la capa de infraestructura `002-tactico` es irrelevante para este módulo salvo como contexto de que existe una vía compuesta separada para lo que Pinot no puede resolver directo.
