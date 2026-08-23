# Feature Specification: Endurecimiento de Seguridad Transversal

**Feature Branch**: `global-endurecimiento-seguridad`

**Created**: 2026-08-23

**Status**: Draft

**Input**: Implementar las diez reglas `PG-SEC-*` del [Plan Global de Pruebas](../PlanPruebas/spec.md) §8, que hoy suman una cubierta, cinco parciales y cuatro pendientes — cinco de ellas de severidad Bloqueante.

---

## Contexto y relación con el plan global

Esta feature **no inventa requisitos nuevos**: implementa un bloque ya especificado. La autoridad
sobre *qué* debe cumplirse es `specs/Global/PlanPruebas/spec.md` §8; esta spec define *cómo* se
construye la verificación y en qué orden.

| Regla del plan | Severidad | Estado hoy | Historia de usuario |
|---|---|---|---|
| `PG-SEC-001` — Aislamiento multi-tenant (IDOR) | Bloqueante | ⚠️ Parcial | US1 |
| `PG-SEC-002` — Autorización vertical por rol | Bloqueante | ⚠️ Parcial | US2 |
| `PG-SEC-003` — Integridad del JWT | Bloqueante | ⚠️ Parcial | US3 |
| `PG-SEC-005` — Inyección | Bloqueante | ❌ Pendiente | US4 |
| `PG-SEC-007` — Datos sensibles en logs y respuestas | Bloqueante | ❌ Pendiente | US5 |
| `PG-SEC-004` — Límite de tasa efectivo | Mayor | ❌ Pendiente | US6 |
| `PG-SEC-006` — Subida de archivos | Mayor | ❌ Pendiente | US7 |
| `PG-SEC-008` — Cabeceras y cookies HTTP | Mayor | ⚠️ Parcial | US8 |
| `PG-SEC-010` — Aislamiento de la demo | Mayor | ⚠️ Parcial | US9 |
| `PG-SEC-009` — Dependencias vulnerables | Mayor | ✅ Cubierta | — (fuera de alcance) |

**Actores implicados** (ver `.specify/docs/actors.md`): Partner, Cliente, Operador, Técnico de
campo, Administrador, Director de departamento.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Un partner no puede ver los datos de otro partner (Priority: P1)

Como **partner de TSI**, cuando consulto la API con mis credenciales, solo obtengo los accidentes,
facturas y unidades de mi propia organización. Si sustituyo un identificador en la URL por el de
otro partner, el sistema me lo deniega sin devolverme ni un dato suyo.

**Why this priority**: es el mayor riesgo real del sistema. TSI sirve a partners, aseguradoras,
municipios y clientes sobre el **mismo** modelo de datos, y un fallo de aislamiento no produce
ningún síntoma: nadie reporta que vio datos de más. Además es el fallo que un evaluador externo
—o un atacante— encontraría primero, porque solo requiere cambiar un número en una URL.

**Independent Test**: autenticarse como tenant A, solicitar recursos de B en todos los endpoints
con identificador, y comprobar que ninguno devuelve datos. Se puede probar y entregar sin tocar
ninguna otra historia.

**Acceptance Scenarios**:

1. **Given** un partner A autenticado y un accidente que pertenece al partner B, **When** A hace
   `GET` del accidente de B por su id, **Then** el sistema no devuelve datos de B, y **si A no es
   gestor** la respuesta es **byte a byte idéntica** a la de un identificador inexistente.
2. **Given** el mismo escenario, **When** A hace `PUT`, `PATCH` o `DELETE` sobre ese recurso,
   **Then** el recurso de B **no se modifica**.
3. **Given** un endpoint que recibe un identificador **en el cuerpo** y no en la URL, **When** A
   envía el id de un recurso de B, **Then** el sistema lo rechaza.
4. **Given** un endpoint nuevo añadido al enrutador sin filtro de tenencia, **When** se ejecuta la
   suite, **Then** la suite **falla** señalando ese endpoint.

