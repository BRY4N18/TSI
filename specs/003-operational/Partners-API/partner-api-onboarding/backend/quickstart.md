# Quickstart — Validación de Onboarding de Partners API

Guía de validación end-to-end de CU-O48, CU-O49 y CU-O50. No contiene código de implementación: eso vive en `tasks.md` y en la fase de implementación.

## Prerrequisitos

- Stack Docker arriba: `zookeeper`, `kafka`, `pinot-controller`, `pinot-broker`, `pinot-server`, `accidentes-django`.
- Esquema del departamento aplicado. **Ya está**, pero es idempotente y se puede reconfirmar:

```bash
python database/migra_partners_esquema.py --dry-run
```

  Debe decir `Sin cambios: el esquema ya esta al dia.`

- Rol **«Partner de integración»** dado de alta en `autenticacion-y-rbac` (⏳ pendiente, ver `checklists/requirements.md`).
- `Dim_Plan.limites` con `api_calls_minuto` (⏳ pendiente en `subscriptions-and-billing`, RN-SUSF-019).
- Un cliente con suscripción vigente y un servicio en `Dim_Servicio` (los siembra `backend/scripts/seed_catalogos_soporte.py`).

## 0) Verificar que la base soporta las reglas del módulo

Antes de probar la API, confirmar que Pinot está configurado como espera la spec. Esto no es opcional: tres reglas de negocio dependen de centinelas concretos y **ninguna prueba con mocks los detecta**.

```bash
python database/verifica_partners.py
```

Debe dar **16/16**. Cubre, entre otras cosas, que la guarda `planapi <> ''` excluye a un partner sin plan (RF-PON-004) y que una credencial de producción no figura como vencida (RF-PON-008).

> Deja filas de prueba. Límpialas con `python database/limpia_datos_prueba.py`.

## 1) Validar el contrato REST (contract-first)

El contrato se escribe y se valida **antes** que la implementación.

```bash
python -c "import yaml; d=yaml.safe_load(open('specs/003-operational/Partners-API/partner-api-onboarding/backend/contracts/partner-api-onboarding.openapi.yaml',encoding='utf-8')); print(len(d['paths']),'paths,',len(d['components']['schemas']),'schemas')"
```

Esperado: `7 paths, 17 schemas`.

**Invariante de seguridad del contrato** — `client_secret` solo puede aparecer en `CredencialCreadaResponse` y `ResolucionProduccionResponse`. Si aparece en `Credencial`, el contrato filtra el secreto en los GET:

```bash
python -c "import yaml; s=yaml.safe_load(open('specs/003-operational/Partners-API/partner-api-onboarding/backend/contracts/partner-api-onboarding.openapi.yaml',encoding='utf-8'))['components']['schemas']; print([n for n,v in s.items() if 'client_secret' in str(v)])"
```

Esperado exactamente: `['CredencialCreadaResponse', 'ResolucionProduccionResponse']`.

## 2) Validar el flujo backend (Vista → Servicio → Repositorio + Kafka)

### Escenario A — Registro exitoso (CU-O48 / RF-PON-001)

```bash
pytest backend/apps/partners/tests/api/test_registrar_partner_contract.py -q
```

Un cliente existente con suscripción vigente → **201**, partner en «Registrado», `planapi=""`, `limitellamadasmes=-1`, y una fila `tipo_cambio="registro"` en la bitácora.

### Escenario B — Segundo partner sobre el mismo cliente (RN-PON-002)

**409** con el `idpartner` existente en el cuerpo, y **ninguna escritura**. La respuesta debe sugerir emitir una credencial nombrada dentro del perfil existente.

### Escenario C — Cliente sin suscripción vigente (RN-PON-011)

**422**. El cupo se deriva de la suscripción, así que sin ella no hay incorporación posible.

### Escenario D — Cupo derivado y congelado (RF-PON-003)

Asignar plan → `limitellamadasmes` y `limitellamadasminuto` toman los valores de `Dim_Plan.limites`. **Después, modificar `Dim_Plan` no debe alterar al partner ya incorporado.** Un `limites` sin `api_calls_minuto` → **422**, nunca un valor asumido.

### Escenario E — Emitir credencial sin plan (RF-PON-004)

Partner en «Registrado» intenta emitir → **409 sin efecto alguno**; sigue en «Registrado».

> Este es el escenario que el esquema roto dejaba pasar: con `planapi` valiendo el string `'null'`, la guarda «no nulo» era siempre cierta. Verificar contra Pinot real, no solo con el doble.

### Escenario F — Varias credenciales nombradas (RF-PON-005)

