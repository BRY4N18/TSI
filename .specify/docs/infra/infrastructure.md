# Infraestructura — TSI (Tráfico Seguro Integral)

**Ubicación de este archivo:** `docs/arquitectura/infraestructura.md`
**Última actualización:** 2026-08-01 (v3 — stack `tactico` ClickHouse+Airflow activo; clarificación Kafka+Pinot = canal único de *dominio*)

> Contexto de referencia sobre qué infraestructura y stack tecnológico existen y cómo se conectan. No es un manual de operación.

---

## 1. Qué es esto

TSI usa **Apache Kafka + Apache Pinot** como **canal único del modelo dimensional de dominio** (`Dim_*`/`Hecho_*`, ver `docs/arquitectura/modelo-datos.md`): no hay ORM Django ni PostgreSQL de negocio para ese modelo. Todo el modelo dimensional vive en Pinot, alimentado en tiempo real vía Kafka.

Aparte de ese canal operativo existe el stack **`tactico`** (ClickHouse + Airflow, ver §2.1): capa analítica batch para informes tácticos compuestos. El Postgres que acompaña a Airflow es **solo metastore del orquestador** (DAGs, runs, conexiones) — no almacena el modelo dimensional ni sustituye a Pinot.

```
Django Service → publica evento → Kafka topic → Pinot ingiere en tiempo real (Kafka consumer)
Django Service → SQL directo → Pinot Broker → resultado (solo lectura)
```

**Módulos de negocio que dependen de esto:** todos — es la única capa de datos del sistema.

---

## 2. Servicios de datos: puertos y orden de dependencia

| Orden | Servicio           | Puerto                               | Rol                                                      |
| ----- | ------------------ | ------------------------------------ | -------------------------------------------------------- |
| 1     | `zookeeper`        | `2181`                               | Coordinación de Kafka y de los nodos de Pinot            |
| 2     | `kafka`            | `9092` (externo) / `29092` (interno) | Cola de eventos / streaming de mensajes                  |
| 3     | `pinot-controller` | `9000`                               | Administra metadata de tablas/esquemas de Pinot          |
| 4     | `pinot-broker`     | `8099`                               | Recibe queries y las enruta a los servers                |
| 5     | `pinot-server`     | `8098`                               | Almacena y ejecuta las queries sobre los datos indexados |

Orden de arranque: `zookeeper` → `kafka` → `pinot-controller` → `pinot-broker` → `pinot-server`. Todos los servicios comparten la red `pipeline-net`.

### 2.1 Stack `tactico`: capa analítica batch (activo, ver §5.1)

Servicios adicionales, definidos en `docker/docker-compose.tactico.yml`, que se levantan de forma **independiente** del stack anterior pero comparten la misma red `pipeline-net`:

| Servicio | Puerto (host) | Rol |
| --- | --- | --- |
| `tactico-clickhouse` | `8123` (HTTP) / `9100` (nativo TCP, remapeado — `9000` ya lo usa `pinot-controller`) | Almacén analítico batch — destino de los informes tácticos compuestos |
| `tactico-airflow-postgres` | *sin publicar* | Metastore de Airflow (DAGs, runs, conexiones, variables) |
| `tactico-airflow-webserver` | `8090` | UI de administración de Airflow |
| `tactico-airflow-scheduler` | *sin publicar* | Planificador de DAGs |

Orden de arranque: `tactico-airflow-postgres` → `tactico-airflow-init` (migraciones + usuario admin, corre una vez) → `tactico-airflow-webserver` / `tactico-airflow-scheduler`. `tactico-clickhouse` no depende de los anteriores. Spec y diseño: `specs/002-tactico/infraestructura/` (`spec.md`, plan, contrato, quickstart, tasks).

Pinot no es un solo servicio: son 3 procesos independientes (controller/broker/server), cada uno con su propio contenedor.

**Cada tabla del modelo dimensional tiene su propio tópico Kafka**, con el formato `{NombreTabla}_topic`. Configuración de ingesta: stream `kafka` (lowlevel consumer), decoder JSON, offset reset `smallest`, modo `MMAP`, upsert `FULL` sobre la columna `fecha_actualizacion`.

---

### 2.1 Despliegue local de `django` y `frontend` (`accidentes.yml`)

Ninguno de los dos servicios de aplicación tiene volumen montado hacia el código fuente — ambos corren desde una **imagen ya compilada** (`COPY . .` en su `Dockerfile`). Un cambio en el código del host **no se refleja** en el contenedor con solo `docker compose restart`; hace falta reconstruir la imagen y recrear el contenedor:

```sh
docker compose -f accidentes.yml build django    # o frontend
docker compose -f accidentes.yml up -d django    # recrea con la imagen nueva
```

