# Quickstart — Informes Tácticos Simples de Suscripciones y Facturación (Backend)

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

Tras cambiar backend, redesplegar:

```bash
docker cp backend/apps accidentes-django:/app/ && docker cp backend/core accidentes-django:/app/ && docker restart accidentes-django
```

---

## 2. Credenciales y datos

Contraseña compartida `password123`.

| Correo | Rol | Para qué |
|---|---|---|
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Ver todas las cuentas |
| `ana.torres.cliente@demo.tsi.com` | Cliente | **Comprobar el acotamiento** |
| `teresa.beltran@demo.tsi.com` | Cliente (Rescate Vial Andino) | **Segunda cuenta con facturación propia** |
| `sofia.castro.operador@demo.tsi.com` | Operador | Comprobar el 403 |

> **Dos cuentas con facturación simultánea son imprescindibles.** Con una sola, filtrar y no filtrar
> dan el mismo resultado y el acotamiento pasa cualquier prueba sin existir. Teresa ya tiene
> suscripción, método de pago y facturas de la revisión anterior; si no, sembrarla.

**Datos que hay que garantizar antes de probar:**

- Una suscripción **con** reducción programada y otra **sin** ninguna (para §3.3).
- Una factura `Fallida` vencida y otra `En disputa` (para §3.4).
- Un método de pago reemplazado, de modo que exista uno inactivo (para §3.6).

---

## 3. Comprobación por escenario

### 3.1 Los cuatro responden

```bash
for r in suscripciones facturas solicitudes-cambio-plan metodos-pago; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/$r"; done
```

**Esperado:** cuatro `200`. Sin filas, `200` con `data: []` — nunca `404`.

### 3.2 El identificador de cobro no sale ⛔ *(SC-003 — la comprobación más importante)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/metodos-pago" | grep -o 'tokenpasarela\|token' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. Repetir sobre los otros tres listados.

**Esto no es cosmético.** El servicio de cobro usa ese identificador para cargar contra la pasarela:
quien lo tenga, puede cobrar. Si aparece, **detener la revisión y corregir antes de seguir**.

### 3.3 El cambio programado se distingue del centinela *(SC-005, research D2)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/suscripciones?con_cambio_programado=true"
```

**Esperado:** **solo** las suscripciones que de verdad tienen una reducción pendiente. Si devuelve
**todas**, el filtro se escribió como comprobación de nulidad y está mal: el modelo guarda un valor
por defecto que significa «sin cambio», no un vacío.

Y en el listado completo, una suscripción sin cambio debe mostrar `cambio_programado` **ausente**,
nunca un plan con identificador cero.

### 3.4 Una factura en disputa no es mora *(research D3)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/facturas?vencidas=true"
```

**Esperado:** aparece la `Fallida` vencida, **no** la `En disputa`. Perseguir un cobro que el sistema
detuvo a propósito es justo lo que corrigió B41.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/facturas?estado_pago=En%20disputa"
```

**Esperado:** aparece con su estado propio y **sin** `dias_mora`.

### 3.5 El acotamiento por organización *(SC-001, SC-002)*

Con el token de **Ana (Cliente)**:

```bash
curl -s -H "Authorization: Bearer $TOKEN_ANA" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/facturas?limit=500"
```

**Esperado:** solo las facturas de su cuenta, y `meta.acotado_a = "propios"`. Contrastar con el
Administrador: el conteo de Ana debe ser **estrictamente menor**, dado que Teresa también tiene
facturas.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN_ANA" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/facturas?cuenta=<ID_DE_TERESA>"
```

**Esperado:** `403` **sin ninguna fila**. Devolver las suyas con `200` sería el defecto que FR-010
previene.

### 3.6 Solo métodos vigentes *(FR-007)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/metodos-pago"
```

**Esperado:** el método reemplazado **no aparece**, aunque su registro siga existiendo en la base.

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/metodos-pago?caduca_en_dias=60"
```

**Esperado:** solo los que caducan en ese plazo, con sus `dias_para_caducar`.

### 3.7 La cuenta suspendida conserva acceso *(FR-011)*

Con el token de una cuenta cuya suscripción esté **Suspendida**, consultar facturas y métodos de
pago.

**Esperado:** `200` con sus datos. Negárselo la dejaría atrapada sin poder ver lo que debe
regularizar — que es lo contrario de lo que la regla de suspensión pretende.

### 3.8 Rango opcional donde corresponde *(FR-016)*

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/facturas"
```

**Esperado:** `200` con el histórico completo. Omitir el rango **no** es un error.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/suscripciones-facturacion/suscripciones?desde=2026-01-01&hasta=2026-08-14"
```

**Esperado:** `400` — es un listado de estado actual. En cambio `cancelada_desde` / `cancelada_hasta`
sí se aceptan: son filtros de columna, no un período.

### 3.9 Nombres, no identificadores

**Esperado:** `plan` con el nombre del plan y `cuenta` con la razón social, nunca `idplan` ni
`idcliente`.

### 3.10 Control de acceso

Con el token del **Operador**: los cuatro listados responden **403**.

---

## 4. Suites

```bash
cd backend && python -m pytest apps/suscripciones core/informes -q
```

```bash
cd backend && python -m pytest apps/informes_tacticos apps/cuentas_clientes apps/ventas_crm -q
```

**Esperado: verde sin cambios.** El segundo comando es el guardián: `core/informes/` gana el eje de
organización en este módulo, y si eso rompe los dos módulos previos o los 19 informes agregados, la
ampliación no fue aditiva.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Una factura recién cobrada puede seguir apareciendo como pendiente.
  **No es un fallo.**
- **El doble en memoria no reproduce el centinela del plan programado.** La prueba de §3.3 debe
  mirar la condición SQL en el código, no el doble.
- **La prueba del identificador de cobro debe inspeccionar la respuesta serializada completa**, no
  los campos declarados en el contrato: un `SELECT *` filtra el campo aunque el contrato no lo
  mencione.
- **Sin dos cuentas con facturación, el acotamiento pasa cualquier prueba.**
