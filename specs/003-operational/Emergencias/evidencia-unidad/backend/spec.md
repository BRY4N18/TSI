# Especificación: Evidencia en Sitio y Gestión de Disponibilidad de Unidad

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.
> **Indice del modulo:** [`../evidencia-unidad.md`](../evidencia-unidad.md).
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — Fase B — autoridad Interaction Capability en capa FE; no duplicar OpenAPI/data-model en FE.


## 1. Objetivo

Enriquecer cada caso de accidente con evidencia objetiva (fotografías, notas de campo) **y datos estructurados del incidente** (condiciones climáticas/período del día, elementos físicos cercanos, conductores/vehículos e implicados no conductores) capturados en el sitio por el Técnico de campo; gestionar la disponibilidad declarada de las unidades de emergencia para el algoritmo de despacho; y sincronizar la evidencia capturada sin conexión cuando el dispositivo recupere conectividad.

## Clarifications

### Session 2026-07-09

- Q: ¿Cuál es el estado por defecto cuando una unidad no tiene filas en `Fact_HistorialEstadoUnidad`? → A: **Fuera de servicio** — excluida del despacho hasta el primer cambio explícito de estado.
- Q: ¿Qué roles pueden consultar la galería de evidencias de un caso? → A: **Técnico de campo + Unidad de emergencia + Administrador**.
- Q: ¿La evidencia offline es visible para otros usuarios antes de sincronizar? → A: **Solo en dispositivo capturador** — otros usuarios la ven tras sync completa.
- Q: ¿Qué ocurre si falla la subida parcial durante la sincronización? → A: **Reintento automático** — exitosas se persisten en backend; fallidas quedan locales y se reintentan en cada ciclo hasta éxito.
- Q: ¿Quién puede consultar estado e historial de disponibilidad de unidades? → A: **Unidad ve solo la propia; Administrador y despacho ven todas**.

### Session 2026-07-28

- Q: ¿Quién captura el enriquecimiento estructurado del accidente (clima/período, elementos físicos, conductores/vehículos, implicados) que el registro inicial deja fuera de alcance? → A: **Técnico de campo** (actor principal) en este spec (`evidencia-unidad`), durante atención en sitio. La **Unidad de emergencia** puede colaborar en los mismos endpoints. No existe un spec `field-operations` separado.
- Q: ¿Los datos estructurados de enriquecimiento soportan captura offline como las fotos? → A: **Sí, mismo patrón** — borradores locales con `sincronizado=false` hasta sync (CU-O43 ampliado).

### Session 2026-07-29

- Q: ¿El Operador de emergencias puede precargar clima/elemento físico en el registro inicial (RF-REG-002)? → A: **No.** Tras alineación al flujo canónico (`flujoscorreguidos/flujo-emergencias-canonico.md`), clima/período, elementos físicos, conductores, **implicados no conductores**, fotos y notas son **exclusivos del Técnico de campo** (Unidad puede colaborar) en este spec (CU-O46 / CU-O27). CU-O21 solo datos a distancia.
- Q: ¿`Dim_Implicado` forma parte de CU-O46? → A: **Sí** — personas involucradas no conductoras, vinculadas solo por `idaccidente` (no por `iddespacho`).
- Q: ¿Qué campos tiene `Dim_Implicado`? → A: **Solo la ontología dimensional** (diagrama / `database/esquemas.json`): `idimplicado`, `idaccidente`, `tipoimplicado`, `genero`, `estadoimplicado`, `activo`, `edad` (+ `fecha_actualizacion` de auditoría infra). **No** cédula/nombres/apellidos ni `lesionado`/`observacion`/`rolobservado` — la identidad PII de conductores vive en `Dim_Conductor` (RF-EVI-009).

## 2. Contexto

El Técnico de campo documenta cada accidente con evidencia objetiva **y datos estructurados del siniestro** que enriquecen el expediente y sirven como respaldo para aseguradoras, auditorías y analítica de siniestralidad. La captura ocurre frecuentemente en zonas sin cobertura móvil, por lo que el sistema debe soportar captura offline y sincronización diferida al recuperar conexión. Simultáneamente, la Unidad de emergencia gestiona su disponibilidad para que el orquestador sepa en tiempo real qué unidades están disponibles.