> El escenario 4 es el que da valor duradero: sin él, la cobertura envejece en cuanto alguien añade
> una ruta.

---

### User Story 2 — Un rol no autorizado no entra por mucho que conozca la URL (Priority: P1)

Como **operador**, si intento acceder a un informe financiero cuyo acceso corresponde a Finanzas,
el sistema me lo deniega en el servidor, no solo ocultándome el botón en la interfaz.

**Why this priority**: complementa a US1 en el eje vertical. Existe cobertura parcial en
`e2e/tests/04-auth-roles.spec.ts`, pero por muestreo: no hay matriz completa rol × endpoint, así
que no se sabe qué combinaciones están sin probar.

**Independent Test**: generar la matriz rol × endpoint y comprobar cada celda.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con un rol no admitido por el endpoint, **When** lo invoca,
   **Then** recibe `403`.
2. **Given** la matriz completa de roles y endpoints, **When** se ejecuta la suite, **Then** toda
   celda no cubierta se reporta explícitamente como descubierta, no se omite en silencio.

---

### User Story 3 — Un token manipulado nunca es aceptado (Priority: P1)

Como **atacante que ha capturado un token válido**, no consigo alterarlo para elevar mi rol,
cambiar de tenant ni prolongar su vigencia.

**Why this priority**: hoy se prueba que un token válido funciona (fixture `auth_headers`), que es
la mitad fácil. Falta probar que los inválidos **no** funcionan, que es donde está el riesgo.

**Independent Test**: batería de tokens deliberadamente malformados contra un endpoint protegido.

**Acceptance Scenarios**:

1. **Given** un token con la firma alterada, **When** se usa, **Then** `401`.
2. **Given** un token con cabecera `alg: none`, **When** se usa, **Then** `401`.
3. **Given** un token firmado con un algoritmo distinto de RS256, **When** se usa, **Then** `401`.
4. **Given** un token expirado, **When** se usa, **Then** `401`.
5. **Given** un token válido cuyos claims de rol o tenant se han modificado, **When** se usa,
   **Then** `401` — la firma deja de cuadrar.
6. **Given** una sesión revocada, **When** se usa su token aún no expirado, **Then** `401`.

---

### User Story 4 — Un filtro de informe no puede alterar la consulta (Priority: P1)

Como **usuario de informes**, los valores que escribo en un filtro se tratan siempre como datos,
nunca como parte de la sentencia que se ejecuta contra Pinot o ClickHouse.

**Why this priority**: los informes con filtros dinámicos, `ORDER BY` variable y nombres de columna
parametrizables son la superficie de máximo riesgo del sistema, porque ahí la parametrización
estándar **no aplica** y hay que usar lista blanca — que es fácil de olvidar.

**Independent Test**: enviar cargas de inyección en cada parámetro de filtro de cada informe.

**Acceptance Scenarios**:

1. **Given** un parámetro de filtro, **When** recibe una carga de inyección, **Then** se rechaza o
   se neutraliza, y la respuesta **no** contiene mensajes de error del motor de base de datos.
2. **Given** un parámetro que nombra una columna o un criterio de orden, **When** recibe un valor
   fuera de la lista blanca, **Then** se rechaza con `400`.

---

### User Story 5 — Un error no revela datos de una víctima (Priority: P1)

Como **responsable del sistema**, ningún registro de log, traza ni respuesta de error contiene
datos personales, coordenadas exactas de víctimas, tokens ni credenciales.

**Why this priority**: TSI maneja ubicación, identidad de víctimas de accidentes y datos
potencialmente de salud. El Principio V de la constitución lo declara dato sensible, y hoy no hay
ninguna prueba que lo verifique.

**Independent Test**: provocar errores en endpoints que manejan datos de víctimas e inspeccionar
tanto la respuesta como la salida de log.

**Acceptance Scenarios**:

1. **Given** un endpoint que maneja datos de una víctima, **When** se produce una excepción,
   **Then** la respuesta no incluye traza, ni rutas internas, ni nombres de tabla, ni SQL.
