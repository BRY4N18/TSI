# Quickstart — Informes Tácticos Simples de Ventas y CRM (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Cómo comprobar que los cuatro listados hacen lo que la spec dice. Esta guía **valida**, no
implementa.

---

## 1. Prerrequisitos

**No hace falta ClickHouse.**

```bash
docker compose -f docker/docker-compose.infraestructura.yml up -d
```

```bash
docker compose -f docker/accidentes.yml up -d
```

Tras cambiar backend, redesplegar — el contenedor sirve código viejo:

```bash
docker cp backend/apps accidentes-django:/app/ && docker cp backend/core accidentes-django:/app/ && docker restart accidentes-django
```

---

## 2. Credenciales

Contraseña compartida `password123`.

| Correo | Rol | Para qué |
|---|---|---|
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Ver todo; filtrar por ejecutivo |
| `lucia.ramos.ventas@demo.tsi.com` | Gerente de Ventas | **Comprobar el acotamiento** |
| `sofia.castro.operador@demo.tsi.com` | Operador | Comprobar el 403 |

> **Hace falta un segundo Gerente con cartera propia** para probar SC-001 y SC-002. Si no existe en
> los datos de demo, sembrar uno y asignarle al menos un prospecto: **sin dos carteras pobladas a la
> vez, el acotamiento no se puede verificar de verdad.**

---

## 3. Comprobación por escenario

### 3.1 Los cuatro responden

```bash
for r in prospectos reasignaciones demos-activas notificaciones-enviadas; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/$r"; done
```

**Esperado:** cuatro `200`. Sin filas, `200` con `data: []` — nunca `404`.

### 3.2 El acotamiento por titularidad *(SC-001 — el escenario central)*

Con el token del **Gerente de Ventas**:

```bash
curl -s -H "Authorization: Bearer $TOKEN_GERENTE" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos?limit=500"
```

**Esperado:** solo sus prospectos, y `meta.acotado_a = "propios"`. Contrastar con el Administrador:
el conteo del Gerente debe ser **estrictamente menor** si hay otra cartera poblada. Si coinciden,
**el acotamiento no está aplicándose** — comprobar antes que el otro Gerente tenga prospectos.

### 3.3 Pedir la cartera ajena es una negativa, no una sustitución *(SC-002)*

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN_GERENTE" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos?ejecutivo=<ID_DE_OTRO>"
```

**Esperado:** `403` **sin ninguna fila**. Devolver la cartera propia con `200` sería el defecto que
FR-008 previene: el solicitante creería estar viendo lo que pidió.

Con el Administrador, la misma petición responde `200` con los prospectos de ese ejecutivo.

### 3.4 Perdido no es lo mismo que inactivo *(research D1 — el defecto más caro de este módulo)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos?estado=perdido"
```

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos?estado=convertido"
```

**Esperado:** conjuntos **disjuntos**. Un prospecto convertido —que es un éxito— **no puede aparecer
en el listado de perdidos**. Con un prospecto de cada clase sembrados, cada listado devuelve
exactamente uno.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos?estado=inactivo"
```

**Esperado:** `400` nombrando los tres valores válidos.

### 3.5 Las demos activas y la página corta *(research D3)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/demos-activas"
```

**Esperado:** solo demos con expiración futura, cada una con sus `dias_restantes`. Una demo ya
expirada **no aparece**, aunque su fecha sea de hoy.

**Puede devolver menos filas que el `limit`.** No es un fallo: `has_next` manda. Verificarlo
sembrando una demo que expire hoy pero ya pasada.

Prueba del formato mixto: sembrar dos demos con la misma fecha, una con sufijo `Z` y otra con
`+00:00`. **Ambas deben aparecer o no aparecer juntas.** Si solo sale una, la comparación de texto
se coló en la consulta.

### 3.6 Sin datos de contacto *(research D4)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos" | grep -o 'gmail\|telefono' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`.

### 3.7 Lo que se muestra son nombres, no identificadores *(SC-005)*

**Esperado:** `ejecutivo` con el nombre de la persona, nunca `idusuario`. Y un prospecto sin
ejecutivo **aparece** con el campo ausente, no se omite (FR-020).

### 3.8 El estado de envío no se expone

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/notificaciones-enviadas" | grep -o 'estado_envio' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. Ningún proceso escribe esa columna; devolverla sugeriría que significa algo.