**Casos de uso incluidos:**
- **CU-O27 — Adjuntar evidencias**: El Técnico de campo o Unidad de emergencia captura y sube evidencia fotográfica y notas de campo asociadas a un accidente. Soporta captura offline (marca `sincronizado=false`). La evidencia se vincula solo por `idaccidente`, sin FK directa a `Fact_Despacho`, permitiendo que múltiples unidades adjunten evidencia al mismo caso de forma independiente.
- **CU-O46 — Enriquecer datos estructurados del accidente en sitio**: El Técnico de campo (o Unidad de emergencia) registra o actualiza en el caso activo: (1) período del día y condiciones climáticas vía `Dim_ElementoClimaticosAccidente` (FKs a `Dim_PeriodosDias`, `Dim_EstadosClimas`); (2) elementos físicos cercanos vía `Dim_ElementoFisicoAccidente` (FK a `Dim_Elementos_Fisicos`); (3) conductores y vehículos involucrados vía `Fact_Conductor_Accidente` enlazando `Dim_Conductor`, `Dim_Estado_Conductor` y `Dim_Vehiculo`; (4) **personas involucradas no conductoras** vía `Dim_Implicado`. Absorbe el alcance que `registro-accidente` defería a un spec `field-operations` inexistente. **Dueño exclusivo** de escritura de estos datos (sin precarga desde CU-O21).
- **CU-O30 — Gestionar disponibilidad**: La Unidad de emergencia declara su estado de disponibilidad (Activa, Ocupada, Fuera de servicio). El cuarto estado, **En Misión**, no es declarable manualmente — lo asigna el sistema automáticamente al confirmar un despacho (`despacho-inteligente`, CU-O24) y se abandona automáticamente al cerrar/abortar el caso (`seguimiento-cierre-de-casos`). Cada cambio se registra como una nueva fila en `Fact_HistorialEstadoUnidad`. El estado actual se deriva consultando la fila con `fechahora` más reciente para esa unidad.
- **CU-O43 — Sincronizar evidencia en diferido**: Un proceso automatizado persiste en backend los registros capturados offline, con `sincronizado=true` en `Dim_EvidenciaFoto`, `Dim_NotaAccidente` y en los ítems de enriquecimiento estructurado pendientes (puentes clima/físico, vínculos conductor-accidente e **implicados**). La `fechahora` original de captura se conserva inalterada.

**Tablas de base de datos utilizadas** (verificadas contra `tablas.json`/`esquemas.json`, ver `data-model.md`):
- `Dim_EvidenciaFoto`: evidencia fotográfica. Campos: `idevidenciafoto`, `idaccidente`, `idusuario`, `urlevidenciafoto`, `sincronizado` (Boolean), `fechahora`.
- `Dim_NotaAccidente`: notas y observaciones. Campos: `idnotaaccidentes`, `idaccidente`, `idusuario`, `nota`, `tipo`, `sincronizado` (Boolean), `fechahora`.
- `Dim_ElementoClimaticosAccidente` (puente): `idelementoclimaticoaccidente`, `idaccidente`, `idperiododia`, `idestadoclima`, `idusuario`, `activo`, `fecha_actualizacion`.
- `Dim_PeriodosDias`, `Dim_EstadosClimas` (catálogos lectura para clima/período).
- `Dim_ElementoFisicoAccidente` (puente): `idelementosfisicosaccidente`, `idelementofisico`, `idaccidente`, `idusuario`, `activo`, `fecha_actualizacion`.
- `Dim_Elementos_Fisicos` (catálogo lectura).
- `Fact_Conductor_Accidente`: `idconductoraccidente`, `idaccidente`, `idconductor`, `idestadoconductor`, `idvehiculo`, `idusuario`, `activo`, `fecha_actualizacion`.
- `Dim_Conductor`, `Dim_Estado_Conductor`, `Dim_Vehiculo` (catálogos / alta en sitio según RF-EVI-007…009).
- `Dim_Implicado`: personas involucradas no conductoras (ontología). Campos: `idimplicado`, `idaccidente`, `tipoimplicado`, `genero`, `estadoimplicado`, `edad`, `activo` (+ `fecha_actualizacion` infra). Solo FK `idaccidente`. Sin PII de identidad.
- `Fact_HistorialEstadoUnidad`: trazabilidad de cambios de estado. Campos: `idhistorialestadosunidadesemergencias`, `idunidademergencia`, `idestadounidademergencia` (FK a `Dim_EstadoUnidadEmergencia`), `estadoanterior`, `estadonuevo`, `fechahora`.
- `Dim_EstadoUnidadEmergencia`: catálogo de estados de unidad (Activa, Ocupada, Fuera de servicio).
- `Dim_UnidadEmergencia`: catálogo de unidades externas.


## 3. Actores

