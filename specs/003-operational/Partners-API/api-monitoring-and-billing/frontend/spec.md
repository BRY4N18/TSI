# Feature Specification: Monitoreo y Facturación de API — Frontend

**Feature Branch / capa**: `api-monitoring-and-billing/frontend`
**Created**: 2026-08-08 · **Especificada**: 2026-08-10
**Status**: ✅ Especificada — lista para `/speckit-plan`
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-APM-*, RNF-APM-*, CA-APM-*, RN-APM-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.
**Referencias globales**: `.specify/docs/design/design-system.md` (patrón Lista → Workpanel, estados no felices, tokens), `.specify/docs/architecture/module-map.md`.

---

## Alcance

Cuatro superficies con tres actores y necesidades muy distintas. **No son cuatro versiones de la misma pantalla**: dos son de vigilancia continua, una es de rendición de cuentas y la cuarta es una cola de trabajo con dinero en juego.

| Superficie | Actor | Cubre |
|---|---|---|
| **Consola de registros** | Desarrollador de APIs | Detalle de cada llamada (endpoint, método, código, IP, latencia) con filtros por partner, código y rango · foco en autodiagnóstico (RF-APM-008) |
| **Panel de consumo** | Partner de integración | Sus métricas del período: llamadas, errores, latencia media, % de cupo y **excedente estimado** (RF-APM-007) |
| **Reporte mensual** | Administrador · Desarrollador de APIs · Partner | Consumo de un mes con **comparación contra otro período** (RF-APM-009) |
| **Excepciones de facturación** | Administrador | Facturas de excedente que agotaron sus reintentos y los partners **no tarificables** (RF-APM-013) |

