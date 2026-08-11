# Especificación: Gestión de Acceso de Partners

> **Capa Speckit:** `backend/` — dominio, API, RF/RN/CA.  
> **Índice del módulo:** [`../partner-access-management.md`](../partner-access-management.md).  
> **UI (Interaction Capability):** [`../frontend/spec.md`](../frontend/spec.md) — no duplicar aquí detalles de pantallas.

## 1. Objetivo

Cortar y restituir el acceso del partner, por **seguridad** o por **mora**. Cubre la revocación de autoservicio ante una credencial comprometida —con reemplazo inmediato—, los avisos previos a la suspensión, la suspensión automática al superarse el límite de mora, y la suspensión y reactivación manuales por parte de un Administrador.

El módulo **no** emite credenciales (dueño = `partner-api-onboarding`), **no** mide consumo ni emite facturas (dueño = `api-monitoring-and-billing`) y **no** suspende suscripciones (dueño = `subscriptions-and-billing`).

## 2. Contexto

Es el módulo que cierra el departamento. Los otros dos habilitan y cobran; este es el que **retira el acceso** cuando algo va mal: una credencial expuesta o una factura sin pagar.

Tiene dos naturalezas muy distintas conviviendo:

- **La revocación por seguridad es autoservicio inmediato**, sin aprobación de nadie, porque es reactiva ante un incidente donde *«esperar autorización sería el peor comportamiento posible»* (SRS L432).
- **La suspensión por mora es gradual y avisada**: el sistema notifica dos veces antes de actuar, y la reactivación **nunca es automática** — siempre la confirma un Administrador.

**Caso de uso incluido:**

- **CU-O55**: Revocar o suspender el acceso de integración. Agrupa cuatro flujos que la documentación legacy trataba por separado: revocación de credencial comprometida, avisos previos de suspensión, suspensión automática por mora, y suspensión/reactivación manual.

El módulo escribe `Dim_CredencialAPI` (invalidación y reemplazo), `Dim_Partner` (estado operativo) y `Fact_HistorialAccesoPartner` (bitácora); lee `Fact_Factura` para determinar la mora.

## Clarifications

### Session 2026-08-08 — Jerarquía de fuentes y renumeración canónica

- Q: ¿Qué numeración de CU se usa? → A: La **canónica del catálogo** (`TSI-Catalogo-CU-RF-RNF.md` §5.5): **CU-O55**, uno solo. La de `PortalPartnersAPI.md` está obsoleta y colisiona con CUs vigentes de otros departamentos.

  **Mapa legacy → canónico:**

  | Legacy (Portal) | Canónico | Flujo |
  |---|---|---|
  | CU-O84 (revocar credencial por compromiso) | **CU-O55** / RF-O55.1, RF-O55.2 | Revocación de autoservicio con reemplazo |
  | CU-O81 (aviso previo de suspensión por mora) | **CU-O55** | Avisos T-10 y T-5 |
  | CU-O79 (suspensión automática por mora) | **CU-O55** / RF-O55.3 | Suspensión con cascada |
  | CU-O76 (suspensión/reactivación manual) | **CU-O55** / RF-O55.3 | Acción del Administrador |

  El catálogo los une porque comparten actor de sistema, tabla y regla de cascada: son **un solo caso de uso con cuatro disparadores**.

- Q: `PortalPartnersAPI.md` fija los avisos en T-10 y T-5 sobre un límite de 15 días de mora. El SRS solo dice «dos momentos anteriores al límite». → A: Se conservan **T-10 y T-5 con límite de 15 días** como valores por defecto **configurables** (RNF-20). El SRS no los contradice, solo no los fija.

### Session 2026-08-08 — Contexto heredado del departamento

- Q: ¿Cómo se representan los valores ausentes? → A: **Pinot no almacena `NULL`.** Toda regla se expresa contra centinelas explícitos, nunca con `IS NULL`. Ver `partner-api-onboarding/backend/spec.md` § 15 D2 y RN-PAC-014.
- Q: ¿Dónde vive el estado operativo del partner? → A: **`Dim_Partner.activo` es la única fuente de verdad.** `fecha_suspension` y `motivo_suspension` son un **snapshot del último evento**, no un historial paralelo que pueda contradecirlo (SRS L442). Ver RN-PAC-012.
- Q: ¿Qué escribe este módulo en la bitácora? → A: Los cinco `tipo_cambio` que faltaban por cubrir: `revocacion_credencial`, `aviso_previo_suspension`, `suspension_automatica`, `suspension_manual` y `reactivacion`. Los otros siete los escribe #07.

### Session 2026-08-08 — Los dos gaps de diseño detectados

- Q: **La reactivación selectiva** exige restituir «únicamente las credenciales que estaban activas antes de la suspensión» (SRS L440), pero la cascada de suspensión las pone **todas** a `activo=false` sin dejar constancia de cuáles lo estaban. ¿Cómo se reconstruye? → **Ver § 15 Q1.**
- Q: **Suscripciones ya suspende por mora** (RF-SUSF-007: `Fact_Suscripcion.estado='Suspendida'` cuando la factura queda `Fallida`). ¿Cuál es la frontera con la suspensión del partner, y qué facturas cuentan como mora aquí? → **Ver § 15 Q2.**

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Partner de integración** | Autoservicio reactivo | Revoca por sí mismo una credencial comprometida, en cualquier momento y sin aprobación, y recibe el reemplazo de inmediato. |
| **Administrador** | Control excepcional | Suspende o reactiva manualmente. **Es el único que puede reactivar**: el sistema nunca lo hace solo. |
| **Sistema** | Vigilante de mora | Detecta la mora, envía los avisos previos sin duplicarlos, y ejecuta la suspensión automática al superarse el límite con su cascada sobre las credenciales. |

## 4. Requisitos funcionales

### RF-PAC-001: Revocación de credencial comprometida por autoservicio (CU-O55 / RF-O55.1)

El **Partner de integración** debe poder revocar una credencial **en cualquier momento y sin aprobación de nadie**.

Al revocar, el sistema debe:

1. Validar que la credencial **pertenece efectivamente a quien la revoca** (SRS L434). Una credencial de otro partner retorna HTTP 403.
2. Rechazar la revocación de una credencial **ya inactiva** (SRS L434) con HTTP 409: es una operación redundante y no debe generar una segunda entrada de revocación en la bitácora.
3. Marcar `Dim_CredencialAPI.activo=false` sobre esa credencial concreta.
4. **Emitir de inmediato una credencial de reemplazo** del **mismo entorno y con el mismo nombre** (RF-PAC-002).
5. Registrar en `Fact_HistorialAccesoPartner` con `tipo_cambio="revocacion_credencial"`, el `idcredencial` exacto afectado, `ejecutado_por="Partner"` y el `motivo` indicado.

