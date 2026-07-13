# Especificación: Autenticación y Control de Acceso Basado en Roles (RBAC)

## 1. Objetivo

Garantizar que solo usuarios autorizados, con el rol correcto, accedan a las funcionalidades del sistema según su perfil, mediante un mecanismo seguro de inicio de sesión con registro de sesión, administración de usuarios, roles de negocio, roles de servidor y recuperación de credenciales.

## 2. Contexto

Tráfico Seguro Integral (TSI) opera como orquestador digital SaaS + APIs que coordina emergencias viales en tiempo real. La plataforma es utilizada por múltiples actores con distintos niveles de acceso y responsabilidades.

## 2.1 Trazabilidad obligatoria (Constitution)

- **Objetivo Operacional (OP)**: OP-TSI-SEG-01 — garantizar acceso seguro, trazable y por rol a capacidades operativas del sistema.
- **Casos de uso (UC) trazados**: CU-O04, CU-O05, CU-O06, CU-O07, CU-O13, CU-O15.
- **Razón de trazabilidad**: este módulo es precondición de control de acceso para todos los demás módulos operativos y cumple la regla de trazabilidad mandatada por constitution.

**Casos de uso incluidos en este spec:**
- **CU-O05: Iniciar sesión** — autentica credenciales, valida activo y estadocredencial, escribe Fact_Session con estadosession='Inicio sesion'. Si estadocredencial='Cambio contraseña', fuerza cambio de contraseña.
- **CU-O04: Gestionar usuarios** — alta, edición y desactivación lógica (activo=false) de usuarios en Dim_Usuarios. Un usuario desactivado no puede autenticar.
- **CU-O13: Gestionar roles** — administración de roles de negocio en Dim_Rol y su asignación a usuarios mediante Dim_Usuario_Rol. El rol es el permiso: no existe tabla de permisos separada.
- **CU-O15: Gestionar usuarios y roles a nivel de servidor** — capa técnica de acceso a infraestructura mediante Dim_UsuariosServidor, Dim_RolesServidor, Dim_UsuariosServidorRolesServidor y Dim_RolesServidorRoles.
- **CU-O06: Recuperar y restablecer contraseña** — genera contraseña temporal, la escribe en Dim_Credencial, marca estadocredencial='Cambio contraseña' y la envía por correo. Mismo mecanismo que O08.
- **CU-O07: Revocar sesión activa** — actualiza Fact_Session.estadosession='Expulsado' y fechahoracierresesion.

## Clarifications

### Session 2026-07-09

- Q: ¿Qué fuente de verdad define si un JWT sigue siendo válido durante su vida útil? → A: Validar firma JWT y consultar Fact_Session en cada request para confirmar que la sesión no esté cerrada ni expulsada.
- Q: Para intentos fallidos de login por usuario/IP, ¿qué política es obligatoria? → A: Se difiere la política obligatoria de rate limiting/bloqueo para una fase posterior de arquitectura/operación.
- Q: ¿Qué SLO mínimo se fija para CU-O05? → A: p95 <= 500 ms y disponibilidad mensual >= 99.5% para el endpoint de autenticación.
- Q: ¿Cuál es el mecanismo oficial de recuperación de contraseña en producción? → A: Se mantiene contraseña temporal enviada por correo electrónico.
- Q: ¿Qué política de refresh token se aplicará? → A: Refresh token estático de 14 días, sin rotación.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Usuario del sistema** | Solicitante de autenticación | Inicia sesión con correo y contraseña. Recibe token. Recupera contraseña. Cambia contraseña forzado. |
| **Administrador** | Gestor de identidades y accesos | Crea, edita, desactiva usuarios. Gestiona roles de negocio. Gestiona accesos a servidor. Revoca sesiones activas. |
| **Director Tecnológico** | Gestor de acceso a infraestructura | Gestiona usuarios y roles a nivel de servidor (CU-O15). |
| **Sistema** | Guardián de seguridad | Valida credenciales contra Dim_Credencial. Valida activo en Dim_Usuarios. Valida estadocredencial. Emite y verifica tokens. Registra Fact_Session. |

### 3.1 Catálogo de roles de negocio (`Dim_Rol`)

El rol es dinámico (lo gestiona el Administrador vía CU-O13), pero los siguientes valores son los roles semilla que otros módulos operativos ya asumen como existentes. Se documentan aquí como referencia única — hasta ahora solo vivían dispersos en código (guards de frontend, `permissions.py` de backend):

