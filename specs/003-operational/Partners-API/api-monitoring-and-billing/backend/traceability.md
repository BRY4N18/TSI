# Trazabilidad: Monitoreo y Facturación de API

**Estado:** Phase 1 completada. Las columnas *Tareas* y *Tests* se rellenan con `/speckit-tasks` y `/speckit-implement`.

## Criterios de aceptación

| CA | Descripción | RF / RN | Tareas | Tests | Estado |
|----|-------------|---------|--------|-------|--------|
| CA-APM-001 | Credencial inexistente/revocada/vencida → 401 sin datos; partner suspendido → 403. Vigencia por comparación de datos, no por marca de job | RF-APM-001 / RN-APM-007 | — | — | ⏳ |
| CA-APM-002 | Solo severidades habilitadas del plan; conjunto no habilitado → 403, no lista vacía | RF-APM-002 | — | — | ⏳ |
| CA-APM-003 | Filtrado por `zonas_geograficas`; cliente sin zonas → conjunto vacío (fail-closed) | RF-APM-003 / RN-APM-008 | — | — | ⏳ |
| CA-APM-004 | Cada llamada atendida escribe una fila en `Fact_LogLlamadaAPI` y otra en `Fact_APIIntegracion`, con `errores` derivado del `codigohttp` | RF-APM-004 | — | — | ⏳ |
| CA-APM-005 | `idestadointegracion` refleja el estado del momento y no cambia después; `Dim_EstadoIntegracion` sembrada | RF-APM-005 / RN-APM-006 | — | — | ⏳ |
| CA-APM-006 | Ninguna agregación incluye `Sandbox`; partner con ambos entornos ve solo producción | RF-APM-006 / RN-APM-001 | — | — | ⏳ |
| CA-APM-007 | El partner consulta sus métricas; las de otro → 403; suspendido sí puede leer su historial | RF-APM-007 / RN-APM-017 | — | — | ⏳ |
| CA-APM-008 | Consola con filtros y paginación por cursor; errores 4xx/5xx visibles con su código | RF-APM-008 / RN-APM-009 | — | — | ⏳ |
| CA-APM-009 | Mes sin consumo devuelve ceros, sin error | RF-APM-009 | — | — | ⏳ |
| CA-APM-010 | Alerta al aproximarse y al alcanzar, sin duplicar. **Superar el cupo no interrumpe el servicio** | RF-APM-010 / RN-APM-002, RN-APM-010 | — | — | ⏳ |
| CA-APM-011 | El corte separa incluido de excedente y emite solo por el excedente con `tipo='excedente_api'` | RF-APM-011 / RN-APM-011 | — | — | ⏳ |
| CA-APM-012 | Reintento sobre período ya facturado **no emite una segunda** factura | RF-APM-012 / RN-APM-012 | — | — | ⏳ |
| CA-APM-013 | Reintentos a 1 h / 6 h / 24 h con estado persistido; agotados → pendiente de emisión manual + alerta | RF-APM-013 / RN-APM-013, RN-APM-014 | — | — | ⏳ |
| CA-APM-014 | Factura en disputa excluida del cobro automático | RF-APM-014 / RN-APM-016 | — | — | ⏳ |
| CA-APM-015 | Si falla la escritura del consumo, la petición se responde igual y el fallo queda registrado | RN-APM-005 | — | — | ⏳ |
| CA-APM-016 | `GET /datos/*` p95 ≤ 2 s con el registro activo | RNF-APM-002 | — | — | ⏳ |

## Requisitos funcionales

