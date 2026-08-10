# Portal de Partners y API — Historia Completa del Módulo (con mapeo a base de datos)

> Redactado en el mismo formato que los demás módulos del sistema, con escenarios de error explícitos para cada CU. Basado íntegramente en el contenido ya existente de `PortalPartnersAPI.md` — no se inventa ninguna regla de negocio nueva; donde se añade un escenario de error que no estaba escrito explícitamente en el original pero se desprende directamente de una condición de entrada ya confirmada, se marca como **🔎 Inferido** para que quede claro qué es fuente original y qué es extensión lógica sujeta a validación.

## Casos de Uso finales del módulo

| Código | Caso de uso | Actor |
| ------ | ----------- | ----- |
| CU-O71 | Registrar partner | Administrador / Desarrollador de APIs |
| CU-O80 | Asignar plan de acceso | Administrador / Desarrollador de APIs |
| CU-O72 | Solicitar y activar acceso a Sandbox y a Producción | Cliente / Partner |
| CU-O73 | Consultar credenciales y métricas | Cliente / Partner |
| CU-O74 | Logs, alertas de cuota y errores en tiempo real | Desarrollador de APIs |
| CU-O75 | Reporte mensual de consumo | Cliente / Administrador |
| CU-O84 | Revocar credenciales por compromiso de seguridad | Cliente / Partner |
| CU-O78 | Facturación de excedentes | Sistema |
| CU-O83 | Gestionar excepción de facturación automática | Sistema |
| CU-O82 | Registrar disputa sobre consumo o facturación | Cliente / Partner |
| CU-O81 | Notificar aviso previo de suspensión por mora | Sistema |
| CU-O79 | Suspensión automática por mora | Sistema |
| CU-O76 | Suspensión/reactivación manual por mora o vencimiento | Administrador |

---

## Modelo de datos base

- **`Dim_Partner`** es el núcleo del módulo. Un partner **es siempre** un `Dim_Cliente` ya existente (`FK idcliente` obligatorio, no nulo) — no existe un partner sin cliente detrás. Su estado operativo vive **únicamente** en `Dim_Partner.activo`: es la única fuente de verdad de si el partner está habilitado o suspendido. `fecha_suspension` y `motivo_suspension` son un snapshot rápido del último evento, no un historial.
- **`Dim_CredencialAPI`** tiene una fila por cada credencial concreta de un partner en un `entorno` específico (Sandbox o Producción). Un mismo partner puede tener credenciales activas simultáneas en ambos entornos, cada una con su propio ciclo de vida (`activo`).
- **`Fact_APIIntegracion`** y **`Fact_LogLlamadaAPI`** se escriben **juntas, en el mismo instante, por cada llamada real a la API** — no hay job de agregación posterior. `Fact_LogLlamadaAPI` guarda el detalle técnico completo de esa llamada puntual (`endpoint`, `metodohttp`, `codigohttp`, `iporigen`, `latenciams`); `Fact_APIIntegracion` guarda esa misma llamada con columnas orientadas a reporte y facturación (`llamadas=1`, `errores=0` o `1` según el `codigohttp`, `latencia`). **Regla confirmada:** los reportes mensuales (CU-O75) y el cálculo de excedente (CU-O78) se resuelven en el momento de la consulta, agregando (`SUM`/`COUNT`) sobre `Fact_APIIntegracion` filtrado por `idpartner`, `entorno` y rango de fechas — no existe una tabla de agregados pre-calculados.
- `Fact_APIIntegracion.idestadointegracion` (FK a `Dim_EstadoIntegracion`) es una **copia histórica** del estado del partner al momento exacto de esa llamada (ej. "Sandbox" o "Producción") — sirve para poder filtrar/reportar consumo histórico incluso si el partner cambió de estado después. **No es la fuente de verdad del estado actual** (esa es `Dim_Partner.activo` + el `entorno` vigente en `Dim_CredencialAPI`).
- **`Fact_HistorialAccesoPartner`** es la bitácora inmutable de todo evento relevante del ciclo de vida del partner — nunca se sobrescribe, cada evento es una fila nueva. `idcredencial` es **nullable**: se llena solo cuando el evento afecta a una credencial puntual (ej. revocación); queda en `NULL` cuando el evento es sobre el partner en general (ej. suspensión).