| Actor | Rol | Interacción principal |
|---|---|---|
| **Unidad de emergencia** | Operador de campo y gestor de disponibilidad | Cambia su estado de disponibilidad. Consulta su propio estado e historial. Captura evidencia/notas y puede colaborar en enriquecimiento estructurado (CU-O46). Consulta galería y datos enriquecidos del caso. |
| **Técnico de campo** | Documentador y enriquecedor en sitio | Captura evidencia fotográfica, notas de campo y **datos estructurados** (clima/período, elementos físicos, conductores/vehículos, **implicados no conductores**). Consulta galería y expediente enriquecido del caso. |
| **Administrador** | Auditor y gestor del sistema | Consulta estado e historial de todas las unidades. Consulta galería y datos enriquecidos de cualquier caso (solo lectura). |
| **Sistema (despacho)** | Orquestador de despacho | Consulta estado de todas las unidades para el algoritmo de despacho (`despacho-inteligente`). |
| **Sistema** | Sincronizador automático | Ejecuta la sincronización diferida de evidencia y enriquecimiento offline al recuperar conectividad. |

## 4. Requisitos funcionales

### RF-EVI-001: Gestión de disponibilidad de unidad (CU-O30)

La Unidad de emergencia debe poder cambiar manualmente su estado de disponibilidad entre 3 de los 4 estados posibles, en cualquier momento:

| Estado | Significado | Declarable manualmente |
|---|---|---|
| **Activa** | Disponible para recibir despachos. | Sí |
| **Ocupada** | No disponible por otra razón operativa (trámites, reabastecimiento, en base) — no ligada a un despacho activo. | Sí |
| **En Misión** | Atendiendo un caso despachado; no recibe nuevos despachos. | No — solo el sistema la asigna al confirmar un despacho (CU-O24) y la retira al cerrar/abortar el caso. |
| **Fuera de servicio** | No operativa (mantenimiento, fin de turno, avería). | Sí |

Un POST de declaración manual con `estadonuevo = En Misión` debe ser rechazado con HTTP 422.

Cada cambio debe:
1. Insertar un nuevo registro en `Fact_HistorialEstadoUnidad` con `idunidademergencia`, `idestadounidademergencia`, `estadoanterior`, `estadonuevo`, `idusuario`, `fechahora`. **`idusuario`** identifica a la unidad autenticada que autodeclara (este CU). *(Nota 2026-07-24: la declaración por Operador sin login — antiguo CU-O59 en `alta-unidades` — fue **eliminada**; este CU-O30 es la única vía de declaración de disponibilidad.)*
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

El sistema debe proveer un mecanismo para sincronizar evidencia **y enriquecimiento estructurado** capturados sin conexión:
1. Persistir en `Dim_EvidenciaFoto`, `Dim_NotaAccidente`, `Dim_ElementoClimaticosAccidente`, `Dim_ElementoFisicoAccidente`, `Dim_Conductor`/`Dim_Vehiculo` (si alta nueva) y `Fact_Conductor_Accidente` los registros pendientes del almacenamiento local, con `sincronizado=true` tras completar escrituras Kafka (y Blob para fotos). No existen registros con `sincronizado=false` en el backend.
2. La `fechahora` original de captura debe conservarse inalterada (no se reemplaza con el momento de sincronización).
3. Ejecutable como comando de gestión (`sync_diferido`) y/o servicio en segundo plano.
4. Debe poder ejecutarse sin intervención del usuario al detectar conectividad.
5. En caso de fallo parcial (ej. timeout al subir a Azure Blob Storage), los registros exitosos se persisten en backend con `sincronizado=true`; los fallidos permanecen en almacenamiento local (`sincronizado=false`) y se reintentan automáticamente en cada ciclo de sync subsiguiente hasta completar con éxito.

### RF-EVI-007: Registrar período del día y condiciones climáticas en sitio (CU-O46)

El Técnico de campo o Unidad de emergencia debe poder asociar al `idaccidente` activo:

1. `idperiododia` (INT, FK a `Dim_PeriodosDias`, opcional pero recomendado) — seleccionable desde catálogo; si el Operador ya precargó un valor en registro (RF-REG-002), el Técnico puede sobrescribirlo.
2. `idestadoclima` (INT, FK a `Dim_EstadosClimas`, opcional pero recomendado) — seleccionable desde catálogo (condiciones observadas en sitio).
3. Persistencia vía upsert en `Dim_ElementoClimaticosAccidente` (`idaccidente`, `idperiododia`, `idestadoclima`, `idusuario`, `activo`, `fecha_actualizacion`) escrita solo por Kafka.
4. El sistema debe exponer lectura de catálogos `Dim_PeriodosDias` y `Dim_EstadosClimas` para poblar selectores en la UI de campo.
5. Mismas restricciones de caso activo que RN-EVI-006 (no Cerrado/Descartado).

### RF-EVI-008: Registrar elementos físicos cercanos en sitio (CU-O46)