**El autoservicio es deliberado, no una simplificación.** La revocación es reactiva ante un incidente de seguridad; exigir aprobación dejaría una credencial comprometida operando mientras alguien la autoriza (SRS L432).

**Disponible desde que el partner tiene su primera credencial**, en cualquier estado posterior de su ciclo de vida.

### RF-PAC-002: Reemplazo inmediato, sin interrumpir el resto (CU-O55 / RF-O55.1, RF-O55.2)

Junto con la revocación, el sistema debe emitir una credencial nueva **del mismo entorno y con el mismo nombre** que la revocada, con secreto nuevo y `activo=true`.

**El secreto se entrega una sola vez**, en la respuesta de la revocación, y no es recuperable después — misma regla que en la emisión (RN-PON-005 de #07).

**Las demás credenciales del partner siguen operando sin interrupción** (RF-O55.2). Revocar una no afecta a ninguna otra: es justo el motivo por el que #07 permite credenciales nombradas por sistema.

### RF-PAC-003: Avisos previos a la suspensión por mora (CU-O55)

**Ante mora, el sistema avisa antes de actuar.** Debe enviar avisos previos de suspensión en **dos momentos anteriores al límite** — por defecto **T-10 y T-5 días** sobre un límite de **15 días** de mora, todos configurables.

**No debe duplicar el mismo aviso dentro del mismo ciclo de mora** (SRS L436): antes de enviar, comprueba si ya existe ese aviso para ese partner en el ciclo vigente.

Cada aviso registra `tipo_cambio="aviso_previo_suspension"` con el momento (`T-10` / `T-5`) en `motivo`, `ejecutado_por="Sistema"`, y **sin cambiar el estado del partner** (`estado_anterior` = `estado_nuevo`).

**Si el partner regulariza entre un aviso y el siguiente, el ciclo se cierra y el aviso pendiente nunca se envía** (SRS L436). No requiere lógica de cancelación: es consecuencia natural de la condición de entrada, que solo considera facturas impagadas.

### RF-PAC-004: Suspensión automática por mora (CU-O55 / RF-O55.3)

**Superado el límite de mora, la suspensión es automática** (SRS L438), sin intervención humana.

Al suspender, el sistema debe:

1. Actualizar `Dim_Partner`: `activo=false`, `fecha_suspension=now`, `motivo_suspension` con la causa.
2. Ejecutar la **cascada** sobre las credenciales (RF-PAC-006).
3. Registrar `tipo_cambio="suspension_automatica"`, `ejecutado_por="Sistema"`, `motivo` con la causa y los días de mora.

**Efecto inmediato sobre el consumo:** a partir de ese momento, toda llamada a la API con cualquier credencial de ese partner debe rechazarse. Lo aplica `api-monitoring-and-billing` leyendo `Dim_Partner.activo` (RF-APM-001); este módulo solo fija el estado.

**«Inmediato» significa lo mismo aquí que al revocar (§ 15 D4).** La suspensión también escribe vía Kafka, así que también tiene los 5–15 s de ingesta. La cascada debe añadir a la **lista de denegación** cada credencial que desactiva, igual que hace la revocación (RNF-PAC-001). Sin eso, un partner suspendido seguiría consumiendo durante la ventana con **todas** sus credenciales a la vez — una fuga mayor que la que el módulo cierra en la revocación.

### RF-PAC-005: Suspensión y reactivación manual (CU-O55 / RF-O55.3)

Un **Administrador** puede suspender o reactivar manualmente, por causas distintas a la mora (por ejemplo, vencimiento de contrato o petición del cliente).

**Suspensión manual:** mismo efecto que la automática, con `tipo_cambio="suspension_manual"`, `ejecutado_por="Administrador"` y **motivo obligatorio**.

**Reactivación:**

1. Actualizar `Dim_Partner`: `activo=true`, y limpiar el snapshot de suspensión (`fecha_suspension` y `motivo_suspension` al centinela vacío).
2. Ejecutar la **cascada inversa selectiva** (RF-PAC-006).
3. Registrar `tipo_cambio="reactivacion"`, `ejecutado_por="Administrador"`.

**El sistema nunca reactiva solo** (RN-PAC-009). Aunque la mora que causó la suspensión ya se haya regularizado, la reactivación **siempre requiere confirmación manual de un Administrador**. No existe un proceso automático inverso a RF-PAC-004.

Reactivar un partner que **no está suspendido** es una operación redundante: retorna HTTP 409 y no genera entrada en la bitácora.

### RF-PAC-006: Regla de cascada (CU-O55 / RF-O55.3)

**Al suspender**, se desactivan **todas** las credenciales del partner, **de pruebas y de producción, sin excepción** (SRS L440), mediante actualización explícita de cada fila — no por validación lógica indirecta. Una credencial que figura activa mientras su partner está suspendido es una contradicción de estado, aunque el middleware de consumo la rechazara igualmente.

**Al reactivar**, se restituyen **únicamente las que estaban activas inmediatamente antes de la suspensión**. En concreto, **no se reactivan las credenciales que el propio partner había revocado por seguridad** (SRS L440): resucitar una credencial comprometida sería un fallo de seguridad grave, y es exactamente lo que esta regla previene.

**Cómo se conserva el conjunto activo previo (§ 15 D1).** La cascada de suspensión inserta **una fila de bitácora por cada credencial que desactiva**, con su `idcredencial` en el campo que ya existe para eventos sobre credenciales concretas. La reactivación lee las filas del **último evento de suspensión** de ese partner y restituye exactamente ese conjunto.

Consecuencia deliberada: una credencial que ya estaba inactiva cuando llegó la suspensión —porque el partner la revocó, o porque expiró— **no genera fila de cascada**, así que la reactivación **no la encuentra y no la restituye**. La regla de seguridad se cumple por construcción, no por una comprobación aparte que alguien pudiera olvidar.

El evento de cascada usa `tipo_cambio="desactivacion_por_cascada"` para distinguirse de `revocacion_credencial`: son cosas distintas y confundirlas es justo lo que hay que evitar.

### RF-PAC-007: Determinación de la mora (CU-O55)

El sistema debe evaluar periódicamente qué partners están en mora, calculando los días transcurridos desde el vencimiento de sus facturas impagadas.

Una factura **en disputa** (RN-APM-016) **no cuenta como mora** mientras el reclamo siga abierto: se excluyó del cobro automático precisamente porque está cuestionada, y suspender por ella castigaría al partner por ejercer su derecho a reclamar.

**Qué cuenta como mora aquí (§ 15 D2).** **Únicamente las facturas de excedente de API** (`Fact_Factura.tipo='excedente_api'`) impagadas y vencidas. La suscripción impagada **no** la gestiona este módulo: es competencia de `subscriptions-and-billing` (RF-SUSF-007), que suspende sobre `Fact_Suscripcion.estado`.

**Qué es exactamente «impagada» (§ 15 D3).** El vocabulario real de `Fact_Factura.estado_pago` tiene cuatro valores, y solo **uno** genera mora aquí:

| `estado_pago` | ¿Genera mora en este módulo? | Por qué |
|---|---|---|
| **`Pendiente`** y `fecha_vencimiento` pasada | ✅ **Sí** | Es la única que cuenta |
| `Pagada` | No | No hay deuda |
| `En disputa` | No | RN-PAC-015 — el reclamo sigue abierto |
| **`Fallida`** | **No** | **Es el disparador de `subscriptions-and-billing`** (RF-SUSF-007). Si contase también aquí, **dos módulos suspenderían por la misma factura** con umbrales distintos — exactamente lo que § 15 D2 existe para impedir |

**Cómo se llega de un partner a sus facturas (§ 15 D3).** `Fact_Factura` **no tiene `idpartner`**: su clave de cliente es **`id_cliente`**. La mora se resuelve por `Dim_Partner.idcliente → Fact_Factura.id_cliente`, nunca por un `idpartner` que no existe en esa tabla.

**Qué delimita el ciclo de mora.** La **factura vencida impagada más antigua** del partner. Sus días de mora son los que se comparan con T-10, T-5 y el límite, y su `id_factura` identifica el ciclo a efectos de no duplicar avisos (RNF-PAC-005). Si esa factura se paga y queda otra vencida, **empieza un ciclo nuevo** y los avisos vuelven a contar desde cero: es deuda distinta.

**Las dos suspensiones son independientes por origen**, y el acceso a la API exige **ambas condiciones a la vez**:

| Condición | Dueño | Tabla |
|---|---|---|
| Partner no suspendido | **este módulo** | `Dim_Partner.activo` |
| Suscripción vigente | `subscriptions-and-billing` | `Fact_Suscripcion.estado` |

Un cliente con la **suscripción suspendida** pierde el acceso a la API aunque su partner siga `activo=true`. Eso **no** lo aplica este módulo: lo comprueba el middleware de consumo de `api-monitoring-and-billing` (RF-APM-001), que debe verificar **las dos** condiciones. Hasta ahora solo verificaba el partner, así que esta decisión **cierra un hueco real**: nada impedía que un cliente con la suscripción suspendida siguiera consumiendo datos.

**Por qué no se arrastran mutuamente.** Suscripciones **reactiva automáticamente** tras el cobro exitoso (RN-SUSF-011), pero aquí **el sistema nunca reactiva solo** (RN-PAC-009). Si una suspensión arrastrase a la otra, ambos estados quedarían en contradicción permanente: Suscripciones intentaría reactivar lo que este módulo exige que reactive una persona.

### RF-PAC-008: Bitácora de todo evento de acceso (CU-O55 / RF-O55.4)

**Cada revocación, aviso, suspensión y reactivación queda registrada con su motivo, autor y fecha** (RF-O55.4), insertando una fila nueva en `Fact_HistorialAccesoPartner`. La tabla **nunca se actualiza ni se borra: solo admite INSERT** (RN-PAC-013).

`idcredencial` lleva el identificador de la credencial cuando el evento la afecta puntualmente (revocación), y el centinela **`-1`** cuando el evento es sobre el partner en general (avisos, suspensión, reactivación).

Valores de `tipo_cambio` que **este módulo** escribe:

| `tipo_cambio` | `idcredencial` | Cuándo |
|---|---|---|
| `revocacion_credencial` | la revocada | El partner revoca por seguridad (RF-PAC-001) |
| `desactivacion_por_cascada` | **cada** credencial desactivada | Una fila por credencial al suspender (§ 15 D1) |
| `aviso_previo_suspension` | `-1` | Avisos T-10 y T-5 (RF-PAC-003) |
| `suspension_automatica` | `-1` | Mora superada (RF-PAC-004) |
| `suspension_manual` | `-1` | Acción del Administrador (RF-PAC-005) |
| `reactivacion` | `-1` | Acción del Administrador (RF-PAC-005) |

`desactivacion_por_cascada` **no es lo mismo que** `revocacion_credencial`, y por eso son tipos distintos: la primera se revierte al reactivar, la segunda **nunca**. Confundirlas resucitaría credenciales comprometidas.

**Qué llevan `estado_anterior` y `estado_nuevo`.** El vocabulario es el del **estado de acceso del partner** (§ 9), no el del ciclo de onboarding de #07, y **nunca** el de la credencial:

| `tipo_cambio` | `estado_anterior` | `estado_nuevo` |
|---|---|---|
| `revocacion_credencial` | `Activo` | `Activo` |
| `desactivacion_por_cascada` | `Activo` | `Suspendido` |
| `aviso_previo_suspension` | `Activo` | `Activo` |
| `suspension_automatica` / `suspension_manual` | `Activo` | `Suspendido` |
| `reactivacion` | `Suspendido` | `Activo` |

Que la revocación y el aviso dejen ambos campos **iguales** no es un descuido: es la forma de decir en la bitácora que **el estado del partner no cambió**. Revocar una credencial no suspende a nadie, y avisar tampoco (RF-PAC-003).

### RF-PAC-009: Consulta del estado de acceso (CU-O55)

El sistema debe exponer el estado de acceso vigente en **dos lecturas distintas**, porque son dos preguntas distintas:

**a) El estado de un partner concreto** — `GET /partners/{id}/estado-acceso`. Su propio estado (activo o suspendido, con motivo y fecha si aplica), sus credenciales activas y su bitácora. Un partner suspendido **sí** puede consultar: es lectura y le sirve para entender por qué se le cortó. El Administrador puede consultar el de cualquiera.