**Regla de cascada confirmada (suspensión y reactivación):** al suspender un partner — automáticamente (CU-O79) o manualmente (CU-O76) — se actualiza explícitamente `Dim_CredencialAPI.activo = false` en **todas** las credenciales de ese partner (Sandbox y Producción, sin excepción), mediante un `UPDATE` en cascada, no mediante validación lógica indirecta. Al reactivar (CU-O76), se revierte la cascada de forma simétrica: `Dim_CredencialAPI.activo = true` únicamente en las credenciales que estaban activas antes de la suspensión.

**Regla de promoción a Producción confirmada:** la solicitud de pasar de Sandbox a Producción la inicia el propio partner, dentro de **CU-O72**. La activación efectiva de la credencial de Producción la ejecuta un Administrador mediante un proceso técnico de ciclo de vida de integración (capa táctica, fuera del detalle de este módulo operativo) — es un proceso semi-automatizado: el partner solicita, un humano de la capa técnica ejecuta.

---

## La historia del módulo

### Capítulo 1 — Nace el partner

**CU-O71 (Administrador / Desarrollador de APIs) — Registrar partner**

- `Dim_Partner` — **INSERT**: `idpartner` (PK), `idcliente` (FK), `nombrepartner`, `contacto_tecnico_nombre`, `contacto_tecnico_gmail`, `activo=true`, `planapi=NULL`, `limitellamadasmes=NULL`, `limitellamadasminuto=NULL`, `sandbox_activado=NULL`, `sandbox_expiracion=NULL`, `fecha_suspension=NULL`, `motivo_suspension=NULL`.
- `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial=NULL`, `tipo_cambio="registro"`, `ejecutado_por`, `motivo=NULL`, `estado_anterior=NULL`, `estado_nuevo="Registrado"`, `fecha_cambio=now`.
- **En este punto el partner existe pero no tiene plan ni límites asignados — no puede solicitar Sandbox todavía.**

**Camino de error 1:** se intenta registrar un partner sobre un `idcliente` que no existe en `Dim_Cliente` → el sistema rechaza el registro antes de insertar; el flujo correcto es dar de alta primero al cliente en el módulo Cuentas-Clientes.

**Camino de error 2 — 🔎 Inferido:** se intenta registrar un segundo `Dim_Partner` sobre un `idcliente` que ya tiene un partner activo → no está definido explícitamente en el documento original si un cliente puede tener múltiples partners simultáneos o si la relación es 1:1. **Pendiente de confirmación antes de implementar.**

**CU-O80 (Administrador / Desarrollador de APIs) — Asignar plan de acceso**

- `Dim_Partner` — **UPDATE**: `planapi`, `limitellamadasmes`, `limitellamadasminuto`.
- `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial=NULL`, `tipo_cambio="asignacion_plan"`, `ejecutado_por`, `motivo` (nombre del plan asignado), `estado_anterior="Registrado"`, `estado_nuevo="Plan asignado"`, `fecha_cambio=now`.
- **Solo a partir de aquí el partner queda habilitado para ejecutar CU-O72.**

**Camino de error — 🔎 Inferido:** se intenta asignar un plan a un partner con `Dim_Partner.activo=false` (ej. uno dado de baja o suspendido antes de llegar a operar) → debería rechazarse, siguiendo el mismo principio que el resto del módulo (ninguna acción de habilitación procede sobre un partner inactivo). No está confirmado explícitamente en el original, se documenta como extensión lógica razonable.

---

### Capítulo 2 — El partner prueba y luego pasa a operar

**CU-O72 (Cliente / Partner) — Solicitar y activar acceso a Sandbox y a Producción**

**Sub-flujo A — Activación de Sandbox (autoservicio completo):**