| Valor de rol (`Dim_Rol.rol`) | Usado por (módulo) |
|---|---|
| `Administrador` | Todos los módulos |
| `Operador` | registro-accidente, despacho-inteligente, seguimiento-cierre-de-casos |
| `Unidad` | despacho-inteligente, evidencia-unidad (disponibilidad) |
| `Tecnico` | evidencia-unidad (captura y galería de evidencia) |
| `Despacho` | despacho-inteligente, seguimiento-cierre-de-casos, evidencia-unidad (flota) |
| `DirectorTecnologico` | despacho-inteligente (parámetros del algoritmo), CU-O15 |
| `Cliente` | seguimiento-cierre-de-casos (expedientes propios) |

## 4. Requisitos funcionales

### RF-AUT-001: Inicio de sesión con credenciales (CU-O05)

El sistema debe permitir a cualquier usuario registrado iniciar sesión proporcionando correo electrónico y contraseña:

1. El usuario envía credenciales al endpoint de autenticación.
2. El sistema busca al usuario por `gmail` en `Dim_Usuarios`.
3. Si el usuario no existe o `activo = false`, se rechaza (HTTP 401).
4. El sistema valida la contraseña contra el hash en `Dim_Credencial.contrasena`.
5. El sistema valida `Dim_Credencial.estadocredencial`:
   - Si es 'Inactivo', rechaza (HTTP 401).
   - Si es 'Cambio contraseña', autentica pero fuerza el cambio de contraseña antes de permitir cualquier otra acción.
6. Si las credenciales son válidas y `estadocredencial = 'Activo'`, autentica normalmente.
7. El sistema crea un registro en `Fact_Session` con:
   - `token`: identificador único de la sesión emitida.
   - `navegador`: user agent del cliente.
   - `fechahorainiciosesion`: timestamp actual.
   - `estadosession`: 'Inicio sesion'.
8. Retorna HTTP 200 con token de acceso y datos del perfil.

### RF-AUT-002: Validación de token en cada solicitud

El sistema debe interceptar toda petición a endpoints protegidos validando el token JWT. La verificación debe incluir consulta a `Fact_Session` en cada solicitud para confirmar que la sesión asociada al token no esté en `estadosession = 'Expulsado'` ni `estadosession = 'Cierre sesion'` (CU-O07 y RF-AUT-008).

### RF-AUT-003: Gestión de usuarios (CU-O04)

El sistema debe permitir al Administrador:
1. Crear usuarios en `Dim_Usuarios` con datos: nombres, apellidos, gmail, identificacion, genero, telefono, fechanacimiento.
2. Editar datos de usuarios existentes.
3. Desactivar usuarios: `activo = false` (soft-delete). Nunca se borra físicamente.
4. Un usuario con `activo = false` no puede autenticar en CU-O05.
5. Asignar roles de negocio mediante `Dim_Usuario_Rol`.

### RF-AUT-004: Gestión de roles de negocio (CU-O13)

El sistema debe permitir al Administrador:
1. Administrar el catálogo de roles en `Dim_Rol` (crear, editar, desactivar).
2. Asignar roles a usuarios mediante `Dim_Usuario_Rol`.
3. En este modelo, el rol es el permiso: no existe tabla de permisos separada. Si un usuario tiene el rol "Operador", el código sabe qué acciones están permitidas.

### RF-AUT-005: Gestión de usuarios y roles de servidor (CU-O15)

El sistema debe permitir al Administrador o Director Tecnológico gestionar accesos a nivel de infraestructura, independiente del RBAC de negocio:
1. Administrar usuarios de servidor en `Dim_UsuariosServidor`.
2. Administrar roles de servidor en `Dim_RolesServidor`.
3. Asignar usuarios a roles de servidor mediante `Dim_UsuariosServidorRolesServidor`.
4. Opcionalmente, mapear roles de servidor a roles de aplicativo mediante `Dim_RolesServidorRoles`.

Esta capa es completamente independiente de CU-O04/O13: una cosa es quién opera el sistema como negocio, otra distinta es quién accede a la infraestructura que lo sostiene.

### RF-AUT-006: Recuperar y restablecer contraseña (CU-O06)

El sistema debe permitir a un usuario recuperar su contraseña:
1. El usuario solicita recuperación con su correo registrado.
2. El sistema genera una contraseña temporal.
3. Sobrescribe `Dim_Credencial.contrasena` con el hash de la nueva contraseña temporal.
4. Marca `Dim_Credencial.estadocredencial = 'Cambio contraseña'`.
5. Envía la contraseña temporal por correo electrónico.
6. En el siguiente inicio de sesión (CU-O05), el sistema detecta `estadocredencial = 'Cambio contraseña'` y fuerza el cambio de contraseña antes de continuar.
7. No existe tabla de tokens de recuperación independiente: la propia `Dim_Credencial` hace las veces de estado del proceso.

