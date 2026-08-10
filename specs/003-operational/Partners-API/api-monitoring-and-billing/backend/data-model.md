# Data Model — Monitoreo y Facturación de API

> **Pinot no almacena `NULL`.** Toda regla se expresa contra centinelas explícitos, nunca con `IS NULL` (RN-APM-018). Ver `partner-api-onboarding/backend/spec.md` § 15 D2.

> **Pinot aplica `LIMIT 10` implícito** a toda consulta sin `LIMIT`. Todas las agregaciones de este módulo deben declararlo.

## Entidades que este módulo escribe

### 1) `Fact_APIIntegracion` (consumo orientado a reporte y facturación)

Una fila **por cada llamada atendida**. Es la base de todas las métricas y del cálculo de excedente.

- **PK:** `idapiintegracion` (INT)
- **FKs:** `idpartner` → `Dim_Partner`, `idcliente` → `Dim_Cliente`, `idservicio` → `Dim_Servicio`, `idestadointegracion` → `Dim_EstadoIntegracion`
- **Calificador:** `entorno` (STRING: `Sandbox` | `Producción`) — **obligatorio en todo filtro** (RN-APM-001)
- **Medidas:** `llamadas` (INT, siempre `1`), `errores` (INT, `0` o `1` según `codigohttp`), `latencia` (DOUBLE, ms)
- **Control:** `activo` (BOOLEAN)
- **Timestamps:** `fechahora` (LONG, momento de la llamada), `fecha_actualizacion` (LONG)

**Reglas:**
- **Append-only.** Ninguna fila se modifica ni se borra (RNF-APM-005). El detalle es el respaldo de la tarificación (RF-O52.3).
- `llamadas` vale siempre 1: el agregado se calcula al consultar, no se acumula al escribir (RN-APM-003).
- `errores = 1` si `codigohttp >= 400`, `0` en otro caso.
- **Una petición rechazada con `429` NO genera fila aquí** — no se atendió, no es consumo facturable (§ 15 D2). Sí se registra en `Fact_LogLlamadaAPI`.
- `idestadointegracion` es **copia histórica** del estado del partner en ese instante, no la fuente de verdad actual (RN-APM-006).

### 2) `Fact_LogLlamadaAPI` (detalle técnico)

Una fila por cada petición, **incluidas las rechazadas**. Alimenta la consola del Desarrollador de APIs y el autodiagnóstico del partner.

- **PK:** `idlogllamadaapi` (INT)
- **FKs:** `idpartner` → `Dim_Partner`, `idcredencialapi` → `Dim_CredencialAPI`
- **Detalle:** `endpoint` (STRING), `metodohttp` (STRING), `codigohttp` (INT), `iporigen` (INT), `latenciams` (DOUBLE)
- **Timestamps:** `fechallamada` (LONG), `fecha_actualizacion` (LONG)

**Reglas:**
- **Append-only.**
- Se escribe **junto** con `Fact_APIIntegracion`, en el mismo instante (RN-APM-003), salvo en el caso del `429`, en que solo se escribe esta.
- Los códigos 4xx/5xx se registran igual: son el material de autodiagnóstico del partner (RN-APM-009).
- `iporigen` es INT (IPv4 numérica), conforme al esquema existente.

### 3) `Dim_EstadoIntegracion` (catálogo — **vacío, se siembra aquí**)

- **PK:** `idestadointegracion` (INT)
- **Campos:** `nombre` (STRING), `descripcion` (STRING), `activo` (BOOLEAN), `fecha_actualizacion` (LONG)

**Siembra requerida** (RF-APM-005), alineada con los estados derivados de `partner-api-onboarding` § 9:

| id | nombre | Cuándo se congela en el consumo |
|---|---|---|
| 1 | `Pruebas activo` | Llamada con credencial de `Sandbox` |
| 2 | `Producción activa` | Llamada con credencial de `Producción` |
| 3 | `Suspendido` | El partner fue suspendido; solo aparece en histórico |