- Condición de entrada: `Dim_Partner.planapi IS NOT NULL` (ya pasó por CU-O80).
- `Dim_Partner` — **UPDATE**: `sandbox_activado=now`, `sandbox_expiracion` (now + periodo configurado, ej. 30 días).
- `Dim_CredencialAPI` — **INSERT**: `idcredencial` (PK), `idpartner`, `idcliente`, `client_secret_hash` (generado y encriptado), `entorno="Sandbox"`, `activo=true`, `fecha_creacion=now`.
- `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial` = la recién creada, `tipo_cambio="activacion_sandbox"`, `ejecutado_por="Partner"`, `estado_anterior="Plan asignado"`, `estado_nuevo="Sandbox activo"`, `fecha_cambio=now`.
- Compromiso de aprovisionamiento: menos de 24 horas.

**Camino de error 1 (confirmado por la condición de entrada):** el partner intenta activar Sandbox sin tener plan asignado (`planapi IS NULL`) → el sub-flujo se rechaza antes de cualquier escritura; el partner permanece en estado "Registrado" hasta que un Administrador ejecute `CU-O80`.

**Camino de error 2 — 🔎 Inferido:** el partner intenta activar Sandbox por segunda vez mientras ya tiene una credencial de Sandbox activa (`entorno="Sandbox"`, `activo=true`) → no está definido si el sistema debe rechazar el duplicado, invalidar la anterior, o permitir credenciales Sandbox múltiples. **Pendiente de confirmación.**

**Camino de error 3 — 🔎 Inferido:** vence `sandbox_expiracion` sin que el partner haya solicitado Producción → no hay CU definido en el módulo original que describa qué ocurre al vencimiento (¿se desactiva la credencial automáticamente? ¿se notifica? ¿se re-otorgan 30 días más?). **Gap de especificación real, no resuelto por este documento.**

**Sub-flujo B — Solicitud de promoción a Producción (iniciada por el partner):**

- El partner, tras validar su integración en Sandbox, solicita el paso a Producción dentro de este mismo CU.
- `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial=NULL`, `tipo_cambio="solicitud_promocion_produccion"`, `ejecutado_por="Partner"`, `estado_anterior="Sandbox activo"`, `estado_nuevo="Pendiente de aprobación"`, `fecha_cambio=now`.
- **La activación efectiva no la ejecuta este CU.** Un Administrador, mediante el proceso técnico de ciclo de vida de integración (fuera de este módulo operativo), aprueba y ejecuta:
  - `Dim_CredencialAPI` — **INSERT**: segunda fila, `entorno="Producción"`, `client_secret_hash` nuevo, `activo=true`, `fecha_creacion=now`. (La credencial de Sandbox permanece activa en paralelo, no se elimina.)
  - `Fact_HistorialAccesoPartner` — **INSERT**: `tipo_cambio="activacion_produccion"`, `ejecutado_por="Administrador"`, `estado_anterior="Pendiente de aprobación"`, `estado_nuevo="Producción activa"`, `fecha_cambio=now`.

**Camino de error 1:** el partner solicita promoción a Producción sin haber pasado por Sandbox (`estado_anterior` distinto de "Sandbox activo") → el sub-flujo B no aplica; la ruta obligatoria es siempre Registrado → Plan asignado → Sandbox activo → Pendiente de aprobación, sin atajos.

**Camino de error 2 — 🔎 Inferido:** el Administrador **rechaza** la promoción a Producción → el documento original no define un `tipo_cambio="rechazo_promocion_produccion"` ni un estado de retorno explícito. Extensión lógica razonable: el partner regresaría a `estado_nuevo="Sandbox activo"` con un `motivo` de rechazo, pero esto **no está confirmado** en la fuente y debe validarse antes de implementar.

---

### Capítulo 3 — La vida diaria del partner

**CU-O73 (Cliente / Partner) — Consultar credenciales y métricas**

**Tablas (solo lectura):**

- `Dim_CredencialAPI` filtrado por `idpartner`: credenciales activas, separadas por `entorno`.
- `Fact_APIIntegracion` filtrado por `idpartner`, `entorno="Producción"`, agregado (`SUM(llamadas)`, `SUM(errores)`, `AVG(latencia)`) sobre el periodo vigente — **nunca mezcla consumo de Sandbox con Producción**, ni siquiera para el mismo partner.