`restart` reinicia el proceso pero reutiliza la imagen existente, así que no sirve para desplegar un cambio de código — solo para recuperarse de un proceso colgado.

---

## 3. Stack tecnológico completo

| Componente              | Tecnología                   | Versión                         | Notas                                                |
| ----------------------- | ---------------------------- | ------------------------------- | ---------------------------------------------------- |
| Backend                 | Django (Python)              | 5.x / 3.12+                     | Framework principal server-side                      |
| Frontend                | Angular (TypeScript)         | 19+ / 5.x                       | SPA de interfaz de usuario                           |
| Utilidades CSS           | Tailwind CSS                 | v4                               | Sistema de utilidades CSS del frontend, adoptado para reemplazar el CSS escrito a mano por componente. El `@theme` de Tailwind se mapea a los tokens de `design-system.md` (`--bg-page`, `--accent-primary`, etc., ya definidos como CSS custom properties en `frontend/src/styles.css`), para que ambos mecanismos convivan sobre la misma fuente de verdad de color/radio |
| Iconografía               | @tabler/icons (SVG inline)   | última estable                   | Set de íconos oficial declarado en `design-system.md` §5 — se inlinean los SVG puntuales usados (no el paquete completo) vía un componente wrapper (`TablerIconComponent`), sin depender de una fuente web ni de red |
| Mapas                     | Leaflet + OpenStreetMap (claro) / CartoDB Dark Matter (oscuro) | última estable (`leaflet`)       | Ver sección 6 de este documento — decisión completa con justificación |
| Mensajería              | Apache Kafka                 | 7.6.1 (`confluentinc/cp-kafka`) | Bus de eventos — único canal de escritura de datos   |
| Coordinación            | Apache Zookeeper             | 3.8.4 (`zookeeper`)             | Coordinación de Kafka y Pinot                        |
| Base de datos analítica | Apache Pinot                 | 1.2.0 (`apachepinot/pinot`)     | Almacenamiento analítico — solo lectura desde Django |
| Tiempo real (frontend)  | Server-Sent Events (SSE)     | Nativo del navegador (`EventSource`) | Canal servidor→cliente para tracking de unidades en tiempo real. **Reemplaza a Django Channels + WebSockets** (decisión v2): el tracking de ubicación es estrictamente unidireccional (servidor→cliente), y mantener un WebSocket full-duplex por cada operador/unidad conectada consume más recursos de los que el caso de uso requiere. SSE da reconexión automática nativa y menor overhead por conexión persistente. Si en el futuro aparece un CU genuinamente bidireccional en tiempo real (ej. chat operador↔unidad, hoy fuera de los 89 CU), ahí sí se evalúa WebSocket para ese caso puntual — no como mecanismo general |
| Linter Python           | Ruff                         | última estable                  | Linter y formatter unificado                         |
| Linter TypeScript       | ESLint                       | última estable                  | Análisis estático de código TS                       |
| Formatter TypeScript    | Prettier                     | última estable                  | Auto-formato para TS, HTML, CSS, JSON                |
| Contenedores            | Docker + Docker Compose      | última estable                  | Definición de referencia: `docker-compose.pinot.yml` |
| Almacenamiento de archivos | Azure Blob Storage        | —                                | Almacenamiento de binarios (evidencia fotográfica de accidentes, adjuntos de tickets de soporte). Pinot/Kafka **nunca** almacenan el binario, solo la URL resultante (ej. `Dim_EvidenciaFoto.urlevidenciafoto`, `Fact_ArchivosAdjuntosReclamos.urlarchivo`). No genera conflicto con la regla de canal único de escritura (sección 4): Pinot sigue siendo metadata/analítica, el archivo vive aparte |

---

## 4. Reglas vinculantes de flujo de datos