La tabla existe en Pinot con **0 filas**: sin este seed, `idestadointegracion` apunta a nada.

## Entidad que este módulo escribe en otro departamento

### 4) `Fact_Factura` (dueño = `subscriptions-and-billing`)

Este módulo **calcula y decide**; Suscripciones **persiste** vía `FacturaRepository.create()`.

Campos que este módulo fija al emitir un excedente:

| Campo | Valor |
|---|---|
| `tipo` | **`'excedente_api'`** — discriminador que hace posible RF-O54.3 |
| `id_cliente` | El `idcliente` del partner |
| `periodo` | `YYYY-MM` del período cerrado |
| `monto_total` | `llamadas_excedentes × Dim_Plan.precio_excedente_llamada` |
| `estado_pago` | `'Pendiente'` |
| `reintentos`, `resultado_ultimo_reintento` | Actualizados en cada intento fallido (RF-APM-013) |

**Reglas:**
- **No duplicación (RN-APM-012):** antes de emitir, `SELECT` por `id_cliente` + `periodo` + `tipo='excedente_api'`. Si existe, no se emite.
- Una factura **en disputa** queda excluida del cobro automático (RN-APM-016). La disputa la gestiona Soporte.
- `id_factura` es un **UUID** (STRING) generado por Suscripciones.

## Dimensiones de lectura (no escritas por este módulo)

| Dimensión | Uso | Campo clave |
|---|---|---|
| `Dim_CredencialAPI` | Autenticar cada llamada | `client_secret_hash`, `activo`, `fecha_expiracion` (centinela `253402300799000` = no expira), `entorno` |
| `Dim_Partner` | Estado y cupo | `activo`, `limitellamadasmes`, `limitellamadasminuto` (centinela `-1` = sin cupo) |
| `Dim_Plan` | Tarifa del excedente | **`precio_excedente_llamada`** (centinela `-1.0` = sin tarifa), `severidades_desbloqueadas` |
| `Dim_Preferencias_Cliente` | Zonas contratadas | `zonas_geograficas` (JSON de `idcondado`) |
| `Dim_Servicio` | Servicio consumido | `id_servicio` |
| `Fact_Accidente` + jerarquía geográfica | **Los datos que se entregan** | Solo lectura; este módulo **nunca escribe** aquí |

## Centinelas relevantes para las reglas de este módulo

| Centinela | Dónde | Significa | Regla que lo usa |
|---|---|---|---|
| `-1.0` | `Dim_Plan.precio_excedente_llamada` | Sin tarifa configurada | RF-APM-011: **alerta, no factura cero** |
| `-1` | `Dim_Partner.limitellamadasmes` / `minuto` | Sin cupo asignado | RF-APM-010: no evaluar cuota |
| `253402300799000` | `Dim_CredencialAPI.fecha_expiracion` | No expira nunca | RF-APM-001: `fecha_expiracion < ahora` es falso |
| `""` | `Dim_Partner.planapi` | Sin plan | El partner no debería tener credenciales activas |

**Ninguna consulta usa `IS NULL`.**

## Flujo de una petición de datos (CU-O51 + CU-O52)

```
Petición del partner con credencial
   │
   ├─ 1. Autenticar: hash bcrypt contra Dim_CredencialAPI
   │       credencial inexistente / activo=false / vencida ──► 401  (sin fila en Fact_APIIntegracion)
   │
   ├─ 2. Partner: Dim_Partner.activo=false ──► 403  (sin fila en Fact_APIIntegracion)
   │
   ├─ 3. Throttle por minuto (Dim_Partner.limitellamadasminuto)
   │       superado ──► 429 + Retry-After
   │                     └─► SÍ escribe Fact_LogLlamadaAPI (para que el partner lo vea)
   │                         NO escribe Fact_APIIntegracion (no se atendió, no es consumo)
   │
   ├─ 4. Nivel de acceso: severidades del plan  ──► 403 si el conjunto no está habilitado
   │
   ├─ 5. Zonas contratadas: Dim_Preferencias_Cliente.zonas_geograficas
   │       sin zonas ──► conjunto vacío (fail-closed), pero SÍ cuenta como consumo
   │
   ├─ 6. Resolver y responder al partner
   │
   └─ 7. Registrar (fuera del camino crítico, en try/except):
             Fact_LogLlamadaAPI      ← detalle técnico
             Fact_APIIntegracion     ← llamadas=1, errores según codigohttp, entorno,
                                       idestadointegracion congelado
          si falla ──► se registra el fallo; la respuesta al partner NO se altera
```