**b) La cola de trabajo del Administrador** — `GET /partners/cola-acceso`, **solo Administrador**. Devuelve los partners **suspendidos** y los que están **en ciclo de mora con avisos ya enviados**, con sus días de mora y el último aviso enviado. Sin esta lectura, un Administrador tendría que consultar partner por partner para saber a quién le toca reactivar o a quién está a punto de cortársele el acceso — y la reactivación, que **solo** él puede hacer (RN-PAC-009), no tendría por dónde empezar.

Ambas son **derivadas**: «en mora» no está persistido en ninguna columna (RN-PAC-012) y se calcula al leer.

## 5. Requisitos no funcionales

### RNF-PAC-001: Inmediatez de la revocación (RNF-15, Principio V)

La revocación debe surtir efecto **de inmediato**: p95 ≤ 2 s desde la petición hasta que la credencial deja de servir. Es una acción reactiva ante un incidente de seguridad; cualquier ventana es una ventana de exposición.

> **Advertencia de diseño:** la ingesta de Pinot tarda 5–15 s. Una comprobación de vigencia que dependa solo de leer `Dim_CredencialAPI` **dejaría la credencial revocada operando durante esa ventana**. El diseño debe cerrarla (`/plan`).

### RNF-PAC-002: Autenticidad y revocabilidad (RNF-15)