2. **Given** cualquier operación con datos personales, **When** se escribe en el log, **Then** los
   identificadores personales aparecen enmascarados.

---

### User Story 6 — El cupo por minuto se aplica de verdad (Priority: P2)

Como **plataforma**, cuando un cliente supera su cupo de peticiones por minuto recibe `429`.

**Why this priority**: hay cuatro throttles declarados en `settings.py` y **ninguno tiene prueba**.
Están o no están aplicándose, y hoy no hay forma de saberlo.

**Independent Test**: superar cada cupo declarado y comprobar la respuesta.

**Acceptance Scenarios**:

1. **Given** el throttle `prospecto_registro` (10/min), **When** se hace la petición 11 en un
   minuto, **Then** `429`.
2. **Given** los throttles `demo_sesion_ip` (20/min), `demo_interaccion_token` (60/min) y
   `partner_api` (1000/min), **When** se superan, **Then** `429`.

> **Frontera de negocio que la prueba no debe cruzar:** esto es el techo **técnico** de plataforma.
> **No** es la cuota comercial de `RN-APM-002`, donde el cupo mensual **nunca bloquea: se factura**.
> Una prueba que espere `429` por cuota mensual estaría verificando lo contrario de la regla de
> negocio.

---

### User Story 7 — Un ejecutable renombrado a `.jpg` no entra (Priority: P2)

Como **operador que sube evidencia fotográfica**, el sistema acepta imágenes reales y rechaza
cualquier otra cosa, aunque tenga extensión de imagen.

**Why this priority**: el sistema acepta hasta 50 MB por petición multipart. Validar por extensión
o por `Content-Type` declarado es validar por lo que el cliente dice de sí mismo.

**Independent Test**: subir ficheros de tipos y tamaños diversos al endpoint de evidencia.

**Acceptance Scenarios**:

1. **Given** un ejecutable renombrado a `.jpg`, **When** se sube, **Then** se rechaza tras
   inspeccionar sus **bytes mágicos**, no su extensión.
2. **Given** un fichero de 51 MB, **When** se sube, **Then** `413`.
3. **Given** un nombre de fichero con `../`, **When** se sube, **Then** el nombre se sanea y no
   escapa del directorio previsto.
4. **Given** un SVG con script incrustado, **When** se sube, **Then** se rechaza.

---

### User Story 8 — Toda respuesta lleva sus cabeceras de seguridad (Priority: P2)

Como **navegador del usuario**, recibo en cada respuesta las cabeceras que impiden sniffing de
tipo, incrustación en iframes ajenos y fuga de referer.

**Why this priority**: implementado parcialmente el 2026-08-23 (ver `changelog.md` C2). Faltan la
CSP y la verificación del lado nginx.

**Independent Test**: inspeccionar las cabeceras de respuesta en Django y en `nginx.conf`.

**Acceptance Scenarios**:

1. **Given** cualquier respuesta de la API, **When** se inspeccionan sus cabeceras, **Then**
   incluyen `X-Content-Type-Options`, `X-Frame-Options` y `Referrer-Policy`.
2. **Given** un despliegue no local, **When** se inspecciona, **Then** incluye además
   `Strict-Transport-Security` y una **CSP** declarada.
3. **Given** `frontend/nginx.conf`, **When** se revisa, **Then** no contradice ni omite las
   cabeceras anteriores.

---

### User Story 9 — La demo no es una puerta trasera (Priority: P2)

Como **prospecto que prueba la demo interactiva**, no puedo alcanzar datos reales de clientes ni
usar mi token de demo contra los endpoints de negocio.

**Why this priority**: el flujo de demo emite tokens propios (grant HMAC + sesión HS256) distintos
del JWT RBAC. La guarda de secretos ya existe; falta probar el **aislamiento**.

**Independent Test**: usar un token de demo válido contra endpoints de negocio.

**Acceptance Scenarios**:

1. **Given** un token de sesión de demo válido, **When** se usa contra un endpoint de negocio,
   **Then** `401` — no es del tipo que ese endpoint acepta.
