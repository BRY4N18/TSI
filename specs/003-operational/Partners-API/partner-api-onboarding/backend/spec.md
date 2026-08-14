# Especificación: Onboarding de Partners API

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.  
> **Índice del módulo:** [`../partner-api-onboarding.md`](../partner-api-onboarding.md).  
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — no duplicar aquí detalles de pantallas; RF-PON-012 define capacidad de negocio, el frontend detalla modos y CTAs.

## 1. Objetivo

Llevar a un cliente ya existente desde la decisión de integrarlo hasta que tiene acceso productivo funcionando: registrar su perfil de partner, derivar su cupo de consultas del plan que contrató, emitir sus credenciales de pruebas y de producción, y darle acceso a la documentación versionada del contrato de integración que va a consumir.

El módulo **no** mide el consumo (dueño = `api-monitoring-and-billing`), **no** revoca credenciales por incidente de seguridad ni suspende por mora (dueño = `partner-access-management`), y **no** crea clientes (dueño = `incorporacion-clientes`).

## 2. Contexto

Partners y API es la rama del recorrido de cliente por la que entra el **consumidor de datos**: un cliente que, en vez de recibir el servicio operativo de TSI, quiere consumir su información desde sus propios sistemas (SRS L106, L269). Este módulo es la puerta de entrada de esa rama y prerrequisito habilitante de los otros dos módulos del departamento: sin partner registrado con plan y credenciales, no hay consumo que medir ni acceso que revocar.

**Casos de uso incluidos:**

- **CU-O48**: Registrar el partner e iniciar su incorporación técnica. Registra la organización partner y su responsable técnico sobre un cliente existente con suscripción vigente, impide un segundo partner sobre el mismo cliente, y determina el cupo de consultas a partir del plan contratado.
- **CU-O49**: Emitir las credenciales de acceso a la integración. Emite credenciales nombradas por entorno (pruebas y producción), entrega el secreto una sola vez, permite rotación sin interrumpir las demás, y gestiona la expiración de pruebas sin desactivar al partner.
- **CU-O50**: Consultar el contrato de integración vigente y su documentación. Expone la especificación de la versión vigente, mantiene accesibles las versiones anteriores aún soportadas y señala la fecha de retiro planificada de cada una.

El módulo utiliza las tablas `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` y `Dim_VersionContratoAPI` (nueva, § 15 D1), y en solo lectura `Dim_Cliente`, `Fact_Suscripcion`, `Dim_Plan` y `Dim_Servicio`. `Dim_EstadoIntegracion`, `Fact_APIIntegracion` y `Fact_LogLlamadaAPI` pertenecen a `api-monitoring-and-billing` y este módulo no las escribe.

## Clarifications

### Session 2026-08-08 — Jerarquía de fuentes y renumeración canónica

