# Trazabilidad: Onboarding de Partners API

**Estado:** Phase 1 completada. Las columnas *Tareas* y *Tests* se rellenan con `/speckit-tasks` y `/speckit-implement`.

## Criterios de aceptación

| CA | Descripción | RF / RN | Tareas | Tests | Estado |
|----|-------------|---------|--------|-------|--------|
| CA-PON-001 | Registro sobre cliente existente con suscripción vigente; `idcliente` inexistente → 404 sin escribir | RF-PON-001 | — | — | ⏳ |
| CA-PON-002 | Segundo partner sobre el mismo cliente → 409 con el `idpartner` existente, sin escritura | RF-PON-002 / RN-PON-002 | — | — | ⏳ |
| CA-PON-003 | Cliente sin suscripción vigente → 422 | RN-PON-011 | — | — | ⏳ |
| CA-PON-004 | Cupo leído de `Dim_Plan.limites` y congelado; cambio posterior del plan no altera al partner; `limites` incompleto → 422 | RF-PON-003 / RN-PON-003 | — | — | ⏳ |
| CA-PON-005 | El secreto se entrega exactamente una vez; ningún GET lo devuelve; en BD solo su hash | RF-PON-004 / RN-PON-005 | — | — | ⏳ |
| CA-PON-006 | Varias credenciales activas por entorno con nombre distinto; nombre duplicado entre activas → 409; nombre liberado reutilizable | RF-PON-005 / RN-PON-014 | — | — | ⏳ |
| CA-PON-007 | Emisión sin plan asignado → 409 sin efecto; el partner sigue en «Registrado» | RF-PON-004 | — | — | ⏳ |
| CA-PON-008 | Al vencer pruebas solo esa credencial se desactiva; el partner conserva `activo` y plan; regenera por autoservicio; avisos sin duplicar | RF-PON-006 / RN-PON-006 | — | — | ⏳ |
| CA-PON-009 | Solicitud desde estado distinto de «Pruebas activo» → 409; desde «Pruebas activo» → 202 sin emitir credencial | RF-PON-007 / RN-PON-004 | — | — | ⏳ |
| CA-PON-010 | Solo Administrador resuelve (403 al resto); al aprobar, pruebas sigue activa; al rechazar, motivo obligatorio (422 si falta), vuelta a «Pruebas activo», reintentos sin tope | RF-PON-008 / RN-PON-007 | — | — | ⏳ |
| CA-PON-011 | Los siete eventos del ciclo de vida insertan exactamente una fila; ninguna operación hace UPDATE ni DELETE sobre la bitácora | RF-PON-010 / RN-PON-010 | — | — | ⏳ |
| CA-PON-012 | Toda acción de habilitación sobre partner con `activo=false` → 409 | RN-PON-013 | — | — | ⏳ |
| CA-PON-013 | Contrato por servicio: versión vigente, soportadas y fecha de retiro; servicios distintos en versiones distintas; máximo una `vigente` por servicio | RF-PON-011 / RN-PON-012 | — | — | ⏳ |
| CA-PON-014 | Emisión de credencial de pruebas p95 ≤ 2 s | RNF-PON-001 | — | — | ⏳ |

## Requisitos funcionales

| RF | Descripción | Tareas |
|----|-------------|--------|
| RF-PON-001 | Registro del partner sobre cliente existente | — |
| RF-PON-002 | Unicidad 1:1 cliente ↔ partner | — |
| RF-PON-003 | Cupo derivado del plan contratado | — |
| RF-PON-004 | Emisión de credencial de pruebas por autoservicio | — |
| RF-PON-005 | Credenciales nombradas y múltiples por entorno | — |
| RF-PON-006 | Expiración de pruebas y regeneración por autoservicio | — |
| RF-PON-007 | Solicitud de promoción a producción | — |
| RF-PON-008 | Aprobación o rechazo de la promoción | — |
| RF-PON-009 | Coexistencia de entornos | — |
| RF-PON-010 | Bitácora inmutable del ciclo de vida | — |
| RF-PON-011 | Consulta del contrato de integración versionado | — |
| RF-PON-012 | Consulta del estado de incorporación | — |

## Casos de uso (numeración canónica del catálogo §5.5)

| CU | Descripción | RF del catálogo | RF internos | Tareas |
|----|-------------|-----------------|-------------|--------|
| CU-O48 | Registrar el partner e iniciar su incorporación técnica | RF-O48.1–4 | RF-PON-001, 002, 003 | — |
| CU-O49 | Emitir las credenciales de acceso a la integración | RF-O49.1–4 | RF-PON-004, 005, 006, 007, 008, 009 | — |
| CU-O50 | Consultar el contrato de integración vigente y su documentación | RF-O50.1–3 | RF-PON-011 | — |

### Cobertura RF del catálogo → RF interno

