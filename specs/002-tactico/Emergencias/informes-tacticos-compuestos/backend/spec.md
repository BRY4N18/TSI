# Feature Specification: Informes Tácticos Compuestos de Emergencias (Backend)

**Feature Branch**: `informes-tacticos-compuestos`

**Created**: 2026-08-01

**Status**: Draft

**Input**: User description: "Informes tácticos compuestos de Emergencias — orquestados por Airflow, materializados en ClickHouse, uno por cada módulo operativo (Registro, Despacho, Seguimiento), complementando los workpanels de informes-tacticos-simples. Basado en informestacticos/auditoria-esquemas-informes-v2.md."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detectar misiones con pérdida de señal GPS (Priority: P1)

Como Supervisor de Emergencias, quiero ver un listado y un porcentaje de misiones de despacho que perdieron señal GPS de la unidad (huecos entre pings consecutivos por encima de un umbral configurado), agrupado por unidad y período, para detectar unidades con problemas de conectividad recurrentes antes de que un caso real quede sin seguimiento.

**Why this priority**: Es el caso de uso que la propia auditoría señala explícitamente como "el mejor caso de uso testigo para justificar Airflow" — requiere recorrer secuencialmente los pings de ubicación de cada unidad y detectar huecos, algo que una consulta SQL directa a Pinot no puede expresar razonablemente.

**Independent Test**: Con el DAG de detección de pérdida de señal corriendo sobre datos de prueba con huecos conocidos, se puede verificar que la tabla materializada en ClickHouse contiene exactamente las misiones con huecos por encima del umbral, ni más ni menos.

**Acceptance Scenarios**:

1. **Given** una unidad con pings consecutivos dentro del umbral de `gps_umbral_senal_perdida_seg`, **When** el DAG procesa su historial de ubicación, **Then** esa misión NO aparece en el listado de pérdida de señal.
2. **Given** una unidad con un hueco entre dos pings mayor al umbral, **When** el DAG procesa su historial, **Then** esa misión aparece en el listado, con la unidad y el intervalo de tiempo del hueco.
3. **Given** existen misiones con y sin pérdida de señal en un período, **When** se solicita el % de abortos/pérdidas sobre total de despachos, **Then** el sistema devuelve el porcentaje correcto agrupado por unidad/período.
4. **Given** el DAG ya corrió para un período, **When** se solicita el mismo período de nuevo, **Then** el resultado se sirve desde la tabla materializada en ClickHouse, sin volver a recorrer Pinot.

---

### User Story 2 - Índice consolidado de calidad del histórico (Priority: P2)

Como Supervisor de Emergencias, quiero ver un único indicador de calidad del histórico de accidentes (que combina % de completitud de campos críticos, % de descarte, % de fusión y % de cobertura de evidencia) con su evolución en el tiempo, para tener un semáforo único de qué tan confiable es el histórico que se vende como ventaja competitiva del producto.

**Why this priority**: A diferencia de los 4 informes individuales (ya cubiertos en `informes-tacticos-simples`, que muestran el valor actual), este informe requiere conservar y comparar el valor histórico período a período — algo que el modelo de upsert de Pinot no está pensado para retener; ClickHouse es el lugar natural para guardar la serie temporal ya calculada.

**Independent Test**: Con los 4 informes base ya corriendo (verificados en `informes-tacticos-simples`), se puede correr el DAG de consolidación de forma aislada y verificar que combina correctamente los 4 valores en un solo índice, para al menos 2 períodos consecutivos.

**Acceptance Scenarios**:

1. **Given** los 4 indicadores base tienen valores para un período, **When** el DAG de consolidación corre, **Then** el índice combinado queda materializado en ClickHouse para ese período.
2. **Given** existen valores del índice para varios períodos consecutivos, **When** se solicita la evolución del índice, **Then** el sistema devuelve la serie temporal completa, no solo el último valor.

---

### User Story 3 - Rendimiento de despacho por proveedor de unidades (Priority: P2)

Como Supervisor de Emergencias, quiero ver el rendimiento de despacho agrupado por proveedor de unidades (% de rechazo, tiempo de llegada, abortos), en vez de por unidad individual, para evaluar la calidad del servicio de cada proveedor externo como parte de la relación comercial con ellos.

**Why this priority**: Cruza tres tablas (`Dim_UnidadEmergencia`, `Fact_Despacho`, `Fact_HistorialDespachoUnidad`) agrupando por proveedor a lo largo de rangos de tiempo amplios — es el tipo de agregación pesada y de uso poco frecuente (revisión periódica de proveedores, no consulta operativa del día a día) que conviene materializar en batch en vez de recalcular en cada consulta.

**Independent Test**: Con el DAG corriendo sobre datos de prueba de al menos 2 proveedores con comportamiento distinto, se puede verificar que la tabla materializada distingue correctamente el rendimiento de cada proveedor.

**Acceptance Scenarios**:

1. **Given** dos proveedores con distinto % de rechazo, **When** el DAG procesa el período, **Then** la tabla materializada muestra ambos proveedores con sus métricas diferenciadas.
2. **Given** una unidad cambia de proveedor entre períodos, **When** se solicita el histórico, **Then** cada período refleja el proveedor vigente en ese momento, no el actual retroactivamente.

---

### Edge Cases