El Técnico de campo o Unidad debe poder:

1. Asociar uno o más `idelementofisico` (FK a `Dim_Elementos_Fisicos`: cruces, semáforos, paradas, baches, vías de tren, etc.) al `idaccidente` mediante filas en `Dim_ElementoFisicoAccidente`.
2. Listar y consultar los elementos ya vinculados al caso.
3. Soft-desactivar un vínculo erróneo (`activo=false`) sin DELETE físico (append/upsert Kafka).
4. Exponer catálogo `Dim_Elementos_Fisicos` en solo lectura para la UI.

### RF-EVI-009: Registrar conductores y vehículos involucrados (CU-O46)

El Técnico de campo o Unidad debe poder documentar las personas y vehículos del siniestro:

1. **Alta o reutilización de conductor** en `Dim_Conductor`. Si ya existe por `identificacion`, reutilizar `idconductor`.
   - **Requeridos en sitio:** `identificacion`, `nombres`, `apellidos`.
   - **Opcionales en sitio:** `genero`, `tipolicencia`, `estadolicencia`, `ciudadresidencia`, `aniosexperiencia`.
   - **Sistema:** `idconductor` (PK), `activo=true` al alta.
2. **Estado del conductor en el evento** vía `idestadoconductor` → `Dim_Estado_Conductor` (campos BOOLEAN: `estadosobriedad`, `nivelatencion`, `condicionfisica`, `usoseguridad`). La UI presenta **4 checkboxes** (Sobrio, Atento, Ileso, Con seguridad); al registrar se resuelve el `idestadoconductor` por match exacto contra las 16 filas del catálogo (todas las combinaciones booleanas). **Requerido.**
3. **Alta o reutilización de vehículo** en `Dim_Vehiculo`.
   - **Requerido en sitio:** `tipovehiculo`.
   - **Opcionales en sitio:** `modelovehiculo`, `categoriausovehiculo`, `mercanciapeligrosa`, `ejes`.
   - **Sistema:** `idvehiculo` (PK), `activo=true` al alta.
4. **Vínculo al accidente** insertando `Fact_Conductor_Accidente` con `idaccidente`, `idconductor`, `idestadoconductor`, `idvehiculo`, `idusuario`, `activo`.
5. Consultar la lista de conductores/vehículos vinculados a un `idaccidente`.
6. Soft-desactivar un vínculo erróneo (`activo=false` en `Fact_Conductor_Accidente`).
7. Roles de escritura: **Técnico de campo** y **Unidad de emergencia**. Lectura: además **Administrador**. Otros roles: HTTP 403.
8. Caso debe estar activo (RN-EVI-006). Datos de identidad de conductores son **datos personales sensibles** (Principle V / tie-breaker dominio PII):
   - **Tránsito:** HTTPS/TLS obligatorio en API y sync.
   - **Reposo (servidor):** persistencia Pinot/`Dim_Conductor` bajo cifrado at-rest de la infraestructura de datos del proyecto (discos/volúmenes cifrados del cluster Pinot y backups); el aplicativo no almacena PII en claro fuera de esos stores.
   - **Reposo (cliente offline):** `LocalConductorAccidente` en IndexedDB debe almacenar el payload PII cifrado en el dispositivo (p. ej. Web Crypto / key derivada de sesión autenticada); al completar sync se elimina el borrador local.
   - **RBAC:** escritura Técnico/Unidad; lectura + Administrador (RN-EVI-016); otros roles HTTP 403.
   - **Accountability:** audit log de altas, consultas de listado por caso y soft-deletes (`registrar_conductor_accidente`, `consultar_conductores_accidente`, `desactivar_conductor_accidente`).
   - **Integridad:** escritura solo vía Kafka (sin UPDATE destructivo); soft-delete `activo=false`; reutilización por `identificacion` (RN-EVI-019) evita duplicados de identidad.

### RF-EVI-010: Registrar implicados no conductores (CU-O46)

El Técnico de campo o Unidad debe poder documentar personas involucradas que **no** son conductores (peatones, pasajeros, testigos relevantes, etc.), usando **únicamente** los campos de la ontología `Dim_Implicado`:

1. **Alta** en `Dim_Implicado` vinculada solo por `idaccidente` (RN-EVI-004 — sin `iddespacho`).
   - **Requeridos:** `tipoimplicado` (Peaton / Pasajero / Testigo / Otro), `estadoimplicado` (Ileso / Lesionado / Fallecido / Desconocido).
   - **Opcionales:** `genero` (STRING), `edad` (INT ≥ 0).
   - **Sistema:** `idimplicado` (PK), `activo=true`, `fecha_actualizacion`.
