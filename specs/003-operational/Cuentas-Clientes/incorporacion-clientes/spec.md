# Especificación: Alta, Configuración y Onboarding Digital de Clientes

## 1. Objetivo

Permitir que una aseguradora o municipio se convierta en cliente activo de la plataforma TSI: desde el registro de la cuenta, configuración inicial, onboarding digital con etapas, guardado automático de progreso y reenvío de invitación cuando sea necesario.

## 2. Contexto

Tráfico Seguro Integral opera bajo un modelo B2B/B2G donde los clientes son aseguradoras, municipios y plataformas Smart Cities.

**Casos de uso incluidos:**
- **CU-O01: Registrar cuenta de nuevo cliente** — El Administrador crea el registro base en Dim_Cliente (razón social, NIT, tipo de cliente, fecha inicio contrato).
- **CU-O12: Configurar cuenta de nuevo cliente** — El Administrador define plan_suscripcion, logo_url y establece estado_onboarding='Pendiente'. Es un UPDATE sobre la misma fila de Dim_Cliente creada en O01.
- **CU-O02: Ejecutar onboarding digital** — El Cliente completa etapas registradas en Fact_Onboarding (etapa, completado, fecha_completado).
- **CU-O09: Guardar progreso de onboarding** — El Sistema guarda automáticamente. Cada Fact_Onboarding insertado ya es el progreso guardado. Al reanudar, el sistema consulta qué etapas tienen completado=true.
- **CU-O08: Reenviar invitación** — El Administrador o Cliente pueden reenviar la invitación. El sistema genera contraseña temporal, la escribe en Dim_Credencial.contrasena (hasheada), marca estadocredencial='Cambio contraseña' y la envía por correo. No hay tabla de tokens de invitación independiente.

## Clarifications

### Session 2026-07-09

- Q: ¿Cómo se modela la membresía usuario↔cuenta al registrar un cliente (O01)? → A: No existe `Dim_Usuario_Cliente`; la membresía se infiere solo de `Dim_Cliente.admin_local_id`.
- Q: ¿Cuándo debe establecerse `Dim_Cliente.estado='Activo'`? → A: Desde O01 — al registrar la cuenta en el mismo request de creación.
- Q: ¿Cuál es el catálogo canónico de valores `etapa` en `Fact_Onboarding` (CU-O02)? → A: Lista fija — `cambio_password`, `perfil_corporativo`, `preferencias` (obligatorias) + etapas opcionales según plan.
- Q: ¿Cuándo debe crearse el registro inicial en `Dim_Preferencias_Cliente`? → A: En O02 — al completar/guardar la etapa `preferencias`.
- Q: ¿Qué política concreta aplican los recordatorios si el onboarding no se completa en 30 días (RN-ONB-004)? → A: Correo semanal al admin local desde el día 30 hasta completar onboarding.

## 3. Actores

| Actor | Rol en este módulo | Interacción principal |
|---|---|---|
| **Administrador** | Creador y configurador de cuentas | Registra cuenta (O01), configura plan y logo (O12), reenvía invitación (O08). |
| **Cliente** | Ejecutor del onboarding | Completa etapas del onboarding (O02). |
| **Sistema** | Facilitador automatizado | Guarda progreso automático (O09), envía credenciales temporales (O08), consulta etapas completadas. |

## 4. Requisitos funcionales

### RF-ONB-001: Registrar cuenta de nuevo cliente (CU-O01)

El sistema debe permitir al Administrador registrar una nueva cuenta de cliente en Dim_Cliente:
- razon_social, nombre, tipo (Aseguradora/Municipio/Smart City), nit_identificacion (único), fecha_inicio_contrato.
- Crear el usuario administrador local en Dim_Usuarios, asignarle rol "Cliente" en Dim_Usuario_Rol, generar credenciales temporales en Dim_Credencial.
- Establecer `Dim_Cliente.admin_local_id` apuntando al `idusuario` del administrador local creado.
- Establecer `Dim_Cliente.estado = 'Activo'` en el mismo request de creación (O01).
- **No existe tabla de membresía separada** (`Dim_Usuario_Cliente` u otra): el vínculo usuario↔cuenta se determina exclusivamente por `admin_local_id`.
- Enviar correo al administrador local con credenciales e instrucciones.

### RF-ONB-002: Configurar cuenta de nuevo cliente (CU-O12)

El sistema debe permitir al Administrador configurar la cuenta recién creada:
- Actualizar Dim_Cliente con: plan_suscripcion, logo_url.
- Establecer estado_onboarding = 'Pendiente'.
- Esta operación es un UPDATE sobre la misma fila de Dim_Cliente creada en O01.