Toda credencial es **revocable en cualquier momento**, y la revocación está siempre asociada a una identidad válida que la ejecuta. El control de propiedad es obligatorio: nadie revoca credenciales ajenas.

### RNF-PAC-003: Bitácora inmutable (RNF-16, Principio V)

El 100 % de las acciones de este módulo queda registrado con autor, acción, motivo y fecha. La bitácora no admite UPDATE ni DELETE.

### RNF-PAC-004: Continuidad operativa (RNF-22, Principio IX aplicado a acceso)

**La revocación de un acceso nunca deja operaciones activas sin regla de continuidad definida.** Aquí se concreta en dos garantías: revocar una credencial **entrega un reemplazo en el mismo acto** (el partner nunca queda sin vía de acceso por un incidente de seguridad), y suspender **no destruye** credenciales, solo las desactiva, de modo que la reactivación es siempre posible.

### RNF-PAC-005: No duplicación de avisos (RNF-20)

Los avisos previos no se repiten dentro del mismo ciclo de mora. Los momentos (T-10, T-5) y el límite (15 días) son **configurables sin modificar código**.

### RNF-PAC-006: Testabilidad (RNF-18)

Cobertura ≥ 80 %. Este módulo **no pertenece a la cadena crítica de despacho**, por lo que no le aplica el umbral reforzado del 95 %.

## 5.1 Declaración ISO/IEC 25010:2023 (Golden Rule de la constitución)

| Característica | Aplica | Justificación |
|---|---|---|
| **Functional Suitability** | ✅ | Trazable a CU-O55 y sus cuatro RF del catálogo. Cierra el ciclo de vida del acceso del partner. |
| **Reliability** | ✅ | La suspensión y su cascada deben ser atómicas en efecto: un partner suspendido con credenciales activas es un estado contradictorio. RF-PAC-006. |
| **Performance Efficiency** | ✅ | RNF-PAC-001 declara umbral para la revocación, que es la operación sensible al tiempo. |
| **Interaction Capability** | ⚠️ Parcial | Alcance BE limitado a RF-PAC-009. El detalle vive en `../frontend/spec.md`; la revocación es una acción destructiva que la UI debe presentar con cuidado. |
| **Security** | ✅ | **Característica dominante.** Es el mecanismo de respuesta ante incidente: revocación inmediata, control de propiedad, no resurrección de credenciales comprometidas, bitácora inmutable. |
| **Compatibility** | ⚠️ Parcial | Consume el contrato versionado del departamento; no expone integraciones externas propias. |
| **Maintainability** | ✅ | Propiedad de escritura repartida y documentada frente a #07 y #08 (§ 13). |
| **Flexibility** | ✅ | Umbrales de aviso y límite de mora configurables (RNF-PAC-005). |
| **Safety** | ❌ **No aplica** | Fuera de la cadena crítica registro → asignación → despacho → confirmación. Cortar el acceso de un partner impide consultar datos ya cerrados; **no retrasa la atención de ninguna víctima** ni influye en severidad o asignación de unidades. |

**Tie-breaker:** conflicto entre **Security** y **Functional Suitability** en RF-PAC-006 (cascada inversa) — restituir todas las credenciales sería más simple y más cómodo para el partner, pero resucitaría una credencial que él mismo revocó por estar comprometida. Se prioriza **Security** por la excepción de dominio del Tie-Breaker Mechanism (regla 3: datos sensibles). **Trade-off aceptado:** la reactivación requiere reconstruir el conjunto previo, lo que añade complejidad (§ 15 Q1); a cambio, ninguna credencial comprometida vuelve a la vida.

## 6. Reglas de negocio

### RN-PAC-001

El partner **revoca por sí mismo, sin aprobación de nadie y en cualquier momento**. Es autoservicio deliberado: la revocación es reactiva ante un incidente de seguridad, donde esperar autorización sería el peor comportamiento posible (SRS L432).

### RN-PAC-002

El sistema **valida que la credencial pertenezca efectivamente a quien la revoca** (SRS L434). Nadie revoca credenciales ajenas.

### RN-PAC-003

**No se permite revocar una credencial ya inactiva** (SRS L434). Es una operación redundante y no debe generar una segunda entrada de revocación sobre una credencial que ya no lo está.

### RN-PAC-004

Toda revocación **entrega un reemplazo en el mismo acto**, del mismo entorno y con el mismo nombre. El partner nunca queda sin vía de acceso por haber reaccionado a un incidente.

### RN-PAC-005

**Las demás credenciales del partner siguen operando sin interrupción** (RF-O55.2). Revocar una no afecta a ninguna otra.

### RN-PAC-006

**Ante mora, el sistema avisa antes de actuar**: dos avisos previos al límite, **sin duplicar el mismo aviso dentro del mismo ciclo** (SRS L436).

### RN-PAC-007

**Si el partner regulariza entre un aviso y el siguiente, el ciclo se cierra y el aviso pendiente nunca se envía** (SRS L436). Es consecuencia de la condición de entrada, no requiere cancelación explícita.

### RN-PAC-008

**Superado el límite de mora, la suspensión es automática** (SRS L438). No requiere intervención humana.

### RN-PAC-009

**El sistema nunca reactiva solo.** La reactivación **siempre** requiere confirmación manual de un Administrador, incluso si la mora que causó la suspensión ya fue regularizada. No existe proceso automático inverso a la suspensión.

### RN-PAC-010

**Regla de cascada:** al suspender se desactivan **todas** las credenciales, de pruebas y de producción, **sin excepción**, mediante actualización explícita de cada fila (SRS L440).

### RN-PAC-011

**Cascada inversa selectiva:** al reactivar se restituyen **únicamente** las credenciales que estaban activas antes de la suspensión. **No se reactivan las que el partner había revocado por seguridad** (SRS L440) — resucitar una credencial comprometida sería un fallo de seguridad grave.

### RN-PAC-012

**Fuente de verdad única.** El estado operativo del partner reside únicamente en `Dim_Partner.activo`. `fecha_suspension` y `motivo_suspension` son un **resumen del último evento**, no un historial paralelo que pueda contradecirlo (SRS L442). El historial completo vive en `Fact_HistorialAccesoPartner`.

### RN-PAC-013

`Fact_HistorialAccesoPartner` es **bitácora inmutable**: solo INSERT, nunca UPDATE ni DELETE.

### RN-PAC-014

