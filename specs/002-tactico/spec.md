# Feature Specification: Infraestructura Táctica (ClickHouse + Airflow)

**Feature Branch**: `002-tactico`

**Created**: 2026-08-01

**Status**: Draft

**Input**: User description: "Crear la spec de infraestructura táctica ('tactico-infra') para el nuevo sistema de informes tácticos del departamento de Gestión de Emergencias. Se necesita agregar infraestructura NUEVA (ClickHouse + Apache Airflow) agrupada bajo el nombre 'tactico', separada pero conviviendo con el stack de infraestructura actual (Kafka + Apache Pinot). Es solo infraestructura: servicios, puertos, volúmenes, variables de entorno, y cómo se conecta este stack con Pinot (fuente) hacia ClickHouse (destino de informes compuestos) vía Airflow. No incluye DAGs de negocio ni workpanels de frontend — eso va en specs separadas."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Levantar el stack táctico junto al stack operativo existente (Priority: P1)

Como responsable de infraestructura del proyecto, quiero poder levantar un stack adicional de servicios ("tactico") con un solo comando, sin afectar ni reiniciar el stack operativo existente (Kafka + Pinot), para disponer de un almacén analítico (ClickHouse) y un orquestador (Airflow) dedicados a los informes tácticos compuestos.

**Why this priority**: Sin esta infraestructura base, ninguna de las specs siguientes (informes simples, informes compuestos) tiene dónde ejecutarse. Es el prerrequisito bloqueante de todo el sistema de informes tácticos.

**Independent Test**: Se puede levantar el stack "tactico" de forma aislada y verificar que ClickHouse acepta conexiones y que la interfaz web de Airflow carga, sin necesidad de que exista todavía ningún DAG ni ningún informe.

**Acceptance Scenarios**:

1. **Given** el stack operativo (Kafka + Pinot) está corriendo, **When** se levanta el stack "tactico", **Then** ambos stacks coexisten sin conflictos de puertos, nombres de red ni de volúmenes.
2. **Given** el stack "tactico" está levantado, **When** se detiene o reinicia el stack operativo, **Then** los servicios del stack "tactico" no se ven afectados (y viceversa).
3. **Given** el stack "tactico" recién levantado, **When** se consulta la interfaz de administración de Airflow, **Then** el operador puede autenticarse y ver el listado de DAGs (vacío en esta fase).
4. **Given** el stack "tactico" recién levantado, **When** se ejecuta una consulta de verificación contra ClickHouse, **Then** el servicio responde y permite crear una base de datos/tabla de prueba.

---

### User Story 2 - Persistencia de datos entre reinicios (Priority: P2)

Como responsable de infraestructura, quiero que los datos de ClickHouse y los metadatos de Airflow (DAGs registrados, historial de ejecuciones, conexiones configuradas) sobrevivan a un reinicio de los contenedores, para no perder el trabajo de orquestación ni los informes ya materializados.

**Why this priority**: Sin persistencia, cada reinicio destruiría el histórico de ejecuciones de Airflow y los informes compuestos ya calculados en ClickHouse, obligando a recalcular todo desde cero — inviable en un entorno de desarrollo iterativo.

**Independent Test**: Se puede detener y volver a levantar el stack "tactico" y verificar que una tabla de prueba creada previamente en ClickHouse, y una conexión/variable configurada previamente en Airflow, siguen existiendo.

**Acceptance Scenarios**:

1. **Given** existe una tabla con datos en ClickHouse, **When** se detiene y se vuelve a levantar el stack "tactico", **Then** la tabla y sus datos siguen presentes.
2. **Given** Airflow tiene una conexión o variable configurada, **When** se reinicia el stack, **Then** esa configuración persiste.

---

### User Story 3 - Conectividad Pinot → Airflow → ClickHouse (Priority: P1)

Como responsable de infraestructura, quiero que el orquestador (Airflow) tenga conectividad de red hacia el stack operativo (Pinot, como fuente de datos) y hacia el almacén analítico (ClickHouse, como destino), para que las tareas de orquestación de informes compuestos (a definir en specs posteriores) puedan leer de un lado y escribir en el otro.

**Why this priority**: Es la capacidad mínima que justifica tener Airflow y ClickHouse conviviendo con Pinot — sin esta conectividad verificada, no se puede construir ningún DAG de negocio después.

**Independent Test**: Desde un worker/scheduler de Airflow se puede alcanzar por red tanto el broker de Pinot como el servidor de ClickHouse (por ejemplo, mediante una tarea de prueba que haga un ping/consulta trivial a cada uno), sin exponer credenciales ni datos reales todavía.

**Acceptance Scenarios**:

1. **Given** el stack "tactico" y el stack operativo están levantados simultáneamente, **When** se ejecuta una tarea de conectividad de prueba desde Airflow hacia el broker de Pinot, **Then** la conexión se establece correctamente.
2. **Given** el stack "tactico" está levantado, **When** se ejecuta una tarea de conectividad de prueba desde Airflow hacia ClickHouse, **Then** la conexión se establece correctamente.

---

### Edge Cases