2. Listar implicados activos del caso (`activo=true`).
3. Soft-desactivar registro erróneo (`activo=false`) sin DELETE físico.
4. Roles de escritura: **Técnico de campo** y **Unidad de emergencia**. Lectura: además **Administrador**. Otros roles: HTTP 403.
5. Caso activo (RN-EVI-006).
6. **Fuera de esta entidad:** identificación, nombres, apellidos u otra PII de identidad — no forman parte de `Dim_Implicado` (si se requieren para un conductor, usar RF-EVI-009 / `Dim_Conductor`).
7. Sync diferida (CU-O43): borradores `LocalImplicado` (sin cifrado PII) con `sincronizado=false` hasta persistencia en backend.


## 5. Requisitos no funcionales

- **RNF-EVI-001:** App móvil offline: capturar fotos, notas **y enriquecimiento estructurado CU-O46** (clima/período, elementos físicos, conductores/vehículos, **implicados**) sin conexión; sincronización automática al reconectar.
- **RNF-EVI-002:** Cada foto ≤ 10 MB, compresión automática antes de subir.
- **RNF-EVI-003:** Cambio de estado de unidad reflejado en ≤ 5 segundos para el algoritmo de despacho.
- **RNF-EVI-004:** Sincronización offline debe completarse en ≤ 30 segundos tras reconectar (para batch de evidencias **y enriquecimiento** pendientes). Los registros fallidos en un ciclo no bloquean la persistencia de los exitosos; se reintentan en ciclos posteriores.
- **RNF-EVI-005:** El proceso de sincronización diferida no debe modificar la `fechahora` original de captura.
- **RNF-EVI-006:** La consulta de estado actual de unidad debe resolverse en ≤ 2 segundos (última fila en historial).
- **RNF-EVI-007:** Consultas de catálogos de enriquecimiento (`Dim_PeriodosDias`, `Dim_EstadosClimas`, `Dim_Elementos_Fisicos`, `Dim_Estado_Conductor`) ≤ 2 s p95.
- **RNF-EVI-008:** Alta de vínculo `Fact_Conductor_Accidente` (incluyendo alta de `Dim_Conductor`/`Dim_Vehiculo` si aplica) ≤ 3 s p95 en línea.
- **RNF-EVI-009 (Security / Principle V):** PII de conductores (`identificacion`, nombres, apellidos y datos de licencia) DEBE viajar solo por TLS; DEBE reposar cifrada en infraestructura Pinot/backups; DEBE cifrarse en almacenamiento local offline hasta sync exitosa; tras sync, borrar borrador local. Fallo de cifrado local → no persistir PII en claro (bloquear guardado offline con mensaje claro).
- **RNF-EVI-010 (Interaction / Principle IV):** La UI de enriquecimiento en campo DEBE cumplir `.specify/docs/design/design-system.md` para roles operativos: ≤4 acciones primarias visibles por pantalla, controles ≥44×44 px, validación inline de campos obligatorios, confirmación explícita antes de soft-delete, estados de carga/error/vacío, y priorizar prevención de error sobre densidad visual.
## 6. Reglas de negocio