**Camino de error — 🔎 Inferido:** un partner suspendido (`Dim_Partner.activo=false`) intenta ejecutar esta consulta → como es de solo lectura y no afecta el estado del sistema, es razonable que se le siga permitiendo consultar su propio historial aunque no pueda hacer llamadas reales a la API. **No confirmado explícitamente**, pero coherente con que ningún otro CU de este módulo restrinja la lectura.

**CU-O74 (Desarrollador de APIs) — Logs, alertas de cuota y errores en tiempo real**

**Tablas (solo lectura):**

- `Fact_LogLlamadaAPI` filtrado por `idpartner`/`idcredencialapi`, ordenado por `fechallamada` descendente: consola de logs con `endpoint`, `metodohttp`, `codigohttp`, `iporigen`, `latenciams`.
- Alerta (notificación saliente, sin escritura en el modelo) cuando el conteo de llamadas del periodo (leído sobre `Fact_APIIntegracion`) se acerca o supera `limitellamadasmes`/`limitellamadasminuto` de `Dim_Partner`.

**Regla de negocio confirmada, no un error:** **no hay bloqueo automático del servicio al superar la cuota** — es solo alerta informativa. El exceso se resuelve después, vía `CU-O78` (facturación de excedentes). Esta es una decisión de modelo de negocio *pay-as-you-go*, documentada explícitamente para que nadie la "corrija" por error asumiendo que debería bloquear.

**Camino de error real — códigos HTTP de error de la propia API:** cada llamada con `codigohttp` de error (4xx/5xx) queda registrada igual (`Fact_LogLlamadaAPI.codigohttp`, `Fact_APIIntegracion.errores=1`) — el partner puede diagnosticar sus propios fallos de integración directamente desde este CU, sin intervención de un Administrador.

**CU-O75 (Cliente / Administrador) — Reporte mensual de consumo**

**Tablas (solo lectura):**

- `Fact_APIIntegracion` filtrado por `idpartner`, `entorno="Producción"` y periodo del mes, agregado por `SUM(llamadas)`, `SUM(errores)`, `AVG(latencia)`.

**Camino de error — 🔎 Inferido:** se solicita el reporte de un mes sin ninguna llamada registrada (partner recién activado en Producción o sin uso ese periodo) → el agregado simplemente devuelve cero en todas las métricas; no hay una condición de "error" real, es un caso límite normal del `SUM`/`AVG` sobre conjunto vacío.

**CU-O84 (Cliente / Partner) — Revocar credenciales por compromiso de seguridad**

- `Dim_CredencialAPI` — **UPDATE**: `activo=false` sobre la fila puntual de la credencial comprometida (identificada por `idcredencial`, elegida por el partner entre las que tiene activas).
- `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial` = la credencial exacta afectada, `tipo_cambio="revocacion_credencial"`, `ejecutado_por="Partner"`, `motivo` (texto libre, ej. "credencial expuesta en repositorio público"), `estado_anterior="Activa"`, `estado_nuevo="Revocada"`, `fecha_cambio=now`.
- `Dim_CredencialAPI` — **INSERT** inmediato de reemplazo: nueva fila, mismo `idpartner` y mismo `entorno` que la revocada, `client_secret_hash` nuevo, `activo=true`, `fecha_creacion=now`.
- Disponible en cualquier momento del ciclo de vida del partner desde "Sandbox activo" en adelante, sin depender de aprobación de nadie más — acción reactiva y de autoservicio.

**Camino de error 1:** el partner intenta revocar una credencial que no le pertenece (`idcredencial` de otro `idpartner`) → rechazo directo; la validación de propiedad es obligatoria antes del `UPDATE`.

**Camino de error 2:** el partner intenta revocar una credencial que ya está `activo=false` (ya revocada o suspendida en cascada) → operación redundante, no debería generar una segunda fila de "revocación" en `Fact_HistorialAccesoPartner` sobre una credencial ya inactiva.

**Camino de error 3 — 🔎 Inferido:** el partner intenta revocar una credencial mientras `Dim_Partner.activo=false` (partner suspendido) → dado que la cascada de suspensión (CU-O76/CU-O79) ya dejó todas las credenciales en `activo=false`, este CU no tendría ninguna credencial "Activa" sobre la cual operar — el propio estado de los datos impide el error, no hace falta una validación adicional.