- Q: Cuando el SRS §3.4 y `PortalPartnersAPI.md` se contradicen, ¿cuál manda? → A: **El SRS manda** en reglas de negocio; Portal aporta únicamente el mapeo INSERT/UPDATE a tablas Pinot. El SRS es posterior y resuelve explícitamente cuatro de los cinco gaps que Portal dejó marcados como 🔎 Inferido.
- Q: ¿Qué numeración de CU se usa? → A: La **canónica del catálogo** (`TSI-Catalogo-CU-RF-RNF.md` §5.5): **CU-O48–CU-O55**. La numeración de `PortalPartnersAPI.md` (CU-O71/O72/O80…) está obsoleta y colisiona con CUs **vigentes** de Emergencias (CU-O71 = abortar misión, CU-O72 = cancelar caso despachado, CU-O73 = escalar severidad). Mismo tratamiento que la renumeración de Soporte al Cliente (`decisiones-pendientes.md` #14).

  **Mapa legacy → canónico de este módulo:**

  | Legacy (Portal) | Canónico | Caso de uso |
  |---|---|---|
  | CU-O71 (registrar partner) + CU-O80 (asignar plan de acceso) | **CU-O48** | Registrar el partner e iniciar su incorporación técnica |
  | CU-O72 (solicitar y activar Sandbox y Producción) | **CU-O49** | Emitir las credenciales de acceso a la integración |
  | — (sin equivalente legacy) | **CU-O50** | Consultar el contrato de integración vigente y su documentación |

- Q: `PortalPartnersAPI.md` marca cuatro gaps 🔎 Inferido. ¿Cómo se resuelven? → A: **Todos con el SRS**, que ya los define:
  - *¿Un cliente puede tener más de un partner?* → **No.** Relación 1:1 estricta (SRS L370, RF-O48.2). Ver RN-PON-002.
  - *¿Qué ocurre al vencer el acceso de pruebas?* → **Expira la credencial, no el partner** (SRS L380, RF-O49.4). Ver RN-PON-006.
  - *¿Qué ocurre si el Administrador rechaza la promoción?* → **Motivo obligatorio, vuelve a «Pruebas activo», sin tope de reintentos** (SRS L384). Ver RN-PON-007.
  - *¿Se permite más de una credencial activa por entorno?* → **Sí, credenciales nombradas** (SRS L372, L388; RF-O49.1). Ver RN-PON-005.

### Session 2026-08-08 — Correcciones de esquema aprobadas

- Q: El SRS y RF-O49.1 exigen credenciales *nombradas*, pero `Dim_CredencialAPI` no tiene columna de nombre. → A: **Cambio aditivo aprobado** a `database/esquemas.json`: `nombre_credencial` (STRING) y `fecha_expiracion` (LONG). Mismo patrón de cambio aditivo ya aplicado a `Fact_Reclamo.idfactura` (`decisiones-pendientes.md` #14).
- Q: `Dim_Partner.sandbox_expiracion` es una sola fecha, pero pueden coexistir varias credenciales de pruebas nombradas con vencimientos distintos. → A: La expiración pasa a ser **por credencial** (`Dim_CredencialAPI.fecha_expiracion`). `Dim_Partner.sandbox_activado` / `sandbox_expiracion` se conservan como **snapshot de la primera activación**, no como fuente de verdad. Ver RN-PON-006.
- Q: `Dim_Plan.limites` (JSON, RN-SUSF-019) define `api_calls_mes` pero no un límite por minuto, y el SRS exige ambos. → A: **Aplicado 2026-08-08.** `api_calls_minuto` (INT ≥ 0) añadido al JSON, validado en `CatalogoPlanService._validate_limites`, expuesto en el formulario de plan del frontend y sembrado en los 5 planes existentes. Lo configura el **Director de Estrategia** al crear o editar el plan (CU-O26 / RF-O26.1), como corresponde a un parámetro de negocio (RNF-20) — no es una constante del código. RN-SUSF-019 actualizado en `subscriptions-and-billing`.

### Session 2026-08-08 — Alcance

- Q: CU-O50 (documentación del contrato) y CU-O51 (consumo real de datos) están en el catálogo pero no en el SRS §3.4 ni en Portal. ¿Entran? → A: **Sí, ambos.** CU-O50 se especifica en este módulo; CU-O51 en `api-monitoring-and-billing`. El departamento queda sin huecos frente al catálogo.
- Q: RF-O49.3 («rotación sin interrumpir las demás») parece solaparse con RF-O55.1 («invalidar y entregar reemplazo»). ¿Dónde vive cada uno? → A: **CU-O49 posee la emisión**: alta de credencial nueva y rotación planificada solicitada por el partner. **CU-O55 posee la invalidación**: revocación reactiva ante incidente de seguridad y cascada de suspensión. Ver § 13 Fuera de alcance.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Administrador** | Registrador y aprobador | Registra el perfil de partner sobre un cliente existente, y aprueba o rechaza la promoción a producción. Es el único que puede activar el acceso productivo. |
| **Desarrollador de APIs** | Registrador y responsable técnico | Registra partners y acompaña su incorporación técnica. Responsable del departamento (SRS L358). No aprueba promociones a producción por sí solo. |
| **Partner de integración** | Autoservicio | Activa su acceso de pruebas, emite y nombra credenciales, regenera credenciales de pruebas vencidas, solicita el paso a producción y consulta la documentación del contrato. |
| **Sistema** | Validador y notificador | Verifica la existencia del cliente, la unicidad 1:1, la vigencia de la suscripción, la ruta de estados sin atajos, y avisa antes y al producirse el vencimiento de una credencial de pruebas. |

## 4. Requisitos funcionales

### RF-PON-001: Registro del partner sobre cliente existente (CU-O48 / RF-O48.1, RF-O48.4)

El sistema debe permitir al **Administrador** o al **Desarrollador de APIs** registrar un perfil de partner sobre un cliente ya dado de alta, proporcionando:

- **Cliente:** `idcliente` (INT, FK a `Dim_Cliente`, requerido, no nulo).
- **Nombre del partner:** `nombrepartner` (STRING, requerido, razón social u organización).
- **Contacto técnico:** `contacto_tecnico_nombre` (STRING, requerido) y `contacto_tecnico_gmail` (STRING, requerido, formato de correo válido). Es el destinatario de todas las notificaciones del ciclo de vida.

Al registrar, el sistema debe:

1. Verificar que `idcliente` existe en `Dim_Cliente` y está activo. Si no existe, rechazar con HTTP 404 **antes de cualquier escritura**; el flujo correcto es dar de alta primero al cliente en `incorporacion-clientes`.
2. Verificar que el cliente tiene una **suscripción vigente** (`Fact_Suscripcion` con `estado` activo y `fecha_fin` no vencida). Sin ella, rechazar con HTTP 422 (RN-PON-011).
3. Verificar la unicidad 1:1 (RF-PON-002).
4. Insertar en `Dim_Partner` con `activo=true` y los centinelas de «sin asignar» (§ 15 D2): `planapi=""`, `limitellamadasmes=-1`, `limitellamadasminuto=-1`, `fecha_suspension=""`, `motivo_suspension=""`.
5. Insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="registro"`, `estado_anterior=""`, `estado_nuevo="Registrado"`, `ejecutado_por` = identidad del actor, `fecha_cambio=now`.

**En este punto el partner existe pero no tiene plan ni límites, y no puede emitir credenciales todavía** (SRS L374).

### RF-PON-002: Unicidad uno a uno entre cliente y partner (CU-O48 / RF-O48.2)

**Un cliente tiene un único perfil de partner.** El sistema debe rechazar con HTTP 409 el registro de un segundo partner sobre un `idcliente` que ya tiene uno, indicando el `idpartner` existente.

La restricción se aplica **a nivel de aplicación**, no de esquema: Pinot no soporta `UNIQUE` ni FK declarativos (mismo criterio ya aplicado en `Fact_Reclamo.idfactura`, `decisiones-pendientes.md` #14). El servicio consulta `Dim_Partner` por `idcliente` antes de insertar.

El motivo de la regla es el cupo: las llamadas incluidas se contratan a nivel de cliente en su suscripción, y varios perfiles obligarían a multiplicar o repartir ese cupo sin beneficio alguno (SRS L370). Cuando un cliente necesita integrar desde varios sistemas propios, la solución es **emitir varias credenciales nombradas dentro del mismo perfil** (RF-PON-005), no crear varios partners.

### RF-PON-003: Determinación del cupo desde el plan contratado (CU-O48 / RF-O48.3)

El sistema debe permitir al **Administrador** o al **Desarrollador de APIs** asignar el plan de acceso del partner. El cupo **no se elige libremente**: se deriva del plan que el cliente ya contrató.

Al asignar, el sistema debe:

1. Resolver la suscripción vigente del cliente (`Fact_Suscripcion.idplan`) y leer `Dim_Plan.limites` (JSON).
2. Extraer `api_calls_mes` y `api_calls_minuto` del JSON de límites.
3. Actualizar `Dim_Partner`: `planapi` = `Dim_Plan.nombre`, `limitellamadasmes` = `api_calls_mes`, `limitellamadasminuto` = `api_calls_minuto`. Los valores quedan **congelados** en el partner (mismo patrón que `Fact_Suscripcion.precio`), de modo que un cambio posterior del catálogo de planes no altera retroactivamente el cupo de un partner ya incorporado.
4. Insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="asignacion_plan"`, `motivo` = nombre del plan, `estado_anterior="Registrado"`, `estado_nuevo="Plan asignado"`.

**Solo a partir de aquí el partner queda habilitado para emitir credenciales** (SRS L376).

Restricciones: no se puede asignar plan a un partner con `activo=false` (HTTP 409, RN-PON-013). Si `Dim_Plan.limites` no declara `api_calls_mes` o `api_calls_minuto`, rechazar con HTTP 422 — un cupo indeterminado haría imposible la facturación de excedente de CU-O54.

### RF-PON-004: Emisión de credencial de pruebas por autoservicio (CU-O49 / RF-O49.1, RF-O49.2)

El **Partner de integración** debe poder activar su acceso de pruebas por autoservicio, sin aprobación de nadie.

**Precondición:** `Dim_Partner.planapi <> ''` (ya pasó por RF-PON-003). **La guarda se expresa contra el centinela, no contra `NULL`**: Pinot no almacena nulos y un `planapi` sin asignar vale `""` (§ 15 D2). Si intenta activarlo sin plan asignado, la solicitud se rechaza con HTTP 409 **sin efecto alguno** y el partner permanece en «Registrado» (SRS L378).

Al emitir, el sistema debe:

1. Generar un secreto criptográficamente aleatorio y persistir **únicamente su hash** en `Dim_CredencialAPI.client_secret_hash`.
2. Insertar en `Dim_CredencialAPI`: `idpartner`, `idcliente`, `nombre_credencial`, `entorno="Sandbox"`, `activo=true`, `fecha_creacion=now`, `fecha_expiracion` = `now` + período de vigencia configurado.
3. **Entregar el secreto en claro una sola vez**, en el cuerpo de la respuesta de creación. No existe ningún endpoint que lo recupere después (RN-PON-005).
4. Actualizar `Dim_Partner.sandbox_activado` / `sandbox_expiracion` **solo en la primera activación** (snapshot histórico, no fuente de verdad).
5. Insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="activacion_sandbox"`, `idcredencial` = la recién creada, `estado_anterior="Plan asignado"`, `estado_nuevo="Pruebas activo"`.

### RF-PON-005: Credenciales nombradas y múltiples por entorno (CU-O49 / RF-O49.1, RF-O49.3)

Dentro de cada entorno puede haber **varias credenciales activas simultáneamente, cada una con un nombre que identifica al sistema que la usa** (SRS L372, L388). Ejemplo: una aseguradora que conecta su plataforma de siniestros y la de detección de fraude recibe una credencial por sistema.

El sistema debe:

1. Aceptar `nombre_credencial` (STRING, requerido, no vacío) en toda emisión.
2. Rechazar con HTTP 409 un `nombre_credencial` que ya exista **activo** para el mismo `idpartner` y `entorno`. Un nombre liberado por revocación o expiración puede reutilizarse.
3. Permitir la **rotación planificada** solicitada por el partner: emite una credencial nueva con el mismo nombre lógico y el partner desactiva la anterior cuando su sistema ya migró. La emisión nunca interrumpe las demás credenciales del partner.
4. No imponer tope al número de credenciales activas por entorno (RN-PON-014).

Todo el consumo de todas las credenciales se agrega contra el **único cupo contratado** del partner — el reparto es responsabilidad de `api-monitoring-and-billing`.

### RF-PON-006: Expiración de credencial de pruebas y regeneración por autoservicio (CU-O49 / RF-O49.4)

**Si el acceso de pruebas vence sin que el partner haya solicitado producción, expira la credencial, no el partner** (SRS L380).

El sistema debe:

1. Avisar al contacto técnico **antes del vencimiento** y **de nuevo al producirse**, sin duplicar el mismo aviso dentro del mismo ciclo de vigencia. El aviso es un **envío a una persona**, no una entrada en la bitácora: `Fact_HistorialAccesoPartner` sirve para deduplicarlo (punto 3), no lo sustituye. Se implementó una vez escribiendo solo la bitácora y el partner descubría el vencimiento cuando su integración fallaba. El envío es **fail-open y aislado**: un buzón caído no puede dejar operativa una credencial vencida, que es un control de seguridad.
2. Al vencer, marcar únicamente esa credencial `activo=false`. `Dim_Partner.activo` **no se toca** y el plan asignado se conserva.
3. Insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="expiracion_sandbox"`, `idcredencial` = la vencida, `ejecutado_por="Sistema"`.
4. Permitir al partner **generar una credencial de pruebas nueva por autoservicio**, sin repetir el registro (RF-PON-001) ni la asignación de plan (RF-PON-003).

La regla de fondo: demorar la integración no debe obligar a empezar de cero.

### RF-PON-007: Solicitud de promoción a producción (CU-O49)

Cuando ha validado su integración, el **Partner de integración** debe poder solicitar el paso a producción.

**Precondición:** el partner debe estar en estado «Pruebas activo», es decir, tener o haber tenido al menos una credencial de pruebas emitida. **No se puede solicitar producción sin haber pasado por el entorno de pruebas** (SRS L386). En cualquier otro estado, rechazar con HTTP 409.

Al solicitar, el sistema debe insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="solicitud_promocion_produccion"`, `ejecutado_por="Partner"`, `estado_anterior="Pruebas activo"`, `estado_nuevo="Pendiente de aprobación"`, y notificar a los Administradores.

**La solicitud no emite ninguna credencial de producción.** La activación efectiva la ejecuta un Administrador (RF-PON-008).

### RF-PON-008: Aprobación o rechazo de la promoción (CU-O49)

Es un proceso **deliberadamente semiautomático: el partner pide, una persona aprueba** (SRS L382). Solo el **Administrador** puede resolverlo.

**Al aprobar**, el sistema debe:

1. Emitir la credencial de producción: insertar en `Dim_CredencialAPI` con `entorno="Producción"`, `nombre_credencial`, `client_secret_hash` nuevo, `activo=true`, `fecha_expiracion=253402300799000` (centinela «no expira nunca», § 15 D2 — deliberadamente en el futuro para que ningún job de expiración la alcance). El secreto se entrega una sola vez (RN-PON-005).
2. Insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="activacion_produccion"`, `ejecutado_por="Administrador"`, `estado_anterior="Pendiente de aprobación"`, `estado_nuevo="Producción activa"`.
3. **No eliminar la credencial de pruebas** (RF-PON-009).

**Al rechazar**, el sistema debe:

1. Exigir un **motivo obligatorio** (STRING, no vacío) y notificarlo al contacto técnico del partner.
2. Devolver el partner a **«Pruebas activo», no a «Registrado»**: su acceso de pruebas sigue funcionando, porque es precisamente donde debe corregir lo que motivó el rechazo (SRS L384).
3. Insertar en `Fact_HistorialAccesoPartner` con `tipo_cambio="rechazo_promocion_produccion"`, `motivo` = el motivo indicado, `estado_anterior="Pendiente de aprobación"`, `estado_nuevo="Pruebas activo"`.

El partner puede volver a solicitar producción cuantas veces necesite. **No existe un tope de reintentos**, y cada solicitud y cada rechazo quedan en la bitácora (RN-PON-007).

### RF-PON-009: Coexistencia de entornos (CU-O49)

Las credenciales de pruebas y de producción **coexisten**: activar producción no elimina ni desactiva el acceso de pruebas, porque el partner sigue necesitándolo para probar cambios futuros (SRS L388).

El sistema debe mantener ambos conjuntos de credenciales con ciclos de vida independientes, y toda operación de emisión, rotación o consulta debe estar siempre calificada por `entorno`.

### RF-PON-010: Bitácora inmutable del ciclo de vida (RNF-01, RNF-16)

Todo evento relevante del ciclo de vida del partner debe insertar una fila nueva en `Fact_HistorialAccesoPartner`. **La tabla nunca se actualiza ni se borra: solo admite INSERT** (RN-PON-010).

`idcredencial` se llena cuando el evento afecta a una credencial puntual (emisión, expiración) y vale el centinela **`-1`** cuando el evento es sobre el partner en general (registro, asignación de plan, solicitud, aprobación, rechazo). Pinot no almacena nulos (§ 15 D2).

Valores de `tipo_cambio` que este módulo escribe: `registro`, `asignacion_plan`, `activacion_sandbox`, `expiracion_sandbox`, `solicitud_promocion_produccion`, `activacion_produccion`, `rechazo_promocion_produccion`.

### RF-PON-011: Consulta del contrato de integración vigente y su documentación (CU-O50 / RF-O50.1, RF-O50.2, RF-O50.3)

El **Partner de integración** debe poder consultar, por autoservicio, la especificación del contrato de integración que va a consumir:

1. **Versión vigente:** la especificación completa de la versión actualmente en producción, en formato legible por máquina (OpenAPI) y navegable por humanos.
2. **Versiones anteriores aún soportadas:** accesibles mientras no hayan sido retiradas, para que un partner que aún no migró pueda seguir trabajando contra su versión.
3. **Fecha de retiro planificada:** cada versión declara su estado (`vigente` | `soportada` | `retirada`) y, cuando aplica, la fecha en que dejará de atenderse.

Ninguna versión puede pasar a `retirada` sin que su fecha de retiro haya sido publicada previamente (RN-PON-012, RNF-06).

**Persistencia.** El catálogo vive en la tabla nueva `Dim_VersionContratoAPI`, **con FK obligatoria a `Dim_Servicio`** (§ 15 D1). Las versiones son **por servicio**, no globales: `Dim_Servicio` contiene hoy tres entradas distintas (*API Despacho*, *API Registro de accidentes*, *Portal Cliente*), cada una con su propio ciclo de versionado.

El sistema debe:

4. Exigir que la tupla (`id_servicio`, `version`) sea única entre las filas con `activo=true`, validada a nivel de aplicación (Pinot no soporta `UNIQUE`; mismo criterio que RN-PON-002).
5. Garantizar que exista **como máximo una versión en estado `vigente` por servicio**. Publicar una nueva versión vigente pasa la anterior a `soportada` en la misma operación.
6. Rechazar el paso a `retirada` si `fecha_retiro` es nula o futura (RN-PON-012).

### RF-PON-012: Consulta del estado de incorporación (CU-O48, CU-O49)

El sistema debe exponer el estado de incorporación del partner, con alcance según el actor:

- **Partner de integración:** solo su propio perfil — estado actual, plan y cupo asignados, credenciales activas por entorno (con `nombre_credencial`, `fecha_creacion` y `fecha_expiracion`; **nunca el secreto**) y su bitácora.
- **Administrador / Desarrollador de APIs:** listado de todos los partners, filtrable por estado, plan y entorno, y con la cola de solicitudes **pendientes de aprobación** como vista de trabajo prioritaria.

El detalle de pantallas, filtros y CTAs es responsabilidad de [`../frontend/spec.md`](../frontend/spec.md).

## 5. Requisitos no funcionales

### RNF-PON-001: Compromiso de aprovisionamiento (RNF-01)

La emisión de una credencial de pruebas debe completarse en **menos de veinticuatro horas** desde la solicitud (SRS L378). Al ser autoservicio, el objetivo operativo real es que sea inmediata: **p95 ≤ 2 segundos**.

### RNF-PON-002: Confidencialidad de credenciales (RNF-13, Principio V)

El secreto de una credencial **nunca se persiste en claro** ni se escribe en logs, trazas, mensajes de error o eventos Kafka. Solo se almacena su hash con función de derivación resistente a fuerza bruta. Se transmite exactamente una vez, en la respuesta de creación, sobre canal cifrado. **100 % de las credenciales almacenadas en forma de hash** es criterio verificable.

### RNF-PON-003: Autenticidad y revocabilidad (RNF-15)

Toda credencial emitida está asociada a una identidad válida y vigente (`Dim_Partner` → `Dim_Cliente`) y es revocable en cualquier momento. Una credencial cuyo partner no tiene suscripción vigente no puede emitirse.

### RNF-PON-004: Bitácora inmutable (RNF-16, Principio V)

El 100 % de las acciones de este módulo queda registrado en `Fact_HistorialAccesoPartner` con autor, acción, motivo y fecha. La bitácora no admite UPDATE ni DELETE.

### RNF-PON-005: Contrato versionado sin rupturas no anunciadas (RNF-06, Principio VI)

Ningún cambio incompatible se publica sin anuncio previo y sin fecha de retiro declarada para la versión saliente. El contrato se versiona por path (`/api/v1/`, `/api/v2/`), conforme a `api-standards.md`.

### RNF-PON-006: Modularidad del módulo (RNF-17, Principio VII)

El módulo evoluciona sin acoplamiento directo con `api-monitoring-and-billing` ni `partner-access-management`: la única superficie compartida son las tablas `Dim_Partner` y `Dim_CredencialAPI`, con propiedad de escritura claramente repartida (§ 13).

### RNF-PON-007: Testabilidad (RNF-18)

Cobertura de pruebas automatizadas ≥ 80 %. Este módulo **no pertenece a la cadena crítica de despacho**, por lo que no le aplica el umbral reforzado del 95 %.

## 5.1 Declaración ISO/IEC 25010:2023 (Golden Rule de la constitución)

| Característica | Aplica | Justificación |
|---|---|---|
| **Functional Suitability** | ✅ | Trazable a CU-O48/O49/O50 del catálogo canónico y a SRS §3.4.1. Sin partner incorporado no existe la línea de ingresos por consumo de datos. |
| **Reliability** | ✅ | RF-PON-006 (expiración) y RF-PON-008 (rechazo) definen el comportamiento ante el camino no feliz sin pérdida de estado. |
| **Performance Efficiency** | ✅ | RNF-PON-001 declara umbral temporal explícito. |
| **Interaction Capability** | ⚠️ Parcial | Alcance del backend limitado a RF-PON-012 (capacidad de consulta). El detalle de operabilidad vive en `../frontend/spec.md`. |
| **Security** | ✅ | **Característica dominante.** RNF-PON-002/003/004 cubren confidencialidad, autenticidad, no repudio y responsabilidad. Principio V exige tratarlas antes de `/plan`. |
| **Compatibility** | ✅ | CU-O50 y RNF-PON-005 materializan directamente el Principio VI (API-First). |
| **Maintainability** | ✅ | RNF-PON-006/007. Reparto de propiedad de escritura documentado en § 13. |
| **Flexibility** | ✅ | El cupo se deriva de `Dim_Plan.limites` (configurable, RNF-20), no de constantes en código. |
| **Safety** | ❌ **No aplica** | Este módulo no participa en la cadena crítica registro → asignación → despacho → confirmación. Un partner sin incorporar no retrasa la atención de ninguna víctima. Ningún flujo de este módulo influye en la clasificación de severidad ni en la asignación de unidades. |

**Tie-breaker:** existe un conflicto real entre **Security** e **Interaction Capability** en RN-PON-005 (el secreto se entrega una sola vez y es irrecuperable, lo que obliga al partner a rotar si lo pierde). Se prioriza **Security** por la excepción de dominio del Tie-Breaker Mechanism (regla 3: datos sensibles en tránsito). Trade-off aceptado: un partner que pierde su secreto debe emitir una credencial nueva; el coste es bajo porque RF-PON-005 hace la rotación no disruptiva.

## 6. Reglas de negocio

### RN-PON-001

Todo partner es primero un cliente dado de alta en Cuentas y Clientes. **Un partner sin cliente detrás no puede existir**: `Dim_Partner.idcliente` es obligatorio y no nulo, y el registro se rechaza si el cliente no está dado de alta. Este módulo no crea clientes: habilita a los existentes (SRS L360, L368).

### RN-PON-002

**Un cliente tiene un único perfil de partner.** La relación es uno a uno y el sistema rechaza el registro de un segundo partner sobre un cliente que ya lo tiene (SRS L370, RF-O48.2). Aplicada a nivel de aplicación, no como constraint de esquema.

### RN-PON-003

El cupo de consultas **se deriva del plan contratado por el cliente**, no se elige libremente (RF-O48.3). Los límites mensual y por minuto se leen de `Dim_Plan.limites` y se **congelan** en `Dim_Partner` al asignarse, de modo que un cambio posterior del catálogo de planes no altera retroactivamente a un partner ya incorporado.

### RN-PON-004

**Ruta obligatoria, sin atajos:** `Registrado → Plan asignado → Pruebas activo → Pendiente de aprobación → Producción activa`. No se puede solicitar producción sin haber pasado por el entorno de pruebas (SRS L386). Todo intento de salto retorna HTTP 409.

### RN-PON-005

El secreto de una credencial **se entrega una sola vez, sin posibilidad de recuperarlo después** (RF-O49.2). No existe endpoint de recuperación. Si el partner lo pierde, la vía es emitir una credencial nueva (RF-PON-005) o revocar y reemplazar (CU-O55, módulo `partner-access-management`).

### RN-PON-006

**Si el acceso de pruebas vence, expira la credencial, no el partner** (SRS L380). La credencial queda inactiva, pero el partner permanece registrado y con su plan asignado, y puede generar una credencial de pruebas nueva por autoservicio. La vigencia es **por credencial** (`Dim_CredencialAPI.fecha_expiracion`); `Dim_Partner.sandbox_expiracion` es solo snapshot de la primera activación.

### RN-PON-007

**Si el Administrador rechaza la promoción a producción**, debe indicar un motivo obligatorio, que se notifica al contacto técnico. El partner vuelve al estado **«Pruebas activo», no al de recién registrado**, y su acceso de pruebas sigue funcionando. Puede volver a solicitar producción cuantas veces necesite: **no existe un tope de reintentos**, y cada solicitud y cada rechazo quedan registrados en su bitácora (SRS L384).

### RN-PON-008

Las credenciales de pruebas y de producción **coexisten**. Activar producción no elimina el acceso de pruebas (SRS L388).

### RN-PON-009

**Fuente de verdad única.** El estado operativo del partner reside únicamente en `Dim_Partner.activo` (SRS L442). `fecha_suspension` y `motivo_suspension` son un resumen del último evento, no un historial paralelo que pueda contradecirlo.

### RN-PON-010

`Fact_HistorialAccesoPartner` es una **bitácora inmutable**: solo INSERT, nunca UPDATE ni DELETE. Cada evento es una fila nueva con `fecha_cambio` creciente.

### RN-PON-011

**Sin suscripción vigente no hay incorporación** (RF-O48.4). El registro se rechaza si el cliente no tiene una suscripción activa y no vencida, porque el cupo del partner se deriva precisamente de esa suscripción (RN-PON-003).

### RN-PON-012

El contrato de integración está **versionado** y no introduce cambios incompatibles sin anuncio previo (RNF-06, RF-O50.3). Ninguna versión pasa a `retirada` sin fecha de retiro publicada con antelación.

### RN-PON-013

Ninguna acción de habilitación (asignación de plan, emisión de credencial, solicitud o aprobación de promoción) procede sobre un partner con `Dim_Partner.activo=false`. Todas retornan HTTP 409. La reactivación es competencia de CU-O55 (`partner-access-management`).

### RN-PON-014

No existe tope al número de credenciales activas por entorno. La unicidad se exige sobre la tupla (`idpartner`, `entorno`, `nombre_credencial`) **entre las activas**; un nombre liberado por revocación o expiración puede reutilizarse.

## 7. Entradas

### Para registrar partner (CU-O48 / RF-PON-001)
- `idcliente` (INT, requerido, FK a `Dim_Cliente`).
- `nombrepartner` (STRING, requerido, no vacío).
- `contacto_tecnico_nombre` (STRING, requerido, no vacío).
- `contacto_tecnico_gmail` (STRING, requerido, formato de correo válido).

### Para asignar plan de acceso (CU-O48 / RF-PON-003)
- `idpartner` (INT, requerido, path param).
- Sin cuerpo de cupo: los límites se derivan de la suscripción vigente del cliente. Un cupo enviado explícitamente se ignora (RN-PON-003).

### Para emitir credencial (CU-O49 / RF-PON-004, RF-PON-005)
- `idpartner` (INT, requerido, path param).
- `nombre_credencial` (STRING, requerido, no vacío, identifica el sistema que la usará).
- `entorno` (STRING, requerido, `Sandbox` | `Producción`). El partner solo puede emitir en `Sandbox`; `Producción` es exclusivo del Administrador vía RF-PON-008.

### Para solicitar promoción a producción (CU-O49 / RF-PON-007)
- `idpartner` (INT, requerido, path param).
- `nombre_credencial` (STRING, requerido, nombre de la credencial de producción que se emitirá al aprobarse).

### Para resolver la promoción (CU-O49 / RF-PON-008)
- `idpartner` (INT, requerido, path param).
- `decision` (STRING, requerido, `aprobar` | `rechazar`).
- `motivo` (STRING, **obligatorio y no vacío si `decision="rechazar"`**; ignorado si se aprueba).

### Para consultar el contrato de integración (CU-O50 / RF-PON-011)
- `version` (STRING, opcional; si se omite, devuelve la versión vigente).

## 8. Salidas

### Respuestas exitosas
- **201 Created — Partner registrado:** `{ "data": { "idpartner": 12, "idcliente": 340, "nombrepartner": "...", "estado": "Registrado", "planapi": null } }`
- **200 OK — Plan asignado:** `{ "data": { "idpartner": 12, "estado": "Plan asignado", "planapi": "Empresarial", "limitellamadasmes": 500000, "limitellamadasminuto": 600 } }`
- **201 Created — Credencial emitida:** `{ "data": { "idcredencial": 88, "nombre_credencial": "plataforma-siniestros", "entorno": "Sandbox", "client_id": "...", "client_secret": "<única vez>", "fecha_expiracion": 1767225600000, "estado": "Pruebas activo" } }` — `client_secret` aparece **solo en esta respuesta** (RN-PON-005).
- **202 Accepted — Promoción solicitada:** `{ "data": { "idpartner": 12, "estado": "Pendiente de aprobación" } }` — 202 porque la activación efectiva requiere intervención humana (RF-PON-008).
- **200 OK — Promoción aprobada:** `{ "data": { "idpartner": 12, "estado": "Producción activa", "credencial": { "idcredencial": 91, "entorno": "Producción", "client_secret": "<única vez>" } } }`
- **200 OK — Promoción rechazada:** `{ "data": { "idpartner": 12, "estado": "Pruebas activo", "motivo": "..." } }`
- **200 OK — Detalle del partner:** `{ "data": { "idpartner": 12, "estado": "Producción activa", "planapi": "...", "limitellamadasmes": ..., "credenciales": [...], "historial": [...] } }` — las credenciales **nunca** incluyen el secreto.
- **200 OK — Listado de partners:** `{ "data": [...], "meta": { "pagination": { "cursor": "...", "limit": 20 } } }` — paginación por cursor, conforme a `api-standards.md`.
- **200 OK — Contrato de integración:** `{ "data": { "version": "v1", "estado": "vigente", "fecha_retiro": null, "spec_url": "...", "versiones": [ { "version": "v1", "estado": "vigente", "fecha_retiro": null } ] } }`

### Respuestas de error
- **400 Bad Request** — Campos obligatorios faltantes, `contacto_tecnico_gmail` con formato inválido o `nombre_credencial` vacío.
- **401 Unauthorized** — Token no proporcionado, inválido o expirado.
- **403 Forbidden** — Actor sin el rol requerido: registro y asignación de plan exigen Administrador o Desarrollador de APIs; la resolución de promoción exige Administrador; la emisión en `Sandbox` y la solicitud de promoción exigen ser el propio partner.
- **404 Not Found** — `idcliente` inexistente en `Dim_Cliente` (RF-PON-001 punto 1), o `idpartner` inexistente, o `version` de contrato inexistente.
- **409 Conflict** — Ya existe un partner para ese `idcliente`; incluye el `idpartner` existente (RN-PON-002).
- **409 Conflict** — Emisión de credencial sin plan asignado (`planapi = ''`, RF-PON-004).
- **409 Conflict** — `nombre_credencial` duplicado entre las credenciales activas del mismo partner y entorno (RN-PON-014).
- **409 Conflict** — Solicitud de promoción desde un estado distinto de «Pruebas activo» (RN-PON-004).
- **409 Conflict** — Resolución de promoción sobre un partner que no está en «Pendiente de aprobación».
- **409 Conflict** — Cualquier acción de habilitación sobre un partner con `activo=false` (RN-PON-013).
- **422 Unprocessable Entity** — Cliente sin suscripción vigente (RN-PON-011).
- **422 Unprocessable Entity** — `Dim_Plan.limites` sin `api_calls_mes` o `api_calls_minuto` (RF-PON-003).
- **422 Unprocessable Entity** — Rechazo de promoción sin `motivo` no vacío (RN-PON-007).

Formato de error conforme a `api-standards.md`: `{ "error": "conflict", "detail": "...", "code": "PARTNER_YA_EXISTE" }`.

## 9. Estados posibles

### Estados del partner

| Estado | Origen | Significado |
|---|---|---|
| **Registrado** | RF-PON-001 | El perfil existe. Sin plan ni límites; no puede emitir credenciales. |
| **Plan asignado** | RF-PON-003 | Cupo derivado del plan y congelado. Habilitado para emitir credenciales de pruebas. |
| **Pruebas activo** | RF-PON-004, RF-PON-008 (rechazo) | Tiene credenciales de pruebas. Puede solicitar producción. |
| **Pendiente de aprobación** | RF-PON-007 | Solicitud enviada; espera resolución humana. Su acceso de pruebas sigue operando. |
| **Producción activa** | RF-PON-008 (aprobación) | Credencial de producción emitida. Las de pruebas coexisten (RN-PON-008). |
| **Suspendido** | CU-O55 (`partner-access-management`) | `Dim_Partner.activo=false`. **Estado ajeno a este módulo**: se documenta solo porque ningún flujo de aquí procede sobre él (RN-PON-013). |

El estado no es una columna: se deriva de `Dim_Partner` (`activo`, `planapi`) y del último evento de `Fact_HistorialAccesoPartner`, siendo `Dim_Partner.activo` la fuente de verdad del eje activo/suspendido (RN-PON-009).

### Transiciones

```
Registrado ──RF-PON-003──► Plan asignado ──RF-PON-004──► Pruebas activo
                                                              │  ▲
                                                RF-PON-007────┘  │
                                                              ▼  │
                                                Pendiente de aprobación
                                                     │            │
                                    RF-PON-008 aprobar│            │RF-PON-008 rechazar
                                                     ▼            │  (motivo obligatorio,
                                              Producción activa ──┘   sin tope de reintentos)

Cualquier estado ──CU-O55 (otro módulo)──► Suspendido ──CU-O55──► estado previo
```

La expiración de una credencial de pruebas (RF-PON-006) **no** es una transición de estado del partner: desactiva la credencial y deja al partner en «Plan asignado» efectivo, desde donde puede volver a emitir.

## 10. Escenarios

### Escenario 1: Registro exitoso del partner

Dado que existe un cliente activo con suscripción vigente  
Y el Administrador ha iniciado sesión  
Cuando registra el partner indicando `nombrepartner` y su contacto técnico  
Entonces el sistema debe verificar la existencia del cliente, su suscripción vigente y la unicidad 1:1  
Y debe insertar la fila en `Dim_Partner` con `activo=true` y `planapi=""` (centinela de «sin plan»)  
Y debe insertar `tipo_cambio="registro"` en `Fact_HistorialAccesoPartner`  
Y debe retornar HTTP 201 con el `idpartner` y estado "Registrado".

### Escenario 2: Segundo partner sobre el mismo cliente

Dado que el cliente 340 ya tiene el partner 12  
Cuando el Desarrollador de APIs intenta registrar un segundo partner sobre el cliente 340  
Entonces el sistema debe rechazar con HTTP 409 **sin escribir nada**  
Y debe indicar en la respuesta el `idpartner` existente  
Y debe sugerir emitir una credencial nombrada adicional dentro del perfil existente (RF-PON-005).

### Escenario 3: Registro sobre cliente sin suscripción vigente

Dado que existe un cliente cuya suscripción está cancelada o vencida  
Cuando el Administrador intenta registrarlo como partner  
Entonces el sistema debe rechazar con HTTP 422  
Y debe explicar que el cupo del partner se deriva de una suscripción vigente (RN-PON-011).

### Escenario 4: Emisión de credencial de pruebas sin plan asignado

Dado que un partner está en estado "Registrado"  
Cuando intenta emitir una credencial de pruebas por autoservicio  
Entonces el sistema debe rechazar con HTTP 409 **sin efecto alguno**  
Y el partner debe permanecer en "Registrado" hasta que un Administrador le asigne plan.

### Escenario 5: Varias credenciales nombradas dentro del mismo perfil

Dado que una aseguradora es partner y necesita integrar su plataforma de siniestros y la de detección de fraude  
Cuando emite una credencial `plataforma-siniestros` y otra `deteccion-fraude` en el mismo entorno  
Entonces el sistema debe crear dos filas en `Dim_CredencialAPI` con el mismo `idpartner` y `entorno`  
Y cada secreto debe entregarse una sola vez, en su respuesta de creación  
Y ambas deben consumir contra el único cupo contratado del partner.

### Escenario 6: Vence el acceso de pruebas sin solicitud de producción

Dado que un partner tiene una credencial de pruebas próxima a vencer  
Cuando se alcanza el momento de aviso previo  
Entonces el sistema debe notificar al contacto técnico sin duplicar el aviso dentro del mismo ciclo  
Y al producirse el vencimiento debe marcar solo esa credencial `activo=false`, notificar de nuevo e insertar `tipo_cambio="expiracion_sandbox"`  
Y `Dim_Partner.activo` debe permanecer `true` con su plan intacto  
Y el partner debe poder generar una credencial de pruebas nueva por autoservicio sin repetir registro ni asignación de plan.

### Escenario 7: Promoción a producción aprobada

Dado que un partner en "Pruebas activo" ha validado su integración  
Cuando solicita el paso a producción  
Entonces el sistema debe registrar `tipo_cambio="solicitud_promocion_produccion"`, dejar el partner en "Pendiente de aprobación" y retornar HTTP 202  
Y cuando un Administrador aprueba la solicitud  
Entonces el sistema debe emitir la credencial de producción entregando su secreto una sola vez  
Y debe conservar activa la credencial de pruebas (RN-PON-008)  
Y debe retornar HTTP 200 con estado "Producción activa".

### Escenario 8: Promoción a producción rechazada

Dado que un partner está en "Pendiente de aprobación"  
Cuando el Administrador rechaza la promoción indicando el motivo obligatorio  
Entonces el sistema debe notificar el motivo al contacto técnico  
Y debe devolver el partner a **"Pruebas activo"**, no a "Registrado"  
Y su credencial de pruebas debe seguir operativa  
Y debe insertar `tipo_cambio="rechazo_promocion_produccion"` con el motivo  
Y el partner debe poder volver a solicitar producción sin límite de reintentos.

Dado que el Administrador intenta rechazar sin indicar motivo  
Cuando envía la resolución  
Entonces el sistema debe rechazar con HTTP 422.

### Escenario 9: Intento de atajo a producción

Dado que un partner está en estado "Plan asignado" y nunca emitió una credencial de pruebas  
Cuando intenta solicitar el paso a producción  
Entonces el sistema debe rechazar con HTTP 409  
Y debe indicar que la ruta obligatoria exige pasar por el entorno de pruebas (RN-PON-004).

### Escenario 10: Consulta del contrato de integración

Dado que un partner está integrando contra la versión vigente  
Cuando consulta la documentación del contrato  
Entonces el sistema debe devolver la especificación de la versión vigente  
Y debe listar las versiones anteriores aún soportadas con su estado  
Y debe señalar la fecha de retiro planificada de cada versión que la tenga  
Y ninguna versión debe figurar como retirada sin que su fecha se hubiera publicado antes.

## 11. Criterios de aceptación

### CA-PON-001 (CU-O48)
El Administrador o el Desarrollador de APIs puede registrar un partner sobre un cliente existente con suscripción vigente. El sistema inserta en `Dim_Partner` con `planapi=""` y registra `tipo_cambio="registro"` en la bitácora. Un `idcliente` inexistente retorna HTTP 404 sin escribir nada.

### CA-PON-002 (CU-O48 / RF-O48.2)
El intento de registrar un segundo partner sobre un cliente que ya lo tiene retorna HTTP 409 e indica el `idpartner` existente. No se escribe ninguna fila.

### CA-PON-003 (CU-O48 / RF-O48.4)
El registro sobre un cliente sin suscripción vigente retorna HTTP 422.

### CA-PON-004 (CU-O48 / RF-O48.3)
Al asignar el plan, `limitellamadasmes` y `limitellamadasminuto` se leen de `Dim_Plan.limites` de la suscripción vigente y quedan congelados en `Dim_Partner`. Un cambio posterior en `Dim_Plan` no altera los valores del partner ya incorporado. Un `limites` sin `api_calls_mes` o `api_calls_minuto` retorna HTTP 422.

### CA-PON-005 (CU-O49 / RF-O49.2)
El secreto se entrega exactamente una vez, en la respuesta de creación. Ninguna consulta posterior de credenciales lo devuelve, y no existe endpoint de recuperación. En base de datos solo consta su hash.

### CA-PON-006 (CU-O49 / RF-O49.1)
Un partner puede tener varias credenciales activas simultáneas en el mismo entorno, cada una con `nombre_credencial` distinto. Un nombre duplicado entre las activas del mismo entorno retorna HTTP 409; un nombre liberado por revocación o expiración puede reutilizarse.

### CA-PON-007 (CU-O49)
La emisión de credencial de pruebas sobre un partner sin plan asignado retorna HTTP 409 sin ningún efecto, y el partner permanece en "Registrado".

### CA-PON-008 (CU-O49 / RF-O49.4)
Al vencer una credencial de pruebas, solo esa credencial pasa a `activo=false`. `Dim_Partner.activo` sigue en `true` y `planapi` se conserva. El partner genera una credencial nueva por autoservicio sin repetir registro ni asignación de plan. El sistema avisó antes del vencimiento y al producirse, sin duplicar el aviso en el mismo ciclo.

### CA-PON-009 (CU-O49)
La solicitud de promoción desde un estado distinto de "Pruebas activo" retorna HTTP 409. Desde "Pruebas activo" retorna HTTP 202 y deja al partner en "Pendiente de aprobación" sin emitir credencial de producción.

### CA-PON-010 (CU-O49)
Solo un Administrador puede resolver la promoción; otros roles reciben HTTP 403. Al aprobar, el partner queda habilitado para producción y la de pruebas permanece activa (RN-PON-008); la credencial productiva **no se emite en la aprobación**, la emite el propio partner desde su portal (BE-DELTA-02) porque el secreto solo puede verlo quien lo custodia (RN-PON-005) — devolverlo aquí obligaría al Administrador a transmitírselo por un canal inseguro. Al rechazar se exige motivo no vacío (HTTP 422 si falta), el partner vuelve a "Pruebas activo" con su acceso de pruebas operativo, y puede reintentar sin tope.

### CA-PON-011 (RNF-16)
Cada uno de los siete eventos del ciclo de vida inserta exactamente una fila en `Fact_HistorialAccesoPartner` con autor, motivo y fecha. Ninguna operación del módulo ejecuta UPDATE ni DELETE sobre esa tabla.

### CA-PON-012 (RN-PON-013)
Toda acción de habilitación sobre un partner con `activo=false` retorna HTTP 409.

### CA-PON-013 (CU-O50 / RF-O50.1–3)
La consulta del contrato devuelve, **por servicio**, la especificación de la versión vigente, lista las versiones anteriores aún soportadas y señala la fecha de retiro de cada una. Ninguna versión figura como retirada sin fecha de retiro previamente publicada. Dos servicios distintos pueden estar en versiones vigentes distintas sin interferir entre sí, y ningún servicio tiene más de una versión `vigente` a la vez.

### CA-PON-014 (RNF-PON-001)
La emisión de una credencial de pruebas por autoservicio se completa en p95 ≤ 2 segundos, muy por debajo del compromiso de 24 horas del SRS.

## 12. Dependencias

- **`autenticacion-y-rbac`:** requiere JWT y los roles `Administrador` (idrol 2), `DesarrolladorAPIs` (idrol 5) y `PartnerIntegracion` (**idrol 15, creado 2026-08-08**). Ver la nota del catálogo de roles en su `spec.md` sobre por qué el partner no reutiliza el rol `Cliente`.
- **`incorporacion-clientes`:** provee `Dim_Cliente`. Este módulo solo lee; nunca crea clientes (RN-PON-001).
- **`subscriptions-and-billing`:** provee `Fact_Suscripcion` y `Dim_Plan`. De ahí se derivan la vigencia (RN-PON-011) y el cupo (RN-PON-003). **Requiere la extensión `api_calls_minuto` en RN-SUSF-019.**
- **`Dim_Servicio`** (catálogo transversal, sembrado por `backend/scripts/seed_catalogos_soporte.py`): `Dim_VersionContratoAPI.id_servicio` lo referencia (§ 15 D1). Este módulo solo lee el catálogo; no da de alta servicios.
- Es requerido por:
  - **`api-monitoring-and-billing` (#08):** necesita partners con credenciales de producción activas para tener consumo que medir, limitar y tarificar.
  - **`partner-access-management` (#09):** necesita credenciales emitidas para poder revocarlas y partners incorporados para poder suspenderlos.

## 13. Fuera de alcance

- **Medición del consumo, límites y alertas de cuota:** dueño = `api-monitoring-and-billing` (CU-O51, CU-O52, CU-O53). Este módulo no escribe `Fact_APIIntegracion`, `Fact_LogLlamadaAPI` ni `Dim_EstadoIntegracion`.
- **Tarificación y facturación de excedente:** dueño = `api-monitoring-and-billing` (CU-O54). La emisión de la factura ocurre en `subscriptions-and-billing`.
- **Revocación de credencial por incidente de seguridad:** dueño = `partner-access-management` (CU-O55 / RF-O55.1). Este módulo **emite y rota**; aquel **invalida**.
- **Avisos de mora, suspensión automática o manual, y reactivación:** dueño = `partner-access-management` (CU-O55 / RF-O55.3). Este módulo solo lee `Dim_Partner.activo` para bloquear acciones (RN-PON-013).
- **Disputas sobre consumo o facturación:** dueño = `gestion-tickets-soporte` (CU-O83 / RF-O83.2, ya implementado con `Fact_Reclamo.idfactura`).
- **Alta de clientes y de suscripciones:** dueños = `incorporacion-clientes` y `subscriptions-and-billing`.
- **Autenticación de las llamadas del partner contra la API de datos:** el middleware que valida `Dim_CredencialAPI.activo` en cada petición pertenece a CU-O51 (`api-monitoring-and-billing`).
- **Pantallas, filtros y CTAs:** dueño = [`../frontend/spec.md`](../frontend/spec.md).

## 14. Supuestos

Valores por defecto adoptados donde ni el SRS ni el catálogo fijan un número. Todos son configurables (RNF-20) y ninguno requiere cambio de código para ajustarse:

| Supuesto | Valor por defecto | Fundamento |
|---|---|---|
| Vigencia de la credencial de pruebas | **30 días** | `PortalPartnersAPI.md` L70 lo usa como ejemplo; el SRS solo exige "una fecha de expiración definida". |
| Aviso previo al vencimiento de pruebas | **T-7 días** | El SRS exige "avisa antes del vencimiento y de nuevo al producirse" sin fijar el momento. Un único aviso previo, sin duplicación en el mismo ciclo. |
| Vigencia de la credencial de producción | **Sin expiración por tiempo** | El SRS solo asocia expiración al entorno de pruebas. Producción se corta por revocación o suspensión (CU-O55). |
| Tope de credenciales activas por entorno | **Sin tope** | El SRS habilita "varias credenciales" sin límite (RN-PON-014). |
| Quién solicita la promoción | **El contacto técnico del partner** | El SRS dice "la solicitud la inicia él" (el partner), sin distinguir contacto técnico de cliente titular. |
| Longitud del secreto | **≥ 32 bytes de entropía criptográfica** | Práctica estándar; no fijado por el SRS. |

## 15. Decisiones de esquema

### D1 — `Dim_VersionContratoAPI`: catálogo de versiones del contrato (RF-PON-011 / CU-O50)

**Decidido 2026-08-08 — opción A, con FK a `Dim_Servicio` añadida tras revisión de normalización.**

**Contexto.** RF-O50.1–3 exige exponer la versión vigente, mantener accesibles las versiones anteriores soportadas y señalar la fecha de retiro de cada una. Ni el SRS §3.4 ni `PortalPartnersAPI.md` mencionan CU-O50, y no existía tabla: `Dim_Servicio` (`id_servicio`, `nombre`, `tipo`, `descripcion`, `activo`) no tiene campos de versión ni de retiro.

**Alternativas descartadas.** Extender `Dim_Servicio` con `version`/`estado_version`/`fecha_retiro` (B) obligaría a una fila por versión y destruiría la relación servicio ↔ N versiones. Servir el OpenAPI estáticamente sin persistencia (C) dejaría RF-O50.3 como documentación no consultable por API y chocaría con RNF-20.

**Revisión de normalización (por qué la FK no es opcional).** `Dim_Servicio` **no** es un registro único: contiene hoy tres servicios distintos (*API Despacho*, *API Registro de accidentes*, *Portal Cliente*, sembrados por `backend/scripts/seed_catalogos_soporte.py`), y `Fact_APIIntegracion.idservicio` ya discrimina el consumo por servicio. Una tabla de versiones sin `id_servicio` colapsaría el versionado de los tres en una sola línea temporal — la misma pérdida de 1:N que descarta la opción B. La FK es obligatoria.

```
Dim_VersionContratoAPI
PK idversion              INT       -- clave sustituta, convención de todas las Dim_
FK id_servicio            INT       -- → Dim_Servicio.id_servicio; OBLIGATORIO, no nulo
   version                STRING    -- 'v1', 'v2'; alineado con el versionado por path de api-standards.md
   estado                 STRING    -- 'vigente' | 'soportada' | 'retirada'
   spec_url               STRING    -- nullable; derivable del path, explícito para permitir alojamiento externo
   fecha_publicacion      LONG
   fecha_retiro           LONG      -- nullable; obligatorio antes de pasar a 'retirada' (RN-PON-012)
   activo                 BOOLEAN   -- baja lógica de la fila (RNF-14)
   fecha_actualizacion    LONG      -- timeColumnName y comparisonColumn del upsert (ver D2)
```

Configuración de tabla: `REALTIME`, topic `Dim_VersionContratoAPI_topic`, `upsertConfig.mode=FULL`, `comparisonColumn=fecha_actualizacion`, `primaryKeyColumns=["idversion"]` — idéntica al patrón de `Dim_Servicio`.

**Verificación de formas normales:**

| Criterio | Resultado |
|---|---|
| 1FN — atributos atómicos | ✅ ningún campo multivaluado ni repetido |
| 2FN — dependencia total de la PK | ✅ PK sustituta simple; todo atributo depende de `idversion` |
| 3FN — sin dependencias transitivas | ✅ ningún atributo no clave determina a otro |
| Clave natural | (`id_servicio`, `version`) única entre filas con `activo=true`; a nivel de aplicación (Pinot no soporta `UNIQUE`) |
| Invariante de negocio | Máximo una versión `vigente` por servicio; publicar una nueva pasa la anterior a `soportada` en la misma operación |

**Dos aclaraciones deliberadas, para que no se lean como redundancia:**

- **`activo` vs `estado` no son lo mismo.** `activo` es la baja lógica de la fila exigida por RNF-14 (ningún registro se elimina físicamente). `estado` es el ciclo de vida de la versión frente al partner. Una versión `retirada` sigue con `activo=true`: su historial debe permanecer consultable.
- **`estado` es STRING, no FK a un catálogo propio.** Es un enum cerrado de tres valores; una `Dim_EstadoVersionContrato` sería sobrenormalización. Mismo criterio ya aplicado en `Fact_Factura.estado_pago` y `Dim_CredencialAPI.entorno`.

### D2 — Ausencia de `NULL` en Pinot: centinelas explícitos ✅ APLICADO 2026-08-08

**Detectado durante la revisión de normalización de D1. Corregido y verificado contra Pinot en ejecución.**

> **Rectificación.** La primera versión de este apartado afirmaba que el `comparisonColumn` del upsert descartaría las mutaciones en silencio. **Es falso y queda retirado:** Pinot compara con `>=`, no con `>`, así que un empate en la columna de comparación deja pasar la actualización. Se comprobó ejecutando el ciclo completo (registro → plan → sandbox → suspensión) contra Pinot: los cuatro pasos se aplicaron. El problema real es otro y se describe a continuación.

**El problema real.** Ninguna de las 78 tablas del proyecto habilita `nullHandlingEnabled`, así que **Pinot no almacena `NULL`**: cada valor nulo publicado se materializa como un centinela elegido por Pinot. Medido empíricamente sobre `Dim_Partner`:

| Se publica `NULL` en… | Pinot guardaba | Consecuencia |
|---|---|---|
| `planapi` (STRING) | `'null'` (string literal) | **RF-PON-004 anulado**: la precondición «`planapi` no vacío» era siempre cierta → un partner sin plan podía emitir credenciales |
| `limitellamadasmes` (métrica) | `0` | Cupo 0 indistinguible de «sin plan» → CU-O54 facturaría todo el consumo como excedente |
| `sandbox_activado` (columna de tiempo) | timestamp arbitrario en el pasado | Un partner recién registrado parecía haber activado pruebas |
| `sandbox_expiracion` (dateTime) | `Long.MIN_VALUE` | Un partner recién registrado figuraba como vencido |
| `fecha_expiracion` de producción | `Long.MIN_VALUE` | **El más grave**: un job que busque `fecha_expiracion < ahora` daría por vencidas **todas** las credenciales de producción |

**Decisión: centinelas explícitos por columna** (`defaultNullValue` en `esquemas.json`), elegidos para ser imposibles como dato real y para que las consultas de negocio funcionen sin casos especiales. Se descartó habilitar el manejo de `NULL` solo en este departamento porque introduciría una segunda convención frente a los otros ocho (RNF-17, y Maintainability como prioridad por defecto de la constitución).

| Columna | Centinela | Lectura |
|---|---|---|
| `Dim_Partner.planapi` | `""` | sin plan asignado — la guarda de RF-PON-004 es `planapi <> ''` |
| `Dim_Partner.limitellamadasmes` / `limitellamadasminuto` | `-1` | sin cupo asignado (`0` sería un cupo válido) |
| `Dim_Partner.sandbox_activado` / `sandbox_expiracion` | `0` | nunca activó pruebas |
| `Dim_Partner.fecha_suspension` / `motivo_suspension` | `""` | no suspendido |
| `Dim_CredencialAPI.fecha_expiracion` | `253402300799000` (9999-12-31) | **no expira nunca** — deliberadamente en el futuro, para que `fecha_expiracion < ahora` encuentre solo las realmente vencidas sin excluir producción a mano |
| `Dim_CredencialAPI.nombre_credencial` | `""` | — |
| `Fact_HistorialAccesoPartner.idcredencial` | `-1` | evento del partner, no de una credencial (RF-PON-010) |
| `Fact_HistorialAccesoPartner.motivo` / `estado_anterior` | `""` | — |
| `Dim_VersionContratoAPI.spec_url` | `""` | — |
| `Dim_VersionContratoAPI.fecha_retiro` | `0` | sin fecha de retiro planificada |

**Corrección adicional de `timeColumnName`.** `Dim_Partner` lo tenía en `sandbox_activado`, una columna **opcional** que está vacía hasta la activación de pruebas. La columna de tiempo de Pinot gobierna la gestión de segmentos y la retención, y debe estar siempre poblada. Ambas dimensiones pasan a `fecha_actualizacion` — columna que ya declaraban sin usar y que emplean todas las demás dimensiones mutables (`Dim_Servicio`, `Dim_Plan`, `Dim_Cliente`, `Dim_EstadoIntegracion`). El `comparisonColumn` se alinea con ella por robustez: la última escritura gana, sin depender de empates.

**Cómo se aplicó.** Pinot no permite cambiar `timeColumnName` ni `upsertConfig` en caliente, así que hubo que borrar y recrear las tablas — viable sin migración porque las cuatro estaban vacías. Scripts en `database/`:

- `migra_partners_esquema.py` — aplica centinelas, columnas nuevas y `Dim_VersionContratoAPI` a `esquemas.json` / `tablas.json` (idempotente, con `--dry-run`).
- `despliega_partners.py` — recrea las tablas en Pinot; **se niega a borrar tablas con filas** salvo `--forzar`.
- `verifica_partners.py` — 16 comprobaciones que reproducen las reglas de negocio que estaban rotas.

**Estado: ✅ aplicado y verificado.** 16/16 comprobaciones correctas; suite del backend en verde (1042 pasan, 2 saltados previos); 79 tablas declaradas = 79 desplegadas.

> ⚠️ **Nota operativa.** Recrear una tabla Pinot la hace **re-consumir su topic Kafka desde el principio** (`auto.offset.reset: smallest`). Para dejarla realmente vacía hay que purgar el topic con `kafka-delete-records` antes de recrearla.

> ⚠️ **`database/` está en `.gitignore` y no se versiona.** Los cambios de esquema no tienen respaldo en git: hazlo a mano antes de tocar `esquemas.json` o `tablas.json`.
