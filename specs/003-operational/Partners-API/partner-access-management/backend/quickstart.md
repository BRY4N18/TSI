# Quickstart — Validación de Gestión de Acceso de Partners

Guía de validación end-to-end de CU-O55. No contiene código de implementación: eso vive en `tasks.md`.

## Prerrequisitos

- Stack Docker arriba: `zookeeper`, `kafka`, `pinot-controller`, `pinot-broker`, `pinot-server`, `accidentes-django`.
- **Módulo #07 implementado**: hacen falta partners con varias credenciales nombradas para probar la revocación selectiva y la cascada.
- **Módulo #08 implementado**: hacen falta facturas de excedente para generar mora, y su middleware es quien aplica el corte.
- Esquema del departamento aplicado. **Este módulo no añade nada**: `Fact_HistorialAccesoPartner.idcredencial` y los centinelas ya existen.

> **No hay script de migración para este módulo.** Es el único de los tres que no tocó el esquema.

## 1) Validar el contrato REST (contract-first)

```bash
python -c "import yaml; d=yaml.safe_load(open('specs/003-operational/Partners-API/partner-access-management/backend/contracts/partner-access-management.openapi.yaml',encoding='utf-8')); print(len(d['paths']),'paths,',len(d['components']['schemas']),'schemas')"
```

Esperado: `5 paths, 12 schemas`.

**Invariante de seguridad** — el secreto solo puede aparecer en `RevocacionResponse`. Si apareciera en `Credencial`, el endpoint de estado filtraría secretos:

```bash
python -c "import yaml; s=yaml.safe_load(open('specs/003-operational/Partners-API/partner-access-management/backend/contracts/partner-access-management.openapi.yaml',encoding='utf-8'))['components']['schemas']; print([n for n,v in s.items() if 'client_secret' in str(v)])"
```

Esperado exactamente: `['RevocacionResponse']`.

## 2) Validar el flujo backend

### Escenario A — Revocación con reemplazo (RF-PAC-001, RF-PAC-002)

```bash
pytest backend/apps/partners/tests/api/test_revocar_credencial_contract.py -q
```

Partner con tres credenciales activas revoca una → **200** con la revocada (`activo=false`) y el reemplazo **del mismo entorno y mismo nombre**, con su secreto una sola vez. `credenciales_intactas` debe ser **2**.

### Escenario B — La ventana de exposición está cerrada (RNF-PAC-001)

**El escenario que más importa de este módulo.** Inmediatamente tras revocar —**sin esperar** a la ingesta de Pinot— intentar consumir la API de #08 con la credencial revocada:

```bash
pytest backend/apps/partners/tests/api/test_revocacion_inmediata.py -q
```

Debe rechazarse **ya**, no dentro de 15 segundos. Si este test pasa solo cuando se le añade una espera, la lista de denegación no está funcionando y **una credencial comprometida seguiría sirviendo datos**.

Comprobar también el orden con la caché de #08: si esa caché se consulta antes que la lista de denegación, **alarga** la ventana en vez de cerrarla (`research.md` Decision 2).

### Escenario C — Revocación de credencial ajena

Credencial de otro partner → **403 sin modificar nada**.

### Escenario D — Revocación de credencial ya inactiva

→ **409**, y **ninguna segunda entrada** de revocación en la bitácora (RN-PAC-003).

### Escenario E — El reemplazo no choca de nombre consigo mismo

Revocar y emitir el reemplazo con **el mismo nombre** en la misma operación → **200**. Si la comprobación de unicidad releyera Pinot, vería la revocada aún activa y daría una colisión falsa que **haría fallar la revocación** (`research.md` Decision 4). El test debe correr sin esperas.

### Escenario F — Avisos previos sin duplicación (RF-PAC-003)

Factura de excedente impagada que alcanza T-10 → aviso enviado y registrado con `motivo="T-10"`, **sin cambiar el estado del partner**. Ejecutar el job de nuevo el mismo día → **no envía un segundo aviso**.

### Escenario G — Regularización entre avisos (RN-PAC-007)

Partner que recibió T-10 y paga antes de T-5 → **el aviso T-5 nunca se envía** y el ciclo se cierra sin suspensión. No debe hacer falta lógica de cancelación: la factura pagada desaparece de la condición de entrada del job.

### Escenario H — Suspensión automática con cascada (RF-PAC-004, RF-PAC-006)

Partner que supera el límite → `Dim_Partner.activo=false` con fecha y motivo, **todas** sus credenciales desactivadas (ambos entornos), y **una fila `desactivacion_por_cascada` por cada una**.

Verificar que el número de filas de cascada coincide con el de credenciales que estaban activas.

### Escenario I — Reactivación selectiva 🎯 *el escenario que da sentido al módulo*

Partner con credenciales **A** y **B** activas, y **C** que él mismo revocó por seguridad semanas antes. Se suspende (las tres quedan inactivas) y luego un Administrador lo reactiva.

```bash
pytest backend/apps/partners/tests/services/test_reactivacion_selectiva.py -q
```

Esperado: **A y B restituidas, C sigue inactiva**. Respuesta con `credenciales_restituidas: 2` y `credenciales_no_restituidas: 1`.

> **Si C vuelve activa, el módulo tiene un fallo de seguridad grave**: se ha resucitado una credencial comprometida. Es el test más importante de los tres módulos del departamento.

### Escenario J — El sistema no reactiva solo (RN-PAC-009)

Partner suspendido que **paga íntegramente** su deuda → debe **seguir suspendido**. Ningún job ni disparador lo reactiva.

> Este test protege contra un refactor bienintencionado del tipo «¿por qué no lo reactivamos solo si ya pagó?». La respuesta está en el SRS y en el conflicto con RN-SUSF-011 de Suscripciones.

