# Quickstart — Validar el endurecimiento de seguridad

**Fecha:** 2026-08-23 · **Plan:** [plan.md](plan.md) · **Contrato:** [contracts/respuestas-seguridad.md](contracts/respuestas-seguridad.md)

Cómo comprobar que cada historia funciona de extremo a extremo. **Guía de validación, no de
implementación**: el código va en `tasks.md` y la fase de implementación.

---

## Prerrequisitos

```bash
cd backend
pip install -r requirements.txt
```

Nada más para el ciclo rápido: las suites de este bloque corren con Pinot y Kafka **mockeados**.
Solo US4 necesita infraestructura real (ver más abajo).

⚠️ **Antes de escribir la primera prueba**, releer `research.md` §R7. Toda prueba autenticada
necesita la fixture que mockea Pinot, o la validación de sesión saldrá a buscar un Pinot real y
devolverá `401` — un fallo que aparenta ser de permisos y cuesta horas. Ya costó 42 pruebas en
falso rojo (`changelog.md` C3).

---

## Verificación por historia

### US1 — Aislamiento multi-tenant

```bash
pytest tests/seguridad/test_aislamiento_tenant.py -v
```

**Resultado esperado:** una prueba por cada una de las **92 rutas con identificador**, en `GET`,
`PUT`, `PATCH` y `DELETE`, y por las **dos vías de autenticación**. Ninguna devuelve datos ajenos.

**La comprobación que de verdad importa** (SC-002) — que la suite no envejezca:

```bash
# Añadir a mano una ruta con <int:idalgo> sin filtro de tenencia en un urls.py
pytest tests/seguridad/test_aislamiento_tenant.py -v
# ESPERADO: FALLA, nombrando la ruta nueva. Si pasa, la suite no protege: revísala.
```

> Una suite de aislamiento que pasa cuando añades un endpoint sin proteger es peor que no tenerla,
> porque produce confianza infundada. Esta comprobación es obligatoria antes de dar US1 por cerrada.

**Indistinguibilidad** (contrato C1) — ya cubierta parcialmente:

```bash
pytest apps/partners/tests/unit/test_no_enumeracion_partners.py -v
# ESPERADO: 11 passed
```

---

### US2 — Matriz rol × endpoint

```bash
pytest tests/seguridad/test_matriz_roles.py -v
```

**Resultado esperado:** informe de las 3.510 celdas (15 roles × 234 rutas). Las no verificadas
aparecen como `DESCONOCIDO` **en la salida**, no omitidas.

```bash
pytest tests/seguridad/test_matriz_roles.py -q 2>&1 | grep -c DESCONOCIDO
# ESPERADO al cerrar US2: 0
```

---

### US3 — Integridad del JWT

```bash
pytest tests/seguridad/test_integridad_jwt.py -v
```

**Resultado esperado:** las 6 variantes adversariales devuelven `401` con **cuerpo idéntico**
(contrato C3). Un cuerpo distinto le dice al atacante qué modificar.

⚠️ **Condición previa, bloqueante:** antes de implementar, fijar la lista de endpoints de la cadena
crítica **excluidos** del fail-closed, con su justificación por Principio IX (`research.md` §R5).
Denegar el despacho de una ambulancia porque Redis no responde es peor que el riesgo que se evita.
**Sin esa lista, US3 no empieza.**

---

### US4 — Inyección

```bash
pytest tests/seguridad/test_inyeccion.py -v                    # rápido, motores mockeados
pytest tests/seguridad/test_inyeccion.py -m integration -v     # requiere Pinot y ClickHouse
```

Para la variante `integration`:

```bash
docker compose -f docker/docker-compose.infraestructura.yml up -d
docker compose -f docker/docker-compose.tactico.yml up -d
```

**Por qué hacen falta las dos variantes.** Un mock acepta cualquier SQL que se le pase: no
distingue una consulta correcta de una inyectada. Solo el motor real revela si la carga alteró la
sentencia. Es el mismo motivo por el que `PG-ANA-005` (alias que tapa la columna) reaparece: los
mocks no lo reproducen.

---

### US5 — Datos sensibles

```bash
pytest tests/seguridad/test_datos_sensibles.py -v
```

**Resultado esperado:** ni respuestas de error ni logs contienen datos personales, coordenadas de
víctimas, tokens ni credenciales.

Comprobación manual complementaria, que suele encontrar lo que la prueba no busca:

```bash
DJANGO_DEBUG=false python manage.py runserver 2>&1 | tee /tmp/logs.txt
# provocar errores en endpoints con datos de víctimas, luego:
grep -iE "identificacion|gmail|telefono|latitud|longitud|Bearer" /tmp/logs.txt
# ESPERADO: sin coincidencias sin enmascarar
```

---

### US6 — Cupos

```bash
pytest tests/seguridad/test_throttles.py -v
```

**Resultado esperado:** los 4 throttles declarados devuelven `429` al superarse.

⛔ Comprobar que **ninguna** prueba espera `429` por cuota **mensual** de partner: `RN-APM-002` dice
que el cupo mensual no bloquea, se factura. Sería verificar lo contrario de la regla de negocio.

---

### US7 — Subida de archivos

```bash
pytest tests/seguridad/test_subida_archivos.py -v
```

**Resultado esperado:** ejecutable renombrado a `.jpg` → `400`; 51 MB → `413`; nombre con `../` →
saneado; SVG con script → rechazado.

---

### US8 — Cabeceras

```bash
pytest tests/seguridad/test_cabeceras.py -v
```

Y en el despliegue real, donde se ven las que solo existen fuera de local:

```bash
curl -sI https://<host>/api/v1/health | grep -iE "x-content-type|x-frame|referrer|strict-transport|content-security"
```

---

### US9 — Aislamiento de la demo

```bash
pytest apps/ventas_crm/tests/ -k demo -v
```

**Resultado esperado:** un token de sesión de demo contra un endpoint de negocio → `401`.

---

## Verificación global

Antes de dar el bloque por cerrado:

```bash
# 1. El bloque completo
pytest tests/seguridad/ -v

# 2. Nada roto en el resto del sistema
pytest -m "not integration" -q
# ESPERADO: 0 failed (referencia 2026-08-23: 4142 passed)

# 3. La configuración sigue en pie
pytest tests/test_configuracion_segura.py -q
DJANGO_DEBUG=false TSI_ENV=production python manage.py check --deploy --fail-level WARNING
```

**Y lo que cierra el ciclo, sin lo cual nada de esto protege:** incorporar `tests/seguridad/` al
job correspondiente de `.github/workflows/ci.yml`. Una suite que no corre sola equivale a no tener
suite (`PG-CI-001`).

---

## Criterio de cierre

El bloque está cerrado cuando:

- [ ] Las 9 historias pasan sus criterios de aceptación.
- [ ] Las 5 reglas Bloqueantes (`PG-SEC-001`, `002`, `003`, `005`, `007`) están ✅ en el plan global.
- [ ] Se verificó que **añadir un endpoint sin proteger hace fallar la suite** (SC-002).
- [ ] Ninguna prueba quedó `skip`/`xfail` sin justificación y fecha (`PG-CI-003`).
- [ ] `tests/seguridad/` corre en CI.
- [ ] Se actualizó el estado de las reglas en `PlanPruebas/spec.md` y se **regeneró**
      `PlanPruebas/traceability.md` (se cuenta desde el spec, no se escribe a mano).
