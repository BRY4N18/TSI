# Especificación: Gestión de Cuenta de Cliente

## 1. Objetivo

Dar autonomía al cliente para administrar su propia cuenta corporativa: actualizar perfil y preferencias, transferir la propiedad de la cuenta a otro responsable y gestionar la baja definitiva de la cuenta cuando corresponda.

## 2. Contexto

Una vez que el cliente completó su onboarding, necesita gestionar su cuenta de forma autogestionada. Esto incluye mantener actualizados sus datos corporativos y preferencias operativas, transferir la administración local a otro responsable dentro de su organización y, cuando sea necesario, dar de baja la cuenta.

Nota: la gestión del plan de suscripción (cambio de plan, consulta de uso) y el historial de facturación se han movido al módulo **Suscripciones-Facturacion** (CU-O101, CU-O102).

**Casos de uso incluidos:**
- **CU-O03: Gestionar perfil de cuenta del cliente** — Actualizar datos corporativos en Dim_Cliente y preferencias operativas en Dim_Preferencias_Cliente (umbrales de alerta, canales de notificación, zonas geográficas, destinatarios de reportes). Actor: Administrador / Cliente.
- **CU-O10: Transferir propiedad de cuenta** — Actualizar Dim_Cliente.admin_local_id para apuntar al nuevo responsable. Actor: Cliente.
- **CU-O11: Dar de baja cuenta de cliente** — Marcar `Dim_Cliente.estado='Dado de baja'`. Nunca implica borrado físico. Actor: Administrador.

## Clarifications

### Session 2026-07-09

- Q: ¿Cómo debe completarse la transferencia de propiedad (CU-O10) al seleccionar un nuevo responsable? → A: Inmediata — al confirmar la selección se actualiza `admin_local_id` sin aceptación del nuevo responsable.
- Q: ¿Qué debe ocurrir con las sesiones activas al dar de baja una cuenta (CU-O11)? → A: Revocación inmediata — expulsar todas las sesiones activas de usuarios de la cuenta al momento de la baja.
- Q: ¿Qué campos de `Dim_Preferencias_Cliente` son editables en este módulo (CU-O03)? → A: Todos excepto `activo` — incluye `frecuencia_reportes`, `formato_reportes` y `telefono_sms`.
- Q: ¿Dónde debe almacenarse el motivo de baja (CU-O11)? → A: Solo logs — el motivo se registra en logs de auditoría junto con idusuario, timestamp e idcliente.
- Q: ¿Qué eventos deben generar notificación por correo? → A: Transferencia y baja — correo al nuevo admin, al anterior admin y al admin local en baja. Canal: SMTP (credenciales vía variables de entorno en implementación).

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Cliente** (administrador local) | Gestor de su cuenta | Edita perfil corporativo y preferencias. Transfiere propiedad a otro responsable. |
| **Administrador** | Supervisor global | Puede ver y gestionar cualquier cuenta de cliente. Ejecuta la baja de cuenta. |
| **Sistema** | Validador y notificador | Valida cambios, registra modificaciones en logs, envía notificaciones por correo en transferencia y baja, preserva datos históricos tras la baja. |

## 4. Requisitos funcionales

### RF-CTA-001: Gestión del perfil corporativo (CU-O03)

El sistema debe permitir al Cliente y al Administrador ver y editar los datos del perfil corporativo en Dim_Cliente:
- `razon_social` (string, requerido).
- `nombre` (string, editable).
- `tipo` (string, solo lectura, no modificable después del registro).
- `nit_identificacion` (string, solo lectura).
- `logo_url` (string, URL del logo almacenado en Azure Blob Storage — el archivo binario no vive en Pinot, solo la URL resultante, mismo patrón que `Dim_EvidenciaFoto`).

Cada modificación debe registrarse en logs: idusuario, campos modificados, valores anterior y nuevo, timestamp.

### RF-CTA-002: Gestión de preferencias del cliente (CU-O03)

El sistema debe permitir al Cliente configurar sus preferencias operativas en Dim_Preferencias_Cliente. Son editables todos los campos del modelo excepto `activo` (gestionado por el sistema):
- **Umbrales de alerta** (`umbrales_alerta`): tipo de accidentes que activan notificación, frecuencia mínima.
- **Canales de notificación** (`canales_notificacion`): correo electrónico, SMS, o ambos.
- **Teléfono SMS** (`telefono_sms`): número para notificaciones por SMS cuando el canal SMS está activo.
- **Zonas geográficas** (`zonas_geograficas`): ciudades, regiones de interés.
- **Destinatarios de reportes** (`destinatarios_reportes`): lista de correos que reciben reportes automatizados.
- **Frecuencia de reportes** (`frecuencia_reportes`): periodicidad de reportes automatizados.
- **Formato de reportes** (`formato_reportes`): formato de entrega de reportes (ej. PDF, CSV).

