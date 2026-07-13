# Phase 0 Research - Gestión de Cuenta de Cliente

## Decision 1: Contract-first con OpenAPI para endpoints de cuenta

- Decision: Definir primero contrato OpenAPI 3.0 en `contracts/gestion-cuentas.openapi.yaml` para todos los endpoints bajo `/api/v1/cuentas-clientes/{idcliente}/...`.
- Rationale: Cumple API-first y permite generar/validar tipos TypeScript y tests de contrato antes de implementar vistas DRF.
- Alternatives considered:
  - Implementar vistas DRF primero y documentar después (rechazado: alto riesgo de desalineación frontend/backend).
  - gRPC interno (rechazado: contradice `api-standards.md` REST).

## Decision 2: Endpoints REST y semántica HTTP

- Decision:
  - `GET/PATCH /cuentas-clientes/{idcliente}/perfil` — CU-O03 perfil corporativo.
  - `GET/PATCH /cuentas-clientes/{idcliente}/preferencias` — CU-O03 preferencias.
  - `GET /cuentas-clientes/{idcliente}/usuarios-elegibles` — lista usuarios activos de la cuenta (selector O10).
  - `POST /cuentas-clientes/{idcliente}/transferencia-propiedad` — CU-O10 (inmediata, `Idempotency-Key`).
  - `POST /cuentas-clientes/{idcliente}/baja` — CU-O11 solo Administrador (`Idempotency-Key`).
  - `POST /cuentas-clientes/{idcliente}/logo/upload-url` — URL firmada Azure Blob; cliente sube binario y luego `PATCH perfil` con `logo_url`.
- Rationale: Recursos anidados bajo cuenta; escrituras POST con idempotencia según `api-standards.md`; PATCH para actualizaciones parciales.
- Alternatives considered:
  - PUT para reemplazo completo de perfil (rechazado: spec define campos parciales editables).
  - Subir logo como multipart en mismo endpoint PATCH (rechazado: patrón Dim_EvidenciaFoto exige URL en Pinot, binario en Blob).

## Decision 3: Django por capas (Vista → Servicio → Repositorio) + Kafka-only-write

- Decision:
  - **Vista**: DRF `APIView` por operación (mismo patrón que `auth_views.py`).
  - **Servicio**: un servicio por caso de uso (`CuentaPerfilService`, `TransferenciaPropiedadService`, etc.).
  - **Repositorio**: `ClienteRepository`, `PreferenciasClienteRepository`, `CuentaUsuarioRepository`, reutilizar `SessionRepository`.
  - **Escritura**: `KafkaWriter.publish()` a `Dim_Cliente_topic`, `Dim_Preferencias_Cliente_topic`, `Fact_Session_topic`.
- Rationale: Regla vinculante de `architectural-patterns.md`; consistente con autenticacion-y-rbac ya implementado.
- Alternatives considered:
  - ORM Django con PostgreSQL como fuente de verdad (rechazado: arquitectura Pinot+Kafka del proyecto).
  - Escritura directa a Pinot (rechazado: violación explícita de infraestructura).

## Decision 4: Autenticación JWT + autorización por rol y scope de cuenta

- Decision:
  - Todos los endpoints requieren `Authorization: Bearer <JWT>` y validación de `Fact_Session` (patrón autenticacion-y-rbac).
  - **Cliente**: solo `idcliente` de su membresía; transferencia solo si `request.user_id == admin_local_id`.
  - **Administrador**: acceso a cualquier `idcliente`; único autorizado en `POST .../baja`.
  - Resolución de membresía usuario↔cuenta vía `CuentaUsuarioRepository` (dependencia incorporacion-clientes define el vínculo en onboarding).
- Rationale: Alineado con api-authentication (JWT stateless + verificación de sesión) y RNF-CTA-002.
- Alternatives considered:
  - Claim `idcliente` en JWT sin lookup (rechazado por ahora: JWT actual no incluye claim; lookup en repositorio evita cambio breaking en auth).
  - Autorización solo en frontend (rechazado: riesgo de seguridad).

## Decision 5: Baja de cuenta — expulsión masiva de sesiones

- Decision: `BajaCuentaService` invoca `SessionRepository.expel_all_by_cliente(idcliente)` publicando eventos `Fact_Session` con `estadosession='Expulsado'`.
- Rationale: Clarificación aprobada; mismo patrón que CU-O07 revoke-session.
- Alternatives considered:
  - Bloquear solo nuevos logins (rechazado por clarificación).
  - Expiración natural de JWT (rechazado: ventana de operación no autorizada).

## Decision 6: Notificaciones SMTP vía core transversal

- Decision: `CuentaNotificacionService` delega en `core/notificaciones` (SMTP desde variables de entorno: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). Fallo de envío → log de auditoría, operación no revertida.
- Rationale: Clarificación RN-CTA-006; `project-structure.md` define notificaciones como capacidad transversal.
- Alternatives considered:
  - Notificaciones inline en cada servicio (rechazado: duplicación).
  - Revertir transferencia/baja si falla email (rechazado por spec).

## Decision 7: Angular — servicios tipados y guards

- Decision:
  - `CuentaClienteApiService`: métodos 1:1 con operaciones OpenAPI; tipos en `models/cuenta-cliente.contract.ts`.
  - `CuentaScopeGuard`: Cliente solo navega a rutas con su `idcliente`.
  - `AdminLocalGuard`: bloquea transferencia si usuario no es `admin_local_id`.
  - `CuentaActivaGuard`: redirige si `estado === 'Dado de baja'`.
  - `AdministradorGuard` (core): protege ruta de baja.
  - Componentes standalone OnPush; lógica en servicios/facade, no en templates.
- Rationale: angular-architect + typescript-expert; separación presentación/lógica de `architectural-patterns.md`.
- Alternatives considered:
  - NgRx store global para perfil (rechazado: scope local suficiente con signals/facade en esta fase).
  - Un guard monolítico auth+rol+scope (rechazado: baja claridad y testabilidad).

## Decision 8: Membresía usuario↔cuenta (dependencia incorporacion-clientes)

- Decision: `CuentaUsuarioRepository.list_active_by_cliente(idcliente)` abstrae la consulta Pinot de usuarios de la cuenta; implementación concreta se alinea con el modelo de onboarding cuando esté disponible. Hasta entonces, mock en tests con fixture de membresía.
- Rationale: Spec exige "usuarios de la misma cuenta" sin tabla explícita en `data-model.md` global; onboarding es prerequisito (dependencia spec §12).
- Alternatives considered:
  - Asumir `admin_local_id` como único usuario (rechazado: contradice transferencia a otro usuario de la cuenta).