### Escenario K — Reactivación redundante

Partner nunca suspendido → **409**, sin entrada de reactivación en la bitácora.

### Escenario L — Suspensión manual sin motivo

→ **400**. Con motivo, misma cascada que la automática y `tipo_cambio="suspension_manual"`.

### Escenario M — Factura en disputa no genera mora (RN-PAC-015)

Partner cuya única factura impagada está **en disputa abierta** → no cuenta como mora, no se envían avisos y no se le suspende.

### Escenario N — El suspendido consulta su estado (RN-PAC-016)

Partner suspendido consulta `/estado-acceso` → **200** con `activo=false`, motivo, fecha e historial. Es lo que le permite entender el corte.

Partner consultando el estado de otro → **403**.

### Escenario O — Frontera con la suspensión de suscripción (§ 15 D2)

Cliente con **suscripción suspendida** pero partner `activo=true` → el consumo de la API de #08 debe rechazarse con **403**. Las dos condiciones son independientes y **el acceso exige ambas**.

Verificar también lo contrario: al reactivarse la suscripción, el partner **no** se reactiva solo si estaba suspendido por su propia mora.

### Escenario P — La cola de trabajo del Administrador (RF-PAC-009 b)

Dos partners suspendidos y uno en mora con aviso T-10 ya enviado → `GET /partners/cola-acceso` los devuelve los tres, con `dias_mora` y `ultimo_aviso`. Un partner consultando esa cola → **403**.

Todo es derivado: no hay columna «en mora» y no debe crearse.

### Escenario Q — La suspensión también corta de inmediato (§ 15 D4)

Partner con tres credenciales activas suspendido por mora → las **tres** dejan de servir **sin esperar** a la ingesta.

> Es el escenario B aplicado a la suspensión, y la fuga que cierra es **mayor**: no es una credencial, son todas las suyas a la vez. Si este test necesita un `sleep`, la cascada no alimentó la lista de denegación.

Verificar también la simetría: al reactivar, las credenciales restituidas **vuelven a servir de inmediato**. Si siguieran rechazadas hasta que caduque el TTL, la reactivación no sería tal.

### Validaciones transversales

| Comprobación | Esperado |
|---|---|
| Sin `Authorization` | 401 en todos los endpoints |
| Rol distinto de Administrador intenta suspender o reactivar | **403** |
| Una credencial de API intenta revocar | **401** — no se acepta autenticación por credencial aquí |
| `Fact_HistorialAccesoPartner` | solo INSERT; nunca UPDATE ni DELETE |
| Reintento con el mismo `Idempotency-Key` en la primera revocación | un solo efecto |

## 3) Pruebas sugeridas

```bash
pytest backend/apps/partners -q
```

```bash
cd backend && python -m pytest -q
```

Línea base sin regresiones: **1447 passed** (la que dejó #08 el 2026-08-09; la cifra de 1042 que figuraba aquí era anterior a #07 y #08).

## 4) Criterios de salida

- [ ] Contrato válido, sin refs rotas, y el secreto solo en `RevocacionResponse`.
- [ ] Escenarios A–Q en verde, con **especial atención a B, I, J y Q**.
- [ ] Los 18 criterios CA-PAC-001…018 cubiertos por al menos un test.
- [ ] Cobertura de `apps/partners/services` ≥ 80 % (RNF-PAC-006).
- [ ] Suite completa sin regresiones.
- [ ] **Verificación contra Pinot real** (paso 5).

## 5) Verificación contra Pinot real — obligatoria

La cascada y la reactivación selectiva **tocan estado en tres tablas a la vez**, y el doble de `conftest.py` no reproduce ni los centinelas ni el retraso de ingesta (`decisiones-pendientes.md` #18).

Debe crearse `database/verifica_acceso_partners.py` comprobando al menos:

| Comprobación | Por qué contra Pinot |
|---|---|
| Tras suspender, **ninguna** credencial del partner queda `activo=true` | Un partner suspendido con credenciales activas es un estado contradictorio |
| El nº de filas `desactivacion_por_cascada` = nº de credenciales que estaban activas | Es la lista de la que depende la reactivación |
| Tras reactivar, la credencial revocada **sigue** `activo=false` | El fallo de seguridad que RN-PAC-011 previene |
| `Dim_Partner.activo` y el estado de las credenciales **no se contradicen** | RN-PAC-012: fuente de verdad única |
| El snapshot (`fecha_suspension`, `motivo_suspension`) vuelve al centinela `""` al reactivar | Pinot no almacena NULL |
| La revocación surte efecto **antes** de que Pinot ingiera | La lista de denegación es la única defensa en esa ventana |
| La **suspensión** también surte efecto antes de que Pinot ingiera | § 15 D4: ahí la fuga son **todas** las credenciales del partner |
| La mora se resuelve por `Dim_Partner.idcliente → Fact_Factura.id_cliente` y encuentra al moroso sembrado | § 15 D3: contra `idpartner` daría **cero en silencio**, y el doble en memoria no lo delataría |
| Una factura `Fallida` del mismo cliente **no** lo pone en mora aquí | § 15 D3: es competencia de Suscripciones |

## 6) Evidencia de rendimiento (RNF-PAC-001)

Medir el tiempo desde que se acepta la revocación hasta que la credencial **deja de servir** en la API de datos de #08. Umbral: **p95 ≤ 2 s**.

**Medir sin esperas artificiales.** Si la medición necesita un `sleep` para pasar, lo que se está midiendo es la ingesta de Pinot, no la revocación — y significa que la ventana de exposición sigue abierta.

Registrar la medición en `traceability.md`.