---

### Capítulo 4 — Fin de mes: facturación de excedentes

**CU-O78 (Sistema) — Facturación de excedentes**

- Lectura: `SUM(Fact_APIIntegracion.llamadas)` filtrado por `idpartner`, `entorno="Producción"` y el periodo cerrado, comparado contra `Dim_Partner.limitellamadasmes`.
- Si `SUM(llamadas) > limitellamadasmes`: `Fact_Factura` (módulo Suscripciones-Facturación) — **INSERT**: `id_cliente` (el `idcliente` del partner), `tipo="excedente_api"`, `monto_total` calculado sobre el excedente, `estado_pago="Pendiente"`, `periodo`, `fecha_emision=now`.

**Camino de error (definido explícitamente como CU-O83):** el cálculo o la emisión de la factura falla en el momento del corte (ej. `Fact_APIIntegracion` incompleta o servicio caído) → no se reintenta silenciosamente dentro de este mismo CU, se delega a `CU-O83`.

**CU-O83 (Sistema) — Gestionar excepción de facturación automática**

- Se dispara cuando `CU-O78` falla al calcular o emitir la factura para un partner en el corte mensual.
- Política asumida por defecto **(⚠️ a confirmar con el equipo de negocio antes de implementar):** 3 reintentos automáticos, con 1 hora de espera entre cada uno. Cada intento actualiza `Fact_Factura.reintentos` y `resultado_ultimo_reintento`.
- **Si se agotan los 3 reintentos sin éxito:** se genera una alerta a un Administrador o Desarrollador de APIs para resolución manual. `Fact_Factura.estado_pago` queda en un estado que refleje el fallo (ej. `"Error de generación"`) — **regla explícita: nunca debe quedar silenciosamente sin crearse**, porque eso ocultaría un excedente real no facturado.

**CU-O82 (Cliente / Partner) — Registrar disputa sobre consumo o facturación**

- `Fact_Reclamo` (módulo Soporte-Cliente) — **INSERT**: `tipo_incidencia="API-partner"`, `id_factura` = la factura cuestionada.
- `Fact_Factura` — **UPDATE**: `estado_pago="En disputa"` — el proceso de cobro automático de Suscripciones-Facturación debe excluir explícitamente las facturas en este estado de sus intentos de cobro.
- Resolución del reclamo sigue el flujo estándar de Soporte: al cerrarse, `Fact_Factura.estado_pago` se actualiza de vuelta a `"Pendiente"`, `"Pagada"` o un monto ajustado, según la resolución.

**Camino de error — dependencia entre módulos no confirmada:** este CU depende de un campo (`Fact_Reclamo.id_factura`) que pertenece al módulo Soporte-Cliente y que, a la fecha de este documento, **es una extensión propuesta aún no confirmada como implementada** en ese módulo. Si `id_factura` no existe en `Fact_Reclamo`, este CU no puede ejecutarse tal como está descrito — debe verificarse/agregarse allá antes de construir este flujo aquí.

**Camino de error adicional — 🔎 Inferido:** un partner intenta abrir una disputa sobre una factura que ya está en estado `"En disputa"` por un reclamo anterior aún abierto → debería rechazarse o fusionarse con el reclamo existente para evitar dos procesos de disputa paralelos sobre la misma factura. No definido explícitamente en el original.

---

### Capítulo 5 — Si el partner no paga: mora y suspensión

**CU-O81 (Sistema) — Notificar aviso previo de suspensión por mora**

- Lectura: `Fact_Factura` con `estado_pago` distinto de `"Pagada"` y `tipo="excedente_api"`, calculando días transcurridos desde `fecha_vencimiento`.
- En T-10 y T-5 días antes del límite de 15 días de mora: `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial=NULL`, `tipo_cambio="aviso_previo_suspension"`, `ejecutado_por="Sistema"`, `motivo="T-10"` o `motivo="T-5"`, `estado_anterior=estado_nuevo` (el estado del partner no cambia todavía), `fecha_cambio=now`.