### RF-CTA-003: Transferir propiedad de cuenta (CU-O10)

El sistema debe permitir al Cliente transferir la administración de su cuenta a otro responsable:
1. El Cliente (actual admin_local_id) selecciona un nuevo responsable de entre los usuarios de su cuenta y confirma la operación.
2. La transferencia es **inmediata**: no existe estado pendiente ni flujo de aceptación por parte del nuevo responsable.
3. El sistema actualiza `Dim_Cliente.admin_local_id` al id del nuevo responsable en el mismo request de confirmación.
4. El nuevo responsable adquiere los privilegios de administración local de la cuenta de forma instantánea.
5. El anterior responsable deja de tener privilegios de administración local (aunque sigue siendo usuario de la cuenta).
6. Se registra la transferencia en logs del sistema.
7. El sistema envía notificación por correo (SMTP) al nuevo responsable y al anterior administrador local informando la transferencia.

### RF-CTA-004: Dar de baja cuenta de cliente (CU-O11)

El sistema debe permitir al Administrador dar de baja una cuenta de cliente:
1. El Administrador selecciona la cuenta a dar de baja (puede incluir un `motivo` opcional).
2. El sistema actualiza `Dim_Cliente.estado = 'Dado de baja'`.
3. Si se proporciona `motivo`, el sistema lo registra en logs de auditoría (idusuario, idcliente, motivo, timestamp). El motivo **no** se persiste en `Dim_Cliente`.
4. El sistema revoca **inmediatamente** todas las sesiones activas (`Fact_Session`) de los usuarios de esa cuenta, marcando `estadosession='Expulsado'` y `fechahoracierresesion=now` (mismo patrón que CU-O07).
5. **Nunca se eliminan físicamente registros**: los datos históricos (usuarios, sesiones, onboarding, preferencias) permanecen íntegros en la base.
6. Una cuenta dada de baja no puede iniciar sesión ni operar en el sistema.
7. Los datos permanecen para cumplir con políticas de retención de datos y trazabilidad legal.
8. El sistema envía notificación por correo (SMTP) al administrador local (`admin_local_id`) de la cuenta informando la baja.

### RF-CTA-005: Notificaciones por correo (CU-O10, CU-O11)

El sistema debe enviar notificaciones por correo electrónico vía SMTP en los siguientes eventos:
- **Transferencia de propiedad (O10)**: correo al nuevo responsable y al anterior administrador local.
- **Baja de cuenta (O11)**: correo al administrador local de la cuenta al momento de la baja.

Los cambios de perfil y preferencias (O03) **no** generan notificación por correo. La configuración SMTP (host, puerto, credenciales, remitente) se define en variables de entorno durante la implementación; no forma parte de esta especificación funcional.

## 5. Requisitos no funcionales

### RNF-CTA-001: Disponibilidad
El portal de gestión de cuenta debe tener disponibilidad del 99.9%.

### RNF-CTA-002: Seguridad
Los datos de cada cliente deben ser accesibles solo por los usuarios de esa cuenta y por el Administrador del sistema.

### RNF-CTA-003: Trazabilidad
Toda modificación de perfil, transferencia de propiedad y baja de cuenta debe registrarse en logs del sistema.

## 6. Reglas de negocio

### RN-CTA-001
El `nit_identificacion` y el `tipo` no pueden modificarse después del registro.

### RN-CTA-002
Para transferir la propiedad (O10), el nuevo responsable debe ser un usuario activo de la misma cuenta de cliente. La transferencia surte efecto de forma inmediata al confirmar; no requiere aceptación del nuevo responsable.

### RN-CTA-003
La baja de cuenta (O11) no elimina físicamente ningún registro. Es una baja lógica: `estado='Dado de baja'`. `Dim_Cliente` no tiene columna `activo` — el estado de la cuenta se determina exclusivamente por `estado`.

### RN-CTA-004
Una cuenta dada de baja no puede reactivarse desde este módulo. La reactivación requiere intervención del Administrador a nivel de base de datos o un proceso administrativo especial.

