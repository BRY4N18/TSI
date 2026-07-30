# Phase 0 Research - Autenticacion y RBAC

## Decision 1: Contract-first con OpenAPI para auth endpoints

- Decision: Definir primero contrato OpenAPI 3.0 para `/api/v1/auth/login`, `/logout`, `/revoke-session` y `/password-reset`.
- Rationale: Cumple API-first de constitution y reduce acoplamiento entre backend Django y frontend Angular.
- Alternatives considered:
  - Contrato implícito en código DRF (rechazado por menor trazabilidad).
  - Documentación ad hoc en markdown sin esquema formal (rechazado por baja validación automática).

## Decision 2: Autenticacion JWT RS256 + validacion de sesion en cada request

- Decision: Access JWT RS256 (60 min) + refresh opaco estático (14 días), con consulta a `Fact_Session` para estado en cada request protegida.
- Rationale: Alineado con spec clarificada (revocación inmediata y control de estado `Inicio sesion`/`Cierre sesion`/`Expulsado`).
- Alternatives considered:
  - Solo validacion de firma JWT sin consulta de sesión (rechazado por riesgo de token vigente revocado).
  - Rotación de refresh token por uso (rechazado porque la clarificación aprobó token estático).

## Decision 3: Django por capas (Vista -> Servicio -> Repositorio)

- Decision: DRF View/APIView para capa de Vista; Services para reglas de negocio y repositorios para acceso a `Dim_*`/`Fact_Session`.
- Rationale: Cumple `architectural-patterns.md`, mejora mantenibilidad y testabilidad.
- Alternatives considered:
  - Lógica de negocio dentro de ViewSets (rechazado por acoplamiento y dificultad de pruebas).
  - Acceso directo a datos desde vistas (rechazado por violar regla de repositorios).

## Decision 4: Escritura exclusiva por Kafka, sin escritura directa a Pinot

- Decision: Operaciones de escritura (sesiones, cambios de credencial, RBAC) publican eventos a topics Kafka por tabla (`Fact_Session_topic`, `Dim_Credencial_topic`, etc.).
- Rationale: Regla vinculante del proyecto: Pinot solo lectura, Kafka único canal de escritura.
- Alternatives considered:
  - INSERT/UPDATE directo a Pinot (rechazado: contradice arquitectura).
  - Escritura dual directa + evento (rechazado por inconsistencia eventual y complejidad).

## Decision 5: Angular consume contratos con AuthService + Guards

- Decision: Implementar `AuthApiService` tipado al contrato OpenAPI, `SessionGuard` para autenticación y `RoleGuard` para autorización por `roles` del token/perfil.
- Rationale: Separa presentación de lógica y mantiene consistencia con patrón de inyección de dependencias y módulos Angular.
- Alternatives considered:
  - Guard único con lógica mezclada auth+roles (rechazado por baja claridad).
  - Validación de roles solo en frontend sin enforcement backend (rechazado por riesgo de seguridad).

## Decision 6: Politica de intentos fallidos diferida

- Decision: Mantener explícitamente diferida la política obligatoria de rate limiting/bloqueo/CAPTCHA en este plan.
- Rationale: Refleja clarificación aprobada sin introducir requisitos no acordados.
- Alternatives considered:
  - Forzar throttling específico ahora (rechazado por contradecir la decisión de clarificación).