Emitir `plataforma-siniestros` y `deteccion-fraude` en el mismo entorno → dos filas activas. Repetir un nombre ya activo → **409**. Revocar una y reutilizar su nombre → **201**.

### Escenario G — El secreto se entrega una sola vez (RN-PON-005)

1. `POST /partners/{id}/credenciales` → **201** con `client_secret`.
2. `GET /partners/{id}/credenciales` → la credencial aparece **sin** `client_secret`.
3. `GET /partners/{id}` → tampoco lo incluye.
4. En Pinot, `client_secret_hash` es un hash bcrypt; el valor en claro no aparece **en ninguna parte**:

```bash
docker logs accidentes-django 2>&1 | grep -c "<el-secreto-devuelto>"
```

Esperado: `0`. Repetir la búsqueda sobre el topic Kafka — al evento solo debe viajar el hash.

### Escenario H — Ruta obligatoria sin atajos (RN-PON-004)

Partner en «Plan asignado» que nunca emitió credencial de pruebas solicita producción → **409**.

### Escenario I — Promoción aprobada (RF-PON-008)

Solicitud → **202**, estado «Pendiente de aprobación», **sin credencial emitida**. Administrador aprueba → **200**, credencial de producción con su `client_secret` (única vez) y **la credencial de pruebas sigue activa** (RN-PON-008).

Un rol distinto de Administrador que intente resolver → **403**.

### Escenario J — Promoción rechazada (RN-PON-007)

Rechazo con `motivo` → **200**, el partner vuelve a **«Pruebas activo»** (no a «Registrado») con su acceso de pruebas operativo, y queda `tipo_cambio="rechazo_promocion_produccion"` con el motivo. Puede reintentar **sin tope**.

Rechazo sin `motivo` no vacío → **422**.

### Escenario K — Expiración de pruebas (RF-PON-006)

Credencial de pruebas vencida → solo esa credencial pasa a `activo=false`; `Dim_Partner.activo` sigue en `true` y `planapi` se conserva. El partner emite una nueva por autoservicio **sin repetir registro ni asignación de plan**. El aviso previo no se duplica dentro del mismo ciclo.

### Escenario L — Contrato de integración por servicio (CU-O50)

`GET /contrato-integracion?id_servicio=1` → versión vigente del servicio 1 más su listado de versiones con estado y fecha de retiro.

**Comprobación de la normalización:** dos servicios distintos deben poder estar en versiones vigentes distintas sin interferir. Y ningún servicio puede tener dos versiones `vigente` a la vez.

### Validaciones transversales

| Comprobación | Esperado |
|---|---|
| Sin `Authorization` | 401 en todos los endpoints |
| Partner opera sobre un `idpartner` ajeno | **403** — control de propiedad obligatorio |
| Cualquier acción sobre partner con `activo=false` | 409 (RN-PON-013) |
| `Fact_HistorialAccesoPartner` | solo INSERT; nunca UPDATE ni DELETE |
| Reintento con el mismo `Idempotency-Key` | un solo efecto de negocio |

## 3) Pruebas sugeridas

```bash
# Suite del módulo
pytest backend/apps/partners -q

# Suite completa (no debe haber regresiones: 1042 pasan hoy)
cd backend && python -m pytest -q
```

## 4) Criterios de salida

- [ ] `verifica_partners.py` → 16/16.
- [ ] Contrato OpenAPI válido, sin referencias rotas, y `client_secret` solo en los dos schemas de creación.
- [ ] Escenarios A–L en verde.
- [ ] Los 14 criterios CA-PON-001…014 cubiertos por al menos un test (ver `traceability.md`).
- [ ] Cobertura de `apps/partners/services` ≥ 80 % (RNF-PON-007).
- [ ] Suite completa del backend sin regresiones.
- [ ] El secreto en claro no aparece en logs, trazas, respuestas de consulta ni eventos Kafka.

## 5) Evidencia de rendimiento (RNF-PON-001)

Medir p95 de `POST /partners/{id}/credenciales`. Umbral: **≤ 2 s**, muy por debajo del compromiso de 24 h del SRS. Registrar la medición en `traceability.md`.

## 6) Advertencia sobre el alcance de los tests

Los tests del backend corren contra el **doble en memoria** de `backend/conftest.py`, que **no reproduce los tipos del esquema ni los centinelas de Pinot**. Tres defectos reales de este departamento pasaron inadvertidos en verde hasta que se probaron contra Pinot real (`decisiones-pendientes.md` #18).

**Por eso el paso 0 no es opcional y no puede sustituirse por `pytest`.** Cualquier regla que dependa de un valor ausente —`planapi <> ''`, `fecha_expiracion < ahora`, `idcredencial <> -1`— debe verificarse contra la base real antes de dar el módulo por terminado.
