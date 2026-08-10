# Phase 0 Research — Monitoreo y Facturación de API

Decisiones técnicas previas al diseño. Cubre CU-O51, CU-O52, CU-O53 y CU-O54.

Las dos decisiones de mayor calado ya están cerradas y aplicadas en `spec.md` § 15 (**D1** tarifa de excedente, **D2** throttle técnico ≠ cupo comercial); aquí se recogen solo sus consecuencias de diseño.

## Decision 1: Contract-first OpenAPI, con dos superficies separadas

- **Decision:** un único `contracts/api-monitoring-and-billing.openapi.yaml`, pero con **dos grupos de endpoints claramente separados**: la **API de datos** que el partner consume (`/datos/*`, autenticada por credencial) y la **API de gestión** (`/partners/{id}/metricas`, `/logs-api`, `/reportes-consumo`, autenticada por JWT humano).
- **Rationale:** son dos superficies con autenticación, consumidores y ciclo de versionado distintos. Mezclarlas en un mismo grupo llevaría a aplicarles el mismo esquema de seguridad por descuido.
- **Alternatives considered:** dos archivos de contrato (rechazado: el módulo es uno y separar duplicaría los schemas compartidos); un solo grupo indiferenciado (rechazado: es justo el error que se quiere evitar).

## Decision 2: Autenticación por credencial de API, no por JWT

- **Decision:** clase de autenticación DRF propia (`CredencialAPIAuthentication`) que resuelve `client_id` + `client_secret` contra `Dim_CredencialAPI` verificando el hash **bcrypt**, y deja en el request el partner, el entorno y el cliente resueltos. **Solo** aplica a los endpoints de datos.
- **Rationale:** el partner es un sistema, no una persona: no hay sesión que iniciar ni token que refrescar. Reutilizar `JWTSessionAuthentication` obligaría a que un servidor externo mantuviera una sesión humana, que es justo lo que las credenciales de API evitan.
- **Coste declarado:** verificar bcrypt en **cada** petición es caro por diseño (es su propósito). Con el volumen objetivo (decenas de peticiones/segundo) hay que medirlo contra RNF-APM-002 (p95 ≤ 2 s); si aprieta, la mitigación es cachear en memoria el resultado de la verificación por `client_id` durante una ventana corta, **nunca** debilitar el factor de coste de bcrypt.
- **Alternatives considered:** JWT firmado emitido al partner (rechazado: añade un flujo de renovación y no aporta sobre la credencial); comparar el secreto en claro (rechazado, viola RNF-PON-002).

## Decision 3: El registro del consumo no bloquea la respuesta

- **Decision:** la publicación de `Fact_APIIntegracion` y `Fact_LogLlamadaAPI` ocurre **después** de resolver la respuesta, en el mismo ciclo de petición pero fuera de su camino crítico, y **cualquier excepción se captura y se registra** sin propagarse al partner.
- **Rationale:** RN-APM-005 y el Tie-Breaker de la spec. Perder una medición es ingreso potencialmente no cobrado; caerse la API rompe la integración de una aseguradora en producción. El segundo daño es mayor y menos reversible.
- **Cómo se implementa:** middleware DRF que envuelve la vista, mide la latencia, y al terminar publica ambos eventos dentro de un `try/except` que registra el fallo con nivel `error` y un marcador reconciliable (`idpartner`, `endpoint`, timestamp).
- **Alternatives considered:** cola en memoria con worker (rechazado en esta fase: añade un componente y el proyecto no tiene broker de tareas); escritura síncrona bloqueante (rechazado: convierte un fallo de medición en una caída de servicio).

## Decision 4: Middleware único para medir, no instrumentación por vista

- **Decision:** un solo middleware registra **todas** las llamadas a los endpoints de datos, incluidas las que terminan en 4xx y 5xx. Las vistas no saben que se las está midiendo.
- **Rationale:** RF-O52.1 exige contabilizar *cada* petición atendida y RN-APM-009 exige registrar los errores con su código para autodiagnóstico. Si cada vista tuviera que acordarse de registrar, la primera que se olvide crea un agujero silencioso en la facturación.
- **Alternatives considered:** decorador por vista (rechazado: se olvida); registrar solo los 2xx (rechazado: rompe RN-APM-009 y oculta al partner sus propios errores).

## Decision 5: Agregación en tiempo de consulta, sin tabla de agregados

