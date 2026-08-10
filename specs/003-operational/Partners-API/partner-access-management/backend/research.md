# Phase 0 Research — Gestión de Acceso de Partners

Decisiones técnicas previas al diseño. Cubre CU-O55 en sus cuatro flujos: revocación, avisos, suspensión y reactivación.

Las dos decisiones de mayor calado ya están cerradas en `spec.md` § 15 (**D1** reconstrucción del conjunto activo previo, **D2** independencia de las dos suspensiones); aquí se recogen sus consecuencias de diseño más el resto de decisiones técnicas.

## Decision 1: Contract-first OpenAPI, integrado en la superficie de gestión

- **Decision:** `contracts/partner-access-management.openapi.yaml` con los endpoints de revocación, suspensión, reactivación y consulta de estado, todos bajo **JWT** (`bearerAuth`).
- **Rationale:** ninguno de estos endpoints lo consume una máquina: la revocación la hace una persona del área técnica del partner reaccionando a un incidente, y la suspensión/reactivación un Administrador. La API de datos por credencial pertenece a #08, y son superficies distintas (§ 15 D2 de aquel módulo).
- **Alternatives considered:** permitir revocar con la propia credencial de API (rechazado: una credencial comprometida podría usarse para revocar *otras* del mismo partner — sería darle al atacante la herramienta de sabotaje).

## Decision 2: Cerrar la ventana de exposición tras revocar — lista de denegación en memoria

- **El problema.** La revocación escribe vía Kafka y **Pinot tarda 5–15 s en ingerirla**. Si el middleware de consumo de #08 solo lee `Dim_CredencialAPI`, **una credencial recién revocada seguiría sirviendo datos durante esa ventana** — justo lo contrario de lo que necesita una respuesta a incidente (RNF-PAC-001 exige p95 ≤ 2 s).
- **Decision:** al revocar, además de publicar el evento, se añade el `client_id` a una **lista de denegación en memoria** con TTL algo mayor que la ventana de ingesta (por defecto **60 s**). La autenticación de #08 la consulta **antes** de resolver contra Pinot: si el `client_id` está en la lista, rechaza sin más.
- **Por qué así:** cierra la ventana sin introducir infraestructura nueva y sin tocar el modelo de datos. Pasado el TTL, la revocación ya es visible en Pinot y la lista deja de hacer falta — es un puente, no una fuente de verdad paralela (lo que violaría RN-PAC-012).
- **Interacción crítica con #08.** `api-monitoring-and-billing` Decision 2 contempla cachear el resultado de la verificación bcrypt para aliviar el p95. **Esa caché positiva debe consultarse DESPUÉS de la lista de denegación, y la revocación debe invalidar su entrada.** Si se implementan en el orden inverso, la caché de rendimiento **alarga** la ventana de exposición en vez de acortarla. Es una dependencia de orden entre dos módulos y hay que dejarla escrita.
- **Limitación declarada, no resuelta:** la lista vive en `LocMemCache`, que es **por proceso**. Con un proceso es exacta; con N procesos, la revocación solo cerraría la ventana en el que la atendió. **No bloquea hoy** (despliegue de un proceso), pero es la **misma deuda** que el throttle de #08: escalar horizontalmente exige un almacén compartido. Se registra una sola vez, en `plan.md`.
- **Hallazgo relacionado, fuera de alcance:** `LogoutService` de `cuentas_clientes` tiene el **mismo patrón sin resolver** — cierra la sesión en Pinot vía Kafka, así que un JWT robado seguiría siendo válido durante la ventana de ingesta. No es competencia de este módulo, pero conviene que quede anotado.
- **Alternatives considered:** aceptar la ventana y documentarla (rechazado: 15 s de exposición ante una credencial comprometida contradice el propósito del CU); un almacén compartido tipo Redis (rechazado en esta fase: componente nuevo, y con un proceso no aporta).

## Decision 3: El reemplazo reutiliza el servicio de emisión de #07