### RN-CTA-005
Los usuarios de una cuenta dada de baja conservan su registro histórico pero no pueden operar. Al ejecutar la baja, el sistema debe expulsar inmediatamente todas sus sesiones activas en `Fact_Session`.

### RN-CTA-006
Las notificaciones por correo de transferencia (O10) y baja (O11) son obligatorias. El fallo de envío no debe revertir la operación, pero debe registrarse en logs del sistema.

## 7. Entradas

### Para gestión de perfil (CU-O03)
razon_social, nombre, logo_url.

### Para preferencias (CU-O03)
umbrales_alerta, canales_notificacion, telefono_sms, zonas_geograficas, destinatarios_reportes, frecuencia_reportes, formato_reportes.

### Para transferencia de propiedad (CU-O10)
id_nuevo_responsable (debe pertenecer a la misma cuenta).

### Para baja de cuenta (CU-O11)
idcliente, motivo (opcional, persistido solo en logs de auditoría).

## 8. Salidas

- **200 OK — Perfil actualizado:** { message, campos_modificados }.
- **200 OK — Preferencias actualizadas.**
- **200 OK — Propiedad transferida:** { nuevo_admin_local_id, nombre }.
- **200 OK — Cuenta dada de baja:** { message, estado: 'Dado de baja' }.
- **400/403/404** según validaciones.

## 9. Estados posibles

### Estados de Dim_Cliente
- **Activo**: cuenta en operación normal.
- **Dado de baja**: cuenta desactivada (O11). No existe columna `activo` en `Dim_Cliente`; el estado de la cuenta se determina exclusivamente por `estado`.

### admin_local_id (Dim_Cliente)
- Apunta al usuario que actualmente es el Administrador Principal de la cuenta (O10).

## 10. Escenarios

### Escenario 1: Actualización de perfil y preferencias (O03)
Cliente modifica `razon_social`, `telefono_sms` y umbrales de alerta → sistema actualiza Dim_Cliente y Dim_Preferencias_Cliente → logs.

### Escenario 2: Transferencia de propiedad (O10)
Cliente actual (admin_local_id) selecciona nuevo responsable de la misma cuenta → sistema actualiza Dim_Cliente.admin_local_id → nuevo responsable asume administración → notificación por correo a ambos involucrados.

### Escenario 3: Baja de cuenta (O11)
Administrador da de baja cuenta → `Dim_Cliente.estado='Dado de baja'` → sistema expulsa todas las sesiones activas de usuarios de la cuenta → notificación por correo al admin local → datos históricos preservados → cuenta no puede operar.

## 11. Criterios de aceptación

### CA-CTA-001
Cliente puede editar perfil corporativo y preferencias (O03). Cambios registrados en logs.

### CA-CTA-002
Cliente puede transferir propiedad de la cuenta a otro usuario de la misma cuenta (O10).

### CA-CTA-003
Administrador puede dar de baja una cuenta. `Dim_Cliente.estado='Dado de baja'`. Datos históricos preservados (O11).

### CA-CTA-004
Una cuenta dada de baja no puede iniciar sesión ni operar. Todas las sesiones activas de sus usuarios quedan expulsadas al momento de la baja.

### CA-CTA-005
Los datos de la cuenta (usuarios, sesiones, preferencias) permanecen íntegros tras la baja.

### CA-CTA-006
Transferencia (O10) y baja (O11) generan notificación por correo SMTP a los usuarios involucrados. El fallo de envío se registra en logs sin revertir la operación.

## 12. Dependencias

- **autenticacion-y-rbac**: requiere autenticación JWT y roles "Cliente" y "Administrador".
- **incorporacion-clientes**: requiere que la cuenta de cliente esté creada y configurada.
- **Servicio SMTP**: canal de envío de notificaciones por correo (configuración vía variables de entorno).

## 13. Fuera de alcance

- **Gestión de plan de suscripción** (cambio de plan, consulta de uso, métricas): movido a módulo Suscripciones-Facturacion (CU-O101, CU-O102).
- **Historial de facturación**: movido a módulo Suscripciones-Facturacion (CU-O102).
- **Solicitud de cambio de plan**: movido a Suscripciones-Facturacion.
- **Pipeline comercial y gestión de prospectos**: spec commercial-pipeline-prospects.
- **Alta y onboarding de nuevos clientes**: spec incorporacion-clientes.