**Regla de no-duplicación confirmada (previene un error real de spam de avisos):** antes de insertar el aviso de T-5, el sistema hace `SELECT` sobre `Fact_HistorialAccesoPartner` filtrando `idpartner` + `tipo_cambio="aviso_previo_suspension"` + `motivo="T-10"` dentro del ciclo de mora actual — si ya existe, no se duplica el envío.

**Camino de error — 🔎 Inferido:** el partner regulariza el pago entre el aviso T-10 y el T-5 → el ciclo de mora se cierra (la factura pasa a `"Pagada"`), y por la condición de entrada de este CU (`estado_pago distinto de "Pagada"`), el aviso de T-5 nunca se dispara. No requiere manejo especial, es una consecuencia natural de la condición de lectura.

**CU-O79 (Sistema) — Suspensión automática por mora**

- Condición de entrada: mora de más de 15 días sobre una factura de excedente, sin haber sido regularizada tras los avisos de CU-O81.
- `Dim_Partner` — **UPDATE**: `activo=false`, `fecha_suspension=now`, `motivo_suspension="mora"`.
- `Dim_CredencialAPI` — **UPDATE en cascada**: `activo=false` en **todas** las filas de ese `idpartner`, tanto Sandbox como Producción.
- `Fact_HistorialAccesoPartner` — **INSERT**: `idpartner`, `idcredencial=NULL`, `tipo_cambio="suspension_automatica"`, `ejecutado_por="Sistema"`, `motivo="mora > 15 dias"`, `estado_anterior="Activo"`, `estado_nuevo="Suspendido"`, `fecha_cambio=now`.

**Camino de error real — este ES el camino de error del sistema completo:** todo llamado a la API contra una credencial recién puesta en `activo=false` por esta cascada debe rechazarse a partir de este momento — ninguna llamada nueva debería generar `Fact_APIIntegracion`/`Fact_LogLlamadaAPI` exitosos una vez ejecutada esta suspensión. (El mecanismo exacto de rechazo en tiempo real —middleware de autenticación validando `Dim_CredencialAPI.activo`— es una decisión de implementación técnica, no de modelo de datos, y no se detalla en este documento.)

**CU-O76 (Administrador) — Suspensión/reactivación manual por mora o vencimiento**

**Suspensión manual (motivos distintos a mora, ej. vencimiento de contrato):**

- Mismo patrón que CU-O79: `Dim_Partner` — **UPDATE** (`activo=false`, `fecha_suspension`, `motivo_suspension` = motivo específico), `Dim_CredencialAPI` — **UPDATE en cascada** (`activo=false` en todas), `Fact_HistorialAccesoPartner` — **INSERT** (`tipo_cambio="suspension_manual"`, `ejecutado_por="Administrador"`).

**Reactivación:**

- `Dim_Partner` — **UPDATE**: `activo=true`, `fecha_suspension=NULL`, `motivo_suspension=NULL`.
- `Dim_CredencialAPI` — **UPDATE en cascada inversa**: `activo=true` en las credenciales que estaban activas inmediatamente antes de la suspensión (se determina consultando `Fact_HistorialAccesoPartner`).
- `Fact_HistorialAccesoPartner` — **INSERT**: `tipo_cambio="reactivacion"`, `ejecutado_por="Administrador"`, `estado_anterior="Suspendido"`, `estado_nuevo="Activo"`, `fecha_cambio=now`.

**Regla explícita, no un error, pero crítica para no automatizarla por error:** **el sistema nunca reactiva solo** — siempre requiere confirmación manual del Administrador, incluso si la mora que causó la suspensión ya fue regularizada. No existe un `CU-O79` inverso automático.

**Camino de error — 🔎 Inferido:** el Administrador intenta reactivar un partner que nunca fue suspendido (`Dim_Partner.activo` ya es `true`) → operación redundante que debería rechazarse o no generar una nueva fila de `"reactivacion"` sin `estado_anterior="Suspendido"` real que la respalde.

---

## Tabla resumen: CU → Tablas principales que escribe