- **Decision:** `RevocarCredencialService` **no implementa** la generación de credenciales: invoca el servicio de emisión de `partner-api-onboarding` (que ya genera con `secrets.token_urlsafe(32)`, hashea con bcrypt y entrega el secreto una sola vez).
- **Rationale:** dos implementaciones de generación de secretos es un riesgo de seguridad, no una duplicación cosmética: si una se refuerza y la otra no, el sistema tiene una puerta más débil que nadie está mirando.
- **Alternatives considered:** duplicar la lógica en este módulo (rechazado por lo anterior).

## Decision 4: La colisión de nombre al reemplazar se resuelve en memoria, no releyendo Pinot

- **El problema.** RF-O55.1 exige que el reemplazo lleve **el mismo nombre** que la revocada, pero RN-PON-014 de #07 exige que `nombre_credencial` sea único **entre las activas** del mismo partner y entorno. Al revocar, la anterior pasa a inactiva y libera el nombre — **pero Pinot tarda 5–15 s en verlo**. Una comprobación de unicidad que relea Pinot detectaría una colisión falsa y **haría fallar la revocación**, que es justo la operación que no puede fallar.
- **Decision:** revocación y emisión del reemplazo ocurren en la **misma operación**, y la comprobación de unicidad excluye explícitamente la credencial que se acaba de revocar, cuyo estado se conoce **en memoria**. No se relee Pinot para decidir.
- **Rationale:** es una aplicación directa de la regla del proyecto de no releer lo que se acaba de escribir. Aquí el coste de ignorarla no sería un dato desactualizado, sino un fallo funcional en una respuesta a incidente.
- **Alternatives considered:** dar al reemplazo un nombre derivado (`nombre-2`) (rechazado: RF-O55.1 exige el mismo nombre, y renombrar obligaría al partner a cambiar configuración justo cuando está apagando un fuego); esperar a la ingesta antes de emitir (rechazado: añade 15 s a una operación urgente).

## Decision 5: La cascada escribe una fila de bitácora por credencial

- **Decision:** conforme a `spec.md` § 15 D1, `SuspenderPartnerService` inserta una fila con `tipo_cambio="desactivacion_por_cascada"` **por cada** credencial que desactiva, con su `idcredencial`. `ReactivarPartnerService` lee las filas del último evento de suspensión y restituye exactamente ese conjunto.
- **Rationale:** ya argumentado en la spec. Lo relevante para el diseño es que **la reactivación no necesita saber por qué una credencial está inactiva**: solo restituye las que aparecen en la cascada. Las revocadas y las expiradas sencillamente no están en esa lista.
- **Consecuencia de implementación:** la suspensión debe leer las credenciales activas **antes** de desactivarlas, y esa lectura sí puede venir de Pinot (nada se acaba de escribir en ese momento).
- **Alternatives considered:** las tres de § 15 D1.

## Decision 6: Job diario de mora, con la evaluación derivada de los datos

- **Decision:** `evaluacion_mora_job.py` corre a diario, calcula los días de mora de cada partner desde el vencimiento de sus facturas `tipo='excedente_api'` impagadas, y decide: enviar aviso T-10, enviar aviso T-5, o suspender.
- **Rationale:** granularidad de días; el SRS no exige más precisión. El patrón de job periódico ya existe en el proyecto (`dunning_job.py`, `timeout_despacho_job.py`).
- **No duplicación de avisos:** antes de enviar, consulta `Fact_HistorialAccesoPartner` por (`idpartner`, `tipo_cambio="aviso_previo_suspension"`, `motivo`) dentro del ciclo de mora vigente. El «ciclo» se delimita por la fecha de vencimiento de la factura que originó la mora.
- **La regularización no necesita lógica de cancelación:** si el partner paga, la factura deja de estar impagada y **desaparece de la condición de entrada** del job. El aviso pendiente simplemente nunca se evalúa (RN-PAC-007). Es una propiedad del diseño, no una rama de código.
- **Alternatives considered:** evaluación por evento al cambiar el estado de una factura (rechazado: la mora avanza con el tiempo, no con eventos — nadie «hace» que pasen 10 días).