- **Decision:** métricas, reporte mensual y cálculo de excedente se resuelven con `SUM`/`COUNT`/`AVG` sobre `Fact_APIIntegracion` filtrando por `idpartner`, `entorno='Producción'` y rango de fechas. **No** se crea tabla de agregados ni proceso de consolidación.
- **Rationale:** RN-APM-003, que viene directo del SRS: *«el dato nace completo»*. Una tabla de agregados introduce un segundo lugar donde la verdad puede divergir, y obliga a un job de consolidación que puede fallar.
- **Riesgo asumido y su umbral:** con volúmenes altos, agregar sobre millones de filas puede degradar el reporte. Pinot está diseñado precisamente para eso, y los reportes **no** están en la cadena crítica (RNF-04 admite 2 s). Si algún día no basta, la salida es un índice de agregación en Pinot, no una tabla materializada mantenida a mano.
- **Recordatorio operativo:** Pinot aplica `LIMIT 10` implícito a toda consulta sin `LIMIT`. Toda agregación de este módulo debe declararlo.

## Decision 6: El corte mensual es un job propio, hermano del de Suscripciones

- **Decision:** `facturacion_excedente_job.py` en `apps/partners/jobs/`, con su comando de gestión, **separado** de `apps/suscripciones/jobs/facturacion_mensual_job.py`.
- **Rationale:** son dos cortes con reglas distintas — el de suscripción factura el plan; este factura solo el excedente medido, con su propia verificación de no duplicación (RF-O54.3) y su propia política de reintentos (1 h / 6 h / 24 h). Meterlos en el mismo job acoplaría dos departamentos y haría que un fallo del excedente arrastrara la facturación regular.
- **Reutilización:** la **emisión** del documento sí usa `FacturaRepository.create()` de Suscripciones — este módulo calcula y decide, Suscripciones persiste. Coherente con el reparto de propiedad de la spec § 13.
- **Alternatives considered:** extender `GeneracionFacturaService` (rechazado: mete lógica de Partners en Suscripciones); ejecutar el excedente dentro del job mensual existente (rechazado por el acoplamiento de fallos).

## Decision 7: Reintentos por estado persistido, no por proceso vivo

- **Decision:** los reintentos de 1 h, 6 h y 24 h **no** se implementan con esperas en memoria. Cada intento fallido persiste `Fact_Factura.reintentos` y `resultado_ultimo_reintento`; el job, al ejecutarse, recoge los pendientes cuyo momento de reintento ya venció y los reprocesa.
- **Rationale:** un `sleep` de 24 horas en un proceso muere con el proceso. RF-O54.4 y RN-APM-014 exigen que la factura **nunca** quede sin crearse en silencio, así que el estado del reintento tiene que sobrevivir a un reinicio del contenedor. El proyecto ya tiene el patrón: `dunning_job.py` en Suscripciones.
- **Consecuencia:** el job debe correr con una frecuencia menor que la espera más corta (1 h). Con ejecución horaria, los tres escalones se respetan con precisión suficiente.
- **Alternatives considered:** `time.sleep` encadenado (rechazado: no sobrevive a reinicios); broker de tareas con reintentos nativos (rechazado en esta fase: componente nuevo).

## Decision 8: La verificación de no duplicación se hace contra Pinot, con su ventana asumida

- **Decision:** antes de emitir, `SELECT` sobre `Fact_Factura` por `id_cliente` + `periodo` + `tipo='excedente_api'`. Si aparece, no se emite.
- **Rationale:** RF-O54.3 y RN-APM-012. Es la única defensa contra el doble cobro.
- **Por qué aquí sí vale «consultar y luego escribir», a diferencia de RN-APM-004:** el corte mensual es un proceso **único y secuencial**, no concurrente. La ventana de ingesta de 5–15 s solo sería un problema si dos cortes del mismo período corrieran a la vez, y eso se evita con un cerrojo simple de ejecución. La prohibición de RN-APM-004 aplica al **registro de consumo**, que sí es de alta frecuencia.
- **Refuerzo:** el `Idempotency-Key` de `api-standards.md` sobre la emisión da una segunda red por si el job se dispara dos veces.

## Decision 9: Throttle por partner con la infraestructura actual