| CU | Caso de uso | Tablas que escribe (INSERT/UPDATE) |
| --- | --- | --- |
| CU-O71 | Registrar partner | `Dim_Partner`, `Fact_HistorialAccesoPartner` |
| CU-O80 | Asignar plan de acceso | `Dim_Partner`, `Fact_HistorialAccesoPartner` |
| CU-O72 | Solicitar y activar Sandbox y Producción | `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` |
| CU-O73 | Consultar credenciales y métricas | Solo lectura |
| CU-O74 | Logs, alertas de cuota y errores | Solo lectura |
| CU-O75 | Reporte mensual de consumo | Solo lectura |
| CU-O84 | Revocar credenciales por seguridad | `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` |
| CU-O78 | Facturación de excedentes | `Fact_Factura` (INSERT, tabla de Suscripciones-Facturación) |
| CU-O83 | Excepción de facturación automática | `Fact_Factura` (UPDATE reintentos) + alerta |
| CU-O82 | Registrar disputa | `Fact_Reclamo` (Soporte-Cliente), `Fact_Factura` (UPDATE estado_pago) |
| CU-O81 | Aviso previo de suspensión | `Fact_HistorialAccesoPartner` |
| CU-O79 | Suspensión automática por mora | `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` |
| CU-O76 | Suspensión/reactivación manual | `Dim_Partner`, `Dim_CredencialAPI`, `Fact_HistorialAccesoPartner` |

---

## Modelo de datos completo — DDL de referencia

```
Dim_Partner
PK idpartner                   integer
FK idcliente                   integer      -- vive en módulo Cuentas-Clientes; obligatorio, no nulo
   nombrepartner                character varying
   planapi                     character varying   -- NULL hasta CU-O80
   contacto_tecnico_nombre      character varying
   contacto_tecnico_gmail       character varying
   limitellamadasmes            integer             -- NULL hasta CU-O80
   limitellamadasminuto         integer             -- NULL hasta CU-O80
   sandbox_activado             bigint              -- NULL hasta CU-O72 sub-flujo A
   sandbox_expiracion           bigint              -- NULL hasta CU-O72 sub-flujo A
   fecha_suspension             character varying
   motivo_suspension            character varying
   activo                      boolean             -- única fuente de verdad del estado operativo

Dim_CredencialAPI
PK idcredencial                 integer
FK idpartner                    integer
FK idcliente                    integer
   client_secret_hash           character varying
   entorno                     character varying   -- 'Sandbox' | 'Producción'
   activo                      boolean
   fecha_creacion               bigint

Dim_EstadoIntegracion           -- catálogo de estados históricos de la integración
PK idestadointegracion          integer
   nombre                      character varying
   descripcion                  character varying
   activo                      boolean

Fact_APIIntegracion             -- orientada a reporte/facturación; 1 fila por llamada
PK idapiintegracion             integer
FK idcliente                    integer
FK idservicio                   integer
FK idestadointegracion          integer      -- copia histórica del estado al momento de la llamada
FK idpartner                    integer
   entorno                     character varying
   llamadas                    integer      -- =1 por fila
   errores                     integer      -- 0 o 1 según codigohttp
   latencia                    double precision
   activo                      boolean
   fechahora                   bigint

Fact_LogLlamadaAPI              -- detalle técnico completo; 1 fila por llamada, escrita junto con Fact_APIIntegracion
PK idlogllamadaapi              integer
FK idpartner                    integer
FK idcredencialapi               integer
   endpoint                    character varying
   metodohttp                   character varying
   codigohttp                   integer
   iporigen                    integer
   latenciams                   double precision
   fechallamada                 bigint

Fact_HistorialAccesoPartner     -- bitácora inmutable, solo INSERT
PK idhistorial                  integer
FK idpartner                    integer
FK idcredencial                 integer      -- nullable; NULL si el evento es sobre el partner en general
   tipo_cambio                  character varying   -- 'registro'|'asignacion_plan'|'activacion_sandbox'|
                                                      -- 'solicitud_promocion_produccion'|'activacion_produccion'|
                                                      -- 'revocacion_credencial'|'aviso_previo_suspension'|
                                                      -- 'suspension_automatica'|'suspension_manual'|'reactivacion'
   ejecutado_por                character varying   -- 'Partner' | 'Administrador' | 'Sistema'
   motivo                      character varying
   estado_anterior               character varying
   estado_nuevo                 character varying
   fecha_cambio                 bigint
```