- ¿Qué pasa si el stack operativo (Kafka/Pinot) no está levantado cuando se intenta levantar el stack "tactico"? → El stack "tactico" debe poder levantarse de forma independiente (ClickHouse y Airflow arrancan sin depender de que Pinot esté arriba); solo las tareas de conectividad Pinot→Airflow fallarán hasta que ambos estén activos.
- ¿Qué pasa si hay conflicto de puertos con otros servicios ya usados por el proyecto (backend Django, frontend, Pinot, Kafka)? → Todos los puertos expuestos por el stack "tactico" deben ser distintos a los ya documentados en `infrastructure.md`.
- ¿Qué pasa si se levantan dos veces los stacks en la misma máquina? → Los comandos de levantamiento deben ser idempotentes (reutilizar contenedores/volúmenes existentes en vez de duplicarlos).
- ¿Cómo se identifican los recursos (contenedores, redes, volúmenes) del stack táctico frente a los del stack operativo? → Todos los nombres de servicio, contenedor, volumen y red del stack nuevo deben llevar el prefijo `tactico` para diferenciarse claramente en herramientas de administración de contenedores.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE proveer un stack de infraestructura independiente, identificado con el prefijo `tactico`, que agrupe un servicio de almacenamiento analítico (ClickHouse) y un orquestador de flujos de trabajo (Airflow).
- **FR-002**: El stack `tactico` DEBE poder levantarse y detenerse con un comando independiente del stack operativo existente (Kafka + Pinot), sin requerir modificar ni reiniciar dicho stack.
- **FR-003**: El stack `tactico` DEBE convivir en la misma máquina/red que el stack operativo existente sin colisión de puertos, nombres de contenedor, volúmenes ni redes.
- **FR-004**: El componente de orquestación (Airflow) DEBE incluir sus piezas mínimas de operación: interfaz web de administración, planificador (scheduler) y un almacén de metadatos propio para registrar DAGs, ejecuciones, conexiones y variables.
- **FR-005**: El componente analítico (ClickHouse) DEBE quedar accesible para lectura/escritura desde el orquestador (Airflow) y desde clientes de consulta (para verificación manual), dentro de la misma red del stack `tactico`.
- **FR-006**: Los datos almacenados en ClickHouse y los metadatos de Airflow DEBEN persistir a través de reinicios y recreaciones de contenedores (volúmenes con nombre, no efímeros).
- **FR-007**: El orquestador (Airflow) DEBE tener conectividad de red verificable tanto hacia el broker de Apache Pinot (stack operativo, como fuente) como hacia ClickHouse (stack `tactico`, como destino), sin que esta spec defina todavía ningún DAG de negocio concreto.
- **FR-008**: El acceso administrativo a la interfaz web de Airflow DEBE requerir autenticación (usuario/contraseña), no debe quedar abierto sin credenciales.
- **FR-009**: La documentación de infraestructura del proyecto (según el patrón ya usado en `.specify/docs/infra/infrastructure.md`) DEBE actualizarse para reflejar los nuevos servicios, puertos y variables de entorno del stack `tactico`.
- **FR-010**: El stack `tactico` NO DEBE requerir cambios en el esquema de datos de Pinot ni en el código de las apps de negocio existentes — es exclusivamente infraestructura nueva a su lado.

### Key Entities

- **Stack tactico**: Agrupación lógica de servicios de infraestructura (ClickHouse, Airflow y sus componentes de soporte) identificada con el prefijo `tactico`, independiente pero coexistente con el stack operativo (Kafka + Pinot).
- **Almacén analítico (ClickHouse)**: Servicio donde se materializarán, en specs futuras, los resultados de los informes tácticos compuestos. En esta spec solo se define su disponibilidad, no su modelo de datos.
- **Orquestador (Airflow)**: Servicio que en specs futuras ejecutará los flujos (DAGs) que crucen datos de Pinot y los transformen hacia ClickHouse. En esta spec solo se define su disponibilidad y conectividad, no la lógica de negocio de ningún flujo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El stack `tactico` puede levantarse desde cero en menos de 5 minutos en un entorno de desarrollo estándar.
- **SC-002**: El 100% de los puertos, nombres de contenedor y volúmenes del stack `tactico` son distinguibles a simple vista (prefijo `tactico`) frente a los del stack operativo existente, sin ninguna colisión.
- **SC-003**: Tras un reinicio completo del stack `tactico` (detener y levantar), el 100% de los datos de prueba almacenados previamente en ClickHouse y de la configuración registrada previamente en Airflow permanecen intactos.
- **SC-004**: Una tarea de conectividad de prueba ejecutada desde Airflow alcanza exitosamente tanto Pinot como ClickHouse en el 100% de los intentos, con ambos stacks levantados.
- **SC-005**: Un responsable de infraestructura nuevo en el proyecto puede levantar el stack `tactico` siguiendo únicamente la documentación actualizada, sin soporte adicional.

## Assumptions

- El stack `tactico` se ejecuta en el mismo entorno de desarrollo/despliegue (Docker) que el stack operativo actual (`docker/docker-compose.infraestructura.yml`), como un archivo compose adicional (p. ej. `docker-compose.tactico.yml`) que se levanta junto al existente — no reemplaza ni fusiona con él.
- Airflow requiere una base de datos relacional propia para sus metadatos (independiente de ClickHouse y de las bases operativas del proyecto); se asume Postgres por ser el backend de metadatos estándar y recomendado de Airflow.
- Esta fase no expone ningún puerto de ClickHouse ni de Airflow a internet — el alcance es entorno de desarrollo/interno, igual que el resto de `infrastructure.md`.
- Las credenciales de administración de Airflow y de acceso a ClickHouse en esta fase son de desarrollo (no se define aquí un esquema de gestión de secretos productivo); eso queda fuera de alcance.
- Ningún DAG de negocio, ninguna tabla de ClickHouse con modelo de datos real, ni ningún workpanel de frontend se define en esta spec — son objeto de specs posteriores dedicadas a informes simples e informes compuestos del departamento de Gestión de Emergencias.