### 3.9 Rango opcional donde corresponde *(FR-015)*

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/prospectos?desde=2026-01-01&hasta=2026-08-14"
```

**Esperado:** `400` — es un listado de estado actual.

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/ventas-crm/reasignaciones"
```

**Esperado:** `200` con el histórico completo. Omitir el rango **no** es un error.

### 3.10 Control de acceso *(FR-011, SC-002)*

Con el token del **Operador**: los cuatro listados responden **403**.

---

## 4. Suites

```bash
cd backend && python -m pytest apps/ventas_crm core/informes -q
```

```bash
cd backend && python -m pytest apps/informes_tacticos apps/cuentas_clientes -q
```

**Esperado: verde sin cambios.** El segundo comando es el guardián: `core/informes/` gana una pieza
nueva en este módulo, y si eso rompe el piloto o los 19 informes agregados, la ampliación no fue
aditiva.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Un prospecto recién reasignado puede seguir mostrando su ejecutivo
  anterior. **No es un fallo.**
- **El doble en memoria no reproduce los dos problemas de este módulo.** No distingue perdido de
  convertido ni los formatos mixtos de fecha. Las pruebas de D1 y D3 deben mirar el código o el
  esquema, no el doble.
- **Sin dos carteras pobladas, el acotamiento pasa cualquier prueba.** Es el error más fácil de
  cometer aquí: con un solo Gerente con prospectos, filtrar y no filtrar dan el mismo resultado.

---

## 6. La siembra que hace real la comprobación *(añadido el 2026-08-15)*

Los pasos §3.2, §3.3 y §3.4 **no prueban nada sin datos preparados**. `seed_demo_prospectos.py`
siembra una sola cartera, y con una sola cartera filtrar y no filtrar dan el mismo resultado.

```bash
docker exec accidentes-django python /app/scripts/seed_demo_ventas_tactico.py
```

Añade, de forma aditiva y sin tocar el seed existente:

| Caso | Para qué paso |
|---|---|
| **Segundo gerente con cartera propia** (`pablo.andrade.ventas@demo.tsi.com`) | §3.2 y §3.3 — sin él, el acotamiento pasa aunque no exista |
| Un **perdido** y un **convertido** en esa cartera | §3.4 — los dos tienen `activo = false` |
| Tres demos con **la misma fecha y distinto sufijo** (`Z`, `+00:00`, sin zona) | §3.5 — deben salir o no salir juntas |
| Una demo **expirada hoy más temprano** y otra **sin fecha** | §3.5 — página corta y demo no activa |
| Una notificación dirigida al segundo gerente | §3.8 y el acotamiento por destinatario |

Contraseña `password123`, como el resto de cuentas demo.

---

## 7. Estado de la verificación — 2026-08-15

| Comprobación | Cómo | Estado |
|---|---|:--:|
| Los 4 responden con su envelope y `acotado_a` | `test_informes_openapi_conforme.py`, contra el propio OpenAPI | ✅ |
| Acotamiento real, con **dos carteras pobladas** | `test_informes_cartera_acotamiento.py` | ✅ |
| Pedir lo ajeno es `403` sin filtrar filas | `test_informes_cartera_titularidad_ajena.py` | ✅ |
| Perdido ≠ convertido (datos **y** condición SQL) | `test_informes_cartera_perdido_vs_convertido.py` | ✅ |
| Los tres formatos de fecha se tratan igual | `test_informes_demos_formato_mixto.py` | ✅ |
| Página corta y recorrido completo por cursor | `test_informes_demos_pagina_corta.py` | ✅ |
| Sin datos de contacto (respuesta **y** código) | `test_informes_cartera_sin_contacto.py` | ✅ |
| `estado_envio` no se expone | `test_informes_notificaciones_acotamiento.py` | ✅ |
| Rango opcional donde corresponde | `test_informes_asignacion_rango.py` | ✅ |
| `limit` sobre el máximo → `400` | `test_informes_limite.py` | ✅ |
| Ampliación de `core/informes/` **aditiva** | suite completa: piloto y agregados sin moverse | ✅ |
| **Recorrido de §3 contra el stack Docker levantado** | manual, requiere `docker compose up` | ⏳ **pendiente** |

La última fila es la única que la suite no puede cubrir: necesita Pinot real, y es además donde
aparecerían las diferencias que el doble en memoria no reproduce — en este módulo, muy en concreto
**los formatos mixtos de `demo_expiracion`**, que en el doble se comparan como texto Python y en
Pinot como texto SQL.