2. **Given** una sesión de demo, **When** consulta datos, **Then** solo alcanza datos sintéticos,
   nunca registros reales de clientes.

---

### Edge Cases

- ¿Qué ocurre si un endpoint recibe un identificador **válido y existente** pero de otro tenant,
  y además el usuario tiene el rol correcto? Debe fallar igualmente por tenencia (US1 + US2 son
  ejes independientes y ambos deben aplicarse).
- ¿Qué ocurre con los identificadores anidados dentro de listas en el cuerpo de la petición?
- ¿Qué devuelve el sistema si el token es válido pero el usuario fue desactivado tras emitirlo?
- ¿Qué ocurre si Redis (almacén de sesión) no responde al validar una revocación? Debe denegar,
  nunca conceder por defecto.
- ¿Un `404` por tenencia y un `404` por recurso inexistente son indistinguibles desde fuera? Deben
  serlo: si difieren en cuerpo o en tiempo de respuesta, filtran la existencia del recurso.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-SEC-001**: El sistema DEBE resolver la pertenencia **contra el almacén**, nunca a partir de
  un valor proporcionado por el cliente. El mecanismo actual (`verificar_propiedad()` en la capa de
  servicio, que resuelve el cliente vía `ClienteLookupService`) cumple este requisito; lo que falta
  no es rediseñarlo, sino **verificarlo de forma sistemática en todos los endpoints**.
- **FR-SEC-002**: Para un actor **no gestor**, el sistema DEBE responder de forma indistinguible
  ante «recurso de otro tenant» y «recurso inexistente» — mismo código, mismo cuerpo y tiempo de
  respuesta comparable. Un actor gestor SÍ recibe el diagnóstico preciso.
- **FR-SEC-003**: La suite de aislamiento DEBE construirse sobre el **inventario de rutas** del
  enrutador, de modo que un endpoint nuevo sin cobertura haga fallar la suite.
- **FR-SEC-004**: Cada endpoint DEBE declarar los roles admitidos, y el sistema DEBE responder
  `403` a cualquier rol no declarado.
- **FR-SEC-005**: El sistema DEBE rechazar todo token con firma inválida, `alg: none`, algoritmo
  distinto al declarado, expirado, con claims manipulados, o correspondiente a sesión revocada.
- **FR-SEC-006**: Ninguna consulta a Pinot o ClickHouse DEBE construirse por concatenación de
  entrada del usuario; toda entrada se parametriza o se valida contra lista blanca.
- **FR-SEC-007**: Ningún log, traza ni respuesta de error DEBE incluir datos personales,
  coordenadas exactas de víctimas, tokens ni credenciales.
- **FR-SEC-008**: Los cupos de peticiones declarados DEBEN aplicarse efectivamente, devolviendo
  `429` al superarse.
- **FR-SEC-009**: Las subidas DEBEN validarse por **bytes mágicos**, con límite de tamaño y nombre
  saneado.
- **FR-SEC-010**: Toda respuesta DEBE incluir las cabeceras de seguridad declaradas, y una CSP en
  entornos no locales.
- **FR-SEC-011**: Los tokens del flujo de demo NO DEBEN ser aceptados por los endpoints de negocio.

### Key Entities

- **Tenant**: organización propietaria de un conjunto de datos (partner, cliente corporativo,
  municipio). Es el eje de aislamiento de US1.
- **Rol**: capacidad asignada a un usuario dentro de su tenant. Es el eje de US2, **ortogonal** al
  anterior: tener el rol correcto no da acceso a datos de otro tenant, y pertenecer al tenant
  correcto no da acceso a materias ajenas al rol.
- **Sesión**: vínculo entre un token emitido y su validez actual; permite la revocación de US3.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los endpoints que reciben un identificador está cubierto por la prueba
  de aislamiento, en los métodos `GET`, `PUT`, `PATCH` y `DELETE`, y por **ambas vías de
  autenticación** (JWT de usuario y credencial de partner).