| Catálogo | Cubierto por |
|---|---|
| RF-O48.1 Registrar organización y responsable técnico | RF-PON-001 |
| RF-O48.2 Impedir un segundo partner sobre el mismo cliente | RF-PON-002, RN-PON-002 |
| RF-O48.3 Determinar el cupo a partir del plan contratado | RF-PON-003, RN-PON-003 |
| RF-O48.4 Impedir la incorporación sin suscripción vigente | RF-PON-001 §2, RN-PON-011 |
| RF-O49.1 Varias credenciales por entorno, cada una con nombre | RF-PON-004, RF-PON-005 |
| RF-O49.2 Entregar el secreto una sola vez, irrecuperable | RF-PON-004 §3, RN-PON-005 |
| RF-O49.3 Rotación sin interrumpir las demás | RF-PON-005 §3 |
| RF-O49.4 Expirar pruebas sin desactivar al partner | RF-PON-006, RN-PON-006 |
| RF-O50.1 Exponer la especificación vigente | RF-PON-011 §1 |
| RF-O50.2 Mantener accesibles las versiones soportadas | RF-PON-011 §2 |
| RF-O50.3 Señalar la fecha de retiro planificada | RF-PON-011 §§3 y 6, RN-PON-012 |

**11/11 RF del catálogo cubiertos. Sin huecos.**

## RNF