### RF-ONB-003: Onboarding digital guiado (CU-O02)

El sistema debe guiar al administrador local del cliente a través de un flujo de onboarding estructurado con etapas canónicas en `Fact_Onboarding.etapa`:
1. **`cambio_password`** — cambio de contraseña obligatorio (si aplica).
2. **`perfil_corporativo`** — configuración de perfil corporativo.
3. **`preferencias`** — configuración de preferencias (umbrales, canales, zonas, destinatarios reportes). Al guardar esta etapa, el sistema **crea** el registro en `Dim_Preferencias_Cliente` (no existe fila previa en O01 ni O12).
4. Etapas **opcionales adicionales** según el plan (nombres definidos por catálogo del plan; fuera del alcance de esta spec detallar el catálogo por plan).

Las etapas 1–3 son **obligatorias**. `estado_onboarding='Completado'` solo cuando las tres tienen `completado=true` en `Fact_Onboarding` (más cualquier etapa opcional exigida por el plan, si aplica).

Cada etapa completada se registra en Fact_Onboarding con: etapa (string del catálogo), completado (true), fecha_completado (timestamp).

### RF-ONB-004: Guardar progreso de onboarding (CU-O09)

El sistema debe guardar automáticamente el progreso del onboarding:
- Cada fila de Fact_Onboarding insertada ES el progreso guardado.
- No existe un registro de "progreso" separado: la presencia de una fila con completado=true indica que esa etapa fue superada.
- Cuando el Cliente reanuda el onboarding, el sistema consulta Fact_Onboarding para determinar qué etapas tienen completado=true y lo lleva a la siguiente etapa pendiente.
- No se reinicia ningún progreso previo.

### RF-ONB-005: Reenviar invitación (CU-O08)

El sistema debe permitir al Administrador o al Cliente reenviar la invitación a un usuario:
1. El sistema genera una contraseña temporal.
2. Escribe el hash en Dim_Credencial.contrasena.
3. Marca Dim_Credencial.estadocredencial = 'Cambio contraseña'.
4. Envía la contraseña temporal por correo al gmail registrado en Dim_Usuarios.
5. No existe tabla de tokens de invitación independiente: la propia Dim_Credencial almacena el estado transitorio.

## 5. Requisitos no funcionales

### RNF-ONB-001: Tiempo de registro
El registro de cuenta (O01) debe completarse en menos de 3 minutos.

### RNF-ONB-002: Disponibilidad del onboarding
El flujo de onboarding debe estar disponible 24/7. Debe poderse reanudar sin pérdida de datos.

### RNF-ONB-003: Trazabilidad
Toda creación de cuenta, configuración y reenvío de invitación debe registrarse en logs del sistema.

### RNF-ONB-004: Recordatorios de onboarding
Los recordatorios de RN-ONB-004 se envían como máximo **un correo por semana** por cuenta al gmail del `admin_local_id`, a partir del día 30 desde el registro de la cuenta (O01), mientras `estado_onboarding` ≠ `Completado`.

## 6. Reglas de negocio

### RN-ONB-001
El NIT debe ser único en Dim_Cliente.

### RN-ONB-002
El gmail del administrador local debe ser único en Dim_Usuarios.

### RN-ONB-003
Una cuenta de cliente debe tener al menos un administrador local asignado.

### RN-ONB-004
Si el onboarding no se completa en 30 días (`estado_onboarding` distinto de `Completado`), el sistema envía **recordatorios por correo (SMTP) semanales** al administrador local (`admin_local_id`) desde el día 30 hasta que el onboarding quede `Completado`. El fallo de envío se registra en logs sin detener el job de recordatorios.

### RN-ONB-005
La cuenta permanece en el estado de onboarding donde quedó. No se reinicia el progreso.

### RN-ONB-006
CU-O08 (Reenviar invitación) no requiere tabla de tokens separada. La credencial misma almacena el estado transitorio via estadocredencial='Cambio contraseña'.

### RN-ONB-007
No existe tabla intermedia de membresía usuario↔cuenta. Un usuario pertenece a una cuenta de cliente si y solo si `Dim_Cliente.admin_local_id` apunta a su `idusuario`.

### RN-ONB-008
`Dim_Cliente.estado` y `Dim_Cliente.estado_onboarding` son independientes. `estado='Activo'` se establece en O01; `estado_onboarding` refleja el avance del flujo guiado y no bloquea que la cuenta exista como activa.

### RN-ONB-009
Los valores canónicos de `Fact_Onboarding.etapa` son: `cambio_password`, `perfil_corporativo`, `preferencias` (obligatorias) y etapas opcionales adicionales según plan. No se aceptan nombres de etapa arbitrarios fuera de este catálogo.