**Ninguna consulta usa `IS NULL`.** Pinot no almacena nulos: las guardas comparan contra centinelas (`idcredencial = -1`, `motivo_suspension = ''`).

### RN-PAC-015

Una **factura en disputa no cuenta como mora** mientras el reclamo siga abierto. Suspender por una factura que el partner está cuestionando lo castigaría por ejercer su derecho a reclamar.

### RN-PAC-016

Un partner **suspendido conserva el acceso de lectura** a su propio estado, credenciales e historial. Es lo que le permite entender por qué se le cortó el acceso.

## 7. Entradas

### Para revocar una credencial (RF-PAC-001)
- `idcredencial` (INT, requerido, path param — debe pertenecer al partner del token).
- `motivo` (STRING, requerido, no vacío; ej. «credencial expuesta en repositorio público»).

### Para suspender manualmente (RF-PAC-005)
- `idpartner` (INT, requerido, path param).
- `motivo` (STRING, **obligatorio y no vacío**).

### Para reactivar (RF-PAC-005)
- `idpartner` (INT, requerido, path param).
- `motivo` (STRING, opcional, nota de la reactivación).

### Para consultar el estado de acceso (RF-PAC-009 a)
- `idpartner` (INT, requerido, path param; el partner solo puede consultar el suyo).

### Para consultar la cola del Administrador (RF-PAC-009 b)
- Sin parámetros obligatorios. Opcional: `estado` (`suspendidos` | `en_mora`, por defecto ambos) y paginación por cursor conforme a `api-standards.md`.

## 8. Salidas

### Respuestas exitosas
- **200 OK — Credencial revocada y reemplazada:** `{ "data": { "revocada": { "idcredencial": 88, "nombre_credencial": "plataforma-siniestros", "entorno": "Producción", "activo": false }, "reemplazo": { "idcredencial": 94, "nombre_credencial": "plataforma-siniestros", "entorno": "Producción", "client_id": "...", "client_secret": "<única vez>" } } }` — el secreto del reemplazo aparece **solo aquí**.
- **200 OK — Partner suspendido:** `{ "data": { "idpartner": 12, "activo": false, "fecha_suspension": "...", "motivo_suspension": "...", "credenciales_desactivadas": 3 } }`
- **200 OK — Partner reactivado:** `{ "data": { "idpartner": 12, "activo": true, "credenciales_restituidas": 2, "credenciales_no_restituidas": 1 } }` — el desglose hace visible que **no todas vuelven**: la revocada por seguridad sigue inactiva.
- **200 OK — Estado de acceso:** `{ "data": { "idpartner": 12, "activo": true, "en_mora": false, "avisos_enviados": [], "credenciales": [...], "historial": [...] } }`
- **200 OK — Cola del Administrador:** `{ "data": [ { "idpartner": 12, "nombrepartner": "...", "activo": false, "motivo_suspension": "...", "fecha_suspension": "...", "dias_mora": 21, "ultimo_aviso": "T-5" } ], "meta": { "suspendidos": 2, "en_mora": 1 } }` — `dias_mora` y `ultimo_aviso` son **derivados**, no columnas.

### Respuestas de error
- **400 Bad Request** — `motivo` ausente o vacío donde es obligatorio.
- **401 Unauthorized** — Token ausente, inválido o expirado.
- **403 Forbidden** — El partner intenta revocar una credencial ajena (RN-PAC-002) o consultar el estado de otro; o un rol distinto de Administrador intenta suspender, reactivar o **consultar la cola de acceso**.
- **404 Not Found** — `idcredencial` o `idpartner` inexistentes.
- **409 Conflict** — Revocar una credencial **ya inactiva** (RN-PAC-003).
- **409 Conflict** — Reactivar un partner que **no está suspendido** (RF-PAC-005).
- **409 Conflict** — Suspender un partner que **ya está suspendido**.

Formato conforme a `api-standards.md`.

## 9. Estados

### Estado de acceso del partner

