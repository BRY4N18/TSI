# PLAN GLOBAL DE PRUEBAS Y VALIDACIÓN DEL SISTEMA (SDD)

**Proyecto:** Tráfico Seguro Integral (TSI) — Sistema de Gestión de Emergencias Viales
**Versión de la Especificación:** 2.0.2
**Última actualización:** 2026-08-23
**Ubicación:** `specs/Global/PlanPruebas/spec.md`

---

## 0. QUÉ ES ESTE DOCUMENTO (Y QUÉ NO ES)

Este es el **plan adversarial** del sistema: la lista de todo aquello que puede hacer que TSI
devuelva un dato falso, exponga un dato ajeno, o se caiga — junto con la prueba que lo impide.
Su pregunta rectora no es *"¿funciona el camino feliz?"* sino **"¿de qué manera exacta puede
este sistema mentir, filtrar o romperse, y qué prueba lo detecta antes que un usuario?"**.

### 0.1. Relación con el resto de la documentación (autoridad)

Este documento **no** define pirámide de testing, porcentajes de cobertura, markers, fixtures,
convenciones de nombres ni thresholds de latencia por operación. Todo eso ya vive en
`.specify/docs/architecture/testing.md`, que es la **autoridad única** sobre esos temas.

| Tema | Documento con autoridad |
|---|---|
| Pirámide, cobertura, markers, fixtures, comandos, thresholds P95 | `.specify/docs/architecture/testing.md` |
| Puertos, topología, orden de arranque, stack | `.specify/docs/infra/infrastructure.md` |
| Formato de request/response, envelope, códigos HTTP | `.specify/docs/architecture/api-standards.md` |
| Reglas visuales y de interacción | `.specify/docs/design/design-system.md` |
| Prioridad entre características de calidad (ISO/IEC 25010) | `.specify/memory/constitution.md` |
| **Reglas de validación adversarial y su estado de cobertura** | **este documento** |

Si una regla de este plan contradice a `testing.md` o a la constitución, **gana el otro documento**
y esta se corrige. Este plan puede ser *más estricto* en un caso puntual y justificarlo; nunca
más laxo.

### 0.2. Arquitectura de datos que este plan asume

TSI tiene **dos almacenes de datos con roles distintos**, y confundirlos invalida las pruebas:

| Capa | Motor | Rol | Escritura | Lectura |
|---|---|---|---|---|
| **Operacional** | **Apache Pinot** (+ Kafka, Zookeeper) | Modelo dimensional de dominio (`Dim_*` / `Hecho_*`). Es la **fuente de verdad del negocio**. No hay ORM Django ni Postgres de negocio. | Solo vía evento Kafka → ingesta Pinot | SQL directo al broker, **solo lectura** |
| **Analítica** | **ClickHouse** (+ Airflow, Postgres-metastore, staging Parquet en `ETL/`) | Informes tácticos compuestos, agregaciones batch. Es **derivada**, nunca fuente de verdad. | DAGs de Airflow (batch) | SQL desde Django |

Consecuencia normativa: **un dato que solo existe en ClickHouse y no en Pinot es un dato
corrupto**, no un dato nuevo. Toda regla de la sección 5 se apoya en esto.

> **Deriva documental corregida el 2026-08-23** (`PG-DOC-002`): `infrastructure.md` §3 rotulaba a
> Pinot como "Base de datos analítica", contradiciendo a su propio §1. Ya dice **operacional**, y
> se añadió la fila de ClickHouse que faltaba.

---

## 1. PROTOCOLO DE CORRECCIÓN (El Ciclo SDD)

Cualquier error detectado en desarrollo, *testing* o producción sigue estrictamente este flujo
**antes** de tocar el código fuente:

1. **Identificar la brecha:** ¿el error ocurrió porque la especificación estaba incompleta, era
   ambigua, o porque el código no la respetó?
2. **Actualizar la especificación:** añadir aquí la regla, validación o restricción que faltaba,
   con ID, severidad y estado.
3. **Actualizar las pruebas:** escribir la prueba que valida la nueva regla. **La prueba debe
   fallar primero.** Una prueba que pasa recién escrita no demostró nada.
4. **Modificar el código** hasta que la prueba pase.
5. **Registrar** la entrada en `.specify/docs/changelog.md` con código de hallazgo, causa, efecto
   verificado y archivo tocado; referenciarla desde el `traceability.md` afectado.

**Prohibición explícita:** no se corrige una condición de carrera con un `sleep()`, ni un test
intermitente con un reintento, ni un dato faltante con un `try/except` que lo silencie. Esos tres
patrones son deuda disfrazada de arreglo; obligan a volver al paso 1.

### 1.1. Anatomía de una regla

Cada regla de este plan lleva cuatro campos obligatorios:

- **ID** — estable, nunca se reutiliza ni se renumera. Formato `PG-{ÁREA}-{NNN}`.
- **Severidad** — `Bloqueante` (impide desplegar), `Mayor` (impide cerrar el módulo),
  `Menor` (deuda planificada).
- **Estado** — `✅ Cubierta` (existe prueba que falla si se viola) · `⚠️ Parcial` (hay prueba
  pero no cubre el caso adversarial) · `❌ Pendiente` (regla declarada, sin prueba).
- **Prueba** — ruta del archivo, o `—` si está pendiente.

Un `❌ Pendiente` **no es un error del documento: es su producto más valioso.** Declara deuda
conocida en vez de esconderla. Toda regla `Bloqueante` en `❌` debe además figurar en
`decisiones-pendientes.md` si su resolución requiere una decisión del responsable.

### 1.2. Áreas

| Prefijo | Área |
|---|---|
| `PG-CFG` | Configuración, secretos y entorno |
| `PG-OPE` | Capa operacional — Pinot, Kafka, Zookeeper |
| `PG-ANA` | Capa analítica — ClickHouse, Airflow, ETL |
| `PG-API` | Contratos de API |
| `PG-NEG` | Lógica de negocio y concurrencia |
| `PG-SEC` | Seguridad transversal |
| `PG-UI` | Frontend y E2E |
| `PG-RES` | Rendimiento, resiliencia y observabilidad |
| `PG-CI` | Compuertas de calidad y automatización |
| `PG-DOC` | Coherencia documental |

---

## 2. ALCANCE Y MATRIZ DE RIESGO

Prioridad de esfuerzo de prueba = *(impacto si falla)* × *(probabilidad de fallo silencioso)*.
Un fallo **silencioso** pesa más que uno ruidoso: un 500 se ve; un informe con datos incompletos
se firma y se entrega.

| Componente | Impacto | Fallo silencioso | Prioridad |
|---|---|---|---|
| Ingesta Kafka → Pinot | Crítico | **Muy alta** — un consumidor detenido se ve igual que "no hubo accidentes" | **1** |
| Autorización multi-tenant (partners/clientes) | Crítico | **Muy alta** — nadie reporta que vio datos de más | **1** |
| Cadena crítica de despacho | Crítico (vidas) | Media | **1** |
| Configuración de despliegue (DEBUG/secretos) | Crítico | Alta | **1** |
| DAGs Airflow → ClickHouse | Alto | **Muy alta** — un DAG fallido deja el informe con datos de ayer | **2** |
| Contratos de API (37 OpenAPI) | Alto | Media | **2** |
| Facturación y cuotas de partners | Alto | Alta — un error de cálculo se factura | **2** |
| Frontend: estados de error/vacío | Medio | Baja | **3** |
| Accesibilidad | Medio | Alta | **3** |

**Entornos reconocidos:** `local` (desarrollo, `DJANGO_DEBUG=true` aceptable) ·
`e2e` (`docker-compose.e2e.yml`, efímero, datos sintéticos) · `producción` (todas las reglas
`Bloqueante` aplican sin excepción).

---

## 3. CONFIGURACIÓN, SECRETOS Y ENTORNO

> Sección nueva en la v2.0.0. Al redactarla no existía **ni una sola prueba de configuración**
> en el repositorio, pese a que los defaults inseguros estaban a una variable de entorno olvidada
> de llegar a producción. `PG-CFG-001/002/003` se implementaron el 2026-08-23 (ver §13); el resto
> sigue pendiente.

### PG-CFG-001 — `DEBUG` jamás activo fuera de local
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/test_configuracion_segura.py`

`DJANGO_DEBUG` tiene default `true` (`backend/config/settings.py:21`). Un despliegue que omita la
variable expone, en cada excepción, el traceback completo con settings, rutas y fragmentos de
entorno al navegador.

- **Regla:** el arranque **aborta** con `ImproperlyConfigured` si `DEBUG=True` y `TSI_ENV` no es
  un entorno de desarrollo (`local`, `e2e`, `test`).
- **Implementación:** `core/config/secretos.py::verifica_debug`, invocada al final de
  `config/settings.py` con los valores ya resueltos.
- **Decisión de diseño:** se conserva el default `true` de `DJANGO_DEBUG` en vez de invertirlo.
  Invertirlo protege solo al despliegue que ya olvidó configurar el entorno — y a cambio rompe
  todo arranque local sin `.env`. La guarda por `TSI_ENV` cubre el mismo riesgo sin volver
  hostil el desarrollo.

### PG-CFG-002 — Ningún secreto conserva su valor de desarrollo en producción
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/test_configuracion_segura.py`

