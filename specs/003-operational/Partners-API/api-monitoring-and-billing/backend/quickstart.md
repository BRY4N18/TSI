# Quickstart — Validación de Monitoreo y Facturación de API

Guía de validación end-to-end de CU-O51, CU-O52, CU-O53 y CU-O54. No contiene código de implementación: eso vive en `tasks.md`.

## Prerrequisitos

- Stack Docker arriba: `zookeeper`, `kafka`, `pinot-controller`, `pinot-broker`, `pinot-server`, `accidentes-django`.
- **Módulo #07 implementado**: hacen falta partners con credenciales de producción activas. Sin ellos no hay nada que medir.
- Esquema del departamento aplicado (ya está): centinelas, `Dim_Plan.precio_excedente_llamada`, `Fact_Factura.tipo`.
- `Dim_EstadoIntegracion` **sembrada** — hoy tiene 0 filas; la siembra es tarea de este módulo.
- Un cliente con `Dim_Preferencias_Cliente.zonas_geograficas` configurado y casos cerrados en esas zonas.

Comprobación rápida de que la base soporta las reglas:

```bash
python database/verifica_factura_reclamo.py
```

Debe dar **15/15** (tipos del vínculo factura-disputa y consulta de no-duplicación de RF-O54.3).

## 1) Validar el contrato REST (contract-first)

```bash
python -c "import yaml; d=yaml.safe_load(open('specs/003-operational/Partners-API/api-monitoring-and-billing/backend/contracts/api-monitoring-and-billing.openapi.yaml',encoding='utf-8')); print(len(d['paths']),'paths,',len(d['components']['schemas']),'schemas')"
```

Esperado: `4 paths, 7 schemas`.

**Invariante de seguridad del contrato** — la API de datos debe usar `credencialAuth` y la de gestión `bearerAuth`. Si `/datos/*` apareciera con `bearerAuth`, un partner necesitaría sesión humana; si un endpoint de gestión apareciera con `credencialAuth`, una credencial de máquina accedería al portal:

```bash
python -c "import yaml; d=yaml.safe_load(open('specs/003-operational/Partners-API/api-monitoring-and-billing/backend/contracts/api-monitoring-and-billing.openapi.yaml',encoding='utf-8')); print({p: [list(s)[0] for s in o['get'].get('security',[])] for p,o in d['paths'].items()})"
```

Esperado: solo `/datos/accidentes` con `credencialAuth`; los otros tres con `bearerAuth`.

## 2) Validar el flujo backend

### Escenario A — Consumo exitoso dentro del cupo (CU-O51 + CU-O52)

```bash
pytest backend/apps/partners/tests/api/test_consumo_datos_contract.py -q
```

Credencial de producción activa → **200** con datos filtrados por severidades del plan y zonas contratadas. Debe escribir **una fila en `Fact_LogLlamadaAPI` y otra en `Fact_APIIntegracion`** con `llamadas=1`, `errores=0`, `entorno='Producción'` e `idestadointegracion` congelado.

### Escenario B — Credencial revocada

Credencial con `activo=false` → **401 sin entregar dato alguno**, y **sin fila en `Fact_APIIntegracion`** (no hubo consumo que facturar).

### Escenario C — Partner suspendido

`Dim_Partner.activo=false` → **403**. Ninguna llamada nueva genera consumo exitoso.

### Escenario D — Cliente sin zonas configuradas

Cliente sin `zonas_geograficas` → **conjunto vacío**, no el conjunto completo (fail-closed, RN-APM-008). La llamada **sí** se registra como consumo. `meta.zonas_aplicadas` debe venir vacío, para que el partner entienda el porqué.

### Escenario E — Superar la cuota mensual NO interrumpe

Partner que ya superó `limitellamadasmes` → las llamadas siguientes se **atienden con normalidad** (RN-APM-002) y se registran. Debe haberse alertado al aproximarse y al alcanzar el límite, **sin duplicar avisos** en el período.

> Este es el escenario que más fácil se implementa mal: la intuición dice «bloquear al superar la cuota». El SRS lo prohíbe explícitamente.

### Escenario F — Throttle por minuto SÍ rechaza (§ 15 D2)

Superar `limitellamadasminuto` → **429** con `Retry-After`.

**Comprobación contable, la parte que importa:**
- **Sí** escribe `Fact_LogLlamadaAPI` con `codigohttp=429` (el partner debe poder ver que le limitan).
- **No** escribe `Fact_APIIntegracion` — la petición no se atendió, así que no es consumo facturable.

Facturar peticiones no servidas sería cobrar de más.

### Escenario G — Error del partner, autodiagnóstico

Petición mal formada → 4xx registrado con su `codigohttp` y `errores=1`. El partner lo ve en sus métricas sin escalar a un Administrador (RN-APM-009).

### Escenario H — Separación de entornos

Partner con consumo en pruebas y producción → el reporte y el cálculo de excedente consideran **solo producción**. El de pruebas no aparece ni suma (RN-APM-001).

### Escenario I — Corte con excedente (CU-O54)

