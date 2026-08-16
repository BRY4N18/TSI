# Quickstart: Validar los 16 informes tácticos simples

## Prerrequisitos

- Stack operativo levantado (`docker/docker-compose.infraestructura.yml`) con Pinot poblado con datos de accidentes/despachos/seguimiento (seeds de demo, ver `datos-demo.md`).
- Backend Django corriendo (`docker/accidentes.yml`) con la app `informes_tacticos` registrada e implementada (tarea de `/speckit-tasks` / `/speckit-implement`, no de este documento).
- Un token JWT válido de un usuario con rol Operador o Supervisor de Emergencias.

## 1. Verificar un informe simple (volumen de casos)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/registro/volumen-casos?desde=2026-07-01&hasta=2026-07-31&granularidad=dia"
```

**Resultado esperado**: `200`, `data` con una fila por día del rango que tenga accidentes, `meta.periodo` reflejando el rango pedido.

## 2. Verificar un informe con filtro geográfico (ratio demanda/capacidad)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/despacho/ratio-demanda-capacidad?desde=2026-07-01&hasta=2026-07-31"
```

**Resultado esperado**: `200`, `data` con una fila por condado, cada una con `total_accidentes`, `unidades_activas` y `ratio` coherentes entre sí (`ratio ≈ total_accidentes / unidades_activas`).

## 3. Verificar el caso de "sin datos" (FR-006)

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/registro/volumen-casos?desde=1999-01-01&hasta=1999-01-31"
```

**Resultado esperado**: `200` (no error), `data: []`, distinguible de un fallo de conexión a Pinot (que debe responder `5xx`).

## 4. Verificar control de acceso (FR-007)

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://localhost:8000/api/v1/informes-tacticos/registro/volumen-casos?desde=2026-07-01&hasta=2026-07-31"
```

**Resultado esperado**: `401` sin token; con un token de un rol distinto a Operador/Supervisor, `403`.

## 5. Verificar tiempo de respuesta (SC-001)

```bash
time curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/informes-tacticos/despacho/tiempo-respuesta-por-severidad?desde=2026-05-01&hasta=2026-07-31" \
  > /dev/null
```

**Resultado esperado**: tiempo total bajo 3 segundos para un rango de 90 días.

## 6. Recorrido completo

Repetir el paso 1 (con sus parámetros propios) para cada uno de los 16 informes listados en `contracts/informes-tacticos-agregados.openapi.yaml`, confirmando `200` y una forma de `data` acorde al esquema documentado ahí.