## Decision 7: Facturas en disputa excluidas por consulta, no por marca propia

- **Decision:** la evaluación de mora excluye las facturas cuya `estado_pago` sea el de disputa, leyendo el estado que ya mantiene `subscriptions-and-billing`. Este módulo **no** mantiene su propia marca.
- **Rationale:** RN-PAC-015. La disputa la abre Soporte y la refleja Suscripciones; duplicar la marca aquí crearía una segunda verdad que puede divergir.
- **Alternatives considered:** copiar el estado de disputa a `Dim_Partner` (rechazado por la duplicación de verdad).

## Decision 8: La reactivación es explícita y sin atajos automáticos

- **Decision:** no existe ningún proceso, job ni disparador que reactive un partner. Solo el endpoint que ejecuta un Administrador.
- **Rationale:** RN-PAC-009, explícito en el SRS. Y es lo que hace viable la independencia con Suscripciones (§ 15 D2): si aquí hubiera reactivación automática, chocaría con la de RN-SUSF-011 y ambos estados quedarían peleados.
- **Cómo se protege de una regresión:** un test dedicado que verifica que, tras regularizar el pago, el partner **sigue suspendido**. Es el tipo de regla que un refactor bienintencionado («¿por qué no lo reactivamos solo si ya pagó?») rompería sin darse cuenta.
- **Alternatives considered:** reactivación automática tras el cobro (rechazado por el SRS y por el conflicto con Suscripciones).

## Decision 9: Idempotencia de la revocación por estado, no por clave

- **Decision:** revocar una credencial ya inactiva devuelve **409**, no un 200 idempotente.
- **Rationale:** el SRS es explícito (L434) y la razón es de auditoría: una segunda entrada de revocación sobre una credencial ya revocada ensuciaría la bitácora, que es el respaldo de RF-O55.4. El 409 informa sin escribir.
- **Matiz:** eso no exime del `Idempotency-Key` de `api-standards.md` para el reintento de red de la **primera** revocación, donde sí debe haber un solo efecto.
- **Alternatives considered:** 200 idempotente (rechazado: contradice el SRS y difumina la diferencia entre «ya estaba» y «acabo de hacerlo»).

## Decision 10: Consulta de estado con control de propiedad, accesible estando suspendido

- **Decision:** el endpoint de estado exige que el partner consulte **su propio** perfil (403 en otro caso), pero **no** exige que esté activo.
- **Rationale:** RN-PAC-016. Es lectura, no afecta al estado, y es justo donde el partner entiende por qué se le cortó el acceso y qué debe pagar. Bloquearlo convertiría una suspensión en un callejón sin salida.
- **Alternatives considered:** bloquear todo acceso al suspendido (rechazado: empeora la experiencia sin ganar seguridad, y el dato que ve es suyo).

## Tie-Breaker (constitución)

- **Conflicto:** **Security** vs **Functional Suitability** en RF-PAC-006 (cascada inversa selectiva) — restituir *todas* las credenciales al reactivar sería más simple de implementar y más cómodo para el partner, pero resucitaría una credencial que él mismo revocó por estar comprometida.
- **Prioridad:** **Security**, por la excepción de dominio del Tie-Breaker Mechanism (regla 3: datos sensibles). El acceso a la API entrega geolocalización e identidad de personas involucradas en accidentes.
- **Trade-off aceptado:** la reactivación necesita reconstruir el conjunto previo desde la bitácora (§ 15 D1), lo que añade una lectura y N filas por suspensión. A cambio, **ninguna credencial comprometida vuelve a la vida**, y la garantía es estructural, no una comprobación que se pueda olvidar.
- **Segundo conflicto, menor:** **Security** vs **Performance Efficiency** en Decision 2 — la lista de denegación añade una consulta antes de cada autenticación. Se prioriza Security por la misma regla; el coste es una lectura en memoria, despreciable frente al bcrypt que viene después.
- **Safety:** **no aplica** — cortar el acceso de un partner impide consultar datos de casos ya cerrados; no retrasa la atención de ninguna víctima ni influye en severidad o asignación de unidades. No hay override.