Riesgo cubierto: con la `SECRET_KEY` de desarrollo cualquiera con acceso al repositorio podía
firmar sesiones válidas; con `CLICKHOUSE_PASSWORD=tactico`, el almacén analítico completo quedaba
accesible con una credencial publicada en el `docker-compose`.

- **Regla:** existe un **registro central** (`core/config/secretos.py::DEFAULTS_INSEGUROS`) que
  enumera todo valor por defecto inseguro. Fuera de local, un secreto que conserve su default
  aborta el arranque. El mensaje enumera **todos** los fallos a la vez, no el primero.
- **Cobertura del registro:** `DJANGO_SECRET_KEY`, `CLICKHOUSE_PASSWORD`, `DEMO_GRANT_SECRET`,
  `DEMO_SESSION_SECRET`. La guarda previa de `apps/ventas_crm/demo_tokens.py` se conserva
  (defensa en profundidad en el punto de uso del token).
- **Antienvejecimiento:** `test_registro_cubre_todos_los_defaults_sensibles_de_settings` analiza
  `settings.py` y falla si aparece un secreto con default sin dar de alta en el registro. Sin
  esto el registro se queda atrás y pasa a dar una falsa sensación de cobertura completa.

### PG-CFG-003 — `ALLOWED_HOSTS` y CORS cerrados por defecto
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/test_configuracion_segura.py`

- **Regla:** fuera de local, `ALLOWED_HOSTS` no puede contener `*`, `localhost` ni `127.0.0.1`
  — cubierto por `core/config/secretos.py::verifica_hosts`.
- **Pendiente:** la mitad de CORS. Falta la guarda que impida `CORS_ALLOW_ALL_ORIGINS` y exija
  lista explícita de orígenes.

### PG-CFG-004 — `manage.py check --deploy` sin advertencias
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `.github/workflows/ci.yml` (job `configuracion`)

- **Regla:** el chequeo nativo de despliegue de Django corre en CI y **falla el build** ante
  cualquier advertencia (`--fail-level WARNING`).
- **Detalle de implementación que importa:** el paso se ejecuta con la configuración de un
  despliegue **real** (`DJANGO_DEBUG=false`, `TSI_ENV=production`), no con la de desarrollo. Con
  `DEBUG=true`, `check --deploy` silencia justo las comprobaciones que interesan y el paso pasaría
  siempre sin mirar nada — una compuerta decorativa.
- **Al activarlo aparecieron 5 advertencias reales**, corregidas el 2026-08-23 en el mismo trabajo
  (ver `PG-SEC-008`).

### PG-CFG-005 — Ningún secreto versionado en git
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_secretos_versionados.py`

- **Regla:** escaneo de secretos (`gitleaks` o equivalente) sobre el árbol y el historial.
  `backend/env.example` solo contiene placeholders. `backend/config/keys/` (claves JWT RS256)
  **nunca** se versiona.
- **Corregido 2026-08-23:** `backend/config/keys/` no estaba en `.gitignore` (aunque tampoco
  llegó a versionarse): un `git add -A` habría commiteado `jwt_private.pem`, la clave que firma
  los tokens de sesión. Añadida la regla al `.gitignore`.
- **La regla estaba marcada y nunca se había ejecutado (2026-08-23).** `gitleaks` figuraba en el
  workflow desde el principio, así que la casilla parecía cubierta. Al correrlo por primera vez
  sobre los 30 commits salieron **9 hallazgos**; los 9 se revisaron uno a uno y ninguno es un
  secreto (claves de un diccionario de informes, fixtures de prueba, y `tactico:tactico` contra
  `localhost:8123` en un quickstart — valor que además está en `DEFAULTS_INSEGUROS`, así que el
  arranque aborta si aparece fuera de un entorno local).
- **Allowlist con motivo escrito:** `.gitleaks.toml` nombra los 5 ficheros uno a uno. La
  alternativa era dejar el escaneo en rojo permanente, y un escaneo que siempre falla deja de
  leerse — que es exactamente cómo se cuela el secreto de verdad.
- **CI recibe la config explícitamente** (`GITLEAKS_CONFIG`): sin esa variable la acción usa la
  por defecto y el paso vuelve al rojo permanente.
- **Verificada la no-vacuidad:** con la allowlist puesta, una clave AWS y un token de GitHub de
  aspecto realista se detectan igualmente.

---

## 4. CAPA OPERACIONAL — PINOT, KAFKA, ZOOKEEPER

> Fuente de verdad del negocio. Un fallo aquí no produce un error: produce un **dato que no
> existe** y nadie lo nota.

### PG-OPE-001 — Un consumidor detenido es un fallo, no un silencio
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_ingesta_pinot.py`

Fallo ya observado en el proyecto: una tabla de Pinot sin segmento consumiendo se comporta
exactamente igual que una siembra que no corrió — el endpoint responde `200` con lista vacía.

- **Regla:** toda tabla `REALTIME` debe tener al menos un segmento en estado `CONSUMING`. Su
  ausencia es un fallo de severidad crítica, no un resultado vacío.
- **Ejecutado contra Pinot real el 2026-08-23:** las 5 comprobaciones pasan. Se consulta
  `consumingSegmentsInfo` del controller y se exige `CONSUMING`, además de que ningún servidor deje
  de responder — un servidor mudo deja huecos que el conteo no delata.
- **Corolario para el resto de la suite:** ninguna prueba de listado puede afirmar únicamente
  `status == 200`. Un listado vacío donde se sembraron datos es un fallo.

### PG-OPE-002 — Reconciliación evento publicado → fila consultable
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_ingesta_pinot.py`

- **Regla:** todo evento publicado en `{NombreTabla}_topic` debe ser consultable en Pinot dentro
  de la ventana de frescura declarada. Publicación sin lectura posterior verificada = pérdida
  de dato.
- **Cubierta por offsets**, que responde a «¿ha llegado todo?» sin publicar nada: se compara el
  offset consumido con el del tópico, y el retraso temporal (`availabilityLagMs`) contra un margen
  de 60 s. Un lag creciente es el aviso previo a la pérdida — el consumidor sigue vivo, marca
  `CONSUMING`, y cada vez va más atrás.

### PG-OPE-003 — Esquema declarado == esquema real
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/regression/test_doble_pinot_vs_esquemas.py`

- **Regla:** `database/esquemas.json` y `database/tablas.json` deben coincidir con lo registrado
  en el controller. Una columna añadida en código sin migrar el esquema rompe la ingesta en
  silencio.

### PG-OPE-004 — Upsert `FULL` y monotonía de `fecha_actualizacion`
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/regression/test_fecha_actualizacion_epoch_ms.py`

- **Regla:** el upsert resuelve por `fecha_actualizacion` en **epoch milisegundos**. Un evento con
  timestamp menor al ya ingerido **no** debe sobrescribir al más reciente.
- **Prueba esperada:** publicar el mismo ID con timestamps desordenados (T2, luego T1); afirmar
  que prevalece T2. Hoy se valida el formato, no el desempate.

### PG-OPE-005 — Idempotencia de reintentos
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_escritura_operacional.py`

- **Regla:** republicar el mismo evento no puede producir un registro duplicado ni alterar el
  estado del negocio. Kafka garantiza *al menos una vez*, así que la deduplicación **tiene** que
  ocurrir en el destino.
- **Verificado 2026-08-23:** las **79 tablas** declaran `upsertConfig` con `mode: FULL`, y toda
  columna de comparación existe en su esquema — una declarada y ausente deja el upsert sin criterio
  sin que Pinot avise.
- ⚠️ **Hallazgo:** 26 tablas comparan por **fecha de negocio** (`fecha_emision`, `fecha_inicio`) en
  vez de `fecha_actualizacion`. Esa columna no cambia al corregir el registro, así que la corrección
  gana por el **desempate del motor**, no por comparación. **Hoy funciona** —`Fact_Session` tiene
  292 cierres registrados— pero depende de comportamiento de Pinot, no de una garantía declarada.
  Ver `decisiones-pendientes.md` #52. Una prueba congela el número en 26 para que ninguna tabla
  nueva herede el patrón sin decisión.

### PG-OPE-006 — Límite de resultados explícito en toda consulta
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/regression/test_pinot_client_limit.py`

- **Regla:** Pinot aplica un `LIMIT` implícito (10 por defecto). Toda consulta debe declarar su
  límite explícitamente; omitirlo devuelve resultados truncados **sin ningún aviso** — un informe
  silenciosamente incompleto.

### PG-OPE-007 — Pinot es de solo lectura desde Django
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_pinot_solo_lectura.py`

- **Regla:** ninguna ruta de código de Django emite `INSERT`/`UPDATE`/`DELETE` contra Pinot. El
  único canal de escritura es Kafka.
- **Cubierta 2026-08-23 por análisis estático**, y no por comportamiento: un `INSERT` contra Pinot
  no falla de forma observable con mocks —el doble acepta cualquier SQL, como demostró `PG-SEC-005`
  (`changelog.md` C8)—. Lo comprobable es que la sentencia **no esté escrita en el árbol**.
- **Una sola excepción**, enumerada a mano: `core/pinot/secuencia.py` escribe contra un **SQLite
  local**, no contra Pinot. Hay una prueba que verifica que sigue siendo SQLite: una exclusión que
  ya no se comprueba es peor que no tener regla, porque aparenta cobertura.

### PG-OPE-008 — Borrado lógico en el camino de la API
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_escritura_operacional.py`

