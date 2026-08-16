# Quickstart — Informes Tácticos Simples de Cuentas y Clientes (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Cómo levantar el entorno y comprobar que los ocho listados hacen lo que la spec dice. Esta guía
**valida**, no implementa: el detalle de construcción va en `tasks.md`.

---

## 1. Prerrequisitos

**No hace falta ClickHouse.** Es la razón de empezar por los listados: todo sale de Pinot.

```bash
docker network create pipeline-net
```

```bash
docker compose -f docker/docker-compose.infraestructura.yml up -d
```

```bash
docker compose -f docker/accidentes.yml up -d
```

- API: **http://localhost:8000** · Consola de Pinot: **http://localhost:9000**

Tras cambiar código backend, **hay que redesplegar** — el contenedor sirve el código viejo:

```bash
docker cp backend/apps accidentes-django:/app/ && docker cp backend/core accidentes-django:/app/ && docker restart accidentes-django
```

---

## 2. Credenciales para las pruebas

Contraseña compartida `password123` (`backend/scripts/_demo_seed_common.py`).

| Correo | Rol | Para qué |
|---|---|---|
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Los 8 listados |
| `roberto.paredes.director@demo.tsi.com` | Director Tecnológico | L8 (accesos técnicos) |
| `sofia.castro.operador@demo.tsi.com` | Operador | Comprobar que recibe **403** en los 8 |

Obtener token:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login -H 'Content-Type: application/json' -d '{"gmail":"carlos.mendoza.admin@demo.tsi.com","contrasena":"password123"}'
```

---

## 3. Comprobación por escenario

### 3.1 Los ocho responden

```bash
for r in solicitudes-alta-pendientes onboarding-incompleto cuentas-por-estado transferencias-propiedad usuarios-por-rol sesiones-activas credenciales-temporales accesos-tecnicos; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/$r"; done
```

**Esperado:** ocho `200`. Un listado sin filas devuelve `200` con `data: []` — **nunca 404** (SC-007).

### 3.2 El período es opcional donde corresponde, y prohibido donde no *(FR-012, FR-013)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/cuentas-por-estado?desde=2026-01-01&hasta=2026-08-14"
```

**Esperado:** `400` — es un listado de estado actual y no admite rango.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/transferencias-propiedad"
```

**Esperado:** `200` con el histórico completo paginado. Es el único de los ocho que acepta rango, y
omitirlo **no** es un error.

### 3.3 Ningún identificador interno, ningún dato sensible *(SC-003, research D7)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/credenciales-temporales" | grep -o 'contrasena\|idcredencial\|token' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. Repetir contra `sesiones-activas` (buscando `token`) y `accesos-tecnicos`
(buscando `contrasena`). **Si alguno aparece, es un fallo de seguridad, no un detalle cosmético.**

Y en el sentido inverso — que sí llegue el nombre:

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/usuarios-por-rol" | head -c 400
```

**Esperado:** `roles` con nombres (`"Administrador"`), nunca `idrol`.

### 3.4 Un usuario con dos roles es una fila *(User Story 1, escenario 2)*

Buscar en la respuesta de `usuarios-por-rol` un usuario con más de un rol.

**Esperado:** una sola entrada con `roles` de dos elementos. **Dos entradas con el mismo correo es el
defecto que research D4 previene.**

### 3.5 El usuario sin rol aparece *(FR-023)*

**Esperado:** al menos una entrada con `roles: []` si existe tal usuario. Que desaparezca del listado
sería el fallo, no lo contrario.

### 3.6 La paginación no repite ni salta filas *(SC-005)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/cuentas-por-estado?limit=2"
```

Tomar `meta.pagination.cursor` y pedir la siguiente página con `&cursor=<valor>`. Repetir hasta que
`cursor` sea `null`.

**Esperado:** la concatenación de páginas contiene **cada cuenta exactamente una vez**. Comparar con
el total pidiendo `limit=500` de una vez.

### 3.7 Las cuentas dadas de baja siguen apareciendo *(User Story 3, escenario 2)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/cuentas-por-estado?estado=Dado%20de%20baja"
```

**Esperado:** las cuentas de baja aparecen con su razón social intacta. La baja es lógica.

> **Corregido el 2026-08-15.** Este comando decía `?estado=Baja`. Ese valor **no existe**: el estado
> canónico es `Dado de baja` (`cliente_repository.py`). Con el valor viejo la respuesta es `400`
> nombrando los válidos — que es el comportamiento correcto de FR-015, pero no lo que este paso
> quiere comprobar.