- **RN-EVI-001:** Solo el Administrador puede registrar unidades. Las unidades solo cambian su propia disponibilidad.
- **RN-EVI-002:** Solo el estado "Activa" incluye la unidad en el algoritmo de despacho; "Ocupada", "En Misión" y "Fuera de servicio" la excluyen.
- **RN-EVI-003:** Cada cambio de estado queda en historial inmutable con `fechahora`. No se permite UPDATE ni DELETE sobre `Fact_HistorialEstadoUnidad`.
- **RN-EVI-004:** Evidencia foto, notas y enriquecimiento estructurado se vinculan a un `idaccidente` existente en `Fact_Accidente`. No requieren FK a `Fact_Despacho`.
- **RN-EVI-005:** Notas de campo son solo lectura una vez registradas en backend (INSERT-only en `Dim_NotaAccidente`). Los registros locales pendientes se persisten en backend al sincronizar (INSERT con `sincronizado=true`).
- **RN-EVI-006:** Solo se puede agregar evidencia o enriquecimiento estructurado a casos activos (estado distinto de Cerrado y Descartado).
- **RN-EVI-007:** Cada unidad tiene usuario asociado en `Dim_Usuarios` con rol "Unidad de Emergencia".
- **RN-EVI-008:** El campo `sincronizado` solo puede cambiar de `false` a `true`. No se permite revertir a `false`.
- **RN-EVI-009:** La `fechahora` de captura original no debe modificarse durante la sincronización diferida.
- **RN-EVI-010:** El estado actual de disponibilidad se deriva exclusivamente de `Fact_HistorialEstadoUnidad` (fila con `fechahora` más reciente). No existe campo redundante en `Dim_UnidadEmergencia`.
- **RN-EVI-011:** Si una unidad no tiene filas en `Fact_HistorialEstadoUnidad`, su estado actual es **Fuera de servicio** por defecto. La unidad queda excluida del algoritmo de despacho hasta registrar su primer cambio de estado.
- **RN-EVI-012:** Solo usuarios con rol **Técnico de campo**, **Unidad de emergencia** o **Administrador** pueden consultar la galería de evidencias y el enriquecimiento estructurado de un caso. Otros roles autenticados reciben denegación de acceso.
- **RN-EVI-013:** Evidencia/enriquecimiento con `sincronizado=false` existe únicamente en el almacenamiento local del dispositivo que la capturó. No es visible para otros usuarios ni en consultas al backend hasta completar la sincronización.
- **RN-EVI-014:** Si la subida de un registro falla durante la sincronización, permanece en almacenamiento local y se reintenta automáticamente en cada ciclo de sync hasta éxito. Los registros ya sincronizados en el mismo batch no se revierten.
- **RN-EVI-015:** La **Unidad de emergencia** solo puede consultar su propio estado e historial. El **Administrador** y el **servicio de despacho** pueden consultar el estado e historial de todas las unidades. Otros roles reciben HTTP 403.
- **RN-EVI-016:** Escritura de enriquecimiento estructurado (RF-EVI-007…010) permitida a **Técnico de campo** y **Unidad de emergencia**; Administrador solo lectura.
- **RN-EVI-017:** Un `idaccidente` tiene como máximo una fila activa de `Dim_ElementoClimaticosAccidente` (`activo=true`); nuevos upserts reemplazan/superseden el vínculo climático vigente.
- **RN-EVI-018:** `Fact_Conductor_Accidente` permite hasta `Fact_Accidente.numvehiculos` vínculos activos por accidente (RN-EVI-022); la unicidad lógica recomendada es (`idaccidente`, `idconductor`, `idvehiculo`) con `activo=true`.
- **RN-EVI-019:** Reutilización de `Dim_Conductor` por `identificacion` cuando exista coincidencia activa; no crear duplicados de identidad.
- **RN-EVI-020:** Prohibido persistir PII de conductor en claro en almacenamiento local del dispositivo. El store offline DEBE cifrar `LocalConductorAccidente` (RNF-EVI-009).
- **RN-EVI-021:** Tras sync exitosa de un ítem conductor, el cliente DEBE eliminar el borrador local correspondiente (minimización de datos).
- **RN-EVI-022:** El número de vínculos activos conductor/vehículo (`Fact_Conductor_Accidente` con `activo=true`) DEBE ser ≤ `Fact_Accidente.numvehiculos`. Si `numvehiculos` es nulo o &lt; 1, rechazar altas con error de negocio hasta que el caso declare el número. El intento que excede el tope se rechaza (HTTP 422).

## 7. Entradas

- `idaccidente` (STRING, requerido para adjuntar evidencia/nota/enriquecimiento) — debe existir y estar activo en `Fact_Accidente`.
- Archivo(s) de imagen (JPEG/PNG, ≤10 MB c/u) — para evidencia fotográfica.
- `nota` (STRING, requerido si se registra observación), `tipo` (STRING: Observación general / Declaración de testigo / Daños materiales / Condiciones del sitio).
- `idperiododia`, `idestadoclima` (INT, opcionales) — enriquecimiento climático (RF-EVI-007).
- `idelementofisico` (INT) — uno o más elementos físicos (RF-EVI-008).
- Datos de conductor/vehículo/estado (RF-EVI-009):
  - **Requeridos:** `identificacion`, `nombres`, `apellidos`, `tipovehiculo`, `idestadoconductor` (vía checkboxes de flags).
  - **Opcionales:** `genero`, `tipolicencia`, `estadolicencia`, `ciudadresidencia`, `aniosexperiencia`, `modelovehiculo`, `categoriausovehiculo`, `mercanciapeligrosa`, `ejes`.
- Datos de implicado no conductor (RF-EVI-010) — ontología:
  - **Requeridos:** `tipoimplicado` (Peaton / Pasajero / Testigo / Otro), `estadoimplicado` (Ileso / Lesionado / Fallecido / Desconocido).
  - **Opcionales:** `genero`, `edad` (INT ≥ 0).
- `idunidademergencia` (INT, requerido para cambio de disponibilidad) — implícito por sesión autenticada de la unidad.
- `estadonuevo` (ENUM: Activa / Ocupada / Fuera de servicio — "En Misión" no es aceptado en declaración manual, HTTP 422) — estado destino del cambio de disponibilidad.
- Señal de reconexión del dispositivo (evento de sistema, no ingresado por el usuario) — dispara la sincronización diferida.