Reescritura de la regla ambigua de la v1.0 (que declaraba una prohibición total de `DELETE`,
contradicha por los ~25 scripts de `database/`).

- **Regla:** **ninguna operación expuesta por la API elimina físicamente un registro**; se marca
  como inactivo mediante la columna de estado correspondiente y deja de listarse. El borrado
  físico existe **solo** en scripts de mantenimiento identificados (`limpia_datos_prueba.py`,
  `reset_despachos_demo.py`, migraciones de `database/`), que **no** pueden ejecutarse contra
  producción.
- **Prueba esperada:** tras "eliminar" vía API, el registro no aparece en el listado pero sigue
  siendo recuperable por consulta directa con su marca de inactivo, y conserva su rastro de
  auditoría.
- **Advertencia de implementación:** el literal del estado debe **importarse de la constante
  canónica** del repositorio, nunca copiarse de una spec — literales inexistentes producen
  listados vacíos con `200`.
- **Verificado 2026-08-23:** ningún `DELETE` de la API destruye el registro (`/usuarios` y `/roles`
  llaman a `deactivate_*`), y **ningún módulo de aplicación importa los scripts de mantenimiento**
  de `database/`. Que el borrado físico exista está bien; que esté a un clic de la API no.

---

## 5. CAPA ANALÍTICA — CLICKHOUSE, AIRFLOW, ETL

> Capa **derivada**. Su fallo característico no es caerse, sino servir datos de ayer como si
> fueran de hoy.

### PG-ANA-001 — Cuadre analítica ↔ operacional
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_reconciliacion.py` + `backend/tests/seguridad/test_reconciliacion_integracion.py`

- **Regla:** para todo informe táctico, los conteos e importes agregados en ClickHouse deben
  cuadrar con la misma agregación calculada sobre Pinot para el mismo periodo, dentro de la
  tolerancia declarada por la ventana de frescura del DAG. **Discrepancia = fallo bloqueante.**
- **Por qué es la regla más importante de la sección:** es la única que detecta un informe
  plausible pero falso, que es exactamente lo que un usuario firma sin sospechar.
- **Implementado 2026-08-23 (`changelog.md` C12):** `core/seguridad/reconciliacion.py` declara las
  **20 tablas de hechos** con su origen en Pinot. El cuadre compara claves distintas y sumas de
  medidas para una ventana de 30 días, que es el grano de partición de los DAGs.
- ⚠️ **Los nombres no se adivinaron.** Salen de cruzar `dags/lib/ddl.py` con
  `database/esquemas.json`, y hubo que declarar **clave y medida por lado**: `idsesion` frente a
  `idsession`, `idlog` frente a `idlogllamadaapi`, `numvehiculos` frente a `num_vehiculos`. Con un
  solo nombre, el cuadre habría fallado por una columna mal escrita en vez de por un dato mal
  cargado — y nadie distingue una cosa de la otra leyendo el fallo. Una prueba valida los 20 pares
  contra los esquemas reales.
- **Dos asertos, no uno.** El conteo detecta filas que faltan o sobran; las sumas detectan el caso
  que el conteo no ve: **están todas las filas con los valores cambiados**. El informe da el número
  correcto de accidentes y el número equivocado de heridos, y eso se entrega a aseguradoras.
- **Ejecutado contra Pinot y ClickHouse reales el 2026-08-23: 22 de 25 cuadran exactos**, medidas
  incluidas. Los 3 restantes son desfase de carga, no defecto — la prueba lo distingue y **avisa en
  vez de fallar**, porque no hay nada que arreglar en la transformación: hay un DAG que reanudar.
- **La frescura la vigila `PG-ANA-002`**, que sí falla. Cada regla mira lo suyo y el fallo apunta a
  quien puede resolverlo; mezclarlas haría que un DAG parado tapara una discrepancia real.

### PG-ANA-002 — Frescura declarada y visible
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/seguridad/test_frescura_analitica.py`

- **Regla:** todo informe táctico expone la marca temporal de la última carga exitosa. Si los
  datos superan su ventana de frescura, el sistema lo **indica al usuario**; no sirve datos
  vencidos como si fueran actuales.
- **Implementado 2026-08-23:** margen de 2 días, coherente con la cadencia diaria de los 18 DAGs.
  Una prueba comprueba esa coherencia: con tres días de margen se perdería una corrida entera sin
  aviso, y la regla existiría sin proteger.
- ⚠️ **Se mide por `cargado_en`, no por `fecha`.** La distinción costó un diagnóstico equivocado:
  `fecha` es la fecha de **negocio** y puede estar en el futuro — `hecho_suscripcion` tiene
  contratos que empiezan en meses, así que medir con ella daba «−100 días de antigüedad» y la tabla
  pasaba el control sin haberse cargado nunca. Medido bien, las tablas atrasadas son **5, no 17**.
- **Hallazgo operativo:** `hecho_despacho`, `hecho_estado_unidad`, `hecho_ping_unidad`,
  `hecho_baja_unidad` y `hecho_validacion_region` llevan entre 7 y 8 días sin cargar. No es un
  defecto de código: los DAGs se crean con `is_paused_upon_creation=True`.
- **Pendiente para ✅:** la segunda mitad de la regla — que el informe **exponga** la marca al
  usuario. Hoy se detecta el desfase pero la API no lo comunica, así que un informe viejo se sigue
  leyendo igual que uno al día.

### PG-ANA-003 — Un DAG fallido no deja datos a medias
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/seguridad/test_carga_analitica.py`

- **Regla:** la carga Pinot → staging Parquet (`ETL/`) → ClickHouse es **atómica por partición**:
  o la partición queda completa, o queda como estaba. Un fallo a mitad de DAG nunca deja una
  partición parcialmente cargada — que es indistinguible de un día de poca actividad.
- ⚠️ **Hallazgo 2026-08-23: la carga NO es atómica, y el motor no puede hacerla serlo.**
  `DROP PARTITION` e `INSERT` son dos operaciones sin transacción entre ellas en ClickHouse. Si la
  inserción falla, la partición queda **vacía**.
- **Vacía es menos malo que parcial**, y esa es la parte tranquilizadora: el cuadre de `PG-ANA-001`
  lo detecta como «faltan N», mientras que unas filas de menos pasarían por un mes flojo. Pero
  sigue siendo una ventana en la que el informe muestra cero para un período con datos.
- **Lo cubierto:** que se reemplace la partición entera y nunca por condición —un `DELETE WHERE`
  deja fuera lo que la condición no alcanza—, que un período que se queda vacío también se
  descarte, que el orden sea descartar→insertar, y que **el límite de atomicidad esté documentado
  donde vive el código**, para que nadie suponga una garantía que no existe.
- **Pendiente para ✅:** inyectar un fallo a mitad de carga contra ClickHouse real y comprobar el
  estado resultante.

### PG-ANA-004 — Reejecución de un DAG es idempotente
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `dags/tests/test_carga_particion.py::TestIdempotencia`

- **Regla:** reejecutar un DAG sobre la misma partición produce el mismo resultado, no filas
  duplicadas ni importes al doble.
- **Ya estaba cubierta** por `dags/tests/test_carga_particion.py::TestIdempotencia`, escrita antes
  de este plan. Se enlaza en vez de duplicarla: una segunda prueba de lo mismo envejece por su
  cuenta y acaba contradiciendo a la primera.

### PG-ANA-005 — Alias que tapa la columna en ClickHouse
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_consultas_clickhouse.py`

Causa recurrente y ya diagnosticada de `ILLEGAL_AGGREGATION` y de endpoints en 500 en este
proyecto: un alias de `SELECT` que coincide con el nombre de una columna real.

- **Regla:** ningún alias de proyección puede coincidir con el nombre de una columna de la tabla
  consultada.
- **Ejecutado el 2026-08-23: las 158 consultas del catálogo se ejecutan contra ClickHouse real.**
  Un mock nunca reproduce este error, y por eso reaparecía.
- **Defecto real encontrado y corregido:** `estrategicos/oe5/e5_02_retencion_neta_ingresos.sql`
  fallaba con «no supertype for types Float64, Decimal(38,2)» — las dos ramas de un `if()` tenían
  tipos incompatibles. Ese informe devolvía **500 la primera vez que alguien lo abriera**.
- ⛔ **Se retiró un análisis estático de alias que se había escrito para esto.** Marcaba ocho
  consultas correctas (`ifNull(p.columna, 0) AS columna`, `argMax(idplan, fecha) AS idplan`) que se
  ejecutan sin error. Una prueba que señala código correcto se desactiva en cuanto estorba, y con
  ella se pierde la que sí protege.