### 3.8 El límite no se recorta en silencio *(FR-016)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/cuentas-por-estado?limit=5000"
```

**Esperado:** `400` nombrando el máximo. **Devolver 500 filas calladamente sería el defecto.**

### 3.9 Un filtro inválido se rechaza, no se ignora *(FR-015)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/cuentas-clientes/cuentas-por-estado?estado=Vigente"
```

**Esperado:** `400` nombrando los valores válidos. Devolver el listado completo como si no se hubiera
filtrado es el fallo que este caso previene.

### 3.10 El control de acceso *(FR-017 a FR-020, SC-006)*

Con el token del **Operador**, los ocho listados: **403** en los ocho, sin filtrar ninguna fila.

Con el token del **Director Tecnológico**: `accesos-tecnicos` responde **200** (CU-O08).

---

## 4. Suites

```bash
cd backend && python -m pytest apps/cuentas_clientes core/informes -q
```

**Línea base antes de empezar: 1673 passed, 2 skipped.** Ninguna prueba existente debe romperse —
en particular las de `apps/informes_tacticos`, que **no se toca** (research D1).

> **Verificado el 2026-08-15 (T002), antes de tocar una sola línea:** `cd backend && python -m pytest -q`
> → **1673 passed, 2 skipped en 120,08 s**. Coincide con lo previsto. Los dos omitidos son
> `test_configuracion_cuenta_service.py` (CU-O12 retirado) y `test_registro_cuenta_service.py`
> (CU-O01 retirado), ambos omitidos a propósito y ajenos a este trabajo.

```bash
cd backend && python -m pytest apps/informes_tacticos -q
```

**Esperado: verde sin cambios.** Si esta suite se mueve, el aislamiento del piloto falló.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Una solicitud recién aprobada puede seguir apareciendo en
  `solicitudes-alta-pendientes`. **No es un fallo**: no reintentar ni esperar artificialmente.
- **El doble en memoria de `conftest.py` da confianza falsa.** No valida tipos ni centinelas. Las
  pruebas de D3 (centinelas) y D7 (columnas sensibles) deben mirar el código o el esquema, no el
  doble.
- **Pinot recorta a 10 filas sin avisar** si la consulta no declara `LIMIT`. Ya está neutralizado en
  `core/pinot/client.py:79`, pero cada consulta debe declarar el suyo igualmente.

---

## 6. ⚠️ `transferencias-propiedad` devolverá vacío contra el stack real

**El endpoint está completo y verificado; el dato que debe leer no lo escribe nadie.**

`Fact_HistorialTransferenciaPropiedad` está declarada en `database/esquemas.json`, pero el flujo
operativo de transferencia (`TransferenciaPropiedadService.transferir`) **solo deja rastro en la
bitácora de auditoría** (`AuditService.log_transferencia`); no publica en esa tabla.

Consecuencia: el paso 3.1 devolverá `200` con `data: []` para este listado, y no es un fallo del
informe. Escribir el hecho es trabajo del **módulo operativo (CU-O15)**, no de esta spec — el plan
fija explícitamente que `apps/cuentas_clientes` se extiende *sin tocar su lógica operativa*.

Anotado en [`decisiones-pendientes.md`](../../../../../decisiones-pendientes.md). Las pruebas del
piloto siembran la tabla directamente, así que la corrección del endpoint sí queda demostrada.

---

## 7. Estado de la verificación — 2026-08-15

| Comprobación | Cómo | Estado |
|---|---|:--:|
| Los 8 responden `200` con su envelope | `test_informes_openapi_conforme.py`, contra el propio OpenAPI | ✅ |
| Ningún secreto ni identificador sale | `test_informes_acceso_sin_secretos.py` (respuesta **y** código fuente) | ✅ |
| Paginación sin repetir ni saltar filas | `test_informes_paginacion_integridad.py`, los 8 recorridos completos | ✅ |
| `limit` sobre el máximo → `400` | `test_informes_limite.py` | ✅ |
| Rango rechazado en 7, opcional en 1 | `test_informes_transferencias_rango_opcional.py` | ✅ |
| Centinelas como ausencia | `test_informes_centinelas.py`, contra `_coerce_value` y `formato.py` | ✅ |
| Control de acceso y autoridad acotada | `test_informes_acceso_permisos.py` | ✅ |
| Aislamiento de `apps/informes_tacticos` | suite completa, verde sin cambios | ✅ |
| **Recorrido de §3 contra el stack Docker levantado** | manual, requiere `docker compose up` | ⏳ **pendiente** |

La última fila es la única que no se puede cubrir con la suite: necesita Pinot real, y es además
donde aparecerían las diferencias que el doble en memoria no reproduce (tipos y centinelas).