- **SC-002**: Añadir un endpoint con identificador sin filtro de tenencia hace **fallar** la suite,
  verificado introduciendo uno deliberadamente.
- **SC-003**: La matriz rol × endpoint no tiene celdas sin verificar; las no cubiertas se reportan
  explícitamente.
- **SC-004**: Ninguna de las seis variantes de token manipulado de US3 obtiene acceso.
- **SC-005**: Ninguna carga de inyección altera una consulta ni produce un mensaje del motor de
  base de datos en la respuesta.
- **SC-006**: Las cinco reglas Bloqueantes de este bloque (`PG-SEC-001`, `002`, `003`, `005`,
  `007`) pasan a estado ✅ Cubierta en el plan global.
- **SC-007**: Ninguna prueba de este bloque queda marcada `skip` o `xfail` sin justificación y
  fecha de caducidad (`PG-CI-003`).

---

## Assumptions

- **El token JWT no lleva claim de tenant.** Verificado en `core/jwt_utils.py`: el payload es
  `sub`, `roles` y `session_id`. La pertenencia se resuelve en la capa de servicio con
  `verificar_propiedad()` (`apps/partners/permissions.py`), que consulta el cliente mediante
  `ClienteLookupService`. La suite de aislamiento debe apoyarse en ese mecanismo, no suponer un
  claim que no existe.
- **Hay dos vías de autenticación y ambas necesitan cobertura.** Además del JWT de usuario, los
  partners entran por `CredencialAPIAuthentication` (client_id/credencial), que sí resuelve
  `idpartner` desde la credencial. La suite de US1 debe cubrir **las dos**, o dejará la mitad de la
  superficie sin probar.
- La verificación de bytes mágicos se hará con una biblioteca del ecosistema Python; no se
  implementará detección propia.
- La CSP se definirá restrictiva y se ajustará con lo que el frontend Angular requiera realmente,
  no al revés.
- Se reutiliza la infraestructura de pruebas existente (`conftest.py`, fixtures `mock_pinot`,
  `mock_kafka`, `auth_headers`). **Advertencia aprendida el 2026-08-23** (`changelog.md` C3): toda
  prueba nueva de este bloque debe incluir la fixture que mockea Pinot, o la validación de sesión
  saldrá a buscar un Pinot real y devolverá `401` — un fallo que aparenta ser de permisos.
- `PG-SEC-009` (dependencias vulnerables) queda **fuera de alcance**: ya está cubierta por el job
  `dependencias` del pipeline.

---

## Decisión resuelta — `403` vs `404` ante recurso ajeno

**Resuelta el 2026-08-23** (`decisiones-pendientes.md` #51, `changelog.md` C4). **La disyuntiva era
falsa**: el código correcto depende de **quién pregunta**.

- **Gestor** (Administrador, Desarrollador de APIs) — opera sobre cualquier partner, así que un
  `404` no le revela nada. Conserva el diagnóstico preciso.
- **No gestor** — «no existe» y «no es tuyo» devuelven la **misma respuesta, con el mismo cuerpo**.

Implementado en `apps/partners/permissions.py::resolver_partner_visible`. Los escenarios de US1
afirman **«no devuelve datos de B»** y, para un no gestor, **«la respuesta es idéntica a la de un id
inexistente»** — que es el requisito de seguridad real y no depende del número concreto.

> **Este patrón es el criterio de toda US1**, no solo de Partners: cualquier módulo con recursos por
> tenant debe resolverse igual.

---

## Dependencies

- **Depends-on**: `.github/workflows/ci.yml` — las suites de este bloque deben incorporarse al job
  `configuracion` o a uno propio, o no protegerán nada (`PG-CI-001`).
- **Autoridad**: `specs/Global/PlanPruebas/spec.md` §8 · `.specify/memory/constitution.md`
  (Principio V, datos sensibles) · `.specify/docs/architecture/api-standards.md` (códigos HTTP) ·
  `.specify/docs/architecture/testing.md` (markers, fixtures, umbrales).