### PG-ANA-006 — El Postgres de Airflow no almacena negocio
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_carga_analitica.py`

- **Regla:** `tactico-airflow-postgres` es **exclusivamente** metastore del orquestador. Ninguna
  tabla del modelo dimensional puede residir ahí.
- **Verificado 2026-08-23:** Django no lo referencia, el DDL analítico no crea nada en Postgres, y
  el metastore **no publica puertos al host** — barrera barata contra el atajo de guardar «una
  tablita» ahí.
- **Por qué importa más de lo que parece:** una tabla de negocio en el metastore sería una **tercera
  copia de la verdad**, y el cuadre de `PG-ANA-001` solo compara Pinot con ClickHouse. Las tres
  divergirían sin que nada lo detectara.

---

## 6. CONTRATOS DE API

### PG-API-001 — Implementación conforme al contrato OpenAPI
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `apps/accidentes/tests/api/test_informes_openapi_conforme.py`

Existen **37 contratos OpenAPI**; hoy solo un módulo valida conformidad automáticamente.

- **Regla:** toda respuesta debe validar contra el esquema de su contrato: campos, tipos,
  obligatoriedad, códigos HTTP. Un campo devuelto y no declarado es un fallo del mismo peso que
  uno declarado y no devuelto.
- **Acción:** generalizar el mecanismo existente a los 37 contratos, sin reescribirlo por módulo.

### PG-API-002 — Rechazo estricto de campos no declarados
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** varios `test_*_contract.py`

- **Regla:** todo `POST`/`PUT` valida el payload contra su esquema **antes** de ejecutar lógica.
  Campos adicionales ⇒ `400`, nunca ignorados en silencio.
- **Prueba esperada:** además del clásico `"is_admin": true`, inyectar campos que **sí existen en
  el modelo pero no en el contrato de ese endpoint** (`idpartner`, `estado`, `saldo`) — la
  escalada real ocurre por asignación masiva de campos legítimos, no por uno inventado.

### PG-API-003 — Envelope y errores uniformes
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `core/api/response_envelope.py` (implementación)

- **Regla:** toda respuesta, incluidos los errores, usa el envelope del manejador central. Ningún
  endpoint devuelve un traceback ni un formato propio. Un `500` nunca revela rutas internas,
  nombres de tabla ni SQL.

### PG-API-004 — Validación de límites y tipos
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_validacion_entrada.py`

- **Regla:** batería transversal sobre todo endpoint: cadenas vacías, cadenas de 10.000
  caracteres, negativos donde se espera positivo, cero, `null` en campos obligatorios, unicode y
  emoji, fechas imposibles (`2026-02-30`), fechas futuras donde no procede, coordenadas fuera de
  rango, IDs inexistentes ⇒ `404` (**nunca** `500`).
- **Regla heredada del changelog v1.0:** `fecha_nacimiento <= fecha_actual`.
- **Implementado 2026-08-23:** diez formas de cuerpo malformado —vacío, tipos cambiados, cadena de
  10 000 caracteres, nulos, unicode, `2026-02-30`, negativos, anidado inesperado, JSON inválido y
  array en la raíz— contra **todos los endpoints de escritura sin parámetros**.
- **Segundo defecto del mismo patrón encontrado y corregido:** `LoginView` hacía
  `request.data.get()` sobre un array y lanzaba `AttributeError` → **500**. Es el mismo modo de
  fallo que `changelog.md` C7, y la predicción de T081 se cumplió.
- ⚠️ **Se corrigió de forma central, no vista a vista.** 25 módulos comparten el patrón; arreglar
  25 ficheros a mano deja fuera el número 26, que se escribe la semana siguiente. Un parser
  (`core/api/parsers.py`) rechaza con `400` cualquier cuerpo cuya raíz no sea un objeto, antes de
  que ninguna vista lo vea. Se verificó primero que **ninguna vista espera una lista**.

### PG-API-005 — Paginación íntegra
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `apps/accidentes/tests/api/test_informes_paginacion_integridad.py`

- **Regla:** recorrer todas las páginas devuelve el total exacto, sin repetidos ni omitidos, aun
  con escrituras concurrentes. Límite máximo de página declarado y aplicado (defensa contra
  `?limit=999999`).

---

## 7. LÓGICA DE NEGOCIO Y CONCURRENCIA

### PG-NEG-001 — Escrituras concurrentes sobre el mismo recurso
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_concurrencia_despacho.py`

- **Regla:** una escritura que depende de una lectura previa debe hacer ambas bajo la misma
  exclusión mutua. El recurso crítico es la unidad de emergencia (`PG-NEG-002`).
- **Corrección del enunciado (2026-08-23):** la redacción original pedía bloqueo optimista con
  token de versión y `409`. **No es aplicable aquí:** el bloqueo optimista necesita comparar la
  versión en el momento de escribir, y en este sistema la escritura va a Kafka —que no compara
  nada— y se materializa en Pinot de forma asíncrona. No hay punto donde hacer el
  *compare-and-set*. Se sustituye por reserva previa, que sí es implementable sobre esta
  arquitectura.
- **Prohibición mantenida:** una condición de carrera no se corrige con `sleep()`.

### PG-NEG-002 — Doble asignación de unidad de emergencia
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_concurrencia_despacho.py`

- **Regla:** una misma unidad no puede quedar asignada a dos accidentes simultáneos, bajo ninguna
  secuencia de peticiones concurrentes.
- **Por qué es bloqueante:** es el único fallo de concurrencia del sistema con consecuencia
  física directa — una ambulancia que no llega porque figura despachada a otro sitio.
- **Defecto real, reproducido (2026-08-23).** `asignar()` comprobaba la disponibilidad leyendo de
  Pinot y luego escribía vía Kafka, sin nada entre medias. Con dos operadores simultáneos el
  resultado fue **dos despachos activos para la misma unidad y cero errores**: ambos vieron
  confirmación. La ventana no mide milisegundos entre hilos, sino **lo que tarda la ingesta**: la
  comprobación de la segunda petición no ve el despacho que la primera acaba de crear.
- **Arreglo:** `core/seguridad/reserva_unidad.py`. La comprobación y la escritura pasan a ocurrir
  dentro de una reserva tomada con `cache.add()` —comprobar-e-insertar atómico, la misma llamada
  en LocMem que en Redis— con TTL para que un fallo a mitad no deje la ambulancia bloqueada.
- ⚠️ **Límite conocido y documentado:** sin `CACHES` configurado, Django usa `LocMemCache`, que es
  **por proceso**. Con varios workers de gunicorn dos peticiones repartidas entre workers
  distintos podrían volver a colisionar. La reserva reduce la ventana de *segundos de ingesta* a
  *un reparto entre workers*; cerrarla del todo exige Redis, que hoy no está desplegado.
  **Decisión de infraestructura pendiente** — ver `decisiones-pendientes.md`.
- **Cinco intentos hasta que la prueba probó algo.** Pasó en verde tres veces por motivos
  distintos: los accidentes no existían, la unidad 1 ya tenía despacho activo en la siembra, y el
  estado por defecto de una unidad sin historial es «Fuera de servicio». Cada uno hacía que ambas
  llamadas fallaran antes de llegar a la carrera. La prueba lleva ahora asertos que **fallan si
  eso vuelve a pasar**, en vez de pasar en silencio.

### PG-NEG-003 — Transiciones de estado válidas
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** dispersa por módulo

- **Regla:** cada entidad con ciclo de vida declara su máquina de estados; toda transición no
  declarada se rechaza. Probar explícitamente los **saltos hacia atrás** (cerrado → en curso) y
  los saltos de etapa (registrado → cerrado sin despacho).

### PG-NEG-004 — Unicidad e integridad de identificadores
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/test_secuencia_id.py`

### PG-NEG-005 — Cálculos de facturación y cuotas
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** módulos de suscripciones y partners

- **Regla:** todo importe se prueba con casos borde: cero, cambio de periodo, prorrateo,
  excedente exacto en el límite, y la frontera declarada por `RN-APM-002` (**el cupo mensual
  nunca bloquea: se factura** — un test que espere `429` por cuota mensual estaría probando lo
  contrario de la regla de negocio).
- **Regla de redondeo:** nunca aritmética de punto flotante para dinero.

---

## 8. SEGURIDAD TRANSVERSAL

> Sección enteramente nueva. Es la de mayor densidad de riesgo del sistema y hoy la de menor
> cobertura.

### PG-SEC-001 — Aislamiento multi-tenant (IDOR)
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `apps/partners/tests/unit/test_no_enumeracion_partners.py`

**El riesgo número uno del sistema.** TSI sirve a partners, aseguradoras, municipios y clientes
sobre los mismos datos.

- **Regla:** ninguna entidad puede acceder a datos de otra sustituyendo un identificador. El
  filtro de tenencia se aplica **en la capa de datos**, jamás confiando en un parámetro del
  cliente.
- **Prueba esperada (sistemática, no por muestreo):** para **cada** endpoint que reciba un ID,
  autenticarse como tenant A y solicitar un recurso de B ⇒ `404` (no `403`: un `403` confirma
  que el recurso existe). Cubrir también `PUT`, `PATCH` y `DELETE`, no solo `GET` — y los IDs
  anidados en el cuerpo, no solo los de la URL.
- **Nota de diseño de la prueba:** debe construirse sobre el **inventario de rutas**, de modo que
  un endpoint nuevo sin cobertura haga fallar la suite. Una lista escrita a mano envejece mal y
  da una falsa sensación de cobertura completa.
- **Avance 2026-08-23 (`changelog.md` C4):** cerrado el oráculo de enumeración en Partners. Las
  vistas cortaban con `404` antes de comprobar propiedad y devolvían `403` si era ajeno, con lo que
  `404`/`403` distinguían «no existe» de «no es tuyo». Resuelto **según quién pregunta**: el gestor
  conserva el `404` preciso (no le revela nada), el resto recibe una respuesta idéntica en ambos
  casos. Se unificaron además los mensajes, que filtraban por el cuerpo.
- **Lo que falta para ✅:** la suite sistemática sobre el inventario de rutas; los siete servicios de
  Partners que lanzan `not_found` por su cuenta; el canal temporal (la rama «no existe» responde
  antes); y el resto de módulos más allá de Partners.

### PG-SEC-002 — Autorización vertical por rol
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `e2e/tests/04-auth-roles.spec.ts`

- **Regla:** cada endpoint declara los roles admitidos; un rol no admitido recibe `403`. El
  frontend ocultando un botón **no es** control de acceso.
- **Prueba esperada:** matriz completa rol × endpoint. Toda celda no probada se considera
  descubierta.

### PG-SEC-003 — Integridad del JWT
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_integridad_jwt.py`