Cupo 10 000, consumo 12 500 → separa 10 000 incluidas de 2 500 excedentes, verifica que no exista factura previa, y emite `Fact_Factura` con `tipo='excedente_api'` y `monto_total = 2500 × Dim_Plan.precio_excedente_llamada`.

### Escenario J — Reintento que no duplica

Corte que ya emitió pero cuyo proceso falló después → el reintento **encuentra la factura existente** por `id_cliente` + `periodo` + `tipo` y **no emite una segunda** (RN-APM-012). El doble cobro es peor que no cobrar.

### Escenario K — Reintentos agotados

Emisión que falla de forma persistente → reintentos a **1 h, 6 h y 24 h**, persistiendo `reintentos` y `resultado_ultimo_reintento` en cada uno. Agotados → **pendiente de emisión manual** + alerta a Administrador y Desarrollador de APIs. **Nunca queda sin crearse en silencio** (RN-APM-014).

> Los reintentos se validan manipulando el estado persistido y adelantando el reloj, **no** esperando 24 horas: la espera vive en los datos, no en el proceso (`research.md` Decision 7).

### Escenario L — Tarifa sin configurar

Plan con `precio_excedente_llamada = -1.0` y partner con excedente → **NO se emite factura de importe cero**: se marca como no tarificable y se alerta. Facturar cero sería ingreso no cobrado en silencio.

### Escenario M — Factura en disputa excluida del cobro

Factura con disputa abierta en Soporte → excluida del cobro automático mientras el reclamo siga abierto (RN-APM-016).

### Escenario N — El fallo de medición no tumba la API

Con la publicación del evento fallando → el partner **recibe igualmente sus datos**, y el fallo queda registrado para reconciliación (RN-APM-005). Es el trade-off del Tie-Breaker.

### Validaciones transversales

| Comprobación | Esperado |
|---|---|
| Sin credencial en `/datos/*` | 401 |
| JWT humano en `/datos/*` | 401 — la API de datos no acepta sesión humana |
| Credencial de API en `/logs-api` | 401 — la gestión no acepta credencial de máquina |
| Partner consultando métricas ajenas | **403** (RN-APM-017) |
| Partner suspendido consultando **sus** métricas | **200** — la lectura sigue permitida |
| Toda agregación | lleva `entorno='Producción'` **y** `LIMIT` explícito |
| `Fact_APIIntegracion` / `Fact_LogLlamadaAPI` | solo INSERT; nunca UPDATE ni DELETE |

## 3) Pruebas sugeridas

```bash
pytest backend/apps/partners -q
```

```bash
cd backend && python -m pytest -q
```

Línea base sin regresiones: **1042 passed, 2 skipped**.

## 4) Criterios de salida

- [ ] Contrato válido, sin referencias rotas, y cada superficie con su esquema de autenticación.
- [ ] Escenarios A–N en verde.
- [ ] Los 16 criterios CA-APM-001…016 cubiertos por al menos un test.
- [ ] `Dim_EstadoIntegracion` sembrada y referenciada correctamente desde `Fact_APIIntegracion`.
- [ ] Cobertura de `apps/partners/services` ≥ 80 % (RNF-APM-008).
- [ ] Suite completa sin regresiones.
- [ ] **Verificación contra Pinot real** (paso 5): las agregaciones y los centinelas no se validan con mocks.

## 5) Verificación contra Pinot real — obligatoria

Este módulo vive de **agregaciones sobre datos reales**, y el doble en memoria de `conftest.py` no reproduce ni los centinelas ni el comportamiento de Pinot (`decisiones-pendientes.md` #18).

Debe crearse `database/verifica_monitoreo_api.py`, en la línea de `verifica_partners.py`, comprobando al menos:

| Comprobación | Por qué contra Pinot |
|---|---|
| `SUM(llamadas)` filtrado por partner + entorno + período coincide con las filas escritas | Es el número que se factura |
| Ninguna agregación mezcla `Sandbox` con `Producción` | RN-APM-001; un mock no distingue entornos |
| Un `429` deja fila en `Fact_LogLlamadaAPI` y **ninguna** en `Fact_APIIntegracion` | La regla contable de § 15 D2 |
| `precio_excedente_llamada = -1.0` dispara alerta y **no** factura cero | El centinela solo existe en Pinot |
| Un mes sin consumo devuelve ceros, no error | Agregación sobre conjunto vacío |
| Toda consulta lleva `LIMIT` explícito | Pinot aplica `LIMIT 10` implícito y silencioso |

## 6) Evidencia de rendimiento (RNF-APM-002 y RNF-APM-003)

- **Latencia:** p95 de `GET /datos/accidentes` ≤ **2 s**, con el registro de consumo activo. Medir con y sin registro para aislar su coste.
- **Coste de bcrypt:** se verifica en **cada** petición por diseño (`research.md` Decision 2). Si domina el p95, la mitigación es cachear el resultado de la verificación por `client_id` durante una ventana corta — **nunca** bajar el factor de coste de bcrypt.
- **Capacidad:** sostener **decenas de escrituras por segundo** sin degradar la respuesta. Es el flujo de mayor frecuencia del departamento.

Registrar ambas mediciones en `traceability.md`.
