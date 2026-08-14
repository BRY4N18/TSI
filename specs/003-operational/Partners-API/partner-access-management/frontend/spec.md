# Feature Specification: Gestión de Acceso de Partners — Frontend

**Feature Branch / capa**: `partner-access-management/frontend`  
**Created**: 2026-08-08  
**Status**: ✅ Construida (2026-08-13) — las tres superficies del alcance previsto están implementadas y verificadas contra el stack real  
**Depends-on**: [`../backend/spec.md`](../backend/spec.md) (RF-PAC-*, RNF-PAC-*, CA-PAC-*, OpenAPI). Esta capa **MUST NOT** redefinir reglas de negocio, estados ni contratos REST.

## Alcance previsto

| Superficie | Actor | Cubre |
|---|---|---|
| **Revocación de autoservicio** ✅ | Partner de integración | Revocar una credencial comprometida con motivo, y recibir el reemplazo con su secreto (RF-PAC-001, RF-PAC-002). **Construida el 2026-08-13** en `mi-integracion`: botón por credencial vigente, confirmación en 2 pasos que nombra la credencial y su entorno (punto crítico 1), y el secreto del reemplazo en la pantalla dedicada de una sola vez (punto crítico 2). No se ofrece sobre credenciales vencidas, que se regeneran. |
| **Estado de acceso propio** ✅ | Partner de integración | Su estado (activo/suspendido con motivo y fecha), credenciales e historial — accesible **también estando suspendido** (RF-PAC-009, RN-PAC-016). **Construida el 2026-08-13** en `mi-integracion`: panel con motivo, fecha, días de mora e historial, que solo se pide cuando hay una suspensión que explicar (puntos críticos 4 y 5). |
| **Panel de suspensiones** ✅ | Administrador | Partners suspendidos y en ciclo de mora con avisos enviados; suspender y reactivar manualmente (RF-PAC-005). **Construida el 2026-08-13** en `/partners/consola/suspensiones`, con el desglose `restituidas` / `no restituidas` (punto crítico 3) y los avisos como cuenta atrás (punto crítico 6). **La suspensión vive además en la ficha del partner**: la cola solo lista morosos y suspendidos, así que por sí sola no permitía suspender por vencimiento de contrato o petición del cliente, que el SRS admite expresamente. |

## Interaction Capability — puntos críticos ya identificados

Derivan de reglas del backend y **no** son decisiones libres de esta capa:

1. **Revocar es destructivo e irreversible, pero debe ser rápido.** Hay una tensión real: es una acción de emergencia ante una credencial comprometida, así que ponerle fricción es peligroso; pero revocar la credencial equivocada corta un sistema en producción. La UI debe **identificar con claridad cuál se va a revocar** (nombre y entorno bien visibles) sin convertir la acción en un trámite lento.
2. **El secreto del reemplazo se muestra una sola vez.** Mismo tratamiento que en la emisión de #07: paso dedicado, copia explícita y confirmación antes de cerrar. Si el partner lo pierde aquí, tras un incidente de seguridad, la situación empeora.
3. **La reactivación no restituye todo, y debe verse.** El desglose `credenciales_restituidas` / `credenciales_no_restituidas` no es un detalle técnico: explica que la credencial que el partner revocó por seguridad **sigue inactiva a propósito** (RN-PAC-011). Si la UI no lo muestra, parecerá un fallo.
4. **«Suspendido» no es un error del partner necesariamente.** Puede ser mora, pero también vencimiento de contrato. El motivo debe presentarse como texto redactado, no como código.
5. **El partner suspendido conserva acceso de lectura** (RN-PAC-016). La UI no debe bloquearle el portal entero: es justo donde entiende por qué se le cortó y qué debe pagar.
6. **Los avisos previos son una cuenta atrás, no una alarma.** T-10 y T-5 existen para que el partner pueda reaccionar. Presentarlos con el tiempo restante y la acción concreta que evita la suspensión.

## Verificación contra el stack real (2026-08-13)

La **regla de cascada** ya se puede ejercitar desde la interfaz, y se comprobó en Pinot:
suspender desactivó las 2 credenciales activas; reactivar restituyó **esas 2** y dejó la que
el partner había **revocado por seguridad** inactiva, informándolo en pantalla. Ninguna
credencial comprometida resucitó.

## Pendiente

Nada del alcance previsto. Si se amplía —por ejemplo, editar los umbrales de aviso de mora
(RNF-PAC-005) desde la interfaz—, se especifica aquí.

Referencia de estilo: [`../../partner-api-onboarding/frontend/`](../../partner-api-onboarding/frontend/) y `.specify/docs/design/design-system.md`.