- ¿Qué pasa si el DAG falla a mitad de procesamiento (ej. Pinot no responde)? → El DAG debe reintentar la tarea fallida sin duplicar filas ya materializadas en ClickHouse para ese período (idempotencia por período/clave de agregación).
- ¿Qué pasa si se pide un período que el DAG todavía no ha procesado? → El endpoint de lectura responde explícitamente "no materializado todavía" (no un error genérico ni datos vacíos indistinguibles de "sin accidentes").
- ¿Qué pasa si `Dim_ParametrosSeguimiento.gps_umbral_senal_perdida_seg` cambia entre corridas del DAG? → El resultado materializado indica con qué umbral se calculó cada corrida, para que un cambio de configuración no se confunda con un cambio real de comportamiento de las unidades.
- ¿Qué pasa si dos unidades comparten el mismo proveedor pero una está inactiva? → El informe de rendimiento por proveedor (US3) solo cuenta despachos reales, así que una unidad inactiva sin despachos en el período simplemente no aporta al agregado — no requiere filtro adicional explícito.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE ejecutar, mediante Airflow, un DAG por cada uno de los 3 informes compuestos (pérdida de señal, índice de calidad consolidado, rendimiento por proveedor), cada uno con su propio horario de ejecución (batch, no en tiempo real).
- **FR-002**: Cada DAG DEBE leer sus datos fuente desde Pinot (solo lectura) y escribir su resultado agregado en una tabla propia de ClickHouse — nunca al revés, y nunca escribiendo de vuelta en Pinot.
- **FR-003**: Cada ejecución de un DAG DEBE ser idempotente respecto al período que procesa: volver a ejecutar el mismo período no debe duplicar ni corromper filas ya materializadas.
- **FR-004**: El sistema DEBE exponer un endpoint de lectura por cada informe compuesto, que sirva el resultado ya materializado en ClickHouse (sin recalcular en el momento de la consulta).
- **FR-005**: El DAG de pérdida de señal (User Story 1) DEBE recorrer los pings de `Dim_HistorialUbicacionUnidadEmergencia` en orden cronológico por unidad y detectar huecos mayores al umbral vigente en `Dim_ParametrosSeguimiento.gps_umbral_senal_perdida_seg` en el momento de la corrida.
- **FR-006**: El DAG del índice de calidad consolidado (User Story 2) DEBE combinar los 4 indicadores base ya definidos en `informes-tacticos-simples` (completitud, descarte, fusión, cobertura de evidencia) en un único valor por período, conservando la serie histórica de períodos ya calculados.
- **FR-007**: El DAG de rendimiento por proveedor (User Story 3) DEBE agrupar por `Dim_UnidadEmergencia.idcliente` (o `contactoproveedor`), no por unidad individual, calculando % de rechazo, tiempo de llegada y % de abortos por proveedor y período.
- **FR-008**: Cuando un período solicitado no ha sido procesado todavía por el DAG correspondiente, el endpoint de lectura DEBE responder de forma distinguible de "período sin datos" (FR-006 de `informes-tacticos-simples`).
- **FR-009**: El acceso a estos 3 informes DEBE quedar restringido al rol Supervisor de Emergencias (no Operador raso), dado que son indicadores de gestión, no de operación caso a caso — reutilizando el RBAC existente.
- **FR-010**: El sistema DEBE registrar (log) cada ejecución de DAG con su resultado (éxito/fallo, período procesado, filas materializadas), para poder auditar cuándo se actualizó por última vez cada informe.

### Key Entities

- **DAG de informe compuesto**: Definición de Airflow que orquesta la lectura desde Pinot, el procesamiento (agregación simple o secuencial según el informe) y la escritura en ClickHouse. Vive en `docker/tactico/airflow-dags/` (infraestructura ya provista por `../../infraestructura/`).
- **Tabla materializada de ClickHouse**: Resultado ya calculado de un informe compuesto, particionado por período, con indicación de cuándo y con qué parámetros se calculó. Una por informe (3 en total en esta spec).
- **Ejecución de DAG**: Registro de una corrida concreta (período procesado, resultado, timestamp), usado para auditar frescura de los datos servidos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Supervisor puede consultar cualquiera de los 3 informes compuestos para un período ya procesado en menos de 2 segundos (lectura de tabla materializada, sin recomputar).
- **SC-002**: El DAG de pérdida de señal identifica el 100% de los huecos por encima del umbral configurado en un conjunto de datos de prueba con casos conocidos, sin falsos negativos.
- **SC-003**: Re-ejecutar cualquiera de los 3 DAGs sobre el mismo período no cambia el número de filas materializadas para ese período (idempotencia verificable).
- **SC-004**: Un Supervisor puede identificar, usando el informe de rendimiento por proveedor, cuál de dos o más proveedores tiene peor desempeño, sin ayuda externa ni acceso directo a Pinot/ClickHouse.

## Assumptions

- Los 3 informes de esta spec se integran como tarjetas adicionales dentro de los workpanels ya definidos en `../informes-tacticos-simples/frontend/` (pérdida de señal → workpanel de Seguimiento; índice de calidad → workpanel de Registro; rendimiento por proveedor → workpanel de Despacho) — esta spec de backend no define la disposición visual, solo los datos y su disponibilidad.
- La frecuencia de ejecución de los 3 DAGs es diaria por defecto (procesamiento batch nocturno); un requisito de mayor frecuencia para alguno de los 3 se definiría como ajuste posterior, no como parte de esta primera versión.
- El umbral `gps_umbral_senal_perdida_seg` ya existe como dato de catálogo en `Dim_ParametrosSeguimiento` (ver auditoría) — esta spec no lo crea, solo lo consume.
- Ningún informe de esta spec requiere datos que no existan ya en el esquema real de Pinot v2 (los 3 están marcados ✅ Cubierto o ✅ Cubierto 🆕 en la auditoría) — no se necesita ningún cambio de esquema adicional.
- Esta spec depende en firme de `../../infraestructura/` (ClickHouse + Airflow) ya implementada y verificada — no es viable empezar el plan de esta feature sin esa base arriba.