**El portal del partner ya existe** (`/partners/portal`, #07). El panel de consumo es una **sección nueva de ese portal**, no una aplicación aparte: el partner no debería tener dos sitios donde mirar su integración.

---

## Puntos críticos heredados del dominio

Derivan de reglas del backend y **no** son decisiones libres de esta capa. Los cinco primeros venían ya identificados en el stub; se conservan porque siguen siendo exactos.

1. **Superar la cuota NO es un error (RN-APM-002).** La UI comunica el exceso como **coste previsto**, nunca como fallo ni bloqueo. Un indicador rojo de «límite superado» daría a entender que el servicio se cortó, y **no se corta**: el modelo es de pago por uso. Es el punto donde más fácil sería «arreglar» la UI hacia lo incorrecto.
2. **Separación de entornos siempre visible (RN-APM-001).** Pruebas y producción nunca se mezclan; toda métrica indica su entorno, y **por más que el color** (RNF-09).
3. **«Tiempo real» tiene un límite de 5–15 s.** La consola no promete latencia cero: muestra la marca del último dato disponible. El backend ya la calcula (`datos_hasta`, con el retraso de ingesta restado).
4. **Los 4xx del partner son autodiagnóstico (RN-APM-009)**, no incidencias del sistema. Se presentan como información útil para que el partner corrija su cliente, no como alarma de plataforma.
5. **«Pendiente de emisión manual» es accionable (RF-APM-013)**, no informativo: exige que un Administrador actúe.
6. **Un `429` no es «cuota aplicada» (§ 15 D2 del backend).** Cupo mensual y tasa por minuto son mecanismos distintos: el primero nunca bloquea y se factura; el segundo devuelve 429 y **no cuenta como consumo facturable**. La UI no puede sumarlos en un mismo indicador ni llamarlos igual.
7. **Un mes sin llamadas es cero, no un error (RF-APM-009).** El estado vacío del reporte dice «no hubo consumo», no «no se pudo cargar».
8. **Sin cupo configurado no hay porcentaje.** El backend devuelve `null` en `porcentaje_consumido` y `excedente_estimado` cuando el cupo vale el centinela. La UI muestra «no aplica», **nunca 0 %**: inventar un cero sería peor que decir que no hay dato.

---

## Clarifications

### Session 2026-08-10

- **Q: ¿de dónde saca el Administrador la lista de excepciones de facturación?** Verificado en código: `TarificacionExcedenteService` escribe `reintentos` y `resultado_ultimo_reintento` en `Fact_Factura` y **alerta por correo**, pero **no existe ningún endpoint que las liste**. El contrato de #08 tiene 4 paths y ninguno es de facturación.
  → **A: añadir `GET /facturacion/excepciones`** (`BE-DELTA-04`). Sin él, la cuarta superficie no tiene de dónde leer.
- **Q: ¿y los partners «no tarificables» (tarifa en centinela `-1.0`)?** Verificado: **no se persisten en ninguna parte**. El corte los audita y manda un correo, y ahí muere el rastro.
  → **A: incluirlos en el mismo endpoint** (`BE-DELTA-05`), derivándolos del corte. Es el caso que RN-APM-014 más teme —ingreso real no cobrado **en silencio**— y hoy el único aviso es un correo que puede perderse. Una cola en pantalla es exactamente la contramedida.
- **Q: RF-APM-009 dice que el reporte lo consulta «el Cliente y el Administrador», pero `/reportes-consumo` usa `EsPartnerOGestor` = {PartnerIntegracion, DesarrolladorAPIs, Administrador}: el rol `Cliente` **no entra**.**
  → **A: la UI se ciñe a los roles que el endpoint ya permite** y no se toca el permiso. Ampliarlo sería una decisión de negocio (¿debe un Cliente ver el consumo de su partner?) que excede a esta capa. Queda registrada en `decisiones-pendientes.md` para que la resuelva quien corresponde, no un desarrollador de frontend por conveniencia.
- **Q: ¿la consola de logs necesita auto-refresco?** → **Sí, pero manual por defecto.** Botón «Actualizar» + marca de `datos_hasta` visible. Un polling automático agresivo contra Pinot no compra nada: la ingesta va 5–15 s por detrás y el propio dato lo declara. Se ofrece auto-refresco opcional cada 30 s, apagado por defecto.
- **Q: ¿la consola lleva workpanel?** → **Sí, en modo Ver-only y como página dedicada.** No hay PATCH de un log —son tablas append-only (RN-APM-015)—, así que aplica la «Variante Ver-only / CRUD parcial»: solo `eye`, nunca `pencil` deshabilitado, y sin CTA de alta.
- **Q: ¿copy de los estados vacíos y de error?** → Se define en `research.md` durante `/speckit-plan`, como en #07.

---

## Dependencias de backend (bloqueantes)

Esta capa **no puede completarse** sin estos dos cambios. Reabren la capa `backend/`, cerrada con 71/71 tareas, y por eso se declaran aquí antes de planificar nada.

| ID | Cambio | Por qué es imprescindible | Impacto |
|---|---|---|---|
| **BE-DELTA-04** | `GET /api/v1/facturacion/excepciones` — facturas de excedente con los reintentos agotados, con su partner, período, importe, nº de intentos y el último resultado. Solo Administrador y Desarrollador de APIs | La cuarta superficie **no tiene fuente de datos**. Hoy esas facturas solo existen como filas de `Fact_Factura` que nadie consulta y un correo que puede perderse | 1 vista + 1 lectura de repositorio (`resultado_ultimo_reintento` empieza por `agotados:`) + contract tests |
| **BE-DELTA-05** | Incluir en ese mismo endpoint los **partners no tarificables** del período (tarifa en el centinela `-1.0`), derivados del corte | RF-APM-011 los trata igual que a los reintentos agotados, pero **no deja rastro consultable**. Es literalmente el caso de RN-APM-014: ingreso real no cobrado en silencio | Reutiliza el cálculo ya implementado; no añade columnas ni tablas |
| **BE-DELTA-06** | `GET /logs-api` acepta `cursor`, `codigohttp`, `desde` y `hasta` | Sin ellos la consola tendría que filtrar en memoria —falsa exhaustividad— y el `next_cursor` que el `meta` ya devolvía no se podía usar | 4 parámetros en la vista y el repositorio |

> **Ninguno de los dos cambia una regla de negocio.** BE-DELTA-04 expone datos que ya se escriben; BE-DELTA-05 expone un cálculo que ya se hace. Lo que cambia es que dejan de ser invisibles.

**Lo que NO hace falta:** `GET /partners/me` ya existe desde #07 (BE-DELTA-01), así que el panel de consumo del partner es alcanzable sin nada nuevo.

---

## User Scenarios & Testing *(mandatory)*

### US-FE-1 — El partner entiende su consumo y lo que va a pagar (P1) 🎯

**Como** Partner de integración, **quiero** ver mi consumo del período y lo que me costará el exceso, **para** decidir si ajusto mi integración o subo de plan antes de que llegue la factura.

**Por qué es la P1:** es la superficie que más se usa y la que más fácil se comunica mal. Si el partner lee «límite superado» en rojo y cree que le cortaron el servicio, abrirá un ticket por algo que funciona perfectamente.

**Escenarios**

1. **Dado** un partner con 8 400 de 10 000 llamadas, **cuando** abre su panel, **entonces** ve el 84 % de su cupo, su latencia media y sus errores, con la marca del último dato disponible.
2. **Dado** un partner con 12 500 de 10 000 llamadas, **cuando** abre su panel, **entonces** ve el exceso presentado como **coste previsto** con su importe estimado, **y en ningún sitio** aparece la palabra «bloqueado», «cortado» ni un indicador crítico rojo.
3. **Dado** un partner **sin cupo configurado** (centinela), **cuando** abre su panel, **entonces** ve «no aplica» en porcentaje y excedente, nunca 0 %.
4. **Dado** un partner suspendido, **cuando** abre su panel, **entonces** **sí** puede consultarlo: es lectura, y le sirve para entender su situación (RN-APM-017).
5. **Dado** cualquier partner, **cuando** mira sus métricas, **entonces** el entorno (**Producción**) está indicado explícitamente y no solo por color.

---

### US-FE-2 — El partner diagnostica sus propios errores (P1)

**Como** Partner de integración, **quiero** ver mis llamadas fallidas con su código y su endpoint, **para** corregir mi cliente sin abrir un ticket.

**Escenarios**

1. **Dado** un partner con 4xx recientes, **cuando** filtra por «solo errores», **entonces** ve endpoint, método, código, latencia y hora de cada uno.
2. **Dado** un `429`, **cuando** aparece en la lista, **entonces** se presenta como **límite de ritmo**, distinguible de un `403` de alcance y **sin** sumarse al consumo facturable.
3. **Dado** un partner sin errores, **cuando** filtra por errores, **entonces** ve un vacío que dice que no hubo fallos —una buena noticia—, no un error de carga.

---

### US-FE-3 — El Desarrollador de APIs vigila la plataforma (P1)

**Como** Desarrollador de APIs, **quiero** una consola con el detalle de todas las llamadas y filtros, **para** detectar un partner que está fallando antes de que escale.

**Escenarios**

1. **Dado** el listado, **cuando** filtra por partner, código HTTP o rango temporal, **entonces** la tabla se acota y los filtros activos quedan visibles.
2. **Dado** cualquier momento, **cuando** mira la consola, **entonces** ve la marca del último dato disponible y un indicador de que «tiempo real» significa 5–15 s de retraso.
3. **Dado** un registro concreto, **cuando** pulsa `eye`, **entonces** abre su detalle en modo **Ver**, sin opción de editar: son tablas append-only.
4. **Dado** que pulsa «Actualizar», **entonces** los datos se recargan y la marca temporal avanza.

---

### US-FE-4 — Rendir cuentas de un mes y compararlo (P2)

**Como** Administrador, **quiero** el consumo de un mes y poder compararlo con otro, **para** explicar una variación de facturación.

**Escenarios**

1. **Dado** un mes con consumo, **cuando** lo consulta, **entonces** ve llamadas, errores y latencia media del período.
2. **Dado** dos períodos seleccionados, **cuando** los compara, **entonces** ve ambas cifras y la variación entre ellas.
3. **Dado** un mes **sin llamadas**, **cuando** lo consulta, **entonces** ve ceros con el mensaje de que no hubo consumo —no un error.
4. **Dado** cualquier reporte, **entonces** se refiere **solo a producción** y lo dice explícitamente (RN-APM-001).

---

### US-FE-5 — El Administrador resuelve lo que no se pudo facturar (P2) 🎯

**Como** Administrador, **quiero** una cola con las facturas de excedente que fallaron y los partners que no se pudieron tarificar, **para** emitirlas a mano antes de que se pierda el ingreso.

**Por qué importa:** es la única superficie de este módulo donde **no mirar tiene consecuencia económica directa**. RN-APM-014 dice que una factura de excedente nunca debe quedar silenciosamente sin crearse; hoy el único aviso es un correo.

**Escenarios**

1. **Dado** una factura con sus tres reintentos agotados, **cuando** el Administrador abre la cola, **entonces** la ve con su partner, período, importe, nº de intentos y el motivo del último fallo.
2. **Dado** un partner **sin tarifa configurada** en su plan, **cuando** el Administrador abre la cola, **entonces** también aparece, **distinguido** del caso anterior: no es que la emisión fallara, es que no había con qué calcular.
3. **Dado** que la cola está vacía, **entonces** el mensaje dice que no hay excepciones pendientes —el estado deseable—, y no sugiere que algo se rompió.
4. **Dado** un caso de la cola, **cuando** lo abre, **entonces** ve qué hacer a continuación: para el no tarificable, configurar la tarifa del plan; para el de reintentos agotados, emitir la factura manualmente.

---

### US-FE-6 — Cada rol ve solo lo suyo (P2)

**Como** sistema, **quiero** que la navegación de cada rol contenga solo sus superficies, **para** no exponer lo que no puede usar.

**Escenarios**

1. **Dado** un Partner de integración, **entonces** ve su panel de consumo dentro de su portal y **no** ve la consola ni las excepciones.
2. **Dado** un Desarrollador de APIs, **entonces** ve consola y reporte, y **no** ve el panel de un partner concreto como si fuera suyo.
3. **Dado** un Administrador, **entonces** ve además las excepciones de facturación.
4. **Dado** un partner que intenta la ruta de otro, **entonces** recibe 403 y la UI lo explica sin filtrar datos ajenos.

---

## Functional Requirements (UI)

### Panel de consumo del partner (portal, `PartnerIntegracion`)

- **FR-UI-101**: MUST mostrar llamadas, errores, latencia media y período vigente del partner autenticado, resuelto vía `GET /partners/me`.
- **FR-UI-102**: MUST mostrar el porcentaje de cupo consumido; y **«no aplica»** —nunca 0 %— cuando el backend devuelve `null` por cupo en centinela.
- **FR-UI-103**: MUST presentar el exceso como **coste previsto** con su importe estimado. MUST NOT usar el token `alerta-critica`, la palabra «bloqueado»/«cortado», ni ningún elemento que sugiera interrupción del servicio.
- **FR-UI-104**: MUST indicar el entorno (**Producción**) de forma textual, no solo cromática.
- **FR-UI-105**: MUST mostrar la marca del último dato disponible (`datos_hasta`) junto a las métricas.
- **FR-UI-106**: MUST seguir siendo consultable por un partner suspendido.
- **FR-UI-107**: MUST mostrar «no aplica» —no un importe— cuando el excedente estimado llega `null` por falta de tarifa configurada.

### Consola de registros (`DesarrolladorAPIs`)

- **FR-UI-111**: MUST listar las llamadas ordenadas de la más reciente a la más antigua, con endpoint, método, código, latencia, IP y hora.
- **FR-UI-112**: MUST ofrecer filtros por partner, código HTTP, «solo errores» y rango temporal, con los filtros activos visibles y limpiables. **Todos MUST resolverse en el servidor**: cada cambio dispara una consulta. MUST NOT filtrar en memoria sobre una ventana ya cargada, porque daría una falsa sensación de exhaustividad.
- **FR-UI-113**: MUST mostrar la marca del último dato disponible y explicar que «tiempo real» está limitado por la ingesta (5–15 s). MUST NOT prometer latencia cero.
- **FR-UI-114**: MUST ofrecer refresco manual; MAY ofrecer auto-refresco cada 30 s, **apagado por defecto**.
- **FR-UI-115**: MUST usar la variante **Ver-only** del patrón Lista → Workpanel: únicamente `eye`, sin `pencil` ni CTA de alta (RN-APM-015 — append-only).
- **FR-UI-117**: MUST paginar por cursor con «Cargar más», conservando los filtros activos en cada página. Cambiar un filtro MUST reiniciar la paginación.
- **FR-UI-116**: MUST distinguir visualmente un `429` (límite de ritmo) de un `403` (alcance) y de un `5xx` (fallo de plataforma), y MUST NOT presentar los 4xx del partner con el lenguaje de una incidencia del sistema.

### Reporte mensual (`Administrador` · `DesarrolladorAPIs` · `PartnerIntegracion`)

- **FR-UI-121**: MUST permitir elegir el período y mostrar llamadas, errores y latencia media.
- **FR-UI-122**: MUST permitir comparar contra un segundo período y mostrar la variación.
- **FR-UI-123**: MUST mostrar ceros con copy explícito cuando el mes no tuvo consumo; MUST NOT presentarlo como error.
- **FR-UI-124**: MUST declarar que el reporte se refiere exclusivamente a **producción**.

### Excepciones de facturación (`Administrador`)

- **FR-UI-131**: MUST listar las facturas con reintentos agotados con partner, período, importe, nº de intentos y motivo del último fallo.
- **FR-UI-132**: MUST listar también los partners **no tarificables**, **distinguidos** de los anteriores por tipo de excepción.
- **FR-UI-133**: MUST indicar en cada caso la acción siguiente que corresponde.
- **FR-UI-134**: MUST usar un estado vacío que comunique normalidad («no hay excepciones pendientes»), no ausencia de datos.
- **FR-UI-135**: MUST NOT ofrecer emitir la factura desde la UI en esta iteración — no existe endpoint de emisión manual y fingirlo sería peor que no ofrecerlo.

### Transversales

- **FR-UI-141**: MUST implementar los tres estados no felices con los componentes compartidos (`app-list-loading-skeleton`, `app-list-error-state`, `app-list-empty-state`).
- **FR-UI-142**: MUST registrar cada superficie en `nav-links.ts` con sus roles, dentro del grupo «Partners y API» ya existente.
- **FR-UI-143**: MUST proteger cada ruta con el guard del rol correspondiente y MUST mostrar un 403 explicativo sin exponer datos ajenos.
- **FR-UI-144**: MUST usar `JetBrains Mono` para identificadores y cifras tabulares, y MUST NOT pedir al usuario que teclee PKs.
- **FR-UI-145**: MUST distinguir cupo mensual de tasa por minuto en cualquier texto de la interfaz; MUST NOT agregarlos en un único indicador.

---

## Success Criteria

- **SC-001**: Un partner identifica su consumo, su porcentaje de cupo y su coste previsto **sin abrir ninguna otra pantalla**.
- **SC-002**: Ningún elemento de la interfaz sugiere que superar el cupo interrumpe el servicio — verificable revisando copy y tokens de las tres superficies del partner.
- **SC-003**: Un partner con un `403` o un `429` reciente puede identificar la causa y el endpoint afectado **sin escalar a un Administrador**.
- **SC-004**: El Administrador ve todas las excepciones de facturación pendientes en **una sola pantalla**, sin depender del correo.
- **SC-005**: Toda métrica mostrada indica su entorno y su marca temporal; ninguna se presenta como instantánea.
- **SC-006**: Un rol no ve en su navegación ninguna superficie que no pueda usar.
- **SC-007**: Las cuatro superficies presentan sus tres estados no felices con los componentes compartidos.

---

## Out of Scope

- **Emitir o reintentar la factura desde la UI**: no hay endpoint (FR-UI-135). Requeriría un delta adicional y una decisión sobre quién puede forzar una emisión.
- **Configurar la tarifa del plan**: es de `subscriptions-and-billing` (CU-O26), no de esta capa.
- **Abrir o resolver disputas**: es de `gestion-tickets-soporte`.
- **Gestión de acceso** (revocar, suspender, reactivar): es la capa frontend de #09.
- **Gráficas de series temporales**: el backend agrega por período, no expone series. Añadirlas exigiría un endpoint nuevo sin demanda declarada.
- **Exportación a CSV/PDF** del reporte: no está en RF-APM-009.

---

## Assumptions

| Supuesto | Valor | Fundamento |
|---|---|---|
| Período por defecto del panel | Mes en curso | Es el período de facturación (RF-APM-007) |
| Tamaño de página de la consola | 50 registros, máx. 500 | Es el límite que ya aplica `ConsolaLogsView` |
| Auto-refresco | 30 s, apagado por defecto | La ingesta va 5–15 s por detrás; refrescar más rápido no aporta |
| Rol `Cliente` en el reporte | **Fuera**, hasta que se decida | El endpoint no lo permite; ampliarlo es decisión de negocio |
| Comparación de períodos | Dos períodos a la vez | RF-APM-009 pide «comparar», no una serie histórica |

---

## ISO/IEC 25010:2023 — Justificación

| Característica | Aplica | Justificación |
|---|---|---|
| **Interaction Capability** | ✅ **Dominante** | Es una capa íntegramente de presentación, y su mayor riesgo es de comunicación: presentar un exceso facturable como un fallo de servicio induciría al partner a cortar su propia integración. El valor de esta capa está en **decir bien** lo que el backend ya calcula bien. |
| **Functional Suitability** | ✅ | Cubre las cuatro superficies de RF-APM-007/008/009/013 sin redefinir ninguna regla. |
| **Reliability** | ⚠️ Parcial | Los tres estados no felices son obligatorios, pero la exactitud del dato es del backend (RNF-APM-001). |
| **Performance Efficiency** | ⚠️ Parcial | El techo lo pone la ingesta de Pinot, no la UI. La decisión de no auto-refrescar agresivamente es consecuencia de eso. |
| **Security** | ✅ | Control de propiedad en el panel del partner, guards por rol y **sin secretos en pantalla**: este módulo no maneja credenciales. |
| **Maintainability** | ✅ | Reutiliza el módulo `partners/` de #07, sus guards y sus componentes compartidos. |
| **Compatibility** | ⚠️ Parcial | Consume el contrato de #08; no expone integraciones propias. |
| **Flexibility** | ⚠️ Parcial | Responsividad según los breakpoints globales. |
| **Safety** | ❌ **No aplica** | Fuera de la cadena crítica registro → asignación → despacho → confirmación. Mostrar mal una métrica de consumo no retrasa la atención de ninguna víctima. |

**Tie-breaker:** conflicto entre **Interaction Capability** y **Functional Suitability** en FR-UI-103. Lo funcionalmente completo sería mostrar un indicador de severidad cuando el consumo supera el 100 % del cupo —es la convención de cualquier medidor—, pero aquí ese indicador **mentiría**: comunicaría una interrupción que no existe (RN-APM-002). Se prioriza **Interaction Capability**. **Trade-off aceptado:** el partner que supere su cupo verá un aviso deliberadamente menos llamativo de lo que el patrón visual sugeriría, a cambio de que nadie interprete que su servicio se cortó.