| Estado | `Dim_Partner.activo` | Cómo se llega | Cómo se sale |
|---|---|---|---|
| **Activo** | `true` | Estado normal desde la incorporación (#07) | Suspensión automática (RF-PAC-004) o manual (RF-PAC-005) |
| **En mora, avisado** | `true` | Factura impagada supera T-10 o T-5 | Regularizar (vuelve a Activo) o superar el límite (pasa a Suspendido) |
| **Suspendido** | `false` | Mora superada o acción del Administrador | **Solo** reactivación manual de un Administrador (RN-PAC-009) |

> «En mora, avisado» **no es un estado persistido**: el partner sigue `activo=true`. Se deriva de la existencia de facturas impagadas y de los avisos ya registrados en la bitácora.

### Estado de una credencial

| Estado | `Dim_CredencialAPI.activo` | Se restituye al reactivar |
|---|---|---|
| **Activa** | `true` | — |
| **Desactivada por cascada** | `false` | **Sí** (RN-PAC-011) |
| **Revocada por el partner** | `false` | **No, nunca** (RN-PAC-011) |
| **Expirada** (pruebas vencidas, #07) | `false` | **No** — su vigencia caducó por tiempo |

**Las tres razones de `activo=false` son indistinguibles mirando solo `Dim_CredencialAPI`.** De ahí el gap de § 15 Q1.

### Transiciones

```
                  ┌──────────── regulariza el pago ────────────┐
                  │                                            │
                  ▼                                            │
   ┌──────────┐  factura impagada  ┌──────────────────┐        │
   │  Activo  │───── T-10, T-5 ───►│ En mora, avisado │────────┘
   └──────────┘                    └──────────────────┘
        │  ▲                                │
        │  │                       supera el límite (15 d)
        │  │                                ▼
        │  │                        ┌──────────────┐
        │  └── reactivación ────────│  Suspendido  │
        │      MANUAL (Admin)       └──────────────┘
        │      RN-PAC-009                   ▲
        └──── suspensión manual (Admin) ────┘

Revocar una credencial NO cambia el estado del partner: ocurre en cualquier punto.
```

## 10. Escenarios

### Escenario A: Revocación de credencial comprometida

Dado un partner con tres credenciales activas  
Y detecta que una quedó expuesta en un repositorio público  
Cuando la revoca indicando el motivo  
Entonces el sistema debe validar que la credencial le pertenece  
Y debe marcarla `activo=false`  
Y debe entregarle **de inmediato** una credencial de reemplazo del mismo entorno y con el mismo nombre, con su secreto **una sola vez**  
Y **las otras dos credenciales deben seguir operando sin interrupción**  
Y debe registrar `tipo_cambio="revocacion_credencial"` con el `idcredencial` exacto y el motivo.

### Escenario B: La ventana de exposición está cerrada 🎯

Dado un partner que acaba de revocar una credencial comprometida
Cuando intenta consumir la API de datos con esa misma credencial **de inmediato, sin esperar a la ingesta de Pinot**
Entonces debe rechazarse **ya**, no dentro de 15 segundos
Y si solo se rechaza tras una espera, la lista de denegación no está funcionando y **una credencial comprometida seguiría sirviendo datos** (RNF-PAC-001).

### Escenario C: Revocación de credencial ajena

Dado un partner autenticado  
Cuando intenta revocar una credencial que pertenece a otro partner  
Entonces el sistema debe rechazar con HTTP 403 **sin modificar nada**.

### Escenario D: Revocación de credencial ya inactiva

Dado una credencial que ya fue revocada  
Cuando el partner intenta revocarla de nuevo  
Entonces el sistema debe rechazar con HTTP 409  
Y **no debe generar una segunda entrada de revocación** en la bitácora.

### Escenario E: El reemplazo no choca de nombre consigo mismo

Dado un partner que revoca una credencial llamada «plataforma-siniestros»
Cuando el sistema emite el reemplazo **con el mismo nombre** en la misma operación
Entonces debe devolver 200
Y la comprobación de unicidad **no debe releer Pinot**: aún vería la revocada como activa y daría una colisión falsa que **haría fallar la revocación** — justo la operación que no puede fallar (§ 15 D1 de `research.md` Decision 4).

### Escenario F: Avisos previos sin duplicación

Dado un partner con una factura de excedente impagada  
Cuando se alcanza T-10  
Entonces el sistema debe enviar el aviso y registrarlo con `motivo="T-10"`, **sin cambiar el estado del partner**  
Y si el job vuelve a ejecutarse el mismo día, **no debe enviar un segundo aviso T-10**  
Y al alcanzarse T-5 debe enviar el segundo aviso, también una sola vez.

### Escenario G: Regularización entre avisos

Dado un partner que recibió el aviso T-10  
Cuando paga la factura antes de T-5  
Entonces **el aviso T-5 nunca debe enviarse**  
Y el ciclo de mora debe cerrarse sin suspensión.

### Escenario H: Suspensión automática con cascada

Dado un partner que superó el límite de mora tras ambos avisos  
Cuando se ejecuta la evaluación  
Entonces el sistema debe poner `Dim_Partner.activo=false` con fecha y motivo  
Y debe desactivar **todas** sus credenciales, de pruebas **y** de producción, sin excepción  
Y debe registrar `tipo_cambio="suspension_automatica"` con los días de mora  
Y toda llamada posterior a la API con cualquiera de sus credenciales debe rechazarse.

### Escenario I: Reactivación selectiva — el escenario que da sentido a la regla

Dado un partner con tres credenciales: A y B activas, y C que **él mismo revocó por seguridad** semanas antes  
Y es suspendido por mora, lo que desactiva las tres  
Cuando un Administrador lo reactiva  
Entonces deben restituirse **A y B**  
Y **C debe permanecer inactiva**: era una credencial comprometida y resucitarla sería un fallo de seguridad grave  
Y la respuesta debe informar de `credenciales_restituidas: 2` y `credenciales_no_restituidas: 1`.

### Escenario J: El sistema no reactiva solo

Dado un partner suspendido por mora  
Cuando paga íntegramente la deuda  
Entonces el sistema **no debe reactivarlo automáticamente**  
Y el partner debe permanecer suspendido hasta que un Administrador lo reactive explícitamente (RN-PAC-009).

### Escenario K: Reactivación redundante

Dado un partner que nunca fue suspendido  
Cuando un Administrador intenta reactivarlo  
Entonces el sistema debe rechazar con HTTP 409  
Y no debe generar una entrada de reactivación sin una suspensión real que la respalde.

### Escenario L: Suspensión manual con motivo obligatorio

Dado un contrato vencido  
Cuando el Administrador suspende al partner sin indicar motivo  
Entonces el sistema debe rechazar con HTTP 400  
Y con motivo debe suspenderlo con la misma cascada que la suspensión automática, registrando `tipo_cambio="suspension_manual"`.

### Escenario M: Factura en disputa no genera mora

Dado un partner cuya única factura impagada está **en disputa** abierta en Soporte  
Cuando se evalúa la mora  
Entonces **no debe contarse como mora**  
Y no deben enviarse avisos ni suspenderlo mientras el reclamo siga abierto (RN-PAC-015).

### Escenario N: El partner suspendido consulta su estado

Dado un partner suspendido  
Cuando consulta su estado de acceso  
Entonces debe recibir HTTP 200 con `activo=false`, el motivo y la fecha de suspensión  
Y debe poder ver su historial: es lo que le permite entender por qué se le cortó el acceso.

### Escenario O: Frontera con la suspensión de suscripción

Dado un cliente con la **suscripción suspendida** cuyo partner sigue `activo=true`
Cuando intenta consumir la API de datos
Entonces debe rechazarse con **403**: el acceso exige **las dos** condiciones (§ 15 D2)
Y al reactivarse la suscripción, un partner suspendido por **su propia mora** debe **seguir suspendido**: las dos suspensiones no se arrastran.

### Escenario P: La cola de trabajo del Administrador

Dado un departamento con dos partners suspendidos y uno en mora que ya recibió el aviso T-10
Cuando el Administrador consulta la cola de acceso
Entonces debe recibir los tres, con sus días de mora y el último aviso enviado
Y un partner que intente consultar esa cola debe recibir **403**: es la vista de trabajo del Administrador, no la suya.

### Escenario Q: La suspensión también corta de inmediato

Dado un partner con tres credenciales activas que es suspendido por mora
Cuando intenta consumir la API con **cualquiera** de las tres, **sin esperar a la ingesta**
Entonces las tres deben rechazarse **ya** (§ 15 D4)
Y si alguna sigue sirviendo, la cascada no alimentó la lista de denegación y la fuga es **mayor** que la que se cierra al revocar: son todas sus credenciales a la vez, no una.

## 11. Criterios de aceptación

### CA-PAC-001 (RF-O55.1)
El partner revoca su credencial sin aprobación de nadie; el sistema la marca inactiva y registra el evento con el `idcredencial` exacto, el motivo y el autor.

### CA-PAC-002 (RF-O55.1)
La revocación entrega **en el mismo acto** una credencial de reemplazo del mismo entorno y nombre, con su secreto expuesto una sola vez.

### CA-PAC-003 (RF-O55.2)
Revocar una credencial **no afecta** a ninguna otra del partner: las demás siguen activas y operando.

### CA-PAC-004 (RN-PAC-002)
Revocar una credencial ajena retorna 403 sin modificar nada.

### CA-PAC-005 (RN-PAC-003)
Revocar una credencial ya inactiva retorna 409 y no genera una segunda entrada en la bitácora.

### CA-PAC-006 (RN-PAC-006)
Se envían dos avisos previos (T-10 y T-5 por defecto) y **ninguno se duplica** dentro del mismo ciclo de mora. Los avisos no cambian el estado del partner.

### CA-PAC-007 (RN-PAC-007)
Si el partner regulariza entre avisos, el aviso pendiente **nunca se envía** y el ciclo se cierra sin suspensión.

### CA-PAC-008 (RF-O55.3)
Al superarse el límite, la suspensión ocurre **sin intervención humana**, deja `Dim_Partner.activo=false` con fecha y motivo, y desactiva **todas** las credenciales de ambos entornos.

### CA-PAC-009 (RF-O55.3, RN-PAC-011)
Al reactivar, se restituyen **solo** las credenciales que estaban activas antes de la suspensión. Una credencial revocada por el partner **permanece inactiva**. La respuesta desglosa restituidas y no restituidas.

### CA-PAC-010 (RN-PAC-009)
El sistema **no reactiva automáticamente** ni siquiera tras la regularización del pago: la reactivación exige acción explícita de un Administrador.

### CA-PAC-011 (RF-PAC-005)
Suspender sin motivo retorna 400. Reactivar un partner no suspendido retorna 409 sin entrada en la bitácora. Solo el Administrador puede suspender o reactivar; otros roles reciben 403.

### CA-PAC-012 (RN-PAC-015)
Una factura en disputa abierta no cuenta como mora: no dispara avisos ni suspensión.

### CA-PAC-013 (RF-O55.4, RN-PAC-013)
Los cinco tipos de evento insertan exactamente una fila con motivo, autor y fecha. Ninguna operación ejecuta UPDATE ni DELETE sobre la bitácora.

### CA-PAC-014 (RN-PAC-016)
Un partner suspendido puede consultar su estado, credenciales e historial (200); un partner que intenta consultar el estado de otro recibe 403.

### CA-PAC-015 (RNF-PAC-001)
La revocación surte efecto en p95 ≤ 2 s: transcurrido ese tiempo, la credencial revocada ya no sirve para consumir datos.

### CA-PAC-016 (RF-PAC-009 b)
El Administrador obtiene en una sola lectura los partners suspendidos y los que están en ciclo de mora con avisos enviados, con sus días de mora. Un partner que consulte esa cola recibe 403.

### CA-PAC-017 (RNF-PAC-001, § 15 D4)
Tras suspender a un partner, **ninguna** de sus credenciales sirve ya para consumir datos, **sin esperar** a la ingesta de Pinot.

### CA-PAC-018 (§ 15 D3)
Solo las facturas `tipo='excedente_api'` con `estado_pago='Pendiente'` y vencidas generan mora aquí. Una factura `Fallida` **no** suspende al partner: es competencia de Suscripciones.

## 12. Dependencias

- **`partner-api-onboarding` (#07):** emite las credenciales que este módulo invalida, y define `Dim_CredencialAPI` con `nombre_credencial` y `fecha_expiracion`. La emisión del reemplazo (RF-PAC-002) **reutiliza su servicio de emisión**, no lo duplica.
- **`api-monitoring-and-billing` (#08):** emite las facturas de excedente cuya mora dispara la suspensión, y **aplica** el corte de acceso leyendo `Dim_Partner.activo` en cada llamada (RF-APM-001). Este módulo fija el estado; aquel lo hace cumplir.
- **`subscriptions-and-billing`:** dueño de `Fact_Factura` y de su propia suspensión de suscripción (RF-SUSF-007) — ver § 15 Q2.
- **`gestion-tickets-soporte`:** marca las facturas en disputa (CU-O83 / RF-O83.2), que este módulo excluye de la mora.
- **`autenticacion-y-rbac`:** roles `Administrador` y `PartnerIntegracion` (idrol 15).

## 13. Fuera de alcance

- **Emisión inicial, nombrado y rotación planificada de credenciales:** dueño = `partner-api-onboarding` (CU-O49). Este módulo **invalida**; aquel **emite**. La única emisión que hace este módulo es el reemplazo inmediato de RF-PAC-002, y reutiliza el servicio de #07.
- **Expiración de credenciales de pruebas por tiempo:** dueño = `partner-api-onboarding` (RF-PON-006). Es un vencimiento, no una revocación.
- **Medición del consumo, límites y facturación:** dueño = `api-monitoring-and-billing`.
- **Aplicar el corte en cada llamada a la API:** dueño = `api-monitoring-and-billing` (RF-APM-001). Este módulo fija `Dim_Partner.activo`; el middleware de aquel lo lee.
- **Emisión y cobro de facturas, y suspensión de la suscripción:** dueño = `subscriptions-and-billing`.
- **Apertura y resolución de disputas:** dueño = `gestion-tickets-soporte`.
- **Pantallas y confirmaciones de acciones destructivas:** dueño = [`../frontend/spec.md`](../frontend/spec.md).

## 14. Supuestos

| Supuesto | Valor por defecto | Fundamento |
|---|---|---|
| Momentos de aviso previo | **T-10 y T-5 días** | `PortalPartnersAPI.md` L172; el SRS solo exige «dos momentos anteriores al límite». Configurable. |
| Límite de mora | **15 días** desde el vencimiento | `PortalPartnersAPI.md` L180. Configurable. |
| Frecuencia de evaluación de mora | **Diaria** | Suficiente para una granularidad de días; el SRS no la fija. |
| Motivo en la reactivación | **Opcional** | El SRS exige motivo al rechazar y al suspender, no al reactivar. |
| Vigencia del reemplazo tras revocar en pruebas | **Igual que la original** | Coherente con RF-PON-006; revocar no debe alargar ni acortar la vigencia. |
| Nombre del reemplazo | **El mismo que la revocada** | Lo exige RF-O55.1 explícitamente. Requiere liberar el nombre de la revocada para no chocar con la unicidad de RN-PON-014. |

## 15. Decisiones de diseño

### D1 — El conjunto activo previo se reconstruye desde la bitácora (RF-PAC-006 / RN-PAC-011)

**Decidido 2026-08-08 — opción B.**

**El problema.** El SRS exige restituir «únicamente las que estaban activas antes de la suspensión — no se reactivan credenciales que el propio partner había revocado por seguridad» (L440). Pero la cascada pone **todas** a `activo=false`, y después **las tres razones son indistinguibles** mirando `Dim_CredencialAPI`: desactivada por cascada, revocada por el partner, o expirada por tiempo. Sin resolverlo, la reactivación **resucita una credencial comprometida** — el fallo que RN-PAC-011 existe para prevenir.

**La decisión.** La cascada inserta **una fila de bitácora por cada credencial que desactiva**, con su `idcredencial`, bajo `tipo_cambio="desactivacion_por_cascada"`. La reactivación lee las filas del último evento de suspensión y restituye exactamente ese conjunto.

**Por qué esta y no otra.** No inventa nada: `Fact_HistorialAccesoPartner.idcredencial` existe precisamente para eventos sobre credenciales concretas, y la bitácora inmutable ya es la fuente del historial. Registrar en un campo de texto la lista serializada (A) obligaría a parsear una estructura dentro de un campo libre. Una columna `desactivada_por_cascada` en `Dim_CredencialAPI` (C) sería más rápida de consultar, pero añade un flag de estado que hay que limpiar entre ciclos — y un flag mal limpiado es exactamente cómo se resucita una credencial comprometida.

**La propiedad que hace segura esta opción.** Una credencial que **ya estaba inactiva** cuando llegó la suspensión no genera fila de cascada, así que la reactivación **no la encuentra y no la restituye**. La regla de seguridad se cumple **por construcción**, no por una comprobación aparte que alguien pudiera olvidar al refactorizar.

**Beneficio adicional:** queda auditable *qué* credenciales se desactivaron en cada suspensión, que es información valiosa por sí misma y que RF-O55.4 pide registrar.

**Coste asumido:** N filas por suspensión en vez de una. Irrelevante: un partner tiene unas pocas credenciales y las suspensiones son raras.

**Sin cambios de esquema.** El campo ya existe.

### D2 — Las dos suspensiones son independientes por origen (RF-PAC-007)

**Decidido 2026-08-08 — opción A.**

**El problema.** `subscriptions-and-billing` **ya suspende por mora** (RF-SUSF-007: `Fact_Suscripcion.estado='Suspendida'` cuando la factura queda `Fallida`). Este módulo introduce una segunda suspensión sobre `Dim_Partner.activo`. Sin una frontera clara, o bien un cliente moroso sigue consumiendo gratis, o bien se le suspende dos veces por lo mismo y la reactivación se vuelve ambigua.

**La decisión.** Cada departamento suspende **por lo suyo y sobre su propia tabla**:

| Suspensión | Dispara | Dueño | Tabla |
|---|---|---|---|
| **Del partner** | Facturas `tipo='excedente_api'` impagadas > 15 días | **este módulo** | `Dim_Partner.activo` |
| **De la suscripción** | Factura vigente en estado `Fallida` | `subscriptions-and-billing` | `Fact_Suscripcion.estado` |

**El acceso a la API exige ambas condiciones a la vez.** Lo comprueba el middleware de consumo de `api-monitoring-and-billing` (RF-APM-001), no este módulo.

**Por qué no se arrastran.** Suscripciones **reactiva automáticamente** tras el cobro exitoso (RN-SUSF-011), pero aquí **el sistema nunca reactiva solo** (RN-PAC-009). Si una arrastrase a la otra, ambos estados quedarían en contradicción permanente: Suscripciones intentaría reactivar lo que este módulo exige que reactive una persona. La opción de arrastre se descartó exactamente por eso, no por complejidad.

**Por qué no una regla única de mora.** Suspender aquí por cualquier factura impagada duplicaría la lógica que Suscripciones ya tiene, con umbrales distintos (15 días aquí, `Fallida` allá): dos módulos suspendiendo por la misma factura en momentos distintos.

**Esta decisión cierra un hueco real.** El middleware de #08 hoy solo comprueba `Dim_Partner.activo`, así que **nada impedía que un cliente con la suscripción suspendida siguiera consumiendo la API**. Añadir la comprobación de suscripción vigente es una **tarea derivada en el módulo #08**, ya registrada en su spec.

**Sin cambios de esquema.** Es una regla de negocio sobre tablas existentes.

### D3 — «Impagada» es solo `Pendiente` vencida, y la mora se resuelve por `id_cliente` (RF-PAC-007)

**Decidido 2026-08-10, durante `/speckit-analyze`, antes de implementar.**

**Los dos problemas.** La spec decía «facturas impagadas y vencidas» sin fijar qué valor de `estado_pago` es «impagada», y daba por hecho un camino de datos que **no existe**.

1. El vocabulario real de `Fact_Factura.estado_pago` es `{Pendiente, Pagada, Fallida, En disputa}`. **`Fallida` es precisamente el disparador de `subscriptions-and-billing`** (RF-SUSF-007). Si contase también aquí, dos módulos suspenderían por la misma factura con umbrales distintos — el escenario que § 15 D2 existe para impedir.
2. **`Fact_Factura` no tiene `idpartner`.** Su clave de cliente es `id_cliente`. Una consulta de mora escrita contra `idpartner` no fallaría: **devolvería siempre cero partners en mora**, el job pasaría sus tests con el doble en memoria y nadie se enteraría hasta que un moroso llevase meses consumiendo gratis. Es el mismo fallo que el `idcondado` inexistente que apareció en #08.

**La decisión.** Mora aquí = `tipo='excedente_api'` **y** `estado_pago='Pendiente'` **y** `fecha_vencimiento` pasada. El camino es `Dim_Partner.idcliente → Fact_Factura.id_cliente`. El ciclo lo delimita la **factura vencida impagada más antigua**.

**Consecuencia de implementación.** `FacturaRepository` no expone hoy ninguna lectura de vencidas impagadas — solo `list_by_cliente(limit=20)` y `find_by_suscripcion_periodo`. Hay que añadirla, y el `limit` por defecto de 20 **no sirve** para un job que barre todo el padrón.

### D4 — La suspensión cierra su ventana de exposición igual que la revocación (RF-PAC-004, RNF-PAC-001)

**Decidido 2026-08-10, durante `/speckit-analyze`, antes de implementar.**

**El problema.** El diseño cerraba con la lista de denegación la ventana de ingesta de 5–15 s **solo al revocar**. Pero la suspensión escribe por el mismo Kafka y sufre el mismo retraso, y ahí la fuga es **mayor**: no es una credencial, son **todas** las del partner a la vez, y el partner ya ha demostrado que no paga.

**La decisión.** La cascada de RF-PAC-006 añade a la lista de denegación **cada** credencial que desactiva, con el mismo TTL de 60 s. La reactivación, simétricamente, **retira** de la lista las que restituye — si no, el partner reactivado seguiría rechazado hasta que caducase el TTL.

**Por qué no se dejó como estaba.** Sería incoherente: el módulo entero se justifica por que un acceso indebido se corte *ya*, y aceptar 15 s de fuga en la suspensión mientras se cierran en la revocación es una asimetría sin fundamento. El coste es nulo — la lista ya existe por Decision 2.

**Limitación heredada:** sigue viviendo en `LocMemCache`, por proceso. Es la misma deuda declarada en `plan.md`, no una nueva.
