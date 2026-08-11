# Decisiones pendientes

Registro de puntos detectados durante auditorías (código vs. SRS vs. catálogo vs. specs) que **no bloquean** el funcionamiento del sistema, pero requieren una decisión de negocio o de diseño antes de cerrarse. No son bugs activos — son ambigüedades o inconsistencias documentales/de esquema que alguien con criterio de producto debe resolver.

**Cómo usar este archivo:**
- Cada entrada es un punto abierto, con departamento, contexto, opciones y estado.
- Al decidir, mover la entrada a "Resueltas" con la fecha y qué se eligió (no borrar el historial).
- Cualquier departamento puede agregar entradas aquí, no solo Ventas y CRM.

---

## Pendientes

### 26. El contenedor `accidentes-django` corre una imagen anterior al departamento Partners

- **Departamento:** Infraestructura / entorno de desarrollo
- **Detectado:** 2026-08-10, al verificar el frontend de #08 contra la app real
- **Qué pasa:** `accidentes-django` responde **404** en `/api/v1/partners`,
  `/api/v1/logs-api` y todo lo del departamento, mientras `/api/v1/ventas-crm/planes`
  funciona. `docker inspect` confirma que **no monta el código**: es una imagen
  construida antes de #07.
- **Consecuencia:** cualquier verificación manual contra `localhost:4200`
  prueba una versión vieja del backend. Yo levanté Django desde el working tree
  en el puerto 8001 y apunté el proxy ahí; funcionó, pero es un rodeo que hay
  que repetir cada vez.
- **Salidas posibles:** reconstruir la imagen tras cada cambio de backend, o
  montar `backend/` como volumen en `docker-compose` para que el contenedor
  sirva el código vivo. La segunda es la que evita el problema de raíz.
- **Ojo con el `.env`:** define `PINOT_BROKER_URL=http://pinot-broker:8099`, que
  solo resuelve **dentro** de la red Docker. Para correr Django fuera hay que
  exportar `PINOT_BROKER_URL=http://localhost:8099` (y `KAFKA_BOOTSTRAP_SERVERS`).

### 25. ¿Debe el rol `Cliente` ver el reporte mensual de consumo de API?