### RF-AUT-007: Revocar sesión activa (CU-O07)

El sistema debe permitir al Administrador revocar una sesión activa de un usuario:
1. El Administrador selecciona una sesión activa de Fact_Session.
2. El sistema actualiza `estadosession = 'Expulsado'`.
3. El sistema actualiza `fechahoracierresesion` con el timestamp actual.
4. Cualquier verificación posterior de sesión activa debe revisar `estadosession`, no solo la validez del token.
5. Estados posibles de `estadosession`: 'Inicio sesion', 'Cierre sesion', 'Expulsado'.

### RF-AUT-008: Cierre de sesión

El sistema debe permitir a cualquier usuario cerrar su sesión voluntariamente:
1. Actualiza `Fact_Session.estadosession = 'Cierre sesion'`.
2. Actualiza `fechahoracierresesion`.
3. Invalida el token actual.

## 5. Requisitos no funcionales

### RNF-AUT-001: Seguridad de contraseñas

Las contraseñas deben almacenarse como hash unidireccional en `Dim_Credencial.contrasena` usando bcrypt (salt rounds >= 12) o argon2id. Nunca en texto plano, transmitidas sin cifrado ni registradas en logs.

### RNF-AUT-002: Estructura de tokens

- Access token JWT firmado (RS256), expiración 60 minutos.
- Payload: sub (idusuario), roles, iat, exp, iss.
- Refresh token opaco estático (sin rotación), expiración 14 días.

### RNF-AUT-003: Trazabilidad

Toda operación de inicio de sesión, cierre, revocación, creación de usuario, asignación de rol y cambio de contraseña debe registrarse en logs del sistema con idusuario, timestamp, IP y resultado.

### RNF-AUT-004: Rendimiento y disponibilidad del login

Para CU-O05, el endpoint de autenticación debe cumplir p95 <= 500 ms y disponibilidad mensual >= 99.5%.

### RNF-AUT-005: Política diferida de protección por intentos fallidos

La política obligatoria de rate limiting, bloqueo temporal o CAPTCHA para intentos fallidos de login se difiere a fase posterior de arquitectura/operación. Hasta entonces, no constituye criterio de rechazo de este spec.

## 6. Reglas de negocio

### RN-AUT-001: Usuario siempre con rol
Todo usuario debe tener al menos un rol asignado en `Dim_Usuario_Rol`.

### RN-AUT-002: Correo único
El campo `gmail` debe ser único en `Dim_Usuarios`.

### RN-AUT-003: Desactivación inmediata
Un usuario con `activo = false` no puede iniciar sesión.

### RN-AUT-004: Privilegio exclusivo del Administrador
Solo usuarios con rol "Administrador" pueden gestionar usuarios, roles y revocar sesiones.

### RN-AUT-005: Cambio obligatorio de contraseña
Si `Dim_Credencial.estadocredencial = 'Cambio contraseña'`, el sistema fuerza el cambio antes de permitir cualquier otra acción.

### RN-AUT-006: Sin borrado físico
Nunca se eliminan registros de `Dim_Usuarios`. Solo se marcan con `activo = false`.

## 7. Entradas

### Para inicio de sesión (CU-O05)
- Correo electrónico (string, mapea a Dim_Usuarios.gmail).
- Contraseña (string, se compara contra Dim_Credencial.contrasena).

### Para gestión de usuarios (CU-O04)
- nombres, apellidos, gmail, identificacion, genero, telefono, fechanacimiento, rol(es), activo.

### Para gestión de roles (CU-O13)
- `rol` (STRING, nombre del rol en `Dim_Rol`), `descripcion`. Para la asignación: `idusuario`, `idrol` (se escriben en `Dim_Usuario_Rol`, no en `Dim_Rol`).

### Para gestión de servidor (CU-O15)
- `usuario` (STRING, campo real en `Dim_UsuariosServidor`), `contrasena`; `rolservidor` (STRING, campo real en `Dim_RolesServidor`); asignaciones vía `Dim_UsuariosServidorRolesServidor`.

### Para recuperación de contraseña (CU-O06)
- Correo electrónico registrado.

### Para revocación de sesión (CU-O07)
- `idsession` (INT, PK real de `Fact_Session`).

## 8. Salidas