- **Regla:** se rechaza todo token con firma inválida, `alg: none`, algoritmo distinto al
  declarado (RS256), expirado, emitido para otro público, con claims manipulados (rol/tenant), o
  revocado. La sesión expira y se puede revocar.
- **Prueba esperada:** batería adversarial de tokens malformados. Hoy se prueba que un token
  válido funciona; falta probar que los inválidos **no**.
- **Verificado 2026-08-23 (`changelog.md` C6):** las seis variantes reciben `401` y la revocación
  de sesión funciona. **Sin vulnerabilidades**; no hizo falta corregir código.
- ⚠️ **Matiz que conviene no perder:** la confusión de algoritmo la bloquea **PyJWT**, no la
  configuración del proyecto — la biblioteca se niega a usar una clave asimétrica como secreto
  HMAC. Debilitando `verify_access_token` las pruebas seguían en verde. Se añadieron dos que
  verifican la configuración propia y sí detectan el debilitamiento.
- **Completado 2026-08-23 (`changelog.md` C10):** degradación selectiva implementada tras
  confirmación del responsable. Fuera de la cadena crítica el sistema sigue **fail-closed**; en las
  9 rutas confirmadas, una caída del almacén degrada a la validación criptográfica.
- ⚠️ **Una sesión revocada se deniega SIEMPRE**, cadena crítica incluida. Degradar ante una caída es
  una concesión al Principio IX; dejar entrar a quien se le retiró el acceso a propósito no lo es.
  Hay una prueba dedicada a cada mitad, y ambas se verificaron rompiendo el código a propósito.
- **Ventana de riesgo aceptada y registrada:** durante una caída, un token revocado sigue sirviendo
  en esas 9 rutas hasta expirar. Se anota en WARNING para que el periodo sea auditable.

### PG-SEC-004 — Límite de tasa efectivo
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_throttles.py`

- **Regla:** los throttles declarados (`prospecto_registro` 10/min, `demo_sesion_ip` 20/min,
  `demo_interaccion_token` 60/min, `partner_api` 1000/min) se aplican realmente: superar el cupo
  ⇒ `429`. Están declarados y **ninguno tiene prueba**.
- **Distinción obligatoria:** este es el techo técnico de plataforma. **No** es la cuota comercial
  de `RN-APM-002` (ver `PG-NEG-005`).

### PG-SEC-005 — Inyección
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/seguridad/test_inyeccion.py` + `backend/tests/seguridad/test_inyeccion_integracion.py`

- **Regla:** ninguna consulta a Pinot o ClickHouse se construye por concatenación de entrada del
  usuario. Toda entrada se parametriza o se valida contra lista blanca.
- **Superficie de máximo riesgo:** los informes con filtros dinámicos, `ORDER BY` y nombres de
  columna variables — donde la parametrización estándar no aplica y hay que usar lista blanca.
- **Prueba esperada:** payloads de inyección en cada parámetro de filtro; afirmar rechazo o
  neutralización, y ausencia de mensajes de error del motor en la respuesta.
- **Revisado 2026-08-23 (`changelog.md` C8):** los `WHERE` usan parámetros con nombre, ClickHouse
  liga del lado servidor con tipos, y el `ORDER BY` se compone de constantes de código más un
  booleano. **Sin vulnerabilidades de inyección.**
- ⚠️ **Lección de método, la más importante del día:** la suite rápida (499 pruebas, 62 parámetros
  reales × 8 cargas × 70 endpoints) **no detecta inyecciones**. Se comprobó introduciendo una real
  en el `ORDER BY` y las 497 siguieron en verde: el doble de Pinot no analiza SQL, hace coincidencia
  de patrones. Un mock acepta cualquier sentencia. La suite declara ese límite en su cabecera.
- **Pendiente para ✅:** ejecutar `test_inyeccion_integracion.py` contra Pinot y ClickHouse reales
  en `integracion.yml`. Hasta entonces la ausencia de inyección está **razonada, no verificada**.

### PG-SEC-006 — Subida de archivos
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_subida_archivos.py`

El sistema acepta hasta **50 MB** por petición multipart (evidencia fotográfica, adjuntos de
tickets).

- **Regla:** se valida el **tipo real por bytes mágicos**, no por extensión ni por
  `Content-Type` declarado. Se rechazan ejecutables, SVG con script y archivos que exceden el
  límite. El nombre se sanea (sin `../`). Los binarios viven en Azure Blob, nunca servidos desde
  el origen de la aplicación.
- **Prueba esperada:** subir un ejecutable renombrado a `.jpg` ⇒ rechazo; subir 51 MB ⇒ `413`.

### PG-SEC-007 — Datos sensibles en registros y respuestas
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/seguridad/test_datos_sensibles.py`

TSI maneja ubicación, identidad de víctimas y datos potencialmente de salud (constitución,
Principio V).

- **Regla:** ningún log, traza ni respuesta de error incluye datos personales, coordenadas
  exactas de víctimas, tokens ni credenciales. Los identificadores personales se enmascaran en
  logs.
- **Verificado 2026-08-23 (`changelog.md` C7):** los logs **no** escriben datos personales, tokens
  ni coordenadas en claro, y los errores no revelan traceback, tablas ni SQL. **No hizo falta el
  filtro de enmascarado que este plan preveía**: se comprobó que no es necesario en vez de añadirlo
  por si acaso.
- **Corregido de paso:** `POST /usuarios` devolvía **500** ante un cuerpo incompleto. El `500`
  importa aquí porque es **el único camino que no pasa por el manejador central** —
  `drf_exception_handler` devuelve `None` para excepciones ajenas a DRF— y por tanto el único sin
  garantía de qué muestra.
- **Pendiente para ✅:** auditar el resto de endpoints de escritura. El patrón `request.data` en
  crudo hacia un servicio que indexa por clave puede repetirse (`PG-API-004`).

### PG-SEC-008 — Cabeceras y cookies de seguridad HTTP
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_cabeceras.py`

- **Regla:** toda respuesta incluye `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy` y `Strict-Transport-Security`; las cookies de sesión y CSRF son `Secure` y
  `HttpOnly`.
- **Implementado 2026-08-23** en `config/settings.py`. Las tres que no dependen de HTTPS están
  activas en todo entorno; las que sí (`SECURE_SSL_REDIRECT`, cookies `Secure`, HSTS) se activan
  solo fuera de local — activarlas siempre dejaría el login inservible en el servidor de
  desarrollo, que corre sobre HTTP plano.
- **HSTS se declara explícitamente** (1 año, con subdominios y preload) en vez de heredar el
  default `0`: una política HSTS mal configurada es difícil de revertir, porque el navegador la
  recuerda aunque el servidor deje de enviarla.
- **Completado 2026-08-23 (`changelog.md` C9):** `frontend/nginx.conf` **no declaraba ninguna**
  cabecera de seguridad — Django las enviaba en `/api/` y la aplicación Angular quedaba
  descubierta. Añadidas las tres universales más una CSP con `script-src 'self'` (sin
  `unsafe-inline`) y `frame-ancestors 'none'`.
- ⚠️ **Todas con `always`**, y hay una prueba dedicada a ese modificador: sin él nginx omite la
  cabecera en 4xx y 5xx — se recibe en el camino feliz, una revisión manual la ve, y desaparece
  justo en las respuestas que un atacante provoca.

### PG-SEC-009 — Dependencias sin vulnerabilidades conocidas
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `.github/workflows/ci.yml` (job `dependencias`)

- **Regla:** `pip-audit` y `npm audit` corren en CI. Vulnerabilidad crítica o alta ⇒ build
  fallido. Una excepción temporal se documenta con fecha de caducidad en
  `decisiones-pendientes.md`.
- **Sin verificar localmente:** ninguna de las dos herramientas se ejecutó al montar el pipeline.
  Es el job con más probabilidad de salir en rojo en el primer run — y si lo hace, será por un
  hallazgo legítimo que conviene atender, no por un fallo del workflow.

### PG-SEC-010 — Endpoints de demo aislados del sistema real
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_aislamiento_demo.py`

- **Regla:** el flujo de demo interactiva (grant HMAC + sesión HS256) no puede leer ni escribir
  datos reales de clientes, ni servir de puerta trasera de autenticación al sistema principal.
  Su token es de un tipo distinto al JWT RBAC de usuario y **no** es aceptado por los endpoints
  de negocio.