- Toda escritura de datos de dominio pasa por Kafka, nunca directo a Pinot.
- Todo acceso a datos pasa por repositorios en `core/`, nunca SQL crudo en vistas o servicios.
- Los tópicos de Kafka se definen en la especificación del módulo que los publica, no en el consumidor.
- Pinot es de solo lectura desde Django; Kafka es el canal de escritura.
- Pinot no soporta UPDATE/DELETE tradicional: los cambios de estado (ej. accidente ACTIVO → CERRADO) se modelan como eventos nuevos en Kafka, no como mutaciones de registro.
- **Toda consulta a Pinot declara un `LIMIT` explícito.** Pinot aplica un `LIMIT 10` implícito a las consultas que no lo traen, y la respuesta no distingue "hay 10 filas" de "hay 10 de 500": el recorte es silencioso y sin `ORDER BY` ni siquiera es estable entre llamadas. `PinotClient.query` añade un tope de seguridad, pero un repositorio que filtre o pagine sobre el resultado debe declarar el suyo. Ver `.specify/docs/changelog.md` D1.
- **Filtros, orden y paginación viven en el SQL, no en Python.** Traer un conjunto y recortarlo en memoria del servidor deja los filtros operando sobre un subconjunto arbitrario. La paginación es keyset (cursor sobre una columna monótona), y avanzar de página emite una consulta nueva acotada — nunca se materializa la tabla.
- **Ordenar y paginar usan la misma clave.** Ordenar por un campo y comparar el cursor contra otro deja huecos o repite filas entre páginas.
- **Nunca releer de Pinot lo que se acaba de escribir por Kafka** dentro de la misma operación: la ingesta tarda segundos y la lectura devuelve vacío. Un rollback que dependa de esa relectura falla en silencio (ver B2).
- Las tablas de Pinot son **upsert por clave primaria**: publicar un registro parcial borra el resto de columnas, y dos escritores que reusen un id se pisan sin aviso. Convenciones de seeds en `datos-demo.md`.
- **ClickHouse y el Postgres de Airflow no son almacén de dominio.** El stack `tactico` (ver §2.1) materializa resultados analíticos batch y metadatos del orquestador; no sustituye Kafka→Pinot para el modelo dimensional ni para escrituras de apps Django.

---

## 5. Decisiones de infraestructura evaluadas (historial)

> Decisiones ya discutidas y resueltas, para que no se vuelvan a proponer sin este contexto. Algunas quedaron en roadmap; otras (como §5.1) ya están activas — el estado de cada subsección manda sobre este encabezado.

### 5.1 ClickHouse + Airflow para capa analítica batch (activo desde 2026-08-01)

**Decisión:** ClickHouse + Airflow se incorporan como capa **separada** para analítica pesada/BI (informes tácticos compuestos del departamento de Gestión de Emergencias, ver `informestacticos/auditoria-esquemas-informes-v2.md`), **sin reemplazar a Pinot**. Patrón: Pinot sigue sirviendo lo operativo en tiempo real (despacho, casos activos, todo lo sensible a latencia); Airflow orquesta el ETL desde Kafka/Pinot hacia ClickHouse para lo que no necesita tiempo real. No es redundancia si el límite se mantiene claro: **Pinot = serving en tiempo real, ClickHouse = analítica batch/histórica.**

**Estado:** implementado como infraestructura base (`docker/docker-compose.tactico.yml`) — ver §2.1. Spec y diseño: `specs/002-tactico/infraestructura/`. Esta fase entrega solo el stack verificado (arranque, persistencia, conectividad de red); los DAGs de negocio y las tablas de ClickHouse por informe compuesto son objeto de la spec siguiente de informes tácticos compuestos de Emergencias, todavía no creada.

**Por qué ahora sí:** a diferencia de cuando se escribió esta sección originalmente (sin CU que respaldara las tablas especulativas `Fact_Reporte`/`Fact_Inteligencia`/`Fact_Satisfaccion`), la necesidad quedó trazada en `informestacticos/auditoria-esquemas-informes-v2.md` contra informes tácticos concretos del departamento de Gestión de Emergencias (ej. detección de pérdida de señal GPS, ratio demanda/capacidad por condado) — ya no es especulativo.

### 5.2 Firebase para tracking en tiempo real — evaluado y descartado

**Se evaluó** reemplazar el pipeline Kafka→Pinot por Firebase Realtime DB/Firestore específicamente para la ubicación de unidades (`Dim_HistorialUbicacionUnidadEmergencia`), ya que Firebase está diseñado para pings de geolocalización de alta frecuencia y es un servicio gestionado.

**Se descartó** porque rompe la regla vinculante de la sección 4: *"Toda escritura de datos de dominio pasa por Kafka, nunca directo a Pinot"*. Introducir Firebase solo para este dominio crearía dos fuentes de verdad para el mismo tipo de dato (ubicación de unidad) — una en Kafka/Pinot, otra en Firebase — sin necesidad real, dado que el problema de fondo (WebSocket consumiendo demasiados recursos) se resolvió de otra forma: ver 5.3.

**Si en el futuro se reconsidera:** debe ser una migración completa y documentada (sacar el tracking del modelo Pinot por completo), nunca una mezcla parcial y silenciosa de dos pipelines para el mismo dominio.

### 5.3 WebSocket → Server-Sent Events para tracking (decisión ya aplicada, ver sección 3)

El problema real detrás de la propuesta de Firebase no era Kafka/Pinot — era que Django Channels + WebSockets abre una conexión persistente **full-duplex** por cliente conectado, cuando el tracking de unidades solo necesita **servidor→cliente**. Se resolvió cambiando el mecanismo de entrega al frontend de WebSocket a SSE (ya reflejado en la tabla de stack de la sección 3), sin tocar el pipeline de datos Kafka→Pinot. Esto evita tanto el gasto de recursos de WebSocket como la fragmentación de fuentes de verdad que hubiera traído Firebase.