## 8. Salidas

- Registro creado en `Dim_EvidenciaFoto` o `Dim_NotaAccidente`, con `sincronizado` reflejando el estado de conexión al momento de la captura.
- Upsert en `Dim_ElementoClimaticosAccidente` / `Dim_ElementoFisicoAccidente` / `Fact_Conductor_Accidente` / `Dim_Implicado` (y altas asociadas en `Dim_Conductor` / `Dim_Vehiculo` si aplica).
- Registro nuevo en `Fact_HistorialEstadoUnidad` tras cada cambio de disponibilidad, con `estadoanterior`/`estadonuevo`.
- Galería de evidencias por `idaccidente` (fotos + notas, ordenadas por `fechahora` descendente, con indicador de sincronización y autor).
- Vista de enriquecimiento del caso: clima/período vigentes, elementos físicos activos, lista de conductores/vehículos vinculados, **lista de implicados no conductores**.
- Historial de estados de una unidad, ordenado por `fechahora` descendente.
- Confirmación de sincronización diferida completada (conteo de registros sincronizados y pendientes por reintento).
- Mensajes de error/validación (ej. caso inactivo, foto >10 MB, `idaccidente` inexistente, FK de catálogo inválida).

## 9. Estados posibles

### Estados de disponibilidad de unidad

| Estado | Significado | Incluido en despacho |
|---|---|---|
| **Activa** | Disponible para recibir despachos. | Sí |
| **Ocupada** | No disponible por otra razón operativa (trámites, reabastecimiento, en base), no ligada a un despacho activo. | No |
| **En Misión** | Atendiendo un caso despachado, no recibe nuevos despachos. Asignado automáticamente por el sistema. | No |
| **Fuera de servicio** | No operativa (mantenimiento, fin de turno, avería). | No |

