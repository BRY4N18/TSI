# Trazabilidad: Monitoreo y Facturación de API — Frontend

**Estado:** ✅ **COMPLETO 2026-08-10 (74/74)**, incluida la **verificación manual contra la app real**. Suite frontend **588 passed** (base #07: 459); backend **1596 passed** (base 1569).

## Requisitos funcionales (UI)

| FR | Descripción | Tareas | Tests | Estado |
|----|-------------|--------|-------|--------|
| FR-UI-101 | Métricas del partner autenticado vía `/partners/me` | T016 | `mi-consumo.page.spec.ts` | ✅ |
| FR-UI-102 | Porcentaje de cupo; «no aplica» sin cupo, **nunca 0 %** | T005, T017 | `monitoreo.types.spec.ts`, `mi-consumo.page.spec.ts` | ✅ |
| FR-UI-103 | 🎯 El exceso como **coste previsto**, sin severidad | T017, T018 | `mi-consumo-sin-alarma.spec.ts` | ✅ |
| FR-UI-104 | Entorno en texto, no solo color | T016 | `mi-consumo.page.spec.ts` | ✅ |
| FR-UI-105 | Marca del último dato disponible | T016 | `mi-consumo.page.spec.ts` | ✅ |
| FR-UI-106 | Consultable estando suspendido | T016 | `mi-consumo.page.spec.ts` | ✅ |
| FR-UI-107 | «No aplica» sin tarifa, **nunca 0,00** | T005, T018 | `mi-consumo.page.spec.ts` | ✅ |
| FR-UI-111 | Registros ordenados, con todos sus campos | T033, T035 | `consola-logs.page.spec.ts` | ✅ |
| FR-UI-112 | Filtros, **todos al servidor** | T034, T075 | `consola-logs.page.spec.ts`, `test_consola_logs_paginacion.py` | ✅ |
| FR-UI-117 | Paginación por cursor que conserva los filtros | T075 | `consola-logs.page.spec.ts` | ✅ |
| FR-UI-113 | Marca temporal y límite de «tiempo real» | T037 | `consola-logs.page.spec.ts` | ✅ |
| FR-UI-114 | Refresco manual; auto-refresco apagado por defecto | T037 | `consola-logs.page.spec.ts` | ✅ |
| FR-UI-115 | Variante Ver-only: solo `eye` | T035, T038 | `consola-logs.page.spec.ts`, `detalle-log.page.spec.ts` | ✅ |
| FR-UI-116 | 429 ≠ 403 ≠ 5xx; los 4xx no son alarma | T009, T036 | `monitoreo.types.spec.ts`, `mi-consumo-errores.spec.ts` | ✅ |
| FR-UI-121 | Período elegible con sus tres cifras | T046 | `reporte-consumo.page.spec.ts` | ✅ |
| FR-UI-122 | Comparación entre períodos | T047 | `reporte-consumo.page.spec.ts` | ✅ |
| FR-UI-123 | Mes sin consumo = ceros, no error | T048 | `reporte-consumo.page.spec.ts` | ✅ |
| FR-UI-124 | Declara que es solo producción | T046 | `reporte-consumo.page.spec.ts` | ✅ |
| FR-UI-131 | Facturas con reintentos agotados | T060 | `excepciones-facturacion.page.spec.ts` | ✅ |
| FR-UI-132 | Partners no tarificables, **distinguidos** | T051, T060 | `excepciones-facturacion.page.spec.ts` | ✅ |
| FR-UI-133 | Acción sugerida por tipo | T060 | `excepciones-facturacion.page.spec.ts` | ✅ |
| FR-UI-134 | Vacío en positivo | T060 | `excepciones-facturacion.page.spec.ts` | ✅ |
| FR-UI-135 | **Sin** botón de emitir | T060 | `excepciones-facturacion.page.spec.ts` | ✅ |
| FR-UI-141 | Los tres estados con componentes compartidos | T019, T067 | todas las páginas | ✅ |
| FR-UI-142 | Registro en `nav-links.ts` | T064 | `monitoreo-cableado.spec.ts` | ✅ |
| FR-UI-143 | Guard por ruta y 403 explicativo | T003, T004 | `administrador.guard.spec.ts` | ✅ |
| FR-UI-144 | `JetBrains Mono`; ningún PK tecleado | T033 | `consola-logs.page.spec.ts` | ✅ |
| FR-UI-145 | Cupo mensual ≠ límite de ritmo | T009 | `monitoreo.types.spec.ts` | ✅ |

## Success Criteria

| SC | Verificación | Estado |
|----|---|--------|
| SC-001 | El partner ve consumo, cupo y coste en una sola pantalla | ✅ |
| SC-002 | 🎯 Nada sugiere interrupción — verificado con el cupo al **150 %** | ✅ |
| SC-003 | 403, 429 y 500 distinguibles sin escalar | ✅ |
| SC-004 | Excepciones de facturación en una sola pantalla | ✅ |
| SC-005 | Toda métrica con entorno y marca temporal | ✅ |
| SC-006 | Ningún rol ve lo que no puede usar | ✅ |
| SC-007 | Los tres estados no felices en las cuatro superficies | ✅ |

## Deltas de backend cerrados

| ID | Qué se hizo | Tests |
|---|---|---|
| **BE-DELTA-04** | `GET /api/v1/facturacion/excepciones` + `ExcepcionesFacturacionService` | `test_excepciones_facturacion_contract.py` (11) |
| **BE-DELTA-05** | Los partners **no tarificables** incluidos en esa respuesta, derivados del corte | íd. |
| **BE-DELTA-06** | Paginación por cursor y **todos** los filtros (`codigohttp`, `desde`, `hasta`, `idcredencialapi`, `endpoint`) resueltos en la base | `test_consola_logs_paginacion.py` (11) |

## Hallazgos de la implementación

### 🐛 Una comilla invertida en un comentario HTML rompió el archivo — dos veces

`` ` `` dentro de un comentario de plantilla **cierra el template literal de
TypeScript**. Pasó en `consola-logs.page.ts` y otra vez en `detalle-log.page.ts`
— la segunda, dentro del comentario que advertía precisamente de esto. Corregido
en los dos y anotado en el propio comentario.

### 🐛 `@else if (…; as x)` otra vez

El alias solo se admite en el `@if` primario. **`tsc --noEmit` no lo detecta**:
solo lo caza `ng test`. Reestructurado a `@else { @if (…; as x) }`.

### El test de invariante marcó la frase que tranquiliza

La lista de palabras prohibidas de `mi-consumo-sin-alarma.spec.ts` incluía
«interrump», y saltó con **«tu servicio no se interrumpe»** — la frase que
existe para tranquilizar. Un blacklist por subcadena no distingue una afirmación
de su negación. Se quitó esa entrada y se dejó escrito por qué; el caso
afirmativo lo cubren «cortad» y «bloquead», y hay una comprobación positiva que
exige que la frase de tranquilidad **sí** esté.

### Un timestamp de 2025 en un test de 2026

El fixture del contract test de excepciones usaba `1_751_328_000_000`, que es
**julio de 2025**. El consumo caía fuera de la ventana, no había excedente y la
excepción no aparecía. Sustituido por una constante calculada y comentada.

### `notificar_cuota` no servía, y eso se descubrió en #09

Anotado aquí porque afecta al vocabulario de esta capa: aquel método documenta
que **nunca menciona interrupción del servicio**, y es la misma regla que
gobierna FR-UI-103.

### 🐛 El contrato prometía seis filtros y el código honraba uno

Al cerrar `BE-DELTA-06` apareció algo que no esperaba: el OpenAPI de #08 **ya
declaraba** `codigohttp`, `desde`, `hasta`, `idcredencialapi`, `endpoint` y
`Cursor` para `/logs-api`. No era el contrato el que iba por detrás: era la
implementación, que solo honraba `solo_errores` y `limit`.

Un consumidor que hubiera leído el contrato habría escrito código contra
parámetros que el servidor ignoraba **en silencio** — sin error, simplemente
devolviendo todo. Los seis están implementados ahora.

### 🐛 La capa frontend leía dos columnas que no existen

`LogLlamada` usaba `latencia` e `idcredencial`; el esquema real de
`Fact_LogLlamadaAPI` tiene **`latenciams`** e **`idcredencialapi`**. La columna
de latencia habría salido vacía en la consola y en el detalle. Corregido en los
seis archivos afectados.

Es el mismo tipo de fallo que el `idcondado` de #08 y el `idpartner` de #09:
**inventar un nombre de columna que suena razonable** en vez de leer el esquema.

## Verificación manual contra la app real (T074)

Ejecutada el 2026-08-10 con el stack encendido, sembrando
`database/seed_monitoreo_demo.py` y sirviendo el frontend en `ng serve`.

> **El contenedor `accidentes-django` corre una imagen anterior al departamento
> Partners** (`/api/v1/partners` devuelve 404 y no monta el código). Para
> verificar hubo que levantar Django desde el working tree en el puerto 8001 y
> apuntar el proxy ahí temporalmente. **Los contenedores no se tocaron**, y el
> `proxy.conf.json` quedó restaurado.

| Escenario | Resultado |
|---|---|
| **B** — el exceso no parece un fallo | ✅ 150 % en tono informativo; CSS computado `rgb(157,177,204)`, cero tokens de severidad, cero palabras prohibidas |
| **E** — mes sin consumo | ✅ vacío informativo, sin «Reintentar» |
| **F** — autodiagnóstico | ✅ 403 / 429 «Límite de ritmo» / 500 distinguidos, con la nota de no facturable en el 429 |
| **H** — excepciones | ✅ los dos tipos, `$63,50` en el que tiene factura y **columna vacía** en el no tarificable |
| **I** — suspendido consulta | ✅ banner + métricas completas |
| Filtros y paginación | ✅ `codigohttp=429` al servidor → 3 filas; 4 páginas / 18 registros / 18 únicos |

### Lo que la verificación manual encontró y los tests no

**Seis defectos reales**, cinco de ellos invisibles para la suite:

#### 🐛 1. El partner no podía ver sus propios errores (403)

`GET /logs-api` era exclusivo del Desarrollador de APIs, así que el bloque
«Errores de tu integración» recibía **403 en cada carga**. Contradecía
RN-APM-009, que existe literalmente *«para que el partner pueda diagnosticar sus
propios fallos sin escalar a un Administrador»*.

Corregido (`BE-DELTA-07`): el permiso pasa a `EsPartnerOGestor` **con control de
propiedad**, así que un partner ve los suyos y nunca los de otro.

#### 🐛 2. Un fail-open que mentía

Ese 403 se tragaba y la pantalla decía **«Sin errores en el período. Tu
integración está respondiendo correctamente»** — afirmando salud sin haberla
comprobado. Ahora distingue «no hay errores» de «no se pudieron consultar».

#### 🐛 3. La paginación repetía filas contra Pinot real

El cursor era solo `idlogllamadaapi`, dando por hecho que el id ordena igual que
la fecha. **No está garantizado**: con datos donde no coinciden, la segunda
página repitió **4 de 5 filas**. Los tests no lo vieron porque su fixture tenía
id y fecha correlacionados — el test y el código compartían la suposición.

Corregido con **cursor compuesto** `(fechallamada, idlogllamadaapi)`, que replica
el `ORDER BY` exacto. El fixture ahora usa id y fecha **en sentidos opuestos**.

#### 🐛 4. El importe de la factura de excedente se escribía en una columna inexistente

`_publicar_factura` publicaba `monto`, y `Fact_Factura` tiene **`monto_base` y
`monto_total`**. Pinot descartaba el campo y la factura se creaba **sin
importe**: existe, pero no cobra nada — RN-APM-014 incumplida de la forma más
difícil de ver. Sobrevivió a 18 tests porque los fixtures sembraban `monto` y lo
leían de vuelta.

#### 🐛 5. La IP salía como «—» en casi todas las llamadas

`iporigen` es INT **con signo** de 32 bits: toda IP desde `128.0.0.0` desborda y
se almacena negativa (`192.168.1.1` → `-1062731519`). El formateador rechazaba
los negativos. Ahora los decodifica con desplazamientos sin signo.

#### 🐛 6. `consola/excepciones` abría el detalle de un partner

La ruta literal se declaró **después** de `consola/:idpartner`, que la capturaba.
Ningún test de página lo veía: cada una funciona en aislamiento. Reordenadas, y
el guard de cableado tiene ahora un test que compara las posiciones.

## Pendiente

*(ninguna)*