| RF | Descripción | Tareas |
|----|-------------|--------|
| RF-APM-001 | Consumo autenticado por credencial | — |
| RF-APM-002 | Alcance de datos según nivel de acceso | — |
| RF-APM-003 | Filtrado por zonas contratadas | — |
| RF-APM-004 | Registro de cada llamada en el instante | — |
| RF-APM-005 | Copia histórica del estado de integración | — |
| RF-APM-006 | Separación estricta de entornos | — |
| RF-APM-007 | Métricas de consumo del partner | — |
| RF-APM-008 | Consola en tiempo real y autodiagnóstico | — |
| RF-APM-009 | Reporte mensual de consumo | — |
| RF-APM-010 | Comparación contra el cupo y alertas | — |
| RF-APM-011 | Cálculo del excedente al cierre | — |
| RF-APM-012 | No duplicación de la factura de excedente | — |
| RF-APM-013 | Reintentos escalonados y emisión manual | — |
| RF-APM-014 | Exclusión de facturas en disputa | — |

## Casos de uso (numeración canónica del catálogo §5.5)

| CU | Descripción | RF del catálogo | RF internos | Tareas |
|----|-------------|-----------------|-------------|--------|
| CU-O51 | Consumir los datos mediante la integración | RF-O51.1–3 | RF-APM-001, 002, 003 | — |
| CU-O52 | Registrar el consumo realizado por cada partner | RF-O52.1–3 | RF-APM-004, 005, 006, 007, 008, 009 | — |
| CU-O53 | Aplicar los límites de consumo del plan | RF-O53.1–3 | RF-APM-010 | — |
| CU-O54 | Tarificar el consumo del período | RF-O54.1–4 | RF-APM-011, 012, 013, 014 | — |

### Cobertura RF del catálogo → RF interno

| Catálogo | Cubierto por | Estado |
|---|---|---|
| RF-O51.1 Entregar solo los conjuntos del nivel de acceso | RF-APM-002 | ✅ |
| RF-O51.2 Rechazar credencial inválida, revocada o vencida | RF-APM-001, RN-APM-007 | ✅ |
| RF-O51.3 Filtrar por zonas contratadas | RF-APM-003, RN-APM-008 | ✅ |
| RF-O52.1 Contabilizar cada petición | RF-APM-004 | ✅ |
| RF-O52.2 Acumular por partner y período | RF-APM-009, RF-APM-010 | ✅ |
| RF-O52.3 Conservar el detalle como respaldo | RF-APM-004, RNF-APM-005 | ✅ |
| RF-O53.1 Comparar contra el límite | RF-APM-010 | ✅ |
| RF-O53.2 Restringir o degradar al superarse | RN-APM-002, § 15 D2 | ⚠️ **divergencia deliberada a favor del SRS** |
| RF-O53.3 Notificar al aproximarse y al alcanzar | RF-APM-010, RN-APM-010 | ✅ |
| RF-O54.1 Calcular el importe según la tarifa del plan | RF-APM-011, § 15 D1 | ✅ |
| RF-O54.2 Separar consumo incluido de excedente | RF-APM-011, RN-APM-011 | ✅ |
| RF-O54.3 Verificar que no exista factura previa | RF-APM-012, RN-APM-012 | ✅ |
| RF-O54.4 Reintentar y dejar pendiente con alerta | RF-APM-013, RN-APM-013 | ✅ |

**12/13 RF cubiertos sin reservas.** RF-O53.2 se resuelve a favor del SRS (RN-11): el cupo comercial no bloquea; la tasa por minuto sí devuelve 429, pero como protección de plataforma. **El catálogo debería corregirse.**

## RNF

| RNF | Evidencia | Tarea |
|-----|-----------|-------|
| RNF-APM-001 | Dos ejecuciones del corte sobre el mismo período dan el mismo importe | — |
| RNF-APM-002 | p95 `GET /datos/*` ≤ 2 s — medición con y sin registro (`quickstart.md` §6) | — |
| RNF-APM-003 | Decenas de escrituras/segundo sostenidas | — |
| RNF-APM-004 | Zonas fail-closed + nivel de acceso + auditoría por credencial en `Fact_LogLlamadaAPI` | — |
| RNF-APM-005 | `Fact_APIIntegracion` y `Fact_LogLlamadaAPI` append-only; sin UPDATE ni DELETE | — |
| RNF-APM-006 | Cada intento de emisión y su resultado registrados con autor `Sistema` | — |
| RNF-APM-007 | Umbral de alerta, tarifa y tiempos de reintento configurables | — |
| RNF-APM-008 | Cobertura ≥ 80 % en `apps/partners/services` | — |

