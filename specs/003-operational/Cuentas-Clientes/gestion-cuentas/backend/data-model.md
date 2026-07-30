# Data Model - Gestión de Cuenta de Cliente

## Entidades de dominio (lectura Pinot / escritura Kafka)

## 1) Cuenta corporativa (`Dim_Cliente`)

- Primary key: `idcliente`
- Campos relevantes para este módulo:
  - `razon_social` (STRING, requerido, editable)
  - `nombre` (STRING, editable)
  - `tipo` (STRING, solo lectura post-registro)
  - `nit_identificacion` (STRING, solo lectura)
  - `logo_url` (STRING, URL Azure Blob)
  - `admin_local_id` (INT → `Dim_Usuarios.idusuario`)
  - `estado` (STRING: `Activo` | `Dado de baja`)
  - `fecha_actualizacion` (LONG epoch ms)
- Reglas:
  - `tipo` y `nit_identificacion` inmutables (RN-CTA-001).
  - `estado='Dado de baja'` bloquea operación (RN-CTA-003, RN-CTA-005).
  - No existe columna `activo`; estado exclusivamente por `estado`.

## 2) Preferencias operativas (`Dim_Preferencias_Cliente`)

- Primary key: `id_preferencia`
- Relación: `id_cliente` → `Dim_Cliente.idcliente` (1:1 operativo por cuenta)
- Campos editables (excepto `activo`):
  - `umbrales_alerta` (STRING — JSON serializado o delimitado)
  - `canales_notificacion` (STRING — enum: `email` | `sms` | `ambos`)
  - `telefono_sms` (STRING)
  - `zonas_geograficas` (STRING — JSON/lista)
  - `destinatarios_reportes` (STRING — lista emails)
  - `frecuencia_reportes` (STRING)
  - `formato_reportes` (STRING — ej. `PDF`, `CSV`)
- Campo sistema: `activo` (BOOLEAN, no editable desde este módulo)
- Reglas:
  - Si `canales_notificacion` incluye SMS, `telefono_sms` requerido.
  - `destinatarios_reportes` debe validarse como lista de emails.

## 3) Sesión (`Fact_Session`) — lectura/escritura en baja

- Reutilizada de autenticacion-y-rbac.
- En baja (O11): todas las sesiones con `estadosession='Inicio sesion'` de usuarios de la cuenta → `Expulsado` + `fechahoracierresesion`.

## 4) Usuario (`Dim_Usuarios`) — referencia para transferencia

- Primary key: `idusuario`
- Campos: `gmail`, `nombres`, `apellidos`, `activo`
- Regla O10: nuevo responsable debe tener `activo=true` y pertenecer a la cuenta (vía membresía).

## 5) Membresía usuario↔cuenta (vista lógica)

- No es tabla Pinot independiente en el modelo global actual.
- Abstracción: `CuentaUsuarioRepository` resuelve usuarios por `idcliente` (implementación alineada con spec incorporacion-clientes).
- Usada para: listar elegibles en O10, expulsar sesiones en O11.

## Relaciones principales

- `Dim_Cliente (1) → (1) Dim_Preferencias_Cliente` por `id_cliente`
- `Dim_Cliente.admin_local_id → Dim_Usuarios.idusuario`
- `Dim_Usuarios (N) ↔ cuenta` vía membresía (onboarding)
- `Dim_Usuarios (1) → (N) Fact_Session`

## Transiciones de estado

### Dim_Cliente.estado

- `Activo` → `Dado de baja` (O11, solo Administrador)
- `Dado de baja` → *(sin transición desde este módulo; RN-CTA-004)*

### Dim_Cliente.admin_local_id (O10)

- Valor anterior → nuevo `idusuario` elegible (inmediato, sin estado pendiente)

## Eventos Kafka (escritura)

| Operación | Topic | Campos clave del payload |
|-----------|-------|--------------------------|
| Actualizar perfil | `Dim_Cliente_topic` | `idcliente`, campos modificados, `fecha_actualizacion` |
| Actualizar preferencias | `Dim_Preferencias_Cliente_topic` | `id_preferencia`, `id_cliente`, campos modificados |
| Transferir propiedad | `Dim_Cliente_topic` | `idcliente`, `admin_local_id` (nuevo) |
| Dar de baja | `Dim_Cliente_topic` | `idcliente`, `estado='Dado de baja'` |
| Expulsar sesiones | `Fact_Session_topic` | `idsession`, `estadosession='Expulsado'`, `fechahoracierresesion` |

## Auditoría (logs, no Pinot)

| Evento | Campos registrados |
|--------|-------------------|
| Cambio perfil/preferencias | `idusuario`, `idcliente`, campos, valor_anterior, valor_nuevo, timestamp |
| Transferencia O10 | `idusuario`, `idcliente`, `admin_local_id_anterior`, `admin_local_id_nuevo`, timestamp |
| Baja O11 | `idusuario`, `idcliente`, `motivo` (opcional), timestamp |
| Fallo SMTP | `idusuario`, `idcliente`, `evento`, `error`, timestamp |

## Validaciones de contrato (resumen)

| Campo | Regla |
|-------|-------|
| `razon_social` | requerido, min 2 chars |
| `logo_url` | URL válida HTTPS |
| `id_nuevo_responsable` | ≠ admin actual; usuario activo de la cuenta |
| `motivo` | opcional, max 500 chars; solo logs |
| `estado` en baja | idempotente si ya `Dado de baja` → 200 con mismo estado |