---

## 9. FRONTEND Y E2E

### PG-UI-001 — Componentes sin acceso directo a red
**Severidad:** Menor · **Estado:** ⚠️ Parcial · **Prueba:** 250 `.spec.ts` en `frontend/src`

- **Regla:** ningún componente visual llama directamente a la API; consume servicios inyectados.
- **Nota:** la regla arquitectónica (*standalone*, tokens de diseño) tiene su autoridad en
  `design-system.md`. Aquí solo vive **cómo se verifica**.

### PG-UI-002 — El sistema nunca muestra una pantalla en blanco
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `e2e/tests/`

- **Regla:** ante `500`, `timeout`, pérdida de red o respuesta vacía, la UI muestra un estado
  explícito (error con reintento, o vacío informativo) — nunca un blanco ni un *spinner* eterno.
- **Prueba esperada:** interceptar la red con Playwright y forzar `500`, `timeout` y `[]` en cada
  vista crítica.

### PG-UI-003 — Sesión expirada durante el uso
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `frontend/src/app/core/interceptors/sesion-expirada.interceptor.spec.ts`

- **Regla:** al recibir `401` con trabajo sin guardar, la aplicación redirige a login **sin
  descartar silenciosamente** lo que el usuario escribió.
- **Lo que había antes: nada (2026-08-23).** Ni una sola referencia a `401` en todo el frontend
  fuera de los specs. La sesión caducaba y cada componente mostraba —o no— un error genérico: el
  usuario se quedaba en una pantalla muerta pulsando botones que ya no hacían nada, sin
  redirección ni aviso.
- **Arreglo:** `sesionExpiradaInterceptor` limpia la sesión, deja anotado el motivo, y redirige al
  login con `returnUrl` para volver donde estaba.
- **El detalle que da sentido a la regla:** el interceptor **no** llama a `localStorage.clear()`.
  Borra las cinco claves de sesión una a una y deja intacto `tsi.registro-accidente.draft`, el
  parte a medio escribir. El `clear()` era una línea más corta y se habría llevado por delante el
  trabajo del usuario justo cuando la regla dice que hay que conservarlo. **Verificado
  sustituyéndolo:** la prueba del borrador falla.
- **Tres cosas que a propósito NO dispara:** un `401` del propio login (ahí significa
  «credenciales incorrectas» y redirigir sería un bucle que tapa el mensaje real), un `403` (la
  sesión está viva; cerrarla expulsaría al usuario por pulsar donde no debía) y una respuesta
  correcta. El error se **relanza**, para que un componente que muestra su propio aviso no se
  quede en «cargando…» para siempre.

### PG-UI-004 — Validación duplicada, nunca delegada
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** dispersa

- **Regla:** toda validación del frontend existe también en el backend. El frontend valida para
  la **experiencia**; el backend valida para la **seguridad**. Una regla presente solo en el
  cliente se considera inexistente.
- **Prueba esperada:** para cada validación de formulario, una prueba de API que envíe el valor
  inválido **saltándose el frontend** y afirme `400`.

### PG-UI-005 — Reconexión de SSE
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `frontend/src/app/modules/seguimiento/services/seguimiento-sse.service.spec.ts`, `frontend/src/app/modules/despacho/services/despacho-sse.service.spec.ts`

- **Regla:** el canal SSE de seguimiento en tiempo real se reconecta tras una caída y no deja el
  mapa congelado mostrando posiciones obsoletas **como si fueran actuales**.
- **Hay dos canales, no uno.** `SeguimientoSseService` ya cumplía la regla con pruebas. El de
  **despacho** —la pantalla de una emergencia en curso— no, y su única prueba comprobaba que
  `streamDespacho()` devuelve algo con `.subscribe`: que un `Observable` es un `Observable`.
  Pasaba siempre y no cubría nada.
- **Dos defectos reales encontrados (2026-08-23):**
  1. Ante un error marcaba `offline` y **no reintentaba nunca**: la vista quedaba muerta hasta que
     alguien recargara, aunque la red volviera a los dos segundos.
  2. `complete` no estaba manejado, así que un cierre limpio del upstream dejaba el estado en
     `live` mostrando el último dato **como si fuera actual**. Nginx cierra streams largos sin
     error: ese es el caso habitual, no el raro.
- **El segundo es el que persigue este plan:** la pantalla no miente al fallar, miente al parecer
  que funciona.
- **Arreglo:** `streamResiliente()`, espejo del de seguimiento — reintento con backoff, aviso en
  cada transición, y parada al morir el consumidor (un reintento que sobrevive a la pantalla es
  una fuga).
- **Verificada la no-vacuidad:** quitando el manejo de `complete`, la prueba falla.

### PG-UI-006 — Accesibilidad
**Severidad:** Menor · **Estado:** ⚠️ Parcial · **Prueba:** `frontend/src/app/core/a11y/accesibilidad.spec.ts`

- **Regla:** las vistas críticas cumplen contraste, navegación por teclado, etiquetas de
  formulario y roles ARIA. Verificable con `axe`.
- ⚠️ **La regla se apoyaba en algo que no existe.** Decía «con `axe` en la suite E2E», y el
  proyecto **no tiene suite E2E**: ni Playwright ni Cypress. Llevaba desde el principio sin poder
  cumplirse, y el motivo no estaba escrito en ninguna parte.
- **Enfoque adoptado (2026-08-23):** `axe-core` sobre el DOM que Angular renderiza en Karma,
  aprovechando las 1423 pruebas que ya corren. Reglas `wcag2a` + `wcag2aa`, nombradas
  explícitamente: el conjunto por defecto de axe cambia entre versiones y podría relajarse solo.
- **Defecto real encontrado y corregido:** el marcador arrastrable del mapa de registro
  (`aria-command-name`, impacto *serious*). Leaflet lo renderiza focusable e interactivo, y sin
  nombre accesible un lector solo anunciaba que había un control — no que era la ubicación del
  accidente ni que podía moverse.
- **Queda `⚠️ Parcial`, no `✅`, y por eso:** este enfoque **no** ve el orden de tabulación entre
  pantallas, el foco tras navegar, ni el contraste real con los estilos globales cargados. Está
  declarado en `axe.helper.ts` para que nadie lea «accesibilidad ✅» y suponga más de lo
  comprobado. Cerrarla del todo exige el navegador con la aplicación entera.
- **Control de no-vacuidad:** una prueba comprueba que axe detecta una imagen sin `alt` y un campo
  sin etiqueta. Sin ella, un fallo de configuración daría «0 violaciones» en cualquier pantalla y
  la regla entera quedaría verde sin comprobar nada — que es exactamente cómo `PG-CFG-005` llevaba
  meses marcada como cubierta.

---

## 10. RENDIMIENTO, RESILIENCIA Y OBSERVABILIDAD

### PG-RES-001 — Presupuestos de latencia por motor y percentil
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `PerfTrace` en tests

Corrige la regla ambigua de la v1.0 ("200ms sobre 100.000 registros"), que no declaraba motor ni
percentil y por tanto no era verificable. Los umbrales concretos son los de
**`testing.md §Thresholds de Rendimiento`** (autoridad); aquí solo se fija la **forma**:

- **Regla:** todo presupuesto de latencia declara **motor**, **operación** y **percentil**
  (P95/P99). Un umbral sin percentil no es medible: aprueba o falla según el ruido de la máquina.
- **Regla:** la latencia analítica (ClickHouse, batch) y la operacional (Pinot, tiempo real)
  tienen presupuestos **distintos**; no se comparan entre sí.

### PG-RES-002 — Degradación ante caída de dependencias
**Severidad:** Bloqueante · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/seguridad/test_resiliencia.py`

- **Regla:** con Kafka, Pinot, ClickHouse, Azure Blob u OSRM caídos, el sistema responde con un
  error explícito y acotado (`503`), **nunca** con un dato incompleto presentado como completo,
  ni con un cuelgue indefinido. Todo cliente externo declara *timeout* y política de reintento.
- **Cubierto 2026-08-23:** todo cliente externo declara timeout, y OSRM uno **más corto** (3 s
  frente a 10 s) por estar en la cadena crítica — un despacho que tarda diez segundos en calcular
  ruta ya llegó tarde. Sin timeout, una dependencia lenta cuelga el hilo indefinidamente, que es
  peor que un fallo: no se distingue de un proceso ocupado.
- **Pendiente para ✅:** detener cada dependencia en caliente y comprobar que la respuesta es `503`
  explícito y no un dato parcial. Requiere parar contenedores durante la suite.

### PG-RES-003 — Arranque en orden y reintento
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_resiliencia.py`

- **Regla:** el orden documentado en `infrastructure.md` se respeta; un servicio que arranca antes
  que su dependencia reintenta en vez de morir.
- **Verificado 2026-08-23:** el compose declara `depends_on` con `condition: service_healthy` en
  los cuatro servicios encadenados. **La condición importa tanto como la dependencia**: sin ella se
  espera al arranque del contenedor, no a que acepte conexiones, y Kafka tarda segundos más — Pinot
  arrancaría, no encontraría el bróker y **se quedaría sin consumir en silencio**, que es
  exactamente `PG-OPE-001` provocado por el orden de arranque.