## Escenarios quickstart A–N

| Escenario | Validación | Estado |
|-----------|------------|--------|
| A | Consumo exitoso → 200 + dos filas escritas | ⏳ |
| B | Credencial revocada → 401 sin consumo | ⏳ |
| C | Partner suspendido → 403 | ⏳ |
| D | Cliente sin zonas → conjunto vacío, pero sí cuenta como consumo | ⏳ |
| E | Superar cupo mensual **no** interrumpe; alertas sin duplicar | ⏳ |
| F | Throttle → 429; **log sí, consumo facturable no** | ⏳ |
| G | Error 4xx del partner registrado para autodiagnóstico | ⏳ |
| H | Separación de entornos en reporte y excedente | ⏳ |
| I | Corte con excedente → factura `tipo='excedente_api'` | ⏳ |
| J | Reintento **no duplica** la factura | ⏳ |
| K | Reintentos 1 h/6 h/24 h agotados → pendiente manual + alerta | ⏳ |
| L | Tarifa `-1.0` → alerta, **no** factura de importe cero | ⏳ |
| M | Factura en disputa excluida del cobro | ⏳ |
| N | Fallo de medición no tumba la API | ⏳ |

## Verificación contra Pinot (fuera del alcance de pytest)

Los tests corren contra el doble en memoria de `conftest.py`, que **no reproduce los centinelas ni el comportamiento de agregación de Pinot** (`decisiones-pendientes.md` #18). Este módulo **vive de agregaciones**, así que la verificación real es criterio de salida.

| Verificación | Script | Estado |
|---|---|---|
| Tipos del vínculo factura-disputa y consulta de no-duplicación | `database/verifica_factura_reclamo.py` | **15/15** ✅ |
| Agregaciones, separación de entornos, regla contable del 429, centinela de tarifa, mes vacío, `LIMIT` explícito | `database/verifica_monitoreo_api.py` | ⏳ **a crear** (`quickstart.md` §5) |

## Dependencias externas

| Dependencia | Módulo | Estado |
|---|---|---|
| `Dim_Plan.precio_excedente_llamada` | `subscriptions-and-billing` | ✅ aplicado y verificado (#20) |
| `Fact_Factura.tipo` | `subscriptions-and-billing` | ✅ aplicado y verificado (#17) |
| `Fact_Reclamo.idfactura` STRING | `gestion-tickets-soporte` | ✅ aplicado y verificado (#17) |
| Rol `PartnerIntegracion` | `autenticacion-y-rbac` | ✅ creado (#19) |
| `Dim_Preferencias_Cliente.zonas_geograficas` | `incorporacion-clientes` | ✅ ya existe y en uso por Seguimiento |
| Partners con credenciales de producción | `partner-api-onboarding` (#07) | ⏳ especificado, **pendiente de implementar** |
| Siembra de `Dim_EstadoIntegracion` | **este módulo** | ⏳ tarea propia (0 filas hoy) |
| Throttle rate por partner en `DEFAULT_THROTTLE_RATES` | **este módulo** | ⏳ tarea propia |

**Ninguna dependencia externa abierta.** Lo pendiente es la implementación de #07 y dos tareas internas.

## Deuda técnica declarada

El throttle por minuto **solo es exacto con un proceso** (`LocMemCache` es por proceso). Escalar horizontalmente exigirá un contador compartido. No bloquea hoy. Ver `plan.md` § Deuda técnica y `decisiones-pendientes.md` #20.

## Cambios fuera de ciclo

Antes de este plan se aplicaron y verificaron los cambios de esquema que este módulo necesita: `Fact_Factura.tipo`, `Fact_Reclamo.idfactura` INT → STRING (con migración de 8 tickets sin pérdida) y `Dim_Plan.precio_excedente_llamada` con su centinela `-1.0`. Registrados en `decisiones-pendientes.md` #17 y #20.