### Diagrama de transiciones
```
Activa ←→ Ocupada            (manual, ambas direcciones)
Activa ←→ Fuera de servicio  (manual, ambas direcciones)
Activa → En Misión           (automático, al confirmar despacho — CU-O24)
En Misión → Activa           (automático, al cerrar caso o retirarse)
En Misión → Fuera de servicio  (automático, excepción: avería durante atención)
Fuera de servicio → Activa   (manual, al volver a estar operativa)
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

### Escenario 7: Enriquecimiento climático y elementos físicos (CU-O46)
Dado que el Técnico de campo está en un caso activo en `EN_ATENCIÓN`
Cuando selecciona `idperiododia`, `idestadoclima` y dos `idelementofisico` del catálogo
Y envía el enriquecimiento
Entonces el sistema debe upsert `Dim_ElementoClimaticosAccidente` para ese `idaccidente`
Y debe insertar/activar dos filas en `Dim_ElementoFisicoAccidente`
Y la consulta de enriquecimiento del caso debe reflejar esos valores.

### Escenario 8: Registro de conductor y vehículo (CU-O46)
Dado un caso activo
Cuando el Técnico registra un conductor nuevo (identificación no existente), su estado (`idestadoconductor`) y un vehículo
Entonces el sistema debe crear `Dim_Conductor`, `Dim_Vehiculo` y `Fact_Conductor_Accidente` vinculados al `idaccidente`
Y un segundo registro con la misma `identificacion` debe reutilizar el mismo `idconductor` (RN-EVI-019).

### Escenario 9: Enriquecimiento offline y sync
Dado que el Técnico captura un vínculo conductor-accidente sin conexión
Cuando el dispositivo reconecta y corre `sync_diferido`
Entonces el vínculo debe persistirse en backend y aparecer en la consulta del caso para otros roles autorizados.

### Escenario 10: Implicado no conductor (ontología)
Dado un caso activo
Cuando el Técnico registra `tipoimplicado=Peaton`, `estadoimplicado=Lesionado` y opcionalmente `edad`/`genero`
Entonces el sistema debe crear `Dim_Implicado` solo con campos de ontología vinculados a `idaccidente`
Y la UI no debe solicitar identificación ni nombres.

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
Se ejecuta el comando `sync_diferido`. Los registros pendientes del almacenamiento local (fotos, notas y enriquecimiento estructurado) se persisten en backend con `sincronizado=true`. La `fechahora` de cada registro no se modifica. Los fallidos permanecen locales y se reintentan en ciclos posteriores.

### CA-EVI-007: Galería de evidencias por caso
La consulta GET de evidencias para un `idaccidente` retorna todas las fotos y notas asociadas, ordenadas por `fechahora` descendente, con indicador de sincronización y autor. Solo accesible para roles **Técnico de campo**, **Unidad de emergencia** y **Administrador**; otros roles reciben HTTP 403.

### CA-EVI-008: Multi-unidad
Dos unidades diferentes (ej. grúa y ambulancia) adjuntan evidencia al mismo `idaccidente`. Ambas evidencias aparecen en la galería del caso sin relación con `Fact_Despacho`.

### CA-EVI-009: Historial de cambios de unidad
Se consulta el historial de estado de una unidad. El sistema retorna todas las filas de `Fact_HistorialEstadoUnidad` para esa unidad ordenadas por `fechahora` descendente. La Unidad de emergencia solo puede consultar su propio historial; el Administrador y el servicio de despacho pueden consultar cualquier unidad; otros roles reciben HTTP 403.

### CA-EVI-010: Clima y período en sitio (CU-O46)
El Técnico asocia `idperiododia` e `idestadoclima` a un caso activo. Existe exactamente una fila activa en `Dim_ElementoClimaticosAccidente` para ese `idaccidente` (RN-EVI-017).

### CA-EVI-011: Elementos físicos en sitio (CU-O46)
El Técnico vincula ≥1 `idelementofisico` válido. Las filas activas aparecen en la consulta de enriquecimiento del caso.

### CA-EVI-012: Conductores y vehículos (CU-O46)
El Técnico registra conductor + estado + vehículo y el vínculo `Fact_Conductor_Accidente`. La consulta del caso lista el vínculo. Reintento con misma `identificacion` reutiliza `idconductor`. Rol sin permiso recibe HTTP 403.

### CA-EVI-013: PII conductor en reposo/offline (Principle V)
Un borrador offline de conductor se guarda cifrado en el dispositivo (no legible en claro en IndexedDB). Tras sync exitosa el borrador local desaparece. API de conductores solo responde bajo TLS + RBAC; audit log registra alta/consulta/soft-delete.

### CA-EVI-014: UX enriquecimiento bajo presión (Principle IV)
La página de enriquecimiento muestra como máximo 4 acciones primarias visibles, controles táctiles ≥44×44 px, validación inline y confirmación antes de soft-delete; estados vacío/carga/error presentes.
### CA-EVI-015: Implicados no conductores (CU-O46 / ontología)
El Técnico registra un implicado con `tipoimplicado` y `estadoimplicado` (y opcionalmente `genero`/`edad`) vinculados solo a `idaccidente`. La consulta de enriquecimiento lista el registro activo. Soft-delete pone `activo=false`. El formulario **no** solicita cédula ni nombres. Rol sin permiso recibe HTTP 403.

## 12. Dependencias

- **`autenticacion-y-rbac`:** Autenticación JWT y roles definidos (Técnico de campo, Unidad de Emergencia, Administrador).
- **`registro-accidente`:** Evidencia y enriquecimiento se vinculan a `idaccidente` en `Fact_Accidente`. CU-O21 **no** precarga clima/físico/conductores/implicados; este módulo es el dueño del enriquecimiento en sitio (CU-O46).
- **`despacho-inteligente`:** Consume el estado actual de disponibilidad de todas las unidades para el algoritmo de despacho (acceso de servicio con permisos de consulta de flota completa).
- **`seguimiento-cierre-de-casos`:** Al cerrar un caso, las unidades asociadas deben regresar a estado Activa. Durante atención, las unidades/técnicos pueden adjuntar evidencia y enriquecer datos. El expediente de cliente (CU-O29) debe poder incluir el enriquecimiento estructurado (lectura).

## 13. Fuera de alcance

- Registro de unidades externas (**CU-O54**) → spec `alta-unidades`.
- Geolocalización GPS continua (**CU-O25**) → spec `seguimiento-cierre-de-casos`.
- Confirmación/rechazo de despachos (**CU-O24, CU-O45**) → spec `despacho-inteligente`.
- Análisis de imágenes por IA.
- Almacenamiento de video (solo fotografía fija en esta versión).
- Sincronización bidireccional de notas (solo subida, no edición remota).
- Auto-cálculo de `idperiododia`/`idestadoclima` desde estación meteorológica en el registro inicial → responsabilidad de `registro-accidente` (RN-REG-008); este módulo solo captura/corrige observación en sitio.
- Campos de cierre del caso (`resultado_atencion`, `calificacion`, `observaciones_finales`) → `seguimiento-cierre-de-casos` (fuera de esta iteración de spec).
- Identidad PII de implicados no conductores (cédula, nombres, apellidos) en `Dim_Implicado` — fuera de ontología; no ampliar esta dimensión.