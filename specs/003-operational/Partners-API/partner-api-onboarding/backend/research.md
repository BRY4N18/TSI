# Phase 0 Research — Onboarding de Partners API

Decisiones técnicas previas al diseño. Cubre CU-O48, CU-O49 y CU-O50.

## Decision 1: Contract-first OpenAPI para los endpoints de partners

- **Decision:** Definir primero `contracts/partner-api-onboarding.openapi.yaml` con todos los endpoints de CU-O48/O49/O50 bajo `/api/v1/partners` y `/api/v1/contrato-integracion`, conforme a `api-standards.md`.
- **Rationale:** Es el Principio VI de la constitución (API-First Compatibility) aplicado a su caso más literal: este módulo **es** la puerta de las integraciones externas. Además CU-O50 obliga a publicar la especificación como artefacto de negocio, no solo como documentación interna.
- **Alternatives considered:**
  - Implementar ViewSets y documentar después (rechazado: drift spec↔código, y aquí el contrato es entregable al partner).
  - Contrato solo en markdown (rechazado: sin validación automática ni tipos generables para el frontend).

## Decision 2: App Django `apps/partners/` con capas Vista → Servicio → Repositorio

- **Decision:** Nueva app `backend/apps/partners/` con `views/`, `services/` y `permissions.py`; acceso a datos en `backend/core/repositories/partners/`.
- **Rationale:** Patrón vinculante de `architectural-patterns.md`, idéntico a `accidentes/`, `soporte_cliente/` y `suscripciones/`. Una app por departamento mantiene el acoplamiento bajo que exige RNF-17.
- **Alternatives considered:**
  - Colgar los partners de `suscripciones/` porque el cupo sale del plan (rechazado: son departamentos distintos con responsables distintos; la dependencia es de lectura, no de propiedad).
  - Una sola app `partners/` para los tres módulos del departamento (**aceptado parcialmente**): la app es compartida, pero los servicios se separan por módulo para que `api-monitoring-and-billing` y `partner-access-management` no reabran archivos de este.

## Decision 3: Escritura exclusiva vía Kafka

- **Decision:** Toda mutación de `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` y `Dim_VersionContratoAPI` publica al topic Kafka homónimo. Ningún INSERT directo a Pinot.
- **Rationale:** Regla vinculante del proyecto; Pinot es solo lectura desde Django.
- **Consecuencia operativa que sí afecta al diseño:** Pinot tarda **5–15 s** en ingerir. **Ningún servicio de este módulo puede releer de Pinot algo que acaba de escribir** dentro de la misma operación. Afecta directamente a dos flujos: la respuesta de emisión de credencial (RF-PON-004) debe construirse con los valores **en memoria**, no releyendo la fila; y las validaciones de unicidad (Decision 6) leen el estado *previo*, no el que se está escribiendo.
- **Alternatives considered:** dual-write Pinot+Kafka (rechazado: inconsistencia y complejidad).

## Decision 4: Autenticación JWT + rol nuevo «Partner de integración»

- **Decision:** Endpoints protegidos con `Authorization: Bearer`. Tres permisos DRF: `EsAdministrador` (registro, asignación de plan, resolución de promoción), `EsDesarrolladorAPIs` (registro, asignación de plan, consulta) y `EsPartner` (autoservicio sobre **su propio** perfil). El rol «Partner de integración» **no existe todavía** y debe darse de alta en `autenticacion-y-rbac`.
- **Control de propiedad obligatorio:** todo endpoint de autoservicio verifica que el `idpartner` del path pertenece al `idcliente` del token. Sin esa comprobación, un partner podría emitir o revocar credenciales de otro. Es el mismo defecto que ya apareció tres veces en el proyecto (Red Operativa, Emergencias y los tres endpoints de Soporte corregidos en `decisiones-pendientes.md` #14): se documenta aquí para no repetirlo por cuarta vez.
- **Alternatives considered:**
  - Reutilizar el rol «Cliente» para el partner (rechazado: el partner tiene superficie propia y necesita permisos distintos de los del cliente titular).
  - Autenticar al partner con su propia credencial de API (rechazado en este módulo: esa credencial sirve para **consumir datos**, CU-O51; el portal de onboarding es sesión humana con JWT).

## Decision 5: Generación y almacenamiento del secreto

- **Decision:** Secreto generado con `secrets.token_urlsafe(32)` (≥256 bits de entropía) y persistido **solo** como hash **bcrypt** en `Dim_CredencialAPI.client_secret_hash`, reutilizando el patrón de `core/repositories/cuentas_clientes/credential_repository.py` (`bcrypt.hashpw` + `gensalt(rounds=BCRYPT_ROUNDS)`).
- **Rationale:** No introduce dependencias nuevas ni una segunda convención criptográfica en el proyecto. bcrypt es resistente a fuerza bruta por diseño, que es lo que exige RNF-PON-002.
- **Regla de implementación:** el secreto en claro existe **solo** dentro del stack de la petición de creación. No se registra en logs, trazas, mensajes de error ni **en el evento Kafka** — al topic viaja únicamente el hash. Es fácil de violar por accidente al depurar.
- **Alternatives considered:**
  - SHA-256 sin salt (rechazado: vulnerable a tablas precomputadas).
  - Cifrado reversible para poder mostrar el secreto de nuevo (rechazado: contradice RF-O49.2 y RN-PON-005 — la irrecuperabilidad es el requisito, no un efecto colateral).

## Decision 6: Unicidad e invariantes a nivel de aplicación

- **Decision:** Pinot no soporta `UNIQUE` ni FK declarativos, así que se validan en el servicio, antes de publicar a Kafka: (a) un solo partner por cliente (RN-PON-002); (b) `nombre_credencial` único entre las credenciales activas del mismo partner y entorno (RN-PON-014); (c) una sola versión `vigente` por servicio (RF-PON-011).
- **Rationale:** Mismo criterio ya aplicado y aceptado en `RegistrarTicketService.registrar()` para «una factura, una disputa abierta» (`decisiones-pendientes.md` #14).
- **Limitación asumida y declarada:** por el retraso de ingesta (Decision 3), dos peticiones concurrentes podrían superar ambas la comprobación y crear un duplicado. Se acepta: el volumen de registro de partners es muy bajo (acción manual de un Administrador) y el daño es reparable. **No se acepta** para el registro de consumo de CU-O52, que es de alta frecuencia — ese módulo debe resolverlo por su cuenta.
- **Alternatives considered:** tabla puente o constraint en otro motor (rechazado: introduciría un segundo almacén transaccional solo para esto).

## Decision 7: El cupo se deriva del plan, no se elige

- **Decision:** `AsignarPlanAccesoService` resuelve la suscripción vigente del cliente (`Fact_Suscripcion`), lee `Dim_Plan.limites` (JSON) y **congela** `api_calls_mes` / `api_calls_minuto` en `Dim_Partner`. Un cupo enviado en el cuerpo de la petición se ignora.
- **Rationale:** RF-O48.3 lo exige, y congelarlo replica el patrón ya establecido con `Fact_Suscripcion.precio`: un cambio posterior del catálogo de planes no debe alterar retroactivamente a un partner ya incorporado, porque el cupo es la base del cálculo de excedente de CU-O54.
- **Dependencia abierta:** `Dim_Plan.limites` declara hoy `api_calls_mes` pero **no** `api_calls_minuto` (RN-SUSF-019). La extensión está aprobada y pendiente de aplicar en `subscriptions-and-billing`. Mientras tanto, `limites` sin `api_calls_minuto` retorna HTTP 422 en vez de asumir un valor.
- **Alternatives considered:** leer el plan en cada consulta en vez de congelarlo (rechazado: haría variable el cupo histórico y rompería la reproducibilidad de la facturación).

## Decision 8: Expiración de credenciales de pruebas — cálculo perezoso + job de notificación

- **Decision:** El estado «vencida» se **deriva de la comparación `fecha_expiracion < ahora`** en cada lectura y en la validación de uso; el job periódico solo se encarga de **notificar** (aviso previo T-7 y aviso al vencer) y de materializar `activo=false` con su entrada en la bitácora.
- **Rationale:** Si el vencimiento dependiera únicamente del job, una caída de este dejaría credenciales vencidas operativas — un fallo abierto en un control de seguridad. Derivarlo hace que el sistema falle hacia el lado seguro (Principio II).
- **Por qué el centinela es `253402300799000` y no `0` ni nulo:** una credencial de producción «que no expira» necesita un valor que **nunca** satisfaga `fecha_expiracion < ahora`. Con `0` o `Long.MIN_VALUE` —que es lo que Pinot pone por defecto— toda credencial de producción figuraría como vencida desde el primer día. Ver Decision 9.
- **No duplicación de avisos:** antes de enviar, el job consulta `Fact_HistorialAccesoPartner` por (`idpartner`, `idcredencial`, `tipo_cambio`) dentro del ciclo de vigencia vigente. Mismo patrón que los avisos de mora de CU-O55.
- **Alternatives considered:** solo job (rechazado, fail-open); solo cálculo perezoso (rechazado: RF-PON-006 exige notificar y dejar rastro en bitácora).

## Decision 9: Centinelas explícitos en lugar de `NULL`

- **Decision:** Ninguna regla de este módulo se expresa contra `NULL`. Los campos opcionales declaran `defaultNullValue` en `esquemas.json` y las guardas comparan contra el centinela: `planapi <> ''`, `fecha_expiracion < ahora`, `idcredencial <> -1`.
- **Rationale:** **Pinot no almacena `NULL`** en este proyecto — ninguna de las 78 tablas habilita `nullHandlingEnabled`. Cada nulo se materializa como un centinela que elige Pinot, y los que elige rompen reglas de negocio: `planapi` se guardaba como el string `'null'`, dejando **siempre cierta** la guarda de RF-PON-004; `fecha_expiracion` se guardaba como `Long.MIN_VALUE`, lo que habría hecho que el job de expiración revocara **todas** las credenciales de producción. Detalle completo y medición en `spec.md` § 15 D2.
- **Estado:** aplicado y verificado contra Pinot en ejecución (`database/verifica_partners.py`, 16/16).
- **Alternatives considered:** habilitar `nullHandlingEnabled` solo en este departamento (rechazado: crearía una segunda convención frente a los otros ocho; Maintainability tiene prioridad por defecto según el Tie-Breaker).

## Decision 10: Versionado del contrato de integración por servicio

- **Decision:** `Dim_VersionContratoAPI` con **FK obligatoria a `Dim_Servicio`**. La versión vigente, las soportadas y la fecha de retiro se consultan y filtran por servicio.
- **Rationale:** `Dim_Servicio` no es un registro único: contiene *API Despacho*, *API Registro de accidentes* y *Portal Cliente*, y `Fact_APIIntegracion.idservicio` ya discrimina el consumo por servicio. Sin la FK, el versionado de los tres colapsaría en una sola línea temporal. Justificación de normalización completa en `spec.md` § 15 D1.
- **Alternatives considered:** extender `Dim_Servicio` con campos de versión (rechazado: pierde la relación servicio ↔ N versiones); servir el OpenAPI estáticamente sin persistencia (rechazado: RF-O50.3 dejaría de ser consultable y choca con RNF-20).

## Decision 11: Notificaciones al contacto técnico

- **Decision:** Los seis avisos del módulo (aprobación, rechazo con motivo, aviso previo de vencimiento, vencimiento consumado, emisión de credencial y solicitud pendiente para el Administrador) se emiten mediante el mecanismo de notificación ya existente en el proyecto, con `contacto_tecnico_gmail` como destinatario.
- **Rationale:** No introducir un canal nuevo. El contacto técnico es un campo obligatorio de `Dim_Partner` precisamente para esto.
- **Pendiente de verificar en `/speckit-tasks`:** qué servicio de notificación concreto reutilizar (Ventas y CRM tiene `Fact_NotificacionVentas`, Soporte notifica resoluciones). Debe decidirse leyendo el código antes de implementar, no asumirse.

## Tie-Breaker (constitución)

- **Conflicto:** **Security** vs **Interaction Capability** en RN-PON-005 — el secreto se entrega una sola vez y es irrecuperable; si el partner lo pierde, debe rotar.
- **Prioridad:** **Security**, por la excepción de dominio del Tie-Breaker Mechanism (regla 3: datos sensibles en tránsito y en reposo). La irrecuperabilidad es el requisito explícito de RF-O49.2, no un efecto colateral que convenga suavizar.
- **Trade-off aceptado:** fricción para el partner que pierde su secreto. Se mitiga sin ceder en seguridad: RF-PON-005 hace la rotación no disruptiva (emitir una credencial nueva no interrumpe las demás), y el frontend debe hacer inequívoco que el valor no se podrá recuperar (`../frontend/spec.md`).
- **Safety:** **no aplica** — este módulo está fuera de la cadena crítica registro → asignación → despacho → confirmación. No hay override.