- **Decision:** clase de throttling DRF propia que lee `Dim_Partner.limitellamadasminuto` y aplica el límite por credencial, devolviendo `429` con `Retry-After`. Se apoya en el caché de Django (`LocMemCache`).
- **Rationale:** § 15 D2. Es el mecanismo que ya declara `api-standards.md`.
- **Limitación declarada, no resuelta:** `LocMemCache` es **por proceso**. Con un proceso el límite es exacto; con N procesos el límite efectivo sería N veces mayor. **No bloquea hoy** (el despliegue es de un proceso), pero escalar horizontalmente exigirá un contador compartido. Queda como deuda explícita en `plan.md`.
- **Contabilidad:** una petición rechazada con 429 se registra en `Fact_LogLlamadaAPI` pero **no** en `Fact_APIIntegracion` — no se atendió, así que no es consumo facturable (§ 15 D2).

## Decision 10: Alertas de cuota evaluadas en el corte, no en cada llamada

- **Decision:** la comparación del consumo acumulado contra el cupo (RF-APM-010) la hace un job periódico, no cada petición.
- **Rationale:** evaluar el acumulado del mes en cada llamada obligaría a una agregación por petición — insostenible al volumen objetivo y contrario a RNF-APM-002. Como **la cuota no bloquea** (RN-APM-002), la alerta no necesita ser instantánea: unos minutos de retraso no cambian ninguna decisión.
- **No duplicación:** antes de enviar, el job comprueba si ya se emitió ese aviso para ese partner y período (mismo patrón que los avisos de mora de CU-O55 y que la expiración de credenciales de #07).
- **Alternatives considered:** evaluar en el middleware de cada llamada (rechazado por coste); contador incremental en caché (rechazado: se pierde al reiniciar y el dato de verdad está en Pinot).

## Decision 11: Nivel de acceso y zonas, resueltos por composición de lo que ya existe

- **Decision:** el filtro de RF-APM-002 usa `Dim_Plan.severidades_desbloqueadas` del plan vigente; el de RF-APM-003 usa `Dim_Preferencias_Cliente.zonas_geograficas`, **reutilizando `HistorialEmergenciasService.condados_desde_preferencias()`** que ya implementó `seguimiento-cierre-de-casos` para RF-O82.2.
- **Rationale:** no inventar un segundo mecanismo de zonas. Si la regla de qué zonas ve un cliente cambia, debe cambiar en un solo sitio.
- **Fail-closed:** cliente sin zonas configuradas → conjunto vacío, nunca el completo (RN-APM-008). Exponer siniestralidad de zonas no contratadas es una fuga, no una comodidad.
- **Alternatives considered:** tabla propia de zonas del partner (rechazado: duplicaría la fuente de verdad).

## Decision 12: `Dim_EstadoIntegracion` se siembra en este módulo

- **Decision:** seed con los tres estados alineados a los estados derivados de `partner-api-onboarding` § 9: `Pruebas activo`, `Producción activa`, `Suspendido`. El middleware resuelve el estado vigente del partner en el momento de la llamada y lo congela en `Fact_APIIntegracion.idestadointegracion`.
- **Rationale:** la tabla existe pero está **vacía** (0 filas). Sin ella, `idestadointegracion` apunta a nada y se pierde la capacidad de reportar consumo histórico con el estado que el partner tenía entonces (RF-APM-005).
- **Alternatives considered:** guardar el estado como STRING denormalizado (rechazado: el esquema ya define la FK y el catálogo).

## Tie-Breaker (constitución)

- **Conflicto:** **Reliability** vs **Functional Suitability** en RF-APM-004 — si la escritura del consumo falla, ¿se rechaza la petición (medición exacta, servicio caído) o se responde igual (servicio disponible, medición con hueco)?
- **Prioridad:** **responder al partner**. No hay Safety en juego, así que aplica la regla 2 del mecanismo; aquí Functional Suitability se lee como «el partner recibe el dato que contrató», que es la función del módulo frente al cliente.
- **Trade-off aceptado:** una medición perdida es ingreso potencialmente no cobrado, mitigado con registro del fallo y reconciliación posterior. Una API caída rompe la integración de una aseguradora en producción, con daño reputacional y contractual mayor y menos reversible.
- **Safety:** **no aplica** — este módulo está fuera de la cadena crítica registro → asignación → despacho → confirmación, y su API es de solo lectura sobre casos ya cerrados. No hay override.
