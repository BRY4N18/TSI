# Data Model - Autenticacion y RBAC

## Entidades de negocio (backend Django)

## 1) Usuario (`Dim_Usuarios`)

- Primary key: `idusuario`
- Campos clave:
  - `gmail` (unico)
  - `activo` (boolean)
  - `nombres`, `apellidos`, `identificacion`, `genero`, `telefono`, `fechanacimiento`
  - `fecha_actualizacion` (control de version de evento)
- Reglas:
  - `gmail` debe ser unico.
  - `activo=false` bloquea autenticacion.

## 2) Credencial (`Dim_Credencial`)

- Primary key: `idcredencial` (o equivalente de modelo)
- Relaciones:
  - `idusuario` -> `Dim_Usuarios.idusuario` (1:1 logico para autenticacion)
- Campos clave:
  - `contrasena` (hash bcrypt>=12 o argon2id)
  - `estadocredencial` (`Activo` | `Inactivo` | `Cambio contraseña`)
  - `fecha_actualizacion`
- Reglas:
  - Nunca almacenar contraseña en texto plano.
  - Si estado `Cambio contraseña`, bloquear acceso a funcionalidades no-auth hasta completar cambio.

## 3) Rol de negocio (`Dim_Rol`)

- Primary key: `idrol`
- Campos:
  - `rol` (nombre canonico)
  - `descripcion`
  - `activo`
  - `fecha_actualizacion`
- Reglas:
  - Rol representa permiso (no tabla granular adicional en esta fase).

## 4) Usuario-Rol (`Dim_Usuario_Rol`)

- Primary key compuesto logico: (`idusuario`, `idrol`)
- Relaciones:
  - N:1 hacia `Dim_Usuarios`
  - N:1 hacia `Dim_Rol`
- Regla:
  - Todo usuario debe tener al menos un rol activo.

## 5) Sesion (`Fact_Session`)

- Primary key: `idsession`
- Campos:
  - `token` (identificador de sesion; no exponer en logs completos)
  - `idusuario`
  - `navegador`
  - `fechahorainiciosesion`
  - `fechahoracierresesion` (nullable)
  - `estadosession` (`Inicio sesion` | `Cierre sesion` | `Expulsado`)
- Reglas:
  - Cada request protegida valida JWT y consulta estado de sesión.
  - Estados `Cierre sesion` o `Expulsado` invalidan acceso inmediato.

## 6) Entidades de servidor (CU-O15)

- `Dim_UsuariosServidor`
- `Dim_RolesServidor`
- `Dim_UsuariosServidorRolesServidor`
- `Dim_RolesServidorRoles` (mapeo opcional a roles de aplicativo)

## Relaciones principales

- `Dim_Usuarios (1) -> (1) Dim_Credencial`
- `Dim_Usuarios (1) -> (N) Fact_Session`
- `Dim_Usuarios (N) <-> (N) Dim_Rol` via `Dim_Usuario_Rol`
- `Dim_UsuariosServidor (N) <-> (N) Dim_RolesServidor` via `Dim_UsuariosServidorRolesServidor`

## Transiciones de estado

## Credencial

- `Activo` -> `Cambio contraseña` (por recuperación)
- `Cambio contraseña` -> `Activo` (tras cambio exitoso)
- `Activo` -> `Inactivo` (deshabilitación administrativa)

## Sesion

- `Inicio sesion` -> `Cierre sesion` (logout voluntario)
- `Inicio sesion` -> `Expulsado` (revocación administrativa)

## Eventos Kafka (escritura)

- `Fact_Session_topic`
- `Dim_Credencial_topic`
- `Dim_Usuarios_topic`
- `Dim_Rol_topic`
- `Dim_Usuario_Rol_topic`
- `Dim_UsuariosServidor_topic`
- `Dim_RolesServidor_topic`
- `Dim_UsuariosServidorRolesServidor_topic`
- `Dim_RolesServidorRoles_topic`

Todos los cambios de estas entidades se publican por Kafka; Pinot ingiere en tiempo real y se usa solo para lectura.