### PG-RES-004 — Sonda de salud honesta
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_resiliencia.py`

- **Regla:** el endpoint de salud verifica sus dependencias reales. Una sonda que devuelve `200`
  sin comprobar nada es **peor que no tenerla**: convierte una caída en un silencio — el
  orquestador no reinicia, nadie recibe alerta, y las peticiones siguen llegando a un proceso que
  no puede atenderlas.
- **Implementado 2026-08-23**: `GET /api/v1/salud` ejerce cada dependencia con una consulta real, y
  devuelve **503** si falla una esencial. Verificado tumbando Pinot a propósito.
- ⚠️ **Distinción deliberada entre esencial y accesorio.** Pinot y Kafka tumban la sonda; ClickHouse
  no. Su caída degrada los informes pero **no impide registrar un accidente ni despachar una
  unidad**, y marcar el servicio como indisponible provocaría un reinicio que no arregla nada y que
  sí interrumpe la cadena crítica.
- **Sin autenticación, a propósito:** la consulta el orquestador antes de que exista sesión. A
  cambio la respuesta solo da el nombre de la dependencia y el tipo de excepción — nunca rutas,
  tablas ni cadenas de conexión.

### PG-RES-005 — Prueba de carga sobre la cadena crítica
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `backend/tests/seguridad/test_carga_cadena_critica.py`

- **Regla:** carga concurrente con k6/Locust sobre registro → despacho, sosteniendo el P95
  declarado en `testing.md` y **sin pérdida de eventos** — el criterio de aprobación incluye que
  el 100% de los accidentes generados sea consultable al final.
- **Ejecutada por primera vez el 2026-08-23** contra el stack en marcha: 30 registros, 10
  concurrentes, autenticación real.
- ✅ **Sin pérdida de eventos.** Los 30 accidentes aceptados con `201` eran consultables tras la
  ingesta. Ese era el criterio crítico: un `201` es una promesa, y un reporte confirmado que
  después no existe rompe esa promesa **sin que nadie reciba un error**.
- ❌ **P95 = 708 ms frente a los 500 ms de `testing.md`.** Queda `⚠️ Parcial` por esto, con la
  prueba en `xfail(strict=True)` —no se ignora, y avisa en cuanto empiece a cumplirse— y la
  decisión registrada en `decisiones-pendientes.md`.
- **El matiz que casi cuesta un diagnóstico falso:** desde el host el P95 daba 1477 ms; desde
  dentro del contenedor, 857 ms. Esos ~600 ms son el puente de red de Docker Desktop en Windows,
  no la aplicación.
- **Causa parcial encontrada:** el contenedor sirve con `manage.py runserver`, el servidor de
  desarrollo. Con gunicorn el P95 baja a 708 ms — sigue incumpliendo, pero por menos.
- **Corrección del enunciado:** se usa `ThreadPoolExecutor` en vez de k6/Locust. No añade
  dependencia ni runtime nuevos, y la verificación de no-pérdida —reconsultar cada id registrado—
  es lógica de programa que en k6 habría que escribir igual, en otro lenguaje.

### PG-RES-006 — Migraciones reversibles
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_migraciones_reversibles.py`

- **Regla:** todo script de `database/` declara su reversión y se ensaya contra una copia con
  volumen realista antes de aplicarse. Una migración que solo se probó en una base vacía no está
  probada.
- **Por qué pesa más aquí que en una base con transacciones:** las tablas son upsert por clave y
  las migraciones **republican la fila entera** —hay que hacerlo, publicar solo la columna que
  cambia dejaría el resto en su valor por defecto—. Una migración equivocada no corrompe un campo:
  entierra el estado anterior de la fila completa, y Pinot no guarda la versión previa.
- **Lo que se encontró (2026-08-23):** de las 9 migraciones, **3 escribían sin respaldo previo**
  (`migra_fecha_inicio_contrato`, `migra_severidades_plan_a_idseveridad`, `migra_estadocredencial`)
  y 2 no documentaban su vuelta atrás. El patrón correcto existía, pero copiado a mano en cada
  script — así que las que se lo saltaron no rompieron nada visible: simplemente no tenían red.
- **Extraído a `database/_reversion.py`:** `respaldar()` exporta **y relee** el fichero antes de
  darlo por bueno (un disco lleno da un respaldo truncado que parece correcto hasta el día que
  hace falta) y aborta con los datos aún intactos si no cuadra.
- ⚠️ **Un salto silencioso encontrado en la propia prueba.** El detector de «escribe» solo miraba
  `publish(`, así que `migra_plan_programado.py` —que escribe con un `POST` al controller— se
  saltaba las tres comprobaciones **dándose por solo-lectura**. Se añadió un aserto que falla si
  alguna migración deja de reconocerse como escritora, en vez de callar.
- **Las 2 exenciones se declaran con su motivo** (`SIN_RESPALDO_JUSTIFICADO`): tabla vacía en un
  caso, ficheros versionados con git como respaldo en el otro. Una exención sin motivo escrito es
  indistinguible de un descuido seis meses después.

---

## 11. COMPUERTAS DE CALIDAD Y AUTOMATIZACIÓN

> **La carencia de mayor impacto práctico del proyecto:** no existe `.github/workflows/`. Hay
> **674 pruebas de backend y 250 de frontend** cuya ejecución depende de que alguien se acuerde.
> Una suite que no corre sola equivale, en términos de protección real, a no tener suite.

### PG-CI-001 — Pipeline de integración continua
**Severidad:** Bloqueante · **Estado:** ✅ Cubierta · **Prueba:** `.github/workflows/ci.yml`, `.github/workflows/integracion.yml`

- **Regla:** el pipeline previsto en `testing.md §Integración Continua` existe y bloquea.
- **Diseño en dos velocidades:** `ci.yml` corre en cada push (`rapidas`: solo `-m unit`, ~15 s
  locales) y lo caro en PR y `main`. Si el ciclo de retroalimentación es lento se empieza a hacer
  push sin esperarlo, y el pipeline deja de proteger.
- **`integracion.yml` va aparte, semanal:** levanta Zookeeper + Kafka + los tres procesos de
  Pinot, minutos antes del primer test. Es el único sitio donde pueden correr `PG-OPE-001`,
  `PG-OPE-002` y `PG-ANA-005` — reglas que un mock no puede probar por definición.
- **Jobs:** `rapidas`, `configuracion` (`PG-CFG-004`/`005`), `estatico` (`PG-CI-004`), `backend`
  con cobertura, `frontend` (`ng test` + `ng build`), `dependencias` (`PG-SEC-009`).
- **Pendiente de incorporar:** conformidad OpenAPI de los 37 contratos (`PG-API-001`) y la suite
  de aislamiento multi-tenant (`PG-SEC-001`) — ninguna de las dos existe todavía.
- ⚠️ **Deuda declarada:** el job `backend` excluye dos ficheros de permisos tácticos
  (`test_permisos_red_operativa.py` y `test_emergencias_compuestos_views.py`), **42 fallos
  preexistentes** con una causa compartida: la petición llega sin autenticar y devuelve `401`
  donde se espera `403` o `404`. **Caduca el 2026-09-23**; ver `decisiones-pendientes.md` #50. Un
  paso informativo no bloqueante los sigue ejecutando en cada run para que su estado no
  desaparezca del radar.

### PG-CI-002 — Cobertura como compuerta, no como informe
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `.github/workflows/ci.yml` (`--cov-fail-under=90`)

- **Regla:** los umbrales de `testing.md §Cobertura Objetivo` **fallan el build** al no
  alcanzarse. Publicar el porcentaje sin bloquear no cambia el comportamiento de nadie.
- **Implementado 2026-08-23** con `--cov-fail-under=90`. El umbral es 90 y no el 80 de `testing.md`
  a propósito: la medida real fue **93 %**, y una compuerta al 80 permitiría perder trece puntos en
  silencio. Este plan puede ser más estricto que la autoridad si lo justifica (§0.1).

### PG-CI-003 — Cero pruebas intermitentes o desactivadas
**Severidad:** Mayor · **Estado:** ⚠️ Parcial · **Prueba:** `.github/workflows/ci.yml` (sin exclusiones)

- **Regla:** ninguna prueba puede quedar marcada `skip`/`xfail` sin un enlace a la entrada de
  `decisiones-pendientes.md` que la justifique y una fecha de caducidad. Una prueba intermitente
  se arregla o se elimina — **nunca se reintenta**: entrena al equipo a ignorar fallos reales.
- **2026-08-23:** el gate corre **sin exclusiones**. Los 42 fallos de permisos tácticos se
  resolvieron (les faltaba la fixture que mockea Pinot, ver `changelog.md` C3) y 3 pruebas que
  consultan ClickHouse real pasaron a `integration`, que es donde les corresponde.
- **Corolario aprendido:** una prueba lenta que falla por red es indistinguible de una que falla
  por lógica, y su mensaje apunta al sitio equivocado. **Sospechar del tiempo de ejecución antes
  que del aserto.**
- **Pendiente:** automatizar la regla — hoy nada impide añadir un `skip` sin justificación ni
  fecha. Y `playwright.config.ts` declara `retries: 2` en CI, que contradice el «nunca se
  reintenta» de esta regla; conviene decidir si la excepción para E2E se acepta y se justifica.