### RN-ONB-010
`Dim_Preferencias_Cliente` no se crea en O01 ni O12. La primera fila se inserta al completar la etapa `preferencias` en O02 con los valores configurados por el cliente.

## 7. Entradas

### Para registro de cuenta (CU-O01)
razon_social, nombre, tipo, nit_identificacion, fecha_inicio_contrato, admin_local_nombres, admin_local_apellidos, admin_local_gmail.

### Para configuración de cuenta (CU-O12)
idcliente, plan_suscripcion, logo_url.

### Para onboarding (CU-O02)
idcliente, etapa, datos de la etapa.

### Para reenviar invitación (CU-O08)
id_usuario (o gmail).

## 8. Salidas

- **201 Created — Cuenta creada:** idcliente, estado='Activo' (`estado_onboarding` se asigna en O12).
- **200 OK — Cuenta configurada:** plan_suscripcion, logo_url, estado_onboarding.
- **200 OK — Etapa completada:** { etapa, progreso }.
- **200 OK — Progreso actual:** { etapas_completadas, etapa_actual }.
- **200 OK — Invitación reenviada:** mensaje de confirmación.
- **400/401/403/409** según validaciones.

## 9. Estados posibles

### Estados de cuenta (Dim_Cliente.estado)
- **Activo**: se establece en O01 al registrar la cuenta. Permanece `Activo` durante todo el onboarding salvo baja posterior (módulo gestion-cuentas, CU-O11).

### Estados de onboarding (Dim_Cliente.estado_onboarding)
- **Pendiente**: cuenta creada y configurada, onboarding no iniciado.
- **En progreso**: al menos una Fact_Onboarding registrada, no todas completas.
- **Completado**: las etapas obligatorias (`cambio_password`, `perfil_corporativo`, `preferencias`) tienen `completado=true` en Fact_Onboarding (más etapas opcionales exigidas por plan, si aplica).

### Fact_Onboarding
- Cada fila = una etapa.
- `etapa` (STRING): valor del catálogo canónico — `cambio_password` | `perfil_corporativo` | `preferencias` | *(opcionales por plan)*.
- completado: true/false.
- fecha_completado: timestamp cuando se completó.

### admin_local_id (Dim_Cliente)
- Apunta al único usuario vinculado a la cuenta en este módulo (sin tabla de membresía separada).

### Dim_Preferencias_Cliente
- Se crea en O02 al completar la etapa `preferencias` (no antes).
- Relación 1:1 con `Dim_Cliente` vía `id_cliente`.

## 10. Escenarios

### Escenario 1: Registro + configuración de cliente (O01 + O12)
Administrador crea cuenta en Dim_Cliente (O01) → luego configura plan y logo (O12) → estado_onboarding='Pendiente'.

### Escenario 2: Onboarding con progreso guardado (O02 + O09)
Cliente completa etapa 1 → sistema escribe Fact_Onboarding (etapa='cambio_password', completado=true) → cliente cierra sesión → al reanudar, sistema lee Fact_Onboarding, detecta `cambio_password` completa, lo lleva a `perfil_corporativo`.

### Escenario 3: Reenviar invitación (O08)
Administrador reenvía invitación → sistema genera temp password → Dim_Credencial.contrasena = hash → estadocredencial='Cambio contraseña' → email → próximo login fuerza cambio.

## 11. Criterios de aceptación

### CA-ONB-001
Administrador puede registrar cliente en Dim_Cliente (O01).

### CA-ONB-002
Administrador puede configurar plan_suscripcion y logo_url (O12) sobre el mismo registro.

### CA-ONB-003
Cliente puede completar etapas de onboarding y cada una se persiste en Fact_Onboarding (O02).

### CA-ONB-004
Sistema guarda progreso automáticamente: cada Fact_Onboarding insertado es el progreso (O09).

### CA-ONB-005
Al reanudar, el sistema retoma desde la última etapa incompleta (completado=false).

### CA-ONB-006
Administrador/Cliente puede reenviar invitación: temp password, estadocredencial='Cambio contraseña', email (O08).

### CA-ONB-007
Si `estado_onboarding` ≠ `Completado` tras 30 días, el sistema envía correo semanal de recordatorio al admin local hasta completar el onboarding. Fallos SMTP se registran en logs.

## 12. Dependencias

- **autenticacion-y-rbac**: requiere Dim_Usuarios, Dim_Credencial, Dim_Rol, Dim_Usuario_Rol y autenticación JWT.

## 13. Fuera de alcance

- Auto-registro de cuenta por el propio cliente.
- Gestión detallada de planes de suscripción (spec Suscripciones-Facturacion).
- Facturación y cobros.
- Personalización avanzada del portal del cliente.