## Flujo del corte mensual (CU-O54)

```
Cierre de período (job horario que detecta el corte y los reintentos vencidos)
   │
   └─ por cada partner con credencial de Producción:
         SUM(llamadas) WHERE idpartner=? AND entorno='Producción' AND periodo=?
            │
            ├── ≤ limitellamadasmes ──► sin factura (consumo ya pagado por la suscripción)
            │
            └── > limitellamadasmes
                   │
                   ├─ precio_excedente_llamada == -1.0 ──► NO factura cero:
                   │                                       marca no tarificable + ALERTA
                   │
                   └─ ¿existe ya factura excedente de ese cliente+periodo?
                         ├── sí ──► NO emitir (RN-APM-012, evita doble cobro)
                         └── no ──► FacturaRepository.create(tipo='excedente_api')
                                       │
                                       └─ si falla ──► persistir reintentos+1
                                                        reintento a 1h → 6h → 24h
                                                        agotados ──► pendiente de emisión
                                                                     manual + alerta a
                                                                     Admin y Dev de APIs
```

## Eventos Kafka (escritura)

| Topic | Disparador | Frecuencia |
|---|---|---|
| `Fact_APIIntegracion_topic` | Cada llamada atendida | **Alta** — decenas/segundo |
| `Fact_LogLlamadaAPI_topic` | Cada petición, incluidas 401/403/429/5xx | **Alta** |
| `Dim_EstadoIntegracion_topic` | Solo en el seed inicial | Una vez |
| `Fact_Factura_topic` | Corte mensual, vía `FacturaRepository` de Suscripciones | Mensual |

> **Retraso de ingesta 5–15 s.** Ninguna regla puede depender de leer lo que se acaba de escribir (RN-APM-004). Afecta sobre todo a las métricas: el consumo del último cuarto de minuto aún no es consultable, y así debe comunicarlo la UI.

Lecturas: queries Pinot vía repositorios en `core/repositories/partners/`.

## Auditoría

`Fact_LogLlamadaAPI` **es** la auditoría de acceso a datos sensibles: cada entrega queda asociada a la credencial que la originó (RNF-APM-004, Principio V). Los intentos de emisión del corte y su resultado se registran con autor `Sistema` (RNF-APM-006).

## Mapeo API ↔ persistencia

| Endpoint | Tablas |
|---|---|
| `GET /datos/*` (API del partner) | **escribe** `Fact_APIIntegracion` + `Fact_LogLlamadaAPI`; **lee** `Fact_Accidente` y jerarquía |
| `GET /partners/{id}/metricas` | lee `Fact_APIIntegracion` (agregado) |
| `GET /logs-api` | lee `Fact_LogLlamadaAPI` |
| `GET /reportes-consumo` | lee `Fact_APIIntegracion` (agregado) |
| *(job)* corte de excedente | lee `Fact_APIIntegracion`, `Dim_Partner`, `Dim_Plan`; escribe `Fact_Factura` |
| *(job)* alertas de cuota | lee `Fact_APIIntegracion`, `Dim_Partner`; sin escritura de dominio |

## Fuera de este modelo

`Dim_Partner`, `Dim_CredencialAPI` y `Fact_HistorialAccesoPartner` los escriben `partner-api-onboarding` (#07) y `partner-access-management` (#09). `Fact_Reclamo` (disputas) pertenece a `gestion-tickets-soporte`. `Fact_Accidente` y su jerarquía pertenecen a Emergencias — **este módulo solo lee**.