## 6. Proveedor de mapas (frontend)

`design-system.md` §"Mapa (referencia)" delega esta decisión a este documento. Queda registrada aquí:

**Decisión:** **Leaflet + tiles de OpenStreetMap** para cualquier mapa interactivo del frontend (selector de coordenadas en registro de accidente, futuro mapa de seguimiento de unidades). Librería `leaflet` + `@types/leaflet`, sin SDK de proveedor comercial.

**Por qué:** no requiere API key ni facturación (a diferencia de Mapbox o Google Maps), es suficiente para el caso de uso actual (un pin editable por formulario, sin necesidad de estilos de mapa personalizados todavía), y evita atar el proyecto individual a un plan de pago externo antes de que el volumen de uso lo justifique.

**Tiles oscuros:** para que el mapa respete el tema oscuro del sistema, se añadió **CartoDB Dark Matter** (`basemaps.cartocdn.com`) como proveedor de tiles alternativo cuando el tema activo es oscuro — mismo criterio que OSM (gratuito, sin API key), solo cambia el estilo visual de los tiles. Selección centralizada en `frontend/src/app/shared/ui/map/map-tile.ts` (`crearTileLayer(isDark)`), usado por los tres componentes de mapa (selector de coordenadas, mapa de solo-ruta, mapa de seguimiento), que reaccionan a cambios de tema vía un `effect()` inyectado con `ThemeService`.

**Pendiente (no bloqueante):** comportamiento de clustering de pines para vistas con múltiples unidades/accidentes (relevante cuando el volumen de unidades en el mapa de seguimiento lo justifique).

### 6.1 Ruteo por calles (OSRM)

El mapa de seguimiento traza una línea entre cada unidad de emergencia y el accidente al que fue despachada. Inicialmente esa línea era recta (2 puntos); se decidió reemplazarla por la ruta real siguiendo calles.

**Se evaluó:** Valhalla (más potente — isócronas, multi-modal — pero build de datos y configuración bastante más compleja de operar en solitario, sobre-ingeniería para "solo necesito la ruta más corta en auto"), GraphHopper (requiere JVM, que sumaría un runtime más al stack ya compuesto por Kafka+Zookeeper+Pinot+Django+Angular), y el servidor demo público de OSRM (`router.project-osrm.org`, descartado para producción: sin SLA, rate-limited, y sus términos de uso prohíben tráfico intensivo/comercial — mismo problema de fondo que evitar Mapbox, solo que gratis por ahora).

**Decisión:** **OSRM (Open Source Routing Machine) self-hosted en Docker**, imagen oficial `osrm/osrm-backend`, sirviendo un extracto `.osm.pbf` de la región operativa (por defecto Ciudad de México, vía BBBike — un extracto recortado por ciudad de ~19MB, en vez del extracto de país completo que ofrece Geofabrik para México, ~600MB — coherente con `DEFAULT_CENTER` del mapa). Ver `docker/osrm/README.md` para el proceso de build de datos (`osrm-extract` → `osrm-partition` → `osrm-customize`, ejecutado una sola vez o al cambiar de región).

**Por qué self-hosted y no un proveedor comercial:** mismo criterio que la sección 6 — sin API key, sin facturación, sin atar el proyecto individual a un plan de pago externo.

**Arquitectura de la llamada:** el frontend **no** llama a OSRM directo (a diferencia de los tiles de OSM, que sí se piden directo al navegador). OSRM corre como contenedor propio sin CORS configurado, y publicarlo directo a internet sumaría superficie de exposición sin necesidad. Django expone un endpoint proxy delgado (`GET /api/v1/seguimiento/ruta`, ver `apps/seguimiento/views/ruta_views.py` y `core/osrm/client.py`) que reenvía la petición a `OSRM_URL` (variable de entorno, por red interna del compose — el puerto de OSRM no se publica al host).

**Throttling de recálculo:** el frontend no recalcula la ruta en cada ping de posición GPS (~10s). Solo recalcula si, desde el último cálculo de esa unidad, pasaron ≥30s **y** se movió ≥~100m; mientras tanto solo reajusta visualmente el extremo de la unidad en la polyline existente, sin llamar a OSRM.

**Fallback obligatorio:** si OSRM no responde, tarda más de 3s, o no encuentra ruta, tanto el cliente OSRM del backend como el `RutaService` del frontend degradan a la línea recta original entre los dos puntos — el ruteo por calles es una mejora de visualización sobre el mapa de monitoreo, nunca una dependencia dura: un fallo del contenedor OSRM no debe afectar el resto del sistema ni bloquear la vista del operador.