---

## Diagrama de estados del Partner (resumen visual)

```
Registrado ──► Plan asignado ──► Sandbox activo ──► Pendiente de aprobación ──► Producción activa
  (CU-O71)        (CU-O80)          (CU-O72 A)            (CU-O72 B,                  │
                                                          solicitud del partner)       │
                                                                                        ▼
                                                                                   SUSPENDIDO
                                                                            (CU-O79 automático,
                                                                             tras CU-O81 avisos T-10/T-5;
                                                                             o CU-O76 manual)
                                                                                        │
                                                                                        └─► Producción activa
                                                                                           (CU-O76 reactivación
                                                                                            manual, nunca automática)

CU-O84 (revocación de credencial por compromiso de seguridad) puede ocurrir en cualquier
punto desde "Sandbox activo" en adelante, sin cambiar el estado general del partner.
```

**Nota clave:** el estado general del partner vive únicamente en `Dim_Partner.activo` (+ snapshot de suspensión); la trazabilidad detallada de cada evento —incluyendo avisos, revocaciones y transiciones— vive en `Fact_HistorialAccesoPartner`, nunca se sobrescribe, solo se agregan filas con `fecha_cambio` creciente.

---

## Frontera con otros módulos (para que no quede ambigüedad)

- **Cuentas-Clientes:** todo partner nace de un `Dim_Cliente` ya existente. Este módulo nunca crea clientes, solo los referencia.
- **Suscripciones-Facturación:** `Fact_Factura` es tabla de ese módulo, no de este — `CU-O78` y `CU-O82` la escriben/actualizan, pero su definición completa (ciclo de cobro, dunning, reintentos) vive allá. Las facturas de excedente (`tipo="excedente_api"`) conviven en la misma tabla que las facturas de suscripción regular, distinguidas por ese campo.
- **Soporte-Cliente:** `Fact_Reclamo` es tabla de ese módulo. `CU-O82` depende de una extensión (`id_factura`) no confirmada como implementada allá — es la única dependencia de este módulo marcada explícitamente como bloqueante pendiente de validación externa.
- Este módulo **nunca escribe en `Fact_Accidente`, `Fact_Despacho` ni ninguna tabla del núcleo de Emergencias** — un partner consume datos de accidentes solo a través de lo que la capa de API le exponga (fuera del alcance de este documento de datos), no mediante escritura directa sobre esas tablas.

---

## Nota de alcance (decisiones tomadas conscientemente, y gaps reales sin resolver)

- **El exceso de cuota nunca bloquea el servicio automáticamente** (`CU-O74` solo alerta); el control real de negocio ocurre después, vía facturación de excedentes (`CU-O78`). Decisión de modelo de negocio (*pay-as-you-go*), no una omisión.
- **`CU-O81` no tiene tabla propia** — se resuelve por convención de uso sobre `Fact_HistorialAccesoPartner`, evitando una tabla dedicada solo para avisos de mora.
- **`CU-O82` depende de un campo (`Fact_Reclamo.id_factura`) no confirmado como implementado** en el módulo Soporte-Cliente — debe validarse antes de construir este flujo.
- **La política de reintentos de `CU-O83` (3 intentos, 1 hora de espera) es un valor asumido por defecto**, no confirmado con el equipo de negocio.
- **Gaps reales identificados en esta redacción, no presentes como tales en el documento original:**
  - Qué ocurre cuando vence `sandbox_expiracion` sin promoción a Producción (sin CU definido).
  - Si un `idcliente` puede tener más de un `Dim_Partner` simultáneo (sin regla de unicidad confirmada).
  - Qué ocurre si un Administrador rechaza explícitamente una solicitud de promoción a Producción (sin `tipo_cambio` de rechazo definido en el catálogo).
  - Si se permite más de una credencial activa de Sandbox por partner simultáneamente.