### Respuestas exitosas
- **200 OK — Login exitoso:** token de acceso + perfil usuario.
- **200 OK — Sesión cerrada.**
- **200 OK — Sesión revocada.**
- **200 OK — Contraseña restablecida.**
- **200 OK — Usuario creado / actualizado / desactivado.**
- **200 OK — Roles asignados.**
- **200 OK — Usuario/rol de servidor creado.**

### Respuestas de error
- **400 Bad Request** — Campos inválidos.
- **401 Unauthorized** — Credenciales inválidas, usuario inactivo, credencial inactiva, token inválido/expirado/revocado.
- **403 Forbidden** — Privilegios insuficientes.
- **409 Conflict** — gmail duplicado.

## 9. Estados posibles

### Estados de Dim_Credencial.estadocredencial
- **Activo**: contraseña definitiva, login normal.
- **Inactivo**: credencial no puede usarse para autenticar.
- **Cambio contraseña**: estado transitorio. El sistema fuerza definición de nueva contraseña en el próximo login.

### Estados de Fact_Session.estadosession
- **Inicio sesion**: sesión activa.
- **Cierre sesion**: logout voluntario.
- **Expulsado**: sesión terminada forzadamente por Administrador (CU-O07).

### Estados de Dim_Usuarios
- **activo = true**: usuario puede autenticar.
- **activo = false**: soft-delete, no puede autenticar.

## 10. Escenarios

### Escenario 1: Inicio de sesión exitoso
Usuario con activo=true y estadocredencial='Activo' → valida credenciales → escribe Fact_Session (Inicio sesion) → retorna token.

### Escenario 2: Inicio de sesión con estadocredencial='Cambio contraseña'
Usuario con activo=true y estadocredencial='Cambio contraseña' → valida credenciales → fuerza cambio de contraseña → tras cambiar, estadocredencial='Activo'.

### Escenario 3: Usuario desactivado intenta login
activo=false → HTTP 401.

### Escenario 4: Revocación de sesión
Administrador selecciona sesión activa → estadosession='Expulsado', fechahoracierresesion=now → token queda inválido.

### Escenario 5: Recuperación de contraseña
Usuario solicita recuperación → sistema genera temp password → escribe hash en Dim_Credencial.contrasena → estadocredencial='Cambio contraseña' → envía por correo.

### Escenario 6: Gestión de roles de servidor
Director Tecnológico crea usuario en Dim_UsuariosServidor → asigna rol en Dim_RolesServidor → vincula mediante Dim_UsuariosServidorRolesServidor.

## 11. Criterios de aceptación

### CA-AUT-001
Usuario con credenciales válidas, activo=true y estadocredencial='Activo' inicia sesión, recibe token, y Fact_Session registra la sesión.

### CA-AUT-002
Usuario con activo=false recibe HTTP 401 al intentar login.

### CA-AUT-003
Usuario con estadocredencial='Cambio contraseña' es forzado a cambiar contraseña antes de acceder.

### CA-AUT-004
Administrador puede desactivar usuario (activo=false). Usuario desactivado no puede autenticar.

### CA-AUT-005
Administrador puede gestionar roles en Dim_Rol y asignarlos via Dim_Usuario_Rol.

### CA-AUT-006
Administrador/Director Tecnológico puede gestionar usuarios y roles de servidor.

### CA-AUT-007
Usuario puede recuperar contraseña, recibe temp password por correo, y siguiente login fuerza cambio.

### CA-AUT-008
Administrador puede revocar sesión activa: Fact_Session.estadosession='Expulsado'.

### CA-AUT-009
La validación de endpoints protegidos verifica JWT y estado de sesión en Fact_Session en cada solicitud, rechazando tokens asociados a sesiones en 'Cierre sesion' o 'Expulsado'.

### CA-AUT-010
El endpoint CU-O05 cumple p95 <= 500 ms y disponibilidad mensual >= 99.5%.

## 12. Dependencias

Ninguna funcional — este spec no depende de otros módulos. Todos los demás specs dependen de este para autenticación y control de acceso.

## 13. Fuera de alcance

- Autenticación multifactor (MFA/2FA).
- SSO corporativo (Azure AD, Okta).
- Gestión de permisos granulares por funcionalidad (el rol es el permiso).
- Multi-tenancy a nivel de datos.
- Expiración de cuentas por inactividad.
- Límite de sesiones simultáneas.
- Definición obligatoria de rate limiting/bloqueo/CAPTCHA para intentos fallidos de login (diferido a diseño operativo).