| RNF | Evidencia | Tarea |
|-----|-----------|-------|
| RNF-PON-001 | **p95 = 217 ms** (mediana 207, máx 545, n=20, bcrypt rounds=12) frente al umbral de 2000 ms — `backend/apps/partners/tests/performance/test_emitir_credencial_p95.py` ✅ | T074 |
| RNF-PON-002 | Secreto solo como hash bcrypt; búsqueda del valor en claro en **logs, evento publicado y auditoría** → 0 ocurrencias — `tests/services/test_no_fuga_secreto.py` (6 tests) ✅ | T070 |
| RNF-PON-003 | Credencial siempre ligada a partner con suscripción vigente (`plan_read_repository`, 11 tests incl. suscripción cancelada); revocable en CU-O55 (#09) ✅ | T019 |
| RNF-PON-004 | 100 % de acciones en `Fact_HistorialAccesoPartner`; sin UPDATE ni DELETE (`HistorialAccesoRepository` no expone esos métodos). Auditoría de seguridad complementaria en `audit_partner_service.py`, cobertura 100 % ✅ | T071, T072 |
| RNF-PON-005 | Contrato versionado por servicio; ninguna versión `retirada` sin fecha previa — `test_version_contrato_repository.py` (9 tests) + `test_contrato_integracion_contract.py` (10) ✅ | T061, T062, T064 |
| RNF-PON-006 | Sin acoplamiento directo con los módulos #08 y #09 — propiedad de escritura repartida en `spec.md` §13 | — |
| RNF-PON-007 | Cobertura **97 %** en `apps/partners` + `core/repositories/partners` (umbral 80 %; no aplica el 95 % de la cadena crítica). Servicios nuevos `audit_partner_service` y `partner_notificacion_service` al **100 %** ✅ | T075 |

### Nota sobre el umbral de RNF-PON-001

Los 2 s parecen holgados frente a los 500 ms de otros endpoints, y lo son a
propósito: bcrypt con coste 12 tarda cientos de milisegundos **por diseño** —
es lo que encarece un ataque de fuerza bruta contra el hash almacenado. El
Tie-Breaker de la constitución resolvió este conflicto a favor de **Security**,
así que si la medición empieza a acercarse al umbral, la corrección admisible
es mirar qué se metió en la ruta de emisión, nunca bajar `BCRYPT_ROUNDS` ni
subir el umbral.

## Escenarios quickstart A–L

| Escenario | Validación | Estado |
|-----------|------------|--------|
| A | Registro exitoso → 201, `planapi=""`, `limitellamadasmes=-1`, bitácora | ⏳ |
| B | Segundo partner → 409 sin escritura | ⏳ |
| C | Sin suscripción vigente → 422 | ⏳ |
| D | Cupo derivado y congelado; `limites` incompleto → 422 | ⏳ |
| E | Emisión sin plan → 409 sin efecto | ⏳ |
| F | Varias credenciales nombradas; duplicado → 409 | ⏳ |
| G | Secreto una sola vez; ausente en GET, logs y eventos | ⏳ |
| H | Atajo a producción → 409 | ⏳ |
| I | Promoción aprobada; pruebas sigue activa | ⏳ |
| J | Promoción rechazada; vuelve a «Pruebas activo»; sin motivo → 422 | ⏳ |
| K | Expiración de pruebas sin desactivar al partner | ⏳ |
| L | Contrato por servicio; una sola versión vigente por servicio | ⏳ |

## Verificación de esquema (fuera del alcance de pytest)

Los tests del backend corren contra el doble en memoria de `conftest.py`, que **no reproduce los tipos del esquema ni los centinelas de Pinot** (`decisiones-pendientes.md` #18). Estas comprobaciones solo son válidas contra la base real:

| Verificación | Script | Resultado |
|---|---|---|
| Centinelas, columnas nuevas, `timeColumnName`, FK de versiones, guarda `planapi <> ''`, producción no vencida | `database/verifica_partners.py` | **16/16** ✅ |
| Tipos del vínculo factura-disputa y consulta de no-duplicación de excedente | `database/verifica_factura_reclamo.py` | **15/15** ✅ |
| **Los servicios reales del módulo** contra Pinot real: ciclo CU-O48→CU-O49 completo (registro → plan → emisión → solicitud → aprobación), hash bcrypt persistido, coexistencia pruebas/producción y los 5 eventos de bitácora | `database/verifica_onboarding_e2e.py` | **19/19** ✅ |

Las dos primeras validan el **esquema**; la tercera valida el **código**, que es
donde `verifica_partners.py` no llega. Los tres defectos graves de esta sesión
(centinela `'null'`, `Long.MIN_VALUE`, tipos de `idfactura`) pasaron en verde
contra el doble en memoria antes de aparecer contra la base real.

## Dependencias externas pendientes

**Ninguna pendiente.** Las dos que bloqueaban la implementación se resolvieron el 2026-08-08:

| Dependencia | Módulo | Bloqueaba | Estado |
|---|---|---|---|
| Rol `PartnerIntegracion` (idrol 15) | `autenticacion-y-rbac` | RF-PON-004 y todo el autoservicio | ✅ creado y verificado en Pinot |
| `api_calls_minuto` en `Dim_Plan.limites` (RN-SUSF-019) | `subscriptions-and-billing` | RF-PON-003 | ✅ validado en backend, editable en frontend, 5 planes sembrados |

Ambas en `database/migra_rol_partner_y_limite_minuto.py`; detalle en `decisiones-pendientes.md` #19.

## Cambios fuera de ciclo

Antes de este plan se aplicaron cinco cambios de esquema al Pinot en ejecución, todos verificados y registrados en `decisiones-pendientes.md` #15, #16 y #17: centinelas explícitos y corrección de `timeColumnName` en las dimensiones del departamento, columnas `nombre_credencial` y `fecha_expiracion`, tabla nueva `Dim_VersionContratoAPI` con FK a `Dim_Servicio`, `Fact_Factura.tipo`, y `Fact_Reclamo.idfactura` INT → STRING con migración de las 8 filas existentes sin pérdida.

### ✅ Dos deltas que reabrieron esta capa — **implementados 2026-08-09**

Esta capa se cerró con 81/81 tareas, pero al especificar `../frontend/spec.md` aparecieron **dos
huecos funcionales que solo se ven desde la UI**. Ninguno altera una regla de negocio ya verificada.

**Estado: ambos implementados y verificados.** `MiPartnerView` + ruta `partners/me`, y la guarda de
producción condicionada al estado derivado en `CredencialesView`. **13 tests de contrato nuevos**
(`test_mi_partner_contract.py` 8, `test_emision_produccion_partner.py` 7 → módulo de 208 a **221**),
y la suite completa pasó de 1250 a **1263 passed, 2 skipped: cero regresiones**. Contrato OpenAPI
actualizado con `/partners/me` y con la nueva semántica del 403 de producción.

| ID | Cambio | Hallazgo que lo motiva |
|---|---|---|
| **BE-DELTA-01** | Añadir `GET /api/v1/partners/me` — resuelve el partner del usuario autenticado vía su cliente; 404 si no tiene | **El portal del partner es inalcanzable.** El `Profile` de sesión solo lleva `{idusuario, gmail, roles[]}`, todos los endpoints exigen `{idpartner}` en la ruta, y `GET /partners` es `EsDesarrolladorAPIs`. Un partner no tiene forma de averiguar su propio id |
| **BE-DELTA-02** | Permitir al partner emitir en `Producción` **cuando su estado derivado ya es «Producción activa»** | `PromocionProduccionService.resolver()` devuelve el `client_secret` de producción **al Administrador**, y el partner nunca lo ve. Como el Admin no tiene canal seguro para entregárselo, acabaría por correo o chat — justo lo que RN-PON-005 evita. La emisión debe ejecutarla quien custodia el secreto |
| **BE-DELTA-03** | `GET /api/v1/partners/clientes-elegibles` — clientes con suscripción vigente y sin partner previo | **Detectado al ejecutar la app real (T088), no por los tests.** El alta exige elegir el cliente por nombre legible (design-system § 5), pero **no existía ningún endpoint que expusiera clientes**: el combobox quedaba vacío y el registro era literalmente inalcanzable desde la UI. El test de componente no lo cazó porque solo comprobaba que el control fuera un `<select>`. Al devolver solo los **elegibles**, además, el usuario ya no puede provocar el 422 `sin_suscripcion` ni el 409 `partner_duplicado`: prevenir el error en vez de explicarlo (Principio IV) |

**BE-DELTA-02 no debilita RN-PON-004.** La regla «producción requiere aprobación previa» se mantiene
intacta: lo único que cambia es *dónde* se comprueba la autorización — de un `403` incondicional en
la vista a una guarda condicionada al estado derivado que la propia aprobación produjo.

Resolución y alternativas descartadas: sección *Clarifications* de [`../frontend/spec.md`](../frontend/spec.md).
