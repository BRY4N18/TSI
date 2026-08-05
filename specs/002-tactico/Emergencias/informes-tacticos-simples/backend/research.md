# Phase 0 Research: Informes Tácticos Simples de Emergencias (Backend)

## 1. App Django: nueva vs. extender apps existentes

**Decision**: Crear `backend/apps/informes_tacticos/` como app nueva y aislada.

**Rationale**: `accidentes`, `despacho` y `seguimiento` están organizadas alrededor de sus casos de uso de escritura (registrar, despachar, cerrar) con Kafka como canal único. Los 16 informes de esta feature son lectura pura de agregación, sin relación con esos flujos. Añadir endpoints de reporting a esas apps mezclaría dos razones de cambio distintas (Maintainability, principio de responsabilidad única ya aplicado en el resto del proyecto — ver `conventions-code.md`).

**Alternatives considered**: Extender cada app con un submódulo `informes/` propio (3 submódulos en vez de 1 app) — descartado porque el frontend consume los 16 informes desde 3 workpanels de un mismo módulo conceptual ("Informes Tácticos"), y una sola app con 3 repositorios internos refleja mejor esa agrupación sin triplicar el boilerplate de Django (`apps.py`, `urls.py`, registro en `INSTALLED_APPS`).

## 2. Reutilización de `PinotClient`

**Decision**: Reutilizar `backend/core/pinot/client.py` sin modificarlo. Cada repositorio de `informes_tacticos` instancia `PinotClient` igual que los repositorios de `accidentes`/`despacho`.

**Rationale**: Ya resuelve exactamente lo que FR-003 exige: `LIMIT` explícito por defecto (`DEFAULT_QUERY_LIMIT`), interpolación segura de parámetros (`_quote_literal`), coerción de tipos. Escribir un cliente nuevo duplicaría esa lógica ya probada.

**Alternatives considered**: Ninguna — es la única vía de acceso a Pinot ya establecida en el proyecto; introducir una segunda violaría Compatibility.

## 3. Forma de la respuesta de cada informe

**Decision**: Cada endpoint devuelve una lista de filas agregadas bajo `data`, con `meta` describiendo el período/filtros efectivamente aplicados (no paginación cursor, porque el volumen de un resultado agregado — decenas de grupos, no miles de filas — no lo requiere).

**Rationale**: El formato de éxito estándar del proyecto es `{ "data": {...}, "meta": {...} }` (`api-standards.md`). La paginación por cursor documentada ahí es para listados de detalle (potencialmente miles de filas); un resultado de `GROUP BY` acotado por dimensión (severidad, zona, unidad) no crece sin límite de la misma forma, así que `meta` se reutiliza para describir el período/filtro aplicado en vez de un cursor.

**Alternatives considered**: Paginación cursor idéntica a los listados de detalle — descartada por sobre-ingeniería: ninguno de los 16 informes agrupa por una dimensión con cardinalidad no acotada (el peor caso, "ranking de ubicaciones", ya declara su propio `LIMIT N` como parte del informe, no como paginación).

## 4. Autorización: rol Operador vs. Supervisor

**Decision**: Los 16 endpoints de esta spec son accesibles para ambos roles, Operador y Supervisor (FR-007), reutilizando `backend/core/auth/permissions.py`. La restricción a solo Supervisor se aplica en la spec de informes compuestos (`../../informes-tacticos-compuestos/`), no aquí.

**Rationale**: La spec de backend (FR-007) ya lo declaró así — son indicadores operativos de uso diario, no de gestión estratégica exclusiva. Documentado aquí para que el research quede alineado 1:1 con la spec.

**Alternatives considered**: Ninguna — decisión ya tomada en la fase de especificación, research solo la confirma contra el mecanismo real de permisos existente.

## 5. Agrupación de período (día/semana/mes)

**Decision**: El parámetro de período acepta una granularidad (`dia`, `semana`, `mes`) más un rango de fechas; el `GROUP BY` de cada consulta usa la expresión de truncado de fecha correspondiente en SQL de Pinot (`DATETRUNC`).

**Rationale**: Es la función estándar de Pinot para agrupar timestamps por granularidad sin traer filas crudas a Python (cumple FR-003: filtros/orden en SQL, no en Python).

**Alternatives considered**: Agrupar en Python después de traer filas por día — descartado explícitamente por la regla vinculante de `infrastructure.md` §4 ("Filtros, orden y paginación viven en el SQL, no en Python").