### PG-CI-004 — Análisis estático
**Severidad:** Menor · **Estado:** ⚠️ Parcial · **Prueba:** `.github/workflows/ci.yml` (job `estatico`)

- **Regla:** Ruff (Python) y ESLint + Prettier (TypeScript) corren en CI y fallan el build.
- **Hoy corren pero no bloquean** (`|| true`): ninguna de las tres se ha pasado nunca sobre este
  árbol, y hacerlas bloqueantes de golpe dejaría el pipeline en rojo desde el primer run. Retirar
  los `|| true` en cuanto el árbol esté limpio. Es deuda anotada en el propio workflow, no un
  olvido.

### PG-DOC-001 — Toda regla nueva nace con estado
**Severidad:** Mayor · **Estado:** ✅ Cubierta · **Prueba:** `backend/tests/seguridad/test_coherencia_plan.py`

- **Regla:** ninguna regla se añade a este plan sin ID, severidad, estado y prueba. Una regla en
  `❌ Pendiente` con severidad `Bloqueante` debe tener entrada en `decisiones-pendientes.md`.

### PG-DOC-002 — Coherencia del rol de Pinot en la documentación
**Severidad:** Menor · **Estado:** ✅ Cubierta · **Prueba:** `.specify/docs/infra/infrastructure.md` §3 (corregido)

- **Corregido 2026-08-23.** `infrastructure.md §3` rotulaba a Pinot como «Base de datos
  analítica», contradiciendo a su propio §1 y confundiéndolo con ClickHouse. Ahora dice
  **operacional**, y se añadió la fila de ClickHouse que faltaba, marcada como **derivada**.
- **Corregido también:** `testing.md` daba el E2E por «futuro» con Cypress, cuando el repositorio
  usa **Playwright** con 4 suites desde hace tiempo. La pirámide y los comandos ya lo reflejan.
- Ambas correcciones dejan anotado **qué decía antes**: una deriva silenciosamente arreglada se
  repite, porque nadie sabe que existió.

---

## 12. RESUMEN DE COBERTURA

| Área | Reglas | ✅ | ⚠️ | ❌ |
|---|---|---|---|---|
| Configuración (`PG-CFG`) | 5 | 4 | 1 | 0 |
| Operacional (`PG-OPE`) | 8 | 7 | 1 | 0 |
| Analítica (`PG-ANA`) | 6 | 4 | 2 | 0 |
| API (`PG-API`) | 5 | 1 | 4 | 0 |
| Negocio (`PG-NEG`) | 5 | 3 | 2 | 0 |
| Seguridad (`PG-SEC`) | 10 | 6 | 4 | 0 |
| Frontend (`PG-UI`) | 6 | 2 | 4 | 0 |
| Resiliencia (`PG-RES`) | 6 | 3 | 3 | 0 |
| CI y documentación (`PG-CI`, `PG-DOC`) | 6 | 4 | 2 | 0 |
| **Total** | **57** | **34** | **23** | **0** |

> Los totales de esta tabla se verifican contando las cabeceras de regla del propio documento.
> Si se editan a mano, mienten: ya ocurrió una vez el 2026-08-23 (decían 10/19/28 con 8/18/31
> reales) y se corrigió al recontar.

### 12.1. Por severidad — la lectura que importa

| Severidad | Reglas | ✅ | ⚠️ | ❌ |
|---|---|---|---|---|
| **Bloqueante** (impide desplegar) | 18 | 10 | 8 | 0 |
| Mayor (impide cerrar el módulo) | 35 | 23 | 12 | 0 |
| Menor (deuda planificada) | 4 | 1 | 3 | 0 |

**Ninguna regla bloqueante sigue en ❌.** Las 18 tienen prueba; 8 de ellas solo parcial, que es
donde queda el trabajo. Ese es el número que decide si
el sistema puede considerarse validado, no el 8/57 de la tabla anterior:

`PG-CFG-003` · `PG-CFG-005` · `PG-OPE-001` · `PG-OPE-002` · `PG-ANA-001` · `PG-ANA-003` · `PG-API-002` · `PG-NEG-002` · `PG-SEC-001` · `PG-SEC-002` · `PG-SEC-005` · `PG-SEC-007` · `PG-RES-002`

**Lectura honesta:** 674 pruebas de backend y 250 de frontend cubren bien el comportamiento
funcional de cada módulo, pero solo 17 de 57 reglas adversariales están cubiertas de extremo a
extremo. **La suite actual demuestra que el sistema hace lo que debe; casi no demuestra que no
haga lo que no debe.** Esa es la brecha que este plan existe para cerrar.

### 12.2. Orden de ataque recomendado

1. ~~**`PG-CI-001`**~~ — hecho 2026-08-23.
2. ~~**`PG-CFG-001`, `PG-CFG-002`**~~ — hecho 2026-08-23. Queda `PG-CFG-004` (`check --deploy`).
3. **`PG-SEC-001`** — el mayor riesgo real del sistema.
4. **`PG-OPE-001`, `PG-OPE-002`** — el fallo silencioso más probable, ya observado.
5. **`PG-ANA-001`** — la única regla que detecta un informe falso pero plausible.
6. El resto, por severidad decreciente.

---

## 13. REGISTRO DE CAMBIOS (Changelog SDD de este plan)

> Las correcciones de **código** van a `.specify/docs/changelog.md`. Aquí solo se registra cuándo
> y por qué cambió **este plan**.

### 2.0.0 — 2026-08-23 — Reestructuración completa
**Detonante:** revisión de la plantilla v1.0 contra el repositorio real.

**Brechas encontradas en la v1.0:**
- Describía una arquitectura genérica de tres capas; TSI tiene Kafka, Pinot, ClickHouse, Airflow,
  OSRM, SSE y 37 contratos OpenAPI, **ninguno mencionado**.
- **Cero reglas de seguridad**: sin IDOR, sin autorización vertical, sin integridad de JWT, sin
  inyección, sin subida de archivos, sin datos sensibles.
- **Cero reglas de configuración**, pese a `DJANGO_DEBUG=true`, `SECRET_KEY` de desarrollo y
  `CLICKHOUSE_PASSWORD=tactico` como valores por defecto sin guarda.
- Regla de `DELETE` (v1.0 §2.1) contradicha por ~25 scripts de `database/` → reescrita como
  `PG-OPE-008`, acotada al camino de la API.
- Umbral "200ms / 100.000 registros" sin motor ni percentil → sustituido por `PG-RES-001`, que
  delega los valores a `testing.md` y fija la forma exigible.
- Regla arquitectónica de componentes *standalone* mezclada con verificación → su autoridad
  vuelve a `design-system.md`; aquí queda solo el cómo verificar (`PG-UI-001`).
- Placeholders `[Nombre de tu Sistema]` y `[Fecha]` sin sustituir.

**Añadido:** IDs estables, severidad, estado de cobertura y ruta de prueba por regla; matriz de
riesgo; secciones de configuración, capa analítica, seguridad, resiliencia y compuertas de CI;
resumen de cobertura y orden de ataque.

**Corrección de una afirmación previa:** una revisión intermedia dio por desprotegidos los
secretos de la demo interactiva. No lo están: `apps/ventas_crm/demo_tokens.py:34` ya aborta si
conservan su valor por defecto fuera de debug, y hay prueba que lo cubre. Los que sí carecen de
guarda son `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `CLICKHOUSE_PASSWORD` (`PG-CFG-001/002`).

### 2.0.2 — 2026-08-23 — Pipeline de CI montado (`PG-CI-001`)
`.github/workflows/ci.yml` (6 jobs) y `integracion.yml` (semanal). Cierra `PG-CI-001`,
`PG-CFG-004` y `PG-SEC-009`; deja `PG-CI-004` y `PG-SEC-008` en parcial. Detalle en
`.specify/docs/changelog.md`, entrada **C2 (2026-08-23)**.

Dos hallazgos del propio montaje, que es de lo que sirve activar una compuerta:
- `check --deploy` destapó **5 advertencias de seguridad reales** (HSTS, redirección SSL, cookies
  de sesión y CSRF sin `Secure`). Corregidas — ver `PG-SEC-008`.
- La suite completa tiene **42 fallos preexistentes**, repartidos por igual (21 + 21) entre
  `test_permisos_red_operativa.py` y `test_emergencias_compuestos_views.py`, todos por la misma
  causa: petición sin autenticar, `401` donde se espera `403` o `404`. Ajenos a este trabajo,
  verificado con `git stash` sobre ambos. Excluidos del gate con caducidad 2026-09-23 —
  `decisiones-pendientes.md` #50.

### 2.0.1 — 2026-08-23 — `PG-CFG-001/002/003` implementadas
Primer tramo del orden de ataque (§12.1, punto 2). Registro central de secretos en
`backend/core/config/secretos.py`, guardas invocadas desde `settings.py`, y 20 pruebas en
`backend/tests/test_configuracion_segura.py`. Detalle completo, causa y efecto verificado en
`.specify/docs/changelog.md`, entrada **C1 (2026-08-23)**.

Hallazgo lateral del mismo trabajo: `backend/config/keys/` no estaba en `.gitignore`. Corregido.

### 1.0.x — Anterior
- Bug detectado: se ingresaban fechas de nacimiento futuras.
  - Corrección: regla `fecha_nacimiento <= fecha_actual` → absorbida por `PG-API-004`.