- **Departamento:** Partners y API (#08, capa frontend)
- **Detectado:** 2026-08-10, al especificar el frontend de #08
- **La contradicción:** RF-APM-009 dice que el reporte mensual lo consultan «el **Cliente** y el
  Administrador». Pero el endpoint `GET /api/v1/reportes-consumo` usa el permiso `EsPartnerOGestor`,
  que resuelve a `{PartnerIntegracion, DesarrolladorAPIs, Administrador}`: **el rol `Cliente` no
  entra**. Una de las dos cosas está mal desde que se cerró el backend, y nadie lo notó porque no
  había frontend que lo intentara.
- **Por qué no lo resuelvo yo:** las dos salidas son razonables y la elección es de negocio, no
  técnica.
  - **Ampliar el permiso** — el Cliente es quien paga la factura de excedente, así que ver el
    consumo que la origina es defendible.
  - **Corregir el RF** — el Cliente ya ve su facturación en Suscripciones; el consumo técnico de la
    API es cosa del partner que integra, que puede no ser la misma persona.
- **Lo que hice mientras tanto:** el frontend se ciñe a los tres roles que el endpoint ya admite. No
  amplié el permiso por conveniencia de la UI: relajar un control de acceso para que una pantalla
  cargue es exactamente cómo se abren huecos que luego nadie recuerda haber abierto.
- **Impacto si se decide ampliar:** un permiso nuevo, un test de contrato y una línea en
  `nav-links.ts`. Barato en cualquier momento.

### 23. Planes y accidentes usan dos vocabularios de severidad sin equivalencia definida

- **Departamento:** Partners y API (#08), con impacto en Suscripciones y Emergencias
- **Detectado:** 2026-08-09, al implementar `ConsumoDatosService` (RF-APM-002)
- **El problema:** RF-APM-002 exige entregar «solo casos cuya severidad esté en las severidades desbloqueadas del plan». Pero los dos catálogos **no comparten vocabulario** y **no existe tabla ni constante que los relacione**:

  | Origen | Valores |
  |---|---|
  | Planes (`catalogo_plan_service.SEVERIDADES`) | `"Baja"`, `"Media"`, `"Alta"` |
  | Accidentes (`frontend/.../severidad.constants.ts`) | `1` Leve · `2` Moderado · `3` Grave · `4` Fatal |
  | `Dim_Severidad` | **vacía** (0 filas), no resuelve la duda |

- **Por qué importa:** sin equivalencia, el filtro de alcance no se puede aplicar. Y como RF-APM-003 es **fail-closed**, una equivalencia mal elegida no da un error visible: da **cero resultados**, que el partner interpretará como «no hubo accidentes».
- **RESUELTO PARCIALMENTE (2026-08-09).** Decisión del responsable: **el catálogo canónico son las severidades de accidente** (1 Leve, 2 Moderado, 3 Grave, 4 Fatal) y deben vivir en `Dim_Severidad`, que es la tabla que existía para eso. Sembrada con `database/seed_severidad.py`.
- **Defecto de esquema que había que corregir antes de poder sembrarla:** `Dim_Severidad.severidad` —la columna del **nombre**— estaba declarada como **métrica INT**. Pinot descarta en silencio toda fila cuyo valor no sea numérico, así que la siembra «funcionaba» sin escribir nada: ni error ni aviso. Corregido a **dimensión STRING** con `database/migra_dim_severidad.py`. La tabla estaba vacía, así que no hubo pérdida. *(Nota operativa: un `PUT /schemas` rechaza cambios de tipo con «Only allow adding new columns»; hay que borrar y recrear el esquema.)*
- **DIRECCIÓN DECIDIDA (2026-08-09):** el vocabulario `"Baja"/"Media"/"Alta"` de los planes **queda deprecado**. Todo el sistema debe trabajar contra `Dim_Severidad` — **también la pantalla de planes**, que debe ofrecer y mostrar las severidades reales (Leve/Moderado/Grave/Fatal), no una escala paralela inventada. Tener dos escalas obliga a traducir, y cada traducción es una oportunidad de equivocarse en silencio: aquí el error no se ve, devuelve cero resultados.
- **Estado:** la traducción `SEVERIDADES_POR_NIVEL` sigue en pie **como puente**, porque hoy los 5 planes sembrados guardan el vocabulario viejo y quitarla rompería el consumo. Desaparece cuando Suscripciones migre.
- **Trabajo pendiente en Suscripciones** (no es de Partners, por eso no se hizo aquí):
  1. `catalogo_plan_service.SEVERIDADES` deja de ser `frozenset({"Baja","Media","Alta"})` y pasa a validar contra `Dim_Severidad`.
  2. `Dim_Plan.severidades_desbloqueadas` y `Fact_Suscripcion.severidades_desbloqueadas` guardan **`idseveridad`**, no nombres. *(Ojo: los 5 planes tienen hoy el centinela `'null'` en `Dim_Plan`; hay que sembrarlos de verdad.)*
  3. La UI del Director de Estrategia ofrece las severidades del catálogo.
  4. Al cerrarse los tres puntos, **borrar `SEVERIDADES_POR_NIVEL`** de `consumo_datos_service.py`.

---

### 24. Datos de catálogo hardcodeados por todo el sistema, en vez de leerse de su tabla

- **Departamento:** transversal (los 9)
- **Detectado:** 2026-08-09, a raíz de la entrada #23
- **El patrón:** `Dim_Severidad` existía como tabla, estaba vacía, **nadie la leía**, y sus valores vivían duplicados en al menos tres sitios — el contrato OpenAPI (`enum: [1,2,3,4]`), las etiquetas en `frontend/src/app/modules/accidentes/severidad.constants.ts`, y una escala paralela en `catalogo_plan_service`. No es un descuido puntual: es una forma de trabajar que se repitió sin que nadie lo notara.
- **Por qué importa:** un catálogo duplicado **diverge en silencio**. Nadie se entera hasta que dos partes del sistema discrepan, y para entonces el dato equivocado ya viajó. En este caso concreto la consecuencia habría sido un partner recibiendo **cero accidentes** e interpretándolo como «no hubo ninguno».
- **Tarea pendiente:** **auditar todo el sistema en busca de datos de catálogo hardcodeados** —constantes de estado, tipos, severidades, roles, niveles— y para cada hallazgo decidir: (a) se lee de su tabla, (b) la tabla sobra y la constante es la fuente, o (c) hay un defecto de esquema que lo impide, como el de `Dim_Severidad.severidad` declarada métrica INT.
- **Sitios por los que empezar** (detectados de pasada, sin auditar aún):
  - `frontend/src/app/modules/accidentes/severidad.constants.ts` — etiquetas de severidad.
  - `apps/suscripciones/services/catalogo_plan_service.SEVERIDADES` — escala paralela.
  - `apps/partners/services/consumo_datos_service.SEVERIDADES_POR_NIVEL` — el puente de la entrada #23.
  - Las tablas `Dim_*` con **0 filas**: son candidatas a estar suplantadas por una constante en código. `Dim_EstadoIntegracion` estaba así hasta hoy.
- **Estado:** abierto. No bloquea nada en curso; se registra porque el patrón ya produjo dos defectos reales (#23 y este) y es razonable esperar más del mismo tipo.
- **Segundo hallazgo del mismo análisis, ya resuelto en código:** el spec dice leer las severidades de `Dim_Plan.severidades_desbloqueadas`, pero **los 5 planes sembrados tienen el centinela `'null'`** ahí. Leer de esa tabla daría conjunto vacío y, con el fail-closed, **ningún partner podría consumir nada**. El valor real vive en `Fact_Suscripcion.severidades_desbloqueadas` (`["Baja","Media"]`), que `alta_suscripcion_service` copia al contratar. Se lee de la suscripción, con el plan como respaldo — y además es lo semánticamente correcto: es lo que el cliente **contrató**, congelado, igual que el cupo de #07. *(Nota: `json.loads('null')` devuelve `None`, no una lista; iterarlo habría lanzado `TypeError` en producción.)*

---

### 22. `Fact_APIIntegracion.idestadointegracion` es redundante con `entorno`

- **Departamento:** Partners y API (#08 `api-monitoring-and-billing`)
- **Detectado:** 2026-08-09, al sembrar `Dim_EstadoIntegracion` (T006)
- **Contexto:** el catálogo debía tener tres estados. Se comprobó que **`Suspendido` es inalcanzable**: un partner suspendido recibe 403 y su llamada no se atiende, así que nunca se escribe una fila con ese estado (mismo motivo por el que un `429` tampoco genera fila, § 15 D2). Quedó **desactivado** (`activo = false`) con la razón en su descripción; el catálogo opera con 2 estados.
- **Lo que eso deja a la vista:** los dos estados que sí ocurren —`Pruebas activo` y `Producción activa`— **son exactamente la columna `entorno`**, que además es obligatoria en todo filtro (RN-APM-001). El FK `idestadointegracion` no aporta información que la fila no tenga ya.
- **Por qué NO se quitó:** el FK está definido en **`PortalPartnersAPI.md`**, el documento fuente del modelo de datos del departamento, que además da como ejemplo de valores *«Sandbox» o «Producción»* — o sea que la redundancia viene del diseño original, no de la spec derivada. Quitarlo implicaría 36 referencias en las specs de #08, 4 en el documento fuente, 7 en `esquemas.json`/`tablas.json`, recrear `Fact_APIIntegracion` en Pinot, y dejar `Dim_EstadoIntegracion` **sin ningún consumidor** (tabla y seed muertos). Deja de ser una limpieza técnica y pasa a ser una decisión de diseño del departamento, con impacto potencial en #09.
- **Decisión tomada (2026-08-09):** **se mantiene el FK.** Al registrar consumo se escribe el estado que corresponde al entorno de la credencial. Cuesta una línea y no bloquea nada.
- **Estado:** deuda aceptada y documentada. Si algún día se rediseña el modelo del departamento, este FK es candidato a desaparecer junto con `Dim_EstadoIntegracion`.

---

### 21. Dos archivos del working tree se revirtieron solos a HEAD durante una sesión de trabajo

- **Departamento:** transversal (herramientas / entorno de desarrollo)
- **Detectado:** 2026-08-09, al ejecutar la verificación manual del frontend de `partner-api-onboarding` (T088)
- **Qué pasó:** `frontend/src/app/app.routes.ts` y `frontend/src/app/shared/layout/nav-links.ts` aparecieron con su contenido de HEAD y `git status` limpio, con **mtime 19:55:20 ambos — el mismo segundo**, varias horas después de haber sido editados. El módulo `partners` seguía existiendo entero y compilando, pero quedó **inalcanzable**: sin entrada de rutas y sin enlaces en el sidebar.
- **Por qué importa:** ni `tsc --noEmit` ni los 461 tests de componente lo detectaron, porque cada pieza estaba correcta por separado; lo que faltaba era el enganche. Se descubrió por casualidad al abrir la app. Un módulo desconectado en silencio es exactamente el tipo de fallo que este proyecto no puede permitirse con una sola persona manteniéndolo.
- **Qué se descartó como causa** (verificado, no supuesto):
  - `git reflog` no registra ningún `checkout`, `reset` ni cambio de rama (último movimiento de HEAD: 2026-08-05). *Nota:* un `git restore <archivo>` no aparecería ahí, así que esto descarta cambios de rama, no un descarte por archivo.
  - No hay hooks en `.claude/settings.json` ni `.claude/settings.local.json`.
  - No hay git hooks activos en `.git/hooks/` (solo `.sample`).
  - Ningún script de `.specify/scripts/` ni de `.claude/` ejecuta `git checkout/restore/reset/stash/clean`.
  - **Auditoría de integridad completa:** ningún otro archivo se vio afectado — ni el código de backend, ni el resto del frontend (incluido `tabler-icon.component.ts`, que también es un archivo *tracked* modificado y sobrevivió), ni las specs. Solo esos dos.
- **Hipótesis más probable:** un descarte manual desde el panel de control de código del IDE sobre esos dos archivos seleccionados. El mismo segundo exacto en ambos apunta a una operación por lotes. **No confirmado.**
- **Mitigación ya aplicada:** `frontend/src/app/modules/partners/partners-cableado.spec.ts` (9 tests) convierte el fallo silencioso en un test rojo: comprueba que la entrada lazy sigue en `routes`, que el grupo «Partners y API» sigue en `NAV_LINKS`, que cada rol conserva sus enlaces y que consola y portal no se fusionan. Si el cableado vuelve a perderse, `ng test` lo dice.
- **Estado:** abierto en cuanto a la causa. El efecto está cubierto para `partners`; **los demás módulos no tienen un guardián equivalente**, así que un descableado silencioso en otro módulo seguiría sin detectarse.
- **Decisión pendiente:** ¿se generaliza el guardián de cableado a todos los módulos (un único spec que recorra `NAV_LINKS` y `routes` verificando que cada módulo con rutas tiene navegación y viceversa), o se deja acotado a `partners` por ser el caso conocido?

---

### 1. `Fact_NotificacionVentas.estado_envio` — columna en el esquema real que la spec dice que no existe

- **Departamento:** Ventas y CRM (`notificacion-ventas`)
- **Detectado:** 2026-08-07, auditoría de Ventas y CRM
- **Contexto:** `database/esquemas.json` define físicamente la columna `estado_envio` (STRING) en `Fact_NotificacionVentas`. Pero `specs/003-operational/Ventas-CRM/notificacion-ventas/backend/data-model.md:17` dice explícitamente *"No modela en Pinot: `estado_envio`"* — la decisión documentada fue no usarla. El código (`EvaluacionReglasDemoService`) nunca la escribe; al ser STRING nullable, Pinot no la exige y no rompe nada en runtime.
- **Por qué importa igual:** es una divergencia entre lo que dice la spec y lo que existe en el esquema real. Si en el futuro alguien lee `data-model.md` para entender qué hay en Pinot, se lleva una idea equivocada del esquema.
- **Opciones:**
  1. Eliminar la columna del esquema Pinot para que coincida con la decisión documentada (cambio de DDL real, requiere migración/recreación de tabla — más delicado).
  2. Actualizar `data-model.md` para reconocer que la columna existe físicamente aunque esté sin usar (cambio solo documental, sin riesgo).
- **Estado:** abierto, sin decidir.

### 8. `Dim_UnidadEmergencia.zonacobertura` — columna huérfana en el esquema Pinot real

- **Departamento:** Red Operativa (`alta-unidades`)
- **Detectado:** 2026-08-08, auditoría de Red Operativa
- **Contexto:** La spec (Session 2026-07-21) decidió eliminar `zonacobertura` de `Dim_UnidadEmergencia` por completo, reemplazándolo por `idcondado`. El código ya no la escribe (`unidad_emergencia_repository.py` solo la lee para mapeo legado). Pero la columna sigue presente tanto en `database/esquemas.json` como en el Pinot real — nunca se limpió.
- **Por qué no lo corregí solo:** quitar una columna de un schema Pinot ya usado requiere el mismo patrón destructivo que se usó para `Fact_Factura.id_factura` (borrar tabla+schema, recrear) — no vale la pena el riesgo por una columna inofensiva sin escritura activa, salvo que tú quieras la limpieza.
- **Opciones:**
  1. Dejarla como está (inofensiva, STRING nullable, sin escritura activa).
  2. Limpiarla del esquema real la próxima vez que se toque esa tabla por otro motivo (evitar una recreación solo para esto).
- **Estado:** abierto, baja prioridad.

### 11. RF-O56.3 y RF-O75.3 — sin validación de coherencia geográfica / proximidad en sitio

- **Departamento:** Emergencias (`registro-accidente`, `evidencia-unidad`, `seguimiento-cierre-de-casos`)
- **Detectado:** 2026-08-08, auditoría de Emergencias
- **Contexto:** Dos requisitos relacionados quedan sin resolver:
  1. **RF-O56.3** (catálogo) / advertencia `discrepancia_geografica` (documentada en el contrato OpenAPI de `registro-accidente`): el registro de accidente no compara la calle indicada (`idcalle`) contra la geocodificación inversa de las coordenadas GPS para advertir inconsistencias.
  2. **RF-O75.3** ("impedir el registro de clima/elementos físicos desde fuera del sitio") y su equivalente para escalar severidad (RF-O73.1, "con base en lo observado en el lugar"): no existe ninguna validación de que el Técnico de Campo o la Unidad estén físicamente en la ubicación del accidente al capturar estos datos.
- **Por qué no los corregí solo:** confirmaste explícitamente que el punto 2 (verificación de presencia en sitio) se deja para después ("hay un hueco... es algo que guardalo para solucionarlo después"). El punto 1 requiere decidir qué fuente de geocodificación usar y qué margen de tolerancia aplicar antes de advertir — no es una corrección mecánica.
- **Opciones para el punto 1 (RF-O56.3):** comparar `idcalle` contra `GeocodificacionInversaService.sugerir()` (ya existe, usado en otro flujo) con algún umbral de distancia/coincidencia a definir.
- **Opciones para el punto 2 (RF-O75.3/RF-O73.1):** validar proximidad GPS del dispositivo contra `Fact_Accidente.latitudinicio/longitudinicio` con un radio configurable; requiere que el cliente envíe su ubicación en cada captura, lo cual no está modelado hoy.
- **Estado:** abierto, diferido explícitamente por el usuario.

### 13. `EscalarTicketService` — sin guarda de estado antes de escalar

- **Departamento:** Soporte al Cliente (`gestion-tickets-soporte`)
- **Detectado:** 2026-08-08, auditoría de Soporte al Cliente
- **Contexto:** `EscalarTicketService.escalar()` (`backend/apps/soporte_cliente/services/escalar_ticket_service.py`) no valida `reclamo["estado"]` antes de permitir el escalado manual — a diferencia de `TomarTicketService`, `ResolverTicketService` y `ConfirmarCierreService`, que sí rechazan la transición si el ticket no está en el estado previo correcto (p. ej. `ResolverTicketService` exige `En_progreso`/`Escalado`). Tal como está, un ticket en cualquier estado (incluyendo `Cerrado`, `Pendiente_de_clasificacion` o ya `Escalado`) podría "escalarse" de nuevo.
- **Por qué no lo corregí solo:** el usuario pidió explícitamente dejarlo para después y revisar primero a qué se refiere exactamente ("dejemoslo para después y revisamos bien a que se refiere") — no se tocó `escalar_ticket_service.py` en esta pasada. Antes de decidir la guarda hay que aclarar: ¿desde qué estados debe permitirse escalar (`Abierto`+`En_progreso` únicamente, o también re-escalar desde `Escalado` a un nivel superior)? ¿Debe el catálogo (RF-O85.1/O85.2) reflejar esa restricción explícitamente, ya que hoy no la menciona?
- **Estado:** abierto, diferido explícitamente por el usuario.

### 18. El doble en memoria de `conftest.py` da confianza falsa sobre la capa de persistencia

- **Departamento:** transversal (afecta a los 9)
- **Detectado:** 2026-08-08, al migrar `Fact_Reclamo.idfactura` (entrada #17)
- **Contexto:** los 1042 tests del backend corren contra el doble en memoria de `backend/conftest.py`, que almacena diccionarios Python sin reproducir **ni los tipos declarados en `esquemas.json` ni los centinelas que Pinot aplica a los valores ausentes**. Consecuencia comprobada: la suite pasaba en verde **igual de bien con `Fact_Reclamo.idfactura` como INT que como STRING**, pese a que con INT el vínculo factura-disputa de RF-O83.2 **nunca podría haber funcionado** contra Pinot real (`Fact_Factura.id_factura` es un UUID). No es un caso aislado; los tres defectos encontrados esta sesión comparten la misma raíz y ninguno era detectable con mocks:
  - `Fact_Reclamo.idfactura` INT vs UUID (#17).
  - `planapi = NULL` materializado como el string `'null'`, que dejaba **siempre cierta** la guarda de RF-PON-004 (un partner sin plan podía emitir credenciales) (#15).
  - `fecha_expiracion = NULL` materializado como `Long.MIN_VALUE`, que habría hecho que un job de expiración **revocara todas las credenciales de producción** (#15).
- **Por qué importa:** el proyecto exige ≥80% de cobertura (RNF-18) y la suite en verde es la señal de "listo para desplegar". Hoy esa señal no cubre la frontera con Pinot, que es donde han aparecido los tres fallos más graves de la sesión. El test `test_doble_pinot_vs_esquemas.py` compara la **forma** (columnas) del doble contra `esquemas.json`, pero no los **tipos** ni el comportamiento ante ausencia de valor.
- **Mitigación provisional ya aplicada:** verificadores contra Pinot real en `database/` (`verifica_partners.py` 16 comprobaciones, `verifica_factura_reclamo.py` 15, `verifica_onboarding_e2e.py` 19). Son manuales y específicos de un cambio: no corren en la suite ni protegen a los demás departamentos.
- **Cerrado solo para el módulo #07 (2026-08-09):** `verifica_onboarding_e2e.py` ejerce los **servicios reales** del onboarding contra Pinot real —no solo el esquema— y pasa 19/19. Es el primer verificador que cubre *código* y no *forma*, y confirma que los tres defectos de #15/#17 están efectivamente corregidos en la base real. **La entrada sigue abierta** para los otros ocho departamentos: el patrón está demostrado, pero no aplicado fuera de Partners y API.
- **Opciones:**
  - **(A)** Extender `test_doble_pinot_vs_esquemas.py` para comparar también `dataType` y `defaultNullValue` de cada columna. Barato, automático, y habría cazado el caso `idfactura` INT→STRING. No cubre el comportamiento ante ausencia de valor.
  - **(B)** Que el doble de `conftest.py` **aplique los centinelas** al escribir: leer `defaultNullValue` de `esquemas.json` y sustituir los ausentes igual que Pinot. Cubre además los casos `planapi`/`fecha_expiracion`. Más trabajo y podría poner en rojo tests que hoy pasan — lo cual sería precisamente la señal buscada.
  - **(C)** Una suite de integración aparte contra el stack Docker, marcada con `@pytest.mark.integracion` y excluida por defecto. La más fiel, la más lenta y la que exige tener el stack arriba.
  - **(A+B)** combinadas cubren los tres defectos de esta sesión sin depender de Docker.
- **Estado:** abierto. No bloquea nada en curso; se registra porque los tres defectos ya encontrados sugieren que puede haber más del mismo tipo en departamentos ya dados por terminados.

---

## Resueltas

### 21. Reactivación selectiva de credenciales y frontera entre las dos suspensiones por mora

- **Resuelto:** 2026-08-08
- **Departamento:** Partners y API (`partner-access-management`, con efecto en `api-monitoring-and-billing`)
- **Contexto:** al especificar el último módulo del departamento aparecieron dos huecos de diseño que el SRS no resuelve. **Ninguna de las dos decisiones requirió cambio de esquema.**

**(D1) Cómo se reconstruye el conjunto de credenciales activas previo a una suspensión.** El SRS exige restituir «únicamente las que estaban activas antes de la suspensión — no se reactivan credenciales que el propio partner había revocado por seguridad» (L440). Pero la cascada pone **todas** a `activo=false`, y después las tres razones son **indistinguibles** mirando `Dim_CredencialAPI`: desactivada por cascada, revocada por el partner, o expirada por tiempo. Sin resolverlo, la reactivación **resucita una credencial comprometida**.

  - **Decisión:** la cascada inserta **una fila de bitácora por cada credencial que desactiva**, con su `idcredencial`, bajo un `tipo_cambio` nuevo: **`desactivacion_por_cascada`**. La reactivación lee las filas del último evento de suspensión y restituye exactamente ese conjunto.
  - **Por qué esta opción:** no inventa nada — `Fact_HistorialAccesoPartner.idcredencial` existe precisamente para eventos sobre credenciales concretas. Se descartó serializar la lista en un campo de texto (obligaría a parsear una estructura dentro de un campo libre) y una columna `desactivada_por_cascada` en `Dim_CredencialAPI` (más rápida de consultar, pero añade un flag de estado que hay que limpiar entre ciclos — y un flag mal limpiado es exactamente cómo se resucita una credencial comprometida).
  - **La propiedad que la hace segura:** una credencial que **ya estaba inactiva** al llegar la suspensión no genera fila de cascada, así que la reactivación **no la encuentra y no la restituye**. La regla de seguridad se cumple **por construcción**, no por una comprobación aparte que alguien pudiera olvidar al refactorizar.
  - **`desactivacion_por_cascada` es deliberadamente distinto de `revocacion_credencial`:** el primero se revierte al reactivar, el segundo **nunca**. Confundirlos sería el fallo.

**(D2) Frontera entre las dos suspensiones por mora.** `subscriptions-and-billing` **ya suspende** por mora (RF-SUSF-007, sobre `Fact_Suscripcion.estado`). Este módulo introduce una segunda suspensión sobre `Dim_Partner.activo`. Sin frontera clara, o un cliente moroso sigue consumiendo gratis, o se le suspende dos veces por lo mismo.

  - **Decisión:** **independientes por origen.** Este módulo suspende **solo** por facturas `tipo='excedente_api'` impagadas más de 15 días; la suscripción impagada la sigue gestionando Suscripciones. **El acceso a la API exige ambas condiciones a la vez**, y lo comprueba el middleware de consumo de `api-monitoring-and-billing`.
  - **Por qué no se arrastran:** Suscripciones **reactiva automáticamente** tras el cobro (RN-SUSF-011), pero en Partners **el sistema nunca reactiva solo** (RN-PAC-009). Si una suspensión arrastrase a la otra, ambos estados quedarían en contradicción permanente. La opción de arrastre se descartó por ese conflicto concreto, no por complejidad.
  - **Por qué no una regla única de mora:** duplicaría la lógica que Suscripciones ya tiene, con umbrales distintos (15 días aquí, `Fallida` allá): dos módulos suspendiendo por la misma factura en momentos distintos.
  - **Cierra un hueco real que existía:** el middleware de #08 solo comprobaba `Dim_Partner.activo`, así que **nada impedía que un cliente con la suscripción suspendida siguiera consumiendo la API**. Añadir la comprobación de suscripción vigente quedó como **tarea T024b** en `api-monitoring-and-billing`, y su RF-APM-001 y RN-APM-007 se actualizaron.

- **Documentación actualizada:** `partner-access-management/backend/spec.md` (§ 15 D1 y D2, RF-PAC-006, RF-PAC-007, RF-PAC-008 con los seis `tipo_cambio`) y su `checklists/requirements.md`; `api-monitoring-and-billing/backend/spec.md` (RF-APM-001, RN-APM-007) y su `tasks.md` (T019 ampliada, T024b nueva); `module-map.md`.
- **Pendiente derivado:** ninguno abierto. T024b está registrada en las tareas de #08.

### 20. Tarifa de excedente de API y naturaleza del límite por minuto

- **Resuelto y aplicado:** 2026-08-08
- **Departamento:** Suscripciones y Facturación (habilitante de Partners y API CU-O54)
- **Contexto:** al especificar `api-monitoring-and-billing` aparecieron dos huecos que impedían cerrar la spec.

**(1) No existía la tarifa de excedente.** RF-O54.1 exige «calcular el importe del consumo según la tarifa vigente del plan», pero `Dim_Plan` no tenía dónde guardarla: su columna `precio` es el importe de la **suscripción mensual**, no el precio unitario del excedente. Sin ese dato, CU-O54 no podía calcular ningún importe y la línea de ingresos por consumo seguía sin ser exigible.

  - **Decisión:** columna `precio_excedente_llamada` (DOUBLE) en `Dim_Plan`, configurable por el **Director de Estrategia** (CU-O26 / RF-O26.1). Mismo actor y mismo criterio que `api_calls_minuto` (#19): es un parámetro de negocio, no una constante (RNF-20). Se descartó una tabla de tramos por volumen (flexible pero no pedida por el negocio; migración natural si hiciera falta) y derivarla del precio del plan (haría que el excedente saliera al mismo precio unitario que el consumo ya pagado, sin margen).
  - **Centinela `-1.0` = «sin tarifa configurada», nunca `0.0`.** Un cero significa «excedente gratis» y el corte emitiría facturas de importe cero sin que nadie lo note: ingreso real no cobrado en silencio, justo lo que prohíbe la regla del SRS de que «una factura de excedente nunca debe quedar silenciosamente sin crearse». Con `-1.0`, CU-O54 distingue gratis (decisión legítima) de sin configurar (error) y **alerta en vez de facturar mal**.
  - **Los valores iniciales se derivan del precio unitario real de cada plan** (`precio / api_calls_mes` × 1,25), **no del nivel**. La primera versión sí usaba el nivel y la simulación la descartó: «Magnifico» es nivel Empresarial con solo 100 llamadas/mes, así que por nivel le tocaba $0,005 cuando su consumo incluido cuesta $1,20/llamada — el excedente habría salido **240 veces más barato que el cupo** y al partner le habría convenido pasarse. Resultado final: Básico $0,06 · Profesional $0,02 · Empresarial $0,005 · Plan Remediation Demo $0,25 · Magnifico $1,50, todos entre ×1,22 y ×1,34 sobre el incluido.
  - **Alcance:** esquema, validación en `CatalogoPlanService` (obligatorio al crear, validado al editar, rechaza negativos porque `-1.0` es centinela), campo «Excedente API (USD/llamada)» en el formulario de plan, tipos `Plan`/`PlanRequest`/`PlanPatchRequest`, seeds, doble de tests y los 5 planes migrados. Script `database/migra_tarifa_excedente.py` (idempotente, `--dry-run`, respaldo releído antes de tocar nada).

**(2) El límite por minuto no tenía efecto definido.** El SRS exige límite «mensual y por minuto» (L376, L408) pero también declara que superar la cuota **nunca bloquea** (RN-11, L406). Un tope por minuto que no corta y que solo se factura al mes no se distingue del mensual.

  - **Decisión:** son **dos mecanismos distintos** y el SRS los mezcla. El **cupo mensual** es compromiso comercial y no bloquea nunca (RN-11 intacta); la **tasa por minuto** es el **throttle técnico** del partner y devuelve **HTTP 429**, como protección de plataforma. Coherente con `api-standards.md`, que ya declara throttling DRF como estándar.
  - **Consecuencia contable:** una petición rechazada con 429 **no se atendió**, así que **no es consumo facturable**. Se registra en `Fact_LogLlamadaAPI` con su código —para que el partner vea que le limitan— pero no suma en `Fact_APIIntegracion`. Facturar peticiones no servidas sería cobrar de más.
  - **Limitación de infraestructura declarada:** el proyecto **no tiene Redis ni caché distribuida** (Django usa `LocMemCache`, por proceso). Con un solo proceso el throttle es fiable; al escalar horizontalmente el límite efectivo se multiplicaría por el número de procesos. **No bloquea hoy**, pero queda como deuda: escalar exigirá un contador compartido.
  - **Pendiente derivado menor:** añadir un throttle rate por partner en `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES` (hoy hay tres, ninguno de partners). Se resuelve en `/speckit-tasks`.

- **Verificación:** 5/5 planes con tarifa confirmados en Pinot por el propio script; backend **1042 passed, 2 skipped**; frontend **316/316**.
- **Documentación actualizada:** `api-monitoring-and-billing/backend/spec.md` § 15 (D1 y D2) y su `checklists/requirements.md`; `subscriptions-and-billing/backend/spec.md` (**RN-SUSF-030** nueva) y su `data-model.md`; **`TSI-Catalogo-CU-RF-RNF.md`** RF-O26.1, que no recogía ni la tarifa ni el límite por minuto.
- **Divergencia que queda abierta a nivel de catálogo:** RF-O53.2 dice «restringir o degradar el servicio al superarse el límite»; el SRS lo prohíbe para el cupo comercial. Se implementa el SRS y **el catálogo debería corregirse** en una pasada aparte.

### 19. Rol `PartnerIntegracion` y límite de llamadas por minuto configurable

- **Resuelto y aplicado:** 2026-08-08
- **Departamentos:** Cuentas y Clientes (RBAC) + Suscripciones y Facturación — ambos habilitantes de Partners y API
- **Qué se hizo:**
  - **Rol `PartnerIntegracion` (idrol 15).** El SRS define «Partner de integración» como actor propio (L121: *«Área técnica de un cliente integrador»*; L820: matriz de responsabilidades), pero ninguno de los 14 roles existentes lo cubría: **un partner no tenía forma de autenticarse** y todo el autoservicio de CU-O49 era inalcanzable. Creado en `backend/scripts/_demo_seed_common.py` (fuente única de `Dim_Rol`) y desplegado.
    - **Por qué no se reutilizó `Cliente` (idrol 1):** todo partner pertenece a un cliente (`Dim_Partner.idcliente` es obligatorio), pero son **personas distintas de la misma organización con permisos distintos**. Darle `Cliente` al partner le abriría la facturación de su empresa; darle `PartnerIntegracion` al titular le quitaría su portal. Tampoco servía `DesarrolladorAPIs` (idrol 5), que es el equipo **de TSI** que registra partners, no quien consume.
    - **Corrección asociada:** la descripción del idrol 5 decía *«Consumo de integraciones via API»* — describía al partner, no al desarrollador, y confundía ambos actores. Ahora dice *«Equipo tecnico de integraciones: registra partners, asigna planes y vigila consumo»*, conforme al SRS L124.
  - **`api_calls_minuto` en `Dim_Plan.limites`.** El SRS §3.4.1 (L376) y §3.4.2 (L408) exigen que el plan defina el límite de llamadas **mensual y por minuto**; solo existía el mensual, así que RF-PON-003 de Partners no tenía de dónde derivar `Dim_Partner.limitellamadasminuto` y habría devuelto 422 siempre.
    - **Implementado como parámetro configurable, no como constante.** La pregunta inicial era «¿qué valor le ponemos a cada plan?», y la respuesta correcta resultó ser otra: **quién lo decide**. El catálogo de planes lo administra el **Director de Estrategia** (SRS L293, L802) vía **CU-O26 / RF-O26.1**, así que el campo se añadió al flujo de crear/editar plan en lugar de fijarse en código — coherente con RNF-20 y con el tratamiento que ya tienen `severidades_desbloqueadas` y `carga_lote_habilitada`.
    - **Backend:** validación en `CatalogoPlanService._validate_limites` (ahora exige las 4 claves). **Frontend:** campo «API calls / minuto» en el formulario de plan, tipo `PlanLimites`, y visualización en las vistas de catálogo y detalle. **Datos:** los 5 planes sembrados con valores iniciales por nivel (Básico 30, Profesional 120, Empresarial 600), reconfigurables desde la UI.
    - El límite por minuto **no es un prorrateo del mensual**: protege contra ráfagas. Por eso 1.000 llamadas/mes no implican 0,02/minuto.
- **Verificación:** backend **1042 passed, 2 skipped**; frontend **316/316**; rol y planes confirmados en Pinot por el propio script de migración. Respaldo de `Dim_Plan` verificado antes de publicar.
- **Documentación actualizada:** `.specify/docs/actors.md` (dos actores diferenciados), `autenticacion-y-rbac/backend/spec.md` (catálogo de roles + nota de por qué no se reutiliza `Cliente`), `subscriptions-and-billing/backend/spec.md` y su `data-model.md` (RN-SUSF-019), y en Partners y API: `spec.md`, `checklists/requirements.md`, `traceability.md` y `tasks.md` (T006 y T007 cerradas).
- **Script:** `database/migra_rol_partner_y_limite_minuto.py` (idempotente, con `--dry-run` y respaldo verificado).
- **Pendiente derivado:** ninguno. `partner-api-onboarding` ya no tiene dependencias externas abiertas.

### 17. Vínculo factura-disputa — `Fact_Factura.tipo` y `Fact_Reclamo.idfactura` INT → STRING

- **Resuelto y aplicado:** 2026-08-08
- **Departamentos:** Suscripciones y Facturación + Soporte al Cliente (habilitantes de Partners y API CU-O54)
- **Qué se hizo:**
  - **`Fact_Factura` += `tipo` (STRING, default `'suscripcion'`).** RF-O54.3 exige verificar que no exista ya una factura de excedente para el mismo partner y período antes de emitir; sin discriminador esa consulta es imposible y un reintento sobre un proceso que sí llegó a emitir generaría un **doble cobro** — el error que el SRS señala como peor que no cobrar. El default es `'suscripcion'` porque el código de facturación actual no escribe la columna y todas sus facturas son de suscripción: sigue siendo correcto sin tocarlo, y una factura mal escrita nunca se cuela como excedente (falla hacia el lado seguro).
  - **`Fact_Reclamo.idfactura` INT → STRING** (default `""`). `Fact_Factura.id_factura` es un **UUID** (`str(uuid.uuid4())` en `backend/core/repositories/suscripciones/factura_repository.py:84`), de modo que el vínculo implementado en #14 **nunca habría enlazado**: un UUID no cabe en un INT. Se comprobó la dirección correcta antes de migrar — cambiar `Fact_Factura.id_factura` a INT no era opción.
  - **Código corregido:** `soporte_cliente/views.py` (parseo `int()` → `str()` con su mensaje de error), `registrar_ticket_service.py` (firma y dos conversiones), `reclamo_repository.py` (firma y comparación tolerante a centinelas), el contrato OpenAPI de Soporte y los dos tests de contrato, que ahora usan un UUID real en vez de `42`.
- **Riesgo encontrado y cómo se manejó:** Pinot no permite cambiar el tipo de una columna, así que había que **recrear `Fact_Reclamo`** — que tenía **8 tickets reales**. Al verificar los offsets de Kafka se descubrió que **`Fact_Reclamo_topic` estaba purgado** (offset inicio == offset final == 16): las filas vivían **solo en Pinot**, y recrear la tabla sin más las habría destruido. `migra_factura_reclamo.py` exporta y **relee** el respaldo antes de tocar nada (aborta si no coincide), recrea y republica. Comparación posterior campo a campo contra el respaldo: **0 diferencias** en las columnas no migradas. `Fact_Factura` estaba vacía, así que su recreación no arrastró datos.
- **Verificación:** `database/verifica_factura_reclamo.py` → **15/15 correctas** (incluye persistir una factura con id UUID sin truncar, la consulta de no-duplicación de RF-O54.3, y que una factura sin `tipo` caiga en `suscripcion` y no contamine la consulta de excedentes). Suite del backend: **1042 pasan, 2 saltados**; Soporte: 99 pasan. 79 tablas declaradas = 79 desplegadas. Recuentos finales: `Fact_Reclamo` 8, `Fact_Historial_Ticket` 9, `Fact_Factura` 0.
- **Por qué hacía falta un verificador aparte:** los tests del backend corren contra el doble en memoria de `conftest.py`, que **no reproduce los tipos del esquema ni los centinelas de Pinot**. Pasaban en verde con `idfactura` INT y con `idfactura` STRING por igual. Este defecto solo era visible contra Pinot real.
- **Documentación actualizada:** `gestion-tickets-soporte/backend/data-model.md`, su `spec.md` y su contrato OpenAPI.
- **Pendiente derivado:** ningún flujo escribe todavía `Fact_Factura.tipo = 'excedente_api'`; lo hará CU-O54 en `api-monitoring-and-billing`. Las facturas de suscripción existentes no necesitan cambio (toman el default).

### 15. Partners y API — CU-O50 sin modelo de datos, y `comparisonColumn` roto en las dimensiones mutables

- **Resuelto:** 2026-08-08
- **Departamento:** Partners y API (los tres módulos)
- **Contexto inicial:** el catálogo canónico define **CU-O50** («Consultar el contrato de integración vigente y su documentación») con tres RF: exponer la versión vigente (RF-O50.1), mantener accesibles las versiones anteriores aún soportadas (RF-O50.2) y señalar la fecha de retiro planificada de cada una (RF-O50.3). Ni el SRS §3.4 ni `PortalPartnersAPI.md` mencionan este CU, y no existía tabla que lo soportara: `Dim_Servicio` no tiene campos de versión ni de retiro.
- **Qué se decidió (D1 — `Dim_VersionContratoAPI`):** tabla nueva con `idversion` (PK sustituta), **`id_servicio` (FK obligatoria a `Dim_Servicio`)**, `version`, `estado` (`vigente`|`soportada`|`retirada`), `spec_url` (nullable), `fecha_publicacion`, `fecha_retiro` (nullable), `activo`, `fecha_actualizacion`. Configuración idéntica a `Dim_Servicio`: `REALTIME`, topic `Dim_VersionContratoAPI_topic`, `upsert FULL` con `comparisonColumn=fecha_actualizacion`.
  - **La FK a `Dim_Servicio` se añadió tras la revisión de normalización pedida por el usuario**, y no estaba en la propuesta original. `Dim_Servicio` **no** es un registro único: contiene tres servicios (*API Despacho*, *API Registro de accidentes*, *Portal Cliente*, sembrados por `backend/scripts/seed_catalogos_soporte.py`) y `Fact_APIIntegracion.idservicio` ya discrimina el consumo por servicio. Sin la FK, el versionado de los tres servicios habría colapsado en una sola línea temporal — la misma pérdida de la relación 1:N que hacía inviable la alternativa de extender `Dim_Servicio`.
  - Verificado 1FN/2FN/3FN: sin atributos multivaluados, PK simple, sin dependencias transitivas. Clave natural (`id_servicio`, `version`) única entre filas activas, e invariante «máximo una versión `vigente` por servicio», ambas a nivel de aplicación porque Pinot no soporta `UNIQUE`.
  - Dos puntos documentados para que no se lean como redundancia: `activo` es la baja lógica de la fila (RNF-14) y `estado` es el ciclo de vida de la versión — una versión `retirada` conserva `activo=true` para que su historial siga consultable; y `estado` se deja como STRING en vez de FK a un catálogo propio por ser un enum cerrado de tres valores (mismo criterio que `Fact_Factura.estado_pago` y `Dim_CredencialAPI.entorno`).
- **Qué se descubrió de paso (D2 — Pinot no almacena NULL):**
  - **Hipótesis inicial, REFUTADA:** se planteó que el `comparisonColumn` del upsert (`sandbox_activado` en `Dim_Partner`, `fecha_creacion` en `Dim_CredencialAPI`) descartaría las mutaciones en silencio, porque esas fechas no cambian en un UPDATE. **Es falso:** Pinot compara con `>=`, no con `>`. Se comprobó ejecutando el ciclo completo contra Pinot en vivo (registro → asignar plan → activar sandbox → suspender por mora) y los cuatro pasos se aplicaron. Queda constancia porque llegó a documentarse como bloqueante antes de validarse.
  - **Problema real encontrado al hacer esa prueba:** **ninguna de las 78 tablas del proyecto habilita `nullHandlingEnabled`**, de modo que Pinot no almacena `NULL` — cada valor nulo publicado se materializa como un centinela elegido por Pinot. Medido: `planapi` → `'null'` (string literal de 4 letras, **no** vacío); `limitellamadasmes` → `0`; `sandbox_activado` (columna de tiempo) → un timestamp arbitrario en el pasado; `sandbox_expiracion` → `Long.MIN_VALUE`.
  - **Impacto en reglas de negocio:** (a) la precondición de RF-PON-004 «`planapi` no nulo» era **siempre cierta**, así que un partner sin plan podía emitir credenciales; (b) `limitellamadasmes = 0` es indistinguible de «sin plan», con lo que CU-O54 facturaría todo el consumo como excedente; (c) el más grave, `fecha_expiracion = NULL` para producción se guardaría como `Long.MIN_VALUE` y un job que busque `fecha_expiracion < ahora` daría por vencidas **todas** las credenciales de producción del sistema. Ninguno de los tres se ve en pruebas con mocks: solo aparecen contra Pinot real.
  - **Decisión: centinelas explícitos por columna** (`defaultNullValue`), elegidos para ser imposibles como dato real y para que las consultas de negocio funcionen sin casos especiales: `planapi=""`, límites `=-1`, `sandbox_*=0`, `Fact_HistorialAccesoPartner.idcredencial=-1`, y `fecha_expiracion=253402300799000` (9999-12-31, **deliberadamente en el futuro** para que «no expira nunca» no sea alcanzable por un job de expiración). Se descartó habilitar el manejo de NULL solo en este departamento, porque introduciría una segunda convención frente a los otros ocho (RNF-17; Maintainability como prioridad por defecto de la constitución).
  - **Corrección adicional real:** `Dim_Partner.timeColumnName` apuntaba a `sandbox_activado`, una columna **opcional** vacía hasta la activación de pruebas. La columna de tiempo de Pinot gobierna segmentos y retención y debe estar siempre poblada: ambas dimensiones pasan a `fecha_actualizacion`, como el resto de dimensiones mutables. El `comparisonColumn` se alinea por robustez (la última escritura gana sin depender de empates).
- **Cómo se aplicó:** Pinot no permite cambiar `timeColumnName` ni `upsertConfig` en caliente, así que hubo que borrar y recrear las tablas — viable sin migración porque las cuatro estaban **vacías (0 filas)**. Tres scripts nuevos en `database/`: `migra_partners_esquema.py` (idempotente, con `--dry-run`), `despliega_partners.py` (se **niega** a borrar tablas con filas salvo `--forzar`) y `verifica_partners.py` (16 comprobaciones que reproducen las reglas que estaban rotas).
- **Verificación:** 16/16 comprobaciones correctas; suite del backend en verde (1042 pasan, 2 saltados previos); `test_doble_pinot_vs_esquemas.py` en verde; 79 tablas declaradas = 79 desplegadas; las 4 tablas del departamento en 0 filas.
- **Dos aprendizajes operativos, no evidentes:**
  1. Recrear una tabla Pinot la hace **re-consumir su topic Kafka desde el principio** (`auto.offset.reset: smallest`): las filas «borradas» reaparecen. Para vaciarla de verdad hay que purgar el topic con `kafka-delete-records` antes de recrearla.
  2. Tras un `DELETE`, Pinot tarda en retirar la *external view* y recrear la tabla devuelve `409` durante unos segundos. No hay endpoint para consultarlo; `despliega_partners.py` reintenta con espera.
- **⚠️ `database/` está en `.gitignore` y no se versiona.** Los cambios de esquema no tienen respaldo en git. Conviene sacarlo del ignore o respaldar a mano antes de tocar `esquemas.json` / `tablas.json`.
- **Estado:** D1 y D2 **resueltos y aplicados**, documentados en `partner-api-onboarding/backend/spec.md` § 15. Ninguno bloquea ya `/speckit-plan` ni `/speckit-implement` de este módulo.

### 16. Partners y API — renumeración canónica de CU y cuatro correcciones de esquema

- **Resuelto:** 2026-08-08
- **Departamento:** Partners y API (los tres módulos) + impacto en Soporte al Cliente y Suscripciones y Facturación
- **Qué se hizo:**
  - **Renumeración completa de CU.** `PortalPartnersAPI.md` y `module-map.md` usaban CU-O71–O84, números que en el catálogo limpio (`TSI-Catalogo-CU-RF-RNF.md` §5.5) pertenecen a **Emergencias** y están **vigentes** allí (CU-O71 abortar misión, CU-O72 cancelar caso despachado, CU-O73 escalar severidad) — mismo tipo de colisión que motivó la renumeración de Soporte (#14). La numeración canónica del departamento es **CU-O48–CU-O55** (8 CU). Mapeo legacy → canónico: O71+O80 → **O48**; O72 → **O49**; (nuevo) → **O50**; (nuevo) → **O51**; O74 escritura + O73 métricas + O75 reporte → **O52**; O74 alertas → **O53**; O78+O83 → **O54**; O84+O81+O79+O76 → **O55**. El legacy CU-O82 (disputa) **no** recibe CU en Partners: ya vive como RF-O83.2 en Soporte y está implementado.
  - **Jerarquía de fuentes fijada:** SRS §3.4 manda en reglas de negocio; el catálogo aporta numeración y RFs; `PortalPartnersAPI.md` queda reducido a mapeo INSERT/UPDATE a tablas Pinot. El SRS resuelve cuatro de los cinco gaps que Portal dejaba marcados como 🔎 Inferido (1:1 cliente-partner, vencimiento de pruebas, rechazo de promoción, credenciales múltiples nombradas) y corrige la política de reintentos de facturación asumida por Portal (3×1h → **1h/6h/24h**).
  - **Conflicto catálogo vs SRS resuelto a favor del SRS:** RF-O53.2 del catálogo dice «restringir o degradar el servicio al superarse el límite», pero RN-11 y el SRS §3.4.2 declaran explícitamente que **superar la cuota nunca bloquea el servicio** — decisión de modelo comercial *pay-as-you-go*, documentada en el SRS "precisamente para que nadie la corrija asumiendo que debería bloquear". Se implementa el SRS; RF-O53.2 queda como divergencia documentada y el catálogo debería corregirse.
  - **Alcance ampliado a los 8 CU:** CU-O50 y CU-O51 están en el catálogo pero no en el SRS §3.4 ni en Portal. Se especifican igual (O50 en `partner-api-onboarding`, O51 en `api-monitoring-and-billing`) para que el departamento no tenga huecos frente al catálogo. El modelo de datos de CU-O50 queda abierto en la entrada #15 de arriba.
  - **Cuatro correcciones de esquema aprobadas** (⏳ decididas, **pendientes de aplicar** a `database/esquemas.json` y al código):
    1. `Dim_CredencialAPI` += `nombre_credencial` (STRING). RF-O49.1 y el SRS L372/L388 exigen credenciales nombradas por sistema; la tabla no tenía dónde guardarlo. Cambio aditivo.
    2. `Dim_CredencialAPI` += `fecha_expiracion` (LONG). `Dim_Partner.sandbox_expiracion` es una sola fecha, pero pueden coexistir varias credenciales de pruebas nombradas con vencimientos distintos. La expiración pasa a ser por credencial; los campos de `Dim_Partner` quedan como snapshot de la primera activación.
    3. `Fact_Factura` += `tipo` (STRING: `suscripcion` | `excedente_api`). RF-O54.3 exige verificar que no exista ya una factura de excedente para el mismo partner y período antes de emitir; sin discriminador esa consulta es imposible y un reintento podría generar doble cobro.
    4. `Fact_Reclamo.idfactura` **INT → STRING**. `Fact_Factura.id_factura` es STRING, así que el vínculo factura-disputa implementado en #14 no enlaza por tipo. Requiere corregir `RegistrarTicketService.registrar()` (los `int(idfactura)` de `backend/apps/soporte_cliente/services/registrar_ticket_service.py`), `ReclamoRepository.find_disputa_abierta_por_factura()`, el contrato OpenAPI de Soporte y sus tests.
  - **Extensión del JSON `Dim_Plan.limites`** (RN-SUSF-019): += `api_calls_minuto` (INT ≥ 0). Hoy solo declara `api_calls_mes`, pero el SRS exige límite mensual **y** por minuto, y RF-O48.3 deriva ambos del plan contratado. Es extensión del contrato JSON, no columna Pinot. Requiere actualizar `subscriptions-and-billing/backend/spec.md`.
  - **Rol nuevo:** «Partner de integración» debe darse de alta en el catálogo de roles de `autenticacion-y-rbac`.
  - Actualizados `module-map.md` (§4 y el índice rápido) y creados `partner-api-onboarding.md`, `backend/spec.md`, `backend/checklists/requirements.md` y el stub `frontend/spec.md`.
- **Pendiente de esta decisión:** aplicar los cinco cambios de esquema/JSON antes de `/speckit-implement`, y resolver la entrada #15 antes de `/speckit-plan`.

### 2. Renumeración de CU en documentos secundarios de Cuentas y Clientes

- **Resuelto:** 2026-08-08
- **Qué se hizo:** Se completó la renumeración en los 17 documentos secundarios restantes (`plan.md`, `tasks.md`, `quickstart.md`, `research.md`, `data-model.md`, contratos `*.openapi.yaml`, incluyendo los 3 archivos de frontend de `incorporacion-clientes` que se habían pasado por alto en la primera pasada) de los tres módulos. Se agregó una nota de cabecera en cada archivo explicando la corrección y distinguiendo explícitamente las capacidades retiradas (registro directo, config. plan+logo — sin CU vigente) del CU-O12 vigente (reenviar invitación), que colisionaban en texto tras el renombrado automático.

### 3. Prospectos de Ventas y CRM creados por "entrada directa" quedan sin usuario administrador

- **Resuelto:** 2026-08-08
- **Qué se hizo:** `EntradaDirectaService` (Ventas y CRM, CU-O96) ahora crea el usuario admin local, su credencial temporal, le asigna el rol `Cliente` y le envía la invitación — mismo mecanismo que `AutorregistroProveedorService`. Se actualizó el contrato de la API (`admin_local` ahora requerido), el formulario de frontend (`entrada-directa.page.ts`) con una sección "Administrador local", y las specs de Ventas y CRM (`commercial-pipeline-prospects` backend y frontend) documentando la corrección.

### 5. Suscripciones y Facturación — `periodicidad`, esquema de `id_factura`, consultas sin filtro y renumeración de CU

- **Resuelto:** 2026-08-08
- **Qué se hizo:**
  - **`periodicidad` implementada de extremo a extremo** (el SRS §3.3.1 la exige — "Cada plan tiene nombre, nivel, precio, periodicidad y límites" — y estaba completamente ausente de spec, código y datos sembrados). Ahora es campo obligatorio del plan (`Mensual`/`Anual`), se propaga a la suscripción en el alta y en cada cambio de plan aprobado, y determina la duración real del ciclo (`add_cycle`) en vez de asumir siempre 1 mes. Se corrigió también el precio mostrado en el catálogo (antes decía "/ mes" siempre, hasta para planes anuales) en ambos catálogos públicos (Suscripciones y Ventas-CRM).
  - **`Fact_Factura.id_factura`** corregido de `INT` a `STRING` en `database/esquemas.json` (ver entrada #4 arriba para lo que falta verificar contra un Pinot real).
  - **`FacturaRepository`** ya no escanea la tabla completa: `list_by_cliente`, `find_by_suscripcion_periodo` y el cálculo de `seq` de `numero_factura` ahora filtran a nivel Pinot (`WHERE`), igual que ya hacía `PlanRepository`.
  - **CU renumerados** de la numeración interna de la spec (`CU-O10x`/`CU-O11x`) al catálogo vigente (`CU-O26`–`CU-O38`) en `spec.md`, `data-model.md`, `tasks.md`, `quickstart.md`, el contrato OpenAPI, y el índice del módulo.
  - **Aclaración sobre "2 tipos de planes":** verificado — **no es un bug**. El SRS es explícito en que existe **un solo catálogo** con un bloque de límites que cubre tanto flota (Proveedor) como consultas (consumidor de datos) en el mismo plan. El seed real (`backend/scripts/seed_planes_publicos.py`) y los fixtures de test ya reflejan esto correctamente: cada plan trae `unidades_max`, `usuarios_max` y `api_calls_mes` juntos. No había que crear un segundo catálogo.
  - 3 tests nuevos de `periodicidad`; suite completa backend (1021 tests) y frontend (`tsc`) en verde.

### 6. `Dim_Plan.nivel` no se congela en `Fact_Suscripcion` (a diferencia de `precio`, que sí) + severidad debía ser configurable, no derivada de `nivel`

- **Resuelto:** 2026-08-08
- **Decisión del usuario:** severidad debe ser un campo **totalmente configurable**, no derivado de `nivel` ("puede que haya planes con bastantes usuarios pero desbloqueas pequeñas severidades, es mejor que sea Configurable totalmente"); y `nivel`/severidades deben congelarse en `Fact_Suscripcion` igual que `precio` ("mismo patrón, consistente").
- **Qué se hizo:**
  - **SRS §3.3.1 y catálogo RF-O26.2** corregidos: `severidades_desbloqueadas` es un dato independiente en `Dim_Plan`, configurable libremente por el Director de Estrategia al crear/editar un plan — ya no se deriva automáticamente de `nivel`.
  - **`CatalogoPlanService`** valida `severidades_desbloqueadas` como lista no vacía, subconjunto de `{Baja, Media, Alta}`, ahora obligatoria al crear un plan.
  - **`PlanRepository`** persiste `severidades_desbloqueadas` (JSON-encoded, mismo patrón que `limites`).
  - **Congelamiento en `Fact_Suscripcion`:** `nivel` y `severidades_desbloqueadas` ahora se copian desde `Dim_Plan` al alta (`AltaSuscripcionService`) y se resincronizan solo en un cambio de plan explícito y aprobado (`CambioPlanService.aprobar`) — exactamente el mismo patrón que ya existía para `precio`. Una edición posterior de `Dim_Plan` ya no altera retroactivamente una suscripción vigente.
  - **`consulta_planes_publicos_service.py`** (Ventas y CRM): se eliminó el mapa de derivación `nivel → severidades`; ahora lee/parsea `Dim_Plan.severidades_desbloqueadas` directamente.
  - **`database/esquemas.json`**: se agregó `severidades_desbloqueadas` a `Dim_Plan`, y se agregaron `nivel` + `severidades_desbloqueadas` a `Fact_Suscripcion` (esta tabla no tenía `nivel` en absoluto).
  - **Frontend:** tipos (`suscripciones.types.ts`), formulario de plan (`plan-form.page.ts/html`, checkboxes de severidad independientes del nivel) y vistas de catálogo/detalle actualizados para mostrar y editar `severidades_desbloqueadas`.
  - **Specs actualizadas:** `subscriptions-and-billing` (`spec.md` RN-SUSF-002/006, `data-model.md`, contrato OpenAPI) y `commercial-pipeline-prospects` (`spec.md`, `data-model.md`, `research.md` Decision 10, `plan.md`, `tasks.md`, contrato OpenAPI) — se corrigieron todas las menciones al mapa cerrado `nivel→severidades`.
  - Suite completa backend (1022 tests) y frontend (`tsc` app + spec) en verde.

### 4. `Fact_Factura.id_factura` — el esquema del archivo se corrigió, pero un Pinot ya desplegado con el tipo viejo no se migraba solo

- **Resuelto:** 2026-08-08
- **Decisión del usuario:** aplicar el cambio contra el Pinot real ya levantado ("cambiale a string para recrear el codigo de la factura de manera correcta").
- **Qué se hizo:**
  1. Verifiqué contra el Controller real (`http://localhost:9000`) que la tabla `Fact_Factura` seguía con `id_factura`/`id_factura_original` en `INT` y tenía **0 filas** (sin riesgo de pérdida de datos).
  2. Borré la tabla `Fact_Factura_REALTIME` (`DELETE /tables/Fact_Factura?type=realtime`) y el schema asociado (`DELETE /schemas/Fact_Factura`) — Pinot no permite cambiar el tipo de una columna del `primaryKeyColumn` sobre un schema/tabla existente ("Backward incompatible schema... Only allow adding new columns").
  3. Recreé el schema desde `database/esquemas.json` (ya corregido a `STRING` para ambas columnas) con `POST /schemas`.
  4. Recreé la tabla `Fact_Factura_REALTIME` con exactamente la misma configuración que tenía antes (mismo topic Kafka `Fact_Factura_topic`, upsert `FULL`, replicación 1) usando `POST /tables`.
  5. Verifiqué con una consulta SQL real que `id_factura`/`id_factura_original` ya son `STRING` y la tabla sigue consumiendo del mismo topic.
- **Estado:** cerrado — archivo de esquema y Pinot real ya coinciden.

### 9. Red Operativa — baja forzada sin control de Administrador, gmail obligatorio indebido, aprobación de región sin Director Tecnológico

- **Resuelto:** 2026-08-08
- **Qué se hizo:**
  - **Baja forzada exclusiva de Administrador (RF-O42.4, SRS 3.5.1):** `BajaUnidadService.dar_de_baja()` no validaba ningún rol al recibir `forzar=true` — cualquier Proveedor podía autoforzar la baja de su propia unidad con un despacho activo, contradiciendo la única excepción al autoservicio que el SRS documenta explícitamente. Además, el endpoint (`UnidadBajaView`) solo aceptaba rol Proveedor/Cliente (`IsProveedorFlota`, con nota "Sin override Admin"), así que un Administrador no tenía ninguna vía para ejecutarla. Corregido: el servicio ahora exige rol `Administrador` cuando hay despacho activo (levanta `PermissionError` → 403 si no); se agregó el permiso `IsProveedorFlotaOrAdministrador` a la vista para que el Administrador pueda llegar al endpoint. El Proveedor conserva la baja ordinaria (sin despacho activo) intacta.
  - **`gmail` opcional en el alta individual (RF-O39.5/O39.6, SRS 3.5.1):** el código, el contrato OpenAPI y el frontend exigían `gmail` como obligatorio al registrar una unidad individualmente — contradiciendo el SRS y la propia spec técnica del módulo (`alta-unidades/backend/spec.md`, RF-CAM-001.6), que documentan que es opcional (la unidad queda en el catálogo sin acceso hasta que se le asigne login después; solo la carga en lote exige correo). Corregido en las cuatro capas: `RegistroUnidadService.registrar()`, `UnidadCreateRequest` del contrato OpenAPI, el modelo TypeScript y el formulario del frontend (quitado `required` + validación JS).
  - **Aprobación de región reservada al Director Tecnológico (SRS 3.5.2):** el endpoint de validación de región (`POST .../regiones/validaciones`) aceptaba `resultado='Aprobada'` de un Administrador solo, sin el Director Tecnológico, contradiciendo *"dos actores en secuencia, no indistintos... el Director Tecnológico es quien queda registrado como responsable de la aprobación final"*. Esta era una decisión consciente pero incorrecta de la spec técnica de `incorporacion-regional` (Clarifications, revisión manual sin distinguir los dos pasos). Corregido a pedido explícito del usuario (opción elegida: restringir el `POST` de aprobación al rol `DirectorTecnologico`, dejando al Administrador solo la ejecución del protocolo y el rechazo): `ValidacionRegionService.ejecutar()` ahora exige el rol para `resultado='Aprobada'`.
  - Specs actualizadas: `alta-unidades/backend/spec.md` (tabla de actores + RF-CAM-004) y su contrato OpenAPI; `incorporacion-regional/backend/spec.md` (Clarifications + RF-REGON-001 + tabla de actores) y su contrato OpenAPI.
  - Suite completa backend (1027 tests) y frontend (`tsc` app + spec) en verde.
- **Queda pendiente, registrada aparte:** entrada #8 (columna `zonacobertura` huérfana) arriba, en Pendientes — es una ambigüedad de bajo riesgo, no un bug objetivo.

### 10. Carga en lote de unidades sin verificar si el plan del Proveedor la habilita (RF-O40.6)

- **Resuelto:** 2026-08-08
- **Decisión del usuario:** agregar un campo `carga_lote_habilitada` (BOOLEAN) independiente y configurable en `Dim_Plan`, mismo patrón que `severidades_desbloqueadas`.
- **Qué se hizo:**
  - **Catálogo:** RF-O40.6 (nuevo) y RF-O26.5 (nuevo) documentan la regla en `TSI-Catalogo-CU-RF-RNF.md`.
  - **`Dim_Plan.carga_lote_habilitada`** (BOOLEAN, default `false`): campo independiente y configurable por el Director de Estrategia al crear/editar un plan (`CatalogoPlanService._validate_carga_lote_habilitada`, `PlanRepository`), opcional (no rompe payloads existentes).
  - **Congelamiento en `Fact_Suscripcion.carga_lote_habilitada`:** mismo patrón que `nivel`/`severidades_desbloqueadas` — se copia al alta (`AltaSuscripcionService`) y se resincroniza solo al aprobar un cambio de plan (`CambioPlanService.aprobar`); una edición posterior de `Dim_Plan` no afecta retroactivamente a un proveedor ya contratado.
  - **Gate en Red Operativa:** nuevo repositorio de solo lectura `core/repositories/red_operativa/suscripcion_activa_read_repository.py` (lee `Fact_Suscripcion`, dominio de Suscripciones y Facturación, sin escribir nada). `ImportacionLoteUnidadService.importar()` verifica la suscripción activa del Proveedor antes de procesar el archivo — si no existe o `carga_lote_habilitada` es falso, `PermissionError` → `403`, sin leer el CSV.
  - **`database/esquemas.json`** y el Pinot real: se agregó `carga_lote_habilitada` a `Dim_Plan` y `Fact_Suscripcion` (ver detalle de aplicación al Pinot real más abajo).
  - **Frontend:** tipos (`suscripciones.types.ts`), formulario de plan (checkbox "Habilitar carga en lote") y detalle de plan actualizados. La UI de carga en lote de Red Operativa no necesitó cambios — ya propaga el `detail` del 403 tal cual.
  - **Specs actualizadas:** `subscriptions-and-billing` (`spec.md` RN-SUSF-030, `data-model.md`, contrato OpenAPI) y `alta-unidades` (`spec.md` RF-CAM-002 punto 0, contrato OpenAPI).
  - Fixtures de prueba (`conftest.py`): `Dim_Plan` (Básico/Legacy=false, Profesional/Empresarial=true) y `Fact_Suscripcion` del cliente de prueba (true, para no romper los tests de lote existentes) + 2 tests nuevos (servicio y contrato API) que verifican el bloqueo cuando el plan no lo habilita.
  - Suite completa backend (1029 tests) y frontend (`tsc` app + spec) en verde.
  - **Pinot real:** subí `carga_lote_habilitada` a `Dim_Plan` y `Fact_Suscripcion` en tu contenedor (mismo procedimiento aditivo que `severidades_desbloqueadas`/`nivel`: `PUT /schemas/{tabla}?reload=true`); verificado con consultas SQL reales. Filas existentes quedan en `false` (dato sembrado antes del cambio), como es esperable.

### 12. Emergencias — renumeración de CU, permisos de disponibilidad, cierre de casos y datos de cierre perdidos

- **Resuelto:** 2026-08-08
- **Qué se hizo (los 4 módulos: registro-accidente, despacho-inteligente, evidencia-unidad, seguimiento-cierre-de-casos):**
  - **Renumeración completa de CU** en las 4 specs técnicas (`spec.md`, `data-model.md`, contratos OpenAPI, `research.md`, `plan.md`, `quickstart.md`, `tasks.md`, `traceability.md`, specs de frontend) y en los docstrings del código (`apps/accidentes`, `apps/despacho`, `apps/seguimiento`): la numeración interna vieja (CU-O21…O46) no coincidía con el catálogo limpio (CU-O56…O82) y colisionaba con CUs de otros departamentos. Casos especiales resueltos por contenido, no por número: CU-O46 (evidencia-unidad) se dividió en CU-O75 (clima/elementos físicos) y CU-O76 (conductores/implicados); CU-O28 (seguimiento) se unificó en CU-O80.
  - **Disponibilidad de unidad — ya no la puede declarar un tercero:** `UnidadHistorialEstadoView` usaba el mismo permiso para leer (GET, Admin/Despacho pueden ver cualquier unidad) y para escribir (POST, declarar el estado) — el POST heredaba el bypass de Admin. Nuevo permiso `IsUnidadEmergenciaSelfStrict` (sin excepción de rol) exclusivo para el POST; el GET conserva la visibilidad de Admin/Despacho. La intervención de un Administrador sobre una unidad equivocadamente en camino a una emergencia sigue cubierta por el mecanismo ya existente de baja forzada de Red Operativa (`BajaUnidadService`), no por este endpoint.
  - **RN-SEG-003 — se restaura correctamente "Fuera de servicio":** `ConfirmarDespachoService` ahora captura el estado de disponibilidad de la unidad *antes* de sobreescribirlo a `En_Mision` y lo guarda en `Fact_Despacho.estado_unidad_previo` (columna nueva). `RetiroDespachoService` y `AbortarMisionService` leen ese campo en vez del estado actual (que siempre era `En_Mision`) para decidir si la unidad vuelve a "Activa" o a "Fuera de servicio".
  - **Cierre de casos — exclusivo del Operador, con cierre automático:** corregida la spec (RN-SEG-002 decía "ambos tienen igual autoridad para cerrar"; el código ya era Operador-only, correcto). El cierre automático al completarse todos los retiros ya existía en `ForzarRetiroService` (reevalúa `todos_retirados_o_abortados()` tras cada retiro forzado) — se documentó explícitamente en la spec.
  - **Retiro forzado ahora distinguible:** nuevo campo `Fact_Despacho.retiro_forzado` (BOOLEAN), poblado por `ForzarRetiroService`. *(Aclaración: `Fact_AccidenteTipoEstadoAccidente.idusuario` — que ya existía — registra quién cambió el estado del **caso**; el campo nuevo resuelve un gap distinto, a nivel de **despacho** individual, que no tenía ningún campo diferenciador.)*
  - **GPS — se conservan las posiciones, no se purgan:** `GpsDepuracionService` nunca borraba nada en la práctica; se corrigió el nombre/documentación para que sea explícito (antes sonaba a que sí purgaba). Campo de retorno renombrado de `depurados` a `elegibles_para_muestreo`.
  - **Escalar severidad movido al módulo correcto:** `EscalarSeveridadService` (CU-O73) vivía en `apps/accidentes` (registro-accidente); el SRS §3.6.4 lo narra en Seguimiento y Cierre de Casos. Movido a `apps/seguimiento`, con su vista, ruta, y tests. De paso, ahora conserva la severidad inicial junto a la escalada en la tabla `Fact_HistorialSeveridadAccidente` (RF-O73.2) — la tabla ya existía en el esquema Pinot desde antes, pero ningún servicio la usaba.
  - **Datos de cierre de caso — ya no se pierden:** `resultado_atencion`, `calificacion` y `observaciones_finales` se escribían contra columnas de `Fact_Accidente` que nunca existieron en el esquema real. Nueva tabla auxiliar `Fact_CierreAccidente` (1:1 con `Fact_Accidente` por `idaccidente`), agregada a `esquemas.json` y `tablas.json` siguiendo la misma sintaxis que el resto de tablas del proyecto.
  - **Catálogo corregido:** RF-O62.3 decía "excluir a la unidad que rechazó del siguiente intento inmediato"; el SRS (autoridad máxima) exige exclusión permanente para ese caso, y el código ya lo implementaba así — se corrigió el catálogo para que coincida con el SRS.
  - **Otros bugs objetivos corregidos:** motivo de descarte de caso ahora opcional (SRS/spec/contrato ya lo decían así, el código lo exigía); la justificación de un registro retrospectivo ahora sí queda auditada en el log (antes se validaba y se descartaba); cuando el primer intento automático de despacho no encuentra candidatas, ahora escala a zonas vecinas y dedja constancia (nota + alerta Admin) en vez de fallar en silencio.
  - Suite completa backend (1035 tests) en verde.
- **Diferido explícitamente:** entrada #11 arriba (validación de coherencia geográfica en registro, y verificación de presencia en sitio para evidencia/escalada de severidad).

### 14. Soporte al Cliente — CU añadido fuera de secuencia, renumeración de CU, vínculo factura-disputa y 3 endpoints sin control de propiedad

- **Resuelto:** 2026-08-08
- **Qué se hizo:**
  - **Catálogo — CU-O97 añadido fuera de secuencia:** "Configurar los niveles de compromiso de tiempo (SLA)" no tenía CU asignado en `informestacticos/TSI-Catalogo-CU-RF-RNF.md` — el flujo ya existía en código (`Dim_SLAConfig`, `ConfigurarSLAService`) y en la spec técnica, documentado con un ID interno que colisionaba con Analítica e Inteligencia. Se agregó siguiendo el mismo tratamiento que CU-O96 (§5.9 "fuera de secuencia"), con actualización del resumen cuantitativo.
  - **Renumeración completa de CU:** la numeración interna de la spec técnica (`gestion-tickets-soporte`) no solo reusaba números obsoletos — colisionaba directamente con CUs **vigentes** de otros departamentos (Analítica e Inteligencia, Ventas y CRM), un problema más severo que en departamentos anteriores. Mapeo aplicado: CU-O91→CU-O83 (registrar), CU-O92→CU-O84/O85/O86/O87 (atender/escalar/resolver/confirmar cierre, según acción concreta), CU-O95→CU-O97 (configurar SLA, el nuevo), CU-O96→CU-O89 (monitoreo SLA), CU-O97(antiguo)→CU-O88 (reabrir). Aplicado con sustitución en dos fases (tokens→placeholders→tokens finales) porque el conjunto de números viejos y nuevos se solapaba (O97 era simultáneamente origen y destino). Corregido en `spec.md`, `data-model.md`, `plan.md`, `research.md`, `quickstart.md`, `tasks.md`, `traceability.md`, el contrato OpenAPI, el spec y contrato de frontend, y todos los docstrings de `backend/apps/soporte_cliente/` y `backend/core/repositories/soporte/`. La tabla "Mapa borrador (chat) → CU canónicos" del spec se reescribió a mano para reflejar el mapeo correcto.
  - **RF-O83.2 — vínculo factura-disputa implementado:** estaba completamente ausente de spec, código y esquema (no un bug parcial). Se agregó `idfactura` (INT, FK a `Fact_Factura`, opcional) a `Fact_Reclamo` en `esquemas.json` — cambio aditivo, ya desplegado en el contenedor Pinot en ejecución. Como Pinot no soporta `UNIQUE`/FK declarativos, la regla del SRS ("una factura admite una sola disputa abierta") se aplica **a nivel de aplicación**: `RegistrarTicketService.registrar()` rechaza con `422` si ya existe otro `Fact_Reclamo` con el mismo `idfactura` y `estado != 'Cerrado'` (`ReclamoRepository.find_disputa_abierta_por_factura()`). Se prioriza el SRS tal como se pidió, sin tocar la normalización del esquema (no se creó tabla puente — la relación es 1 factura → 0..1 disputa abierta, no muchos-a-muchos).
  - **3 endpoints sin control de propiedad corregidos** (mismo patrón que ya había aparecido en Red Operativa y Emergencias — un tercero podía actuar en nombre del Cliente dueño):
    - `ConfirmarCierreTicketView`/`ConfirmarCierreService`: antes cualquier agente podía confirmar el cierre de cualquier ticket; ahora solo el Cliente dueño (permiso restringido a `IsClienteSoporte` + verificación `idcliente` en el servicio, `403` si no coincide).
    - `ReabrirTicketView`/`ReabrirTicketService`: mismo problema y misma corrección — reabrir es acción exclusiva del Cliente dueño (CU-O88, RF-O88.1).
    - `ComentarTicketView`/`ComentarTicketService`: corrección condicional — un agente sigue pudiendo comentar en cualquier ticket (lo necesita para su trabajo), pero un Cliente ahora solo puede comentar en sus propios tickets (mismo patrón ya usado correctamente en `TicketDetalleView`).
  - 6 tests nuevos (renumeración no requiere tests, es documental); suite completa de Soporte al Cliente (99 tests) y backend completo (1042 tests) en verde.
- **Diferido explícitamente:** entrada #13 arriba (guarda de estado faltante en `EscalarTicketService`).
