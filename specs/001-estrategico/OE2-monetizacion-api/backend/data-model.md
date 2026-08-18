# Data Model — OE2, Monetización de APIs

**Fecha:** 2026-08-18 · **Research:** [`research.md`](research.md)

Este módulo **no crea tablas**. Consume el modelo que cargó Partners (y, para excedente cobrado,
`hecho_factura` de Suscripciones).

---

## 1. Tablas leídas

| Tabla | Tipo | `FINAL` | Aporta |
|---|---|:--:|---|
| `hecho_llamada_api` | Transacción | **No** | Llamadas, latencia, HTTP, endpoint, servicio, versión derivada |
| `dim_partner` | Dimensión | **Sí** | Nombre, `plan_api`, `limite_llamadas_mes`, `estado` |
| `dim_plan` | Dimensión | **Sí** | `precio_excedente_llamada` (E2-08) |
| `dim_version_contrato` | Dimensión | **Sí** | Catálogo (servicio, versión) |
| `hecho_factura` | Transacción | **No** | `tipo = 'excedente_api'` = cobrado, no facturable |

**No se lee** ningún log con IP, ni `client_secret`, ni contacto técnico.

`hecho_cambio_acceso` **no es fuente de E2-11**: el crecimiento cuenta la primera llamada 2xx.

---

## 2. Columnas que importan (lista blanca)

### `hecho_llamada_api`

`fecha`, `fechahora`, `idpartner`, `partner`, `idcliente`, `plan_api`, `endpoint_path`,
`metodo_http`, `codigo_http`, `clase_resultado`, `latencia_ms`, `servicio`,
`version_contrato`, `version_es_derivada`

Prohibido: cualquier columna de origen, IP, hash.

### `dim_partner`

`idpartner`, `nombre_partner`, `plan_api`, `limite_llamadas_mes`, `estado`

`estado` sirve al denominador de E2-03: acceso concedido ≠ suspendido de entrada.

### `dim_plan`

`nombre`, `precio_excedente_llamada`, `limite_llamadas_mes`

Join de excedente: `dim_partner.plan_api = dim_plan.nombre` (texto). Si no hay match, el
partner es **no tarificable** y se declara, no se omite.

---

## 3. Los diez informes construibles

| # | Slug HTTP | Grano | Hechos |
|---|---|---|---|
| E2-03 | `integraciones-activas` | período | partners con ≥1 llamada / partners con acceso |
| E2-04 | `consumo-por-partner` | partner × período | llamadas vs cupo |
| E2-05 | `latencia-por-endpoint` | endpoint | p95, media, muestras, `percentil_fiable` |
| E2-07 | `taxonomia-errores` | clase HTTP | 4xx y 5xx **separados** |
| E2-08 | `excedente-facturable` | partner × mes | max(0, llamadas−cupo)×precio; no tarificables aparte |
| E2-01 | `participacion-ingresos-api` | período | volumen + excedente cobrado; **parcial** sin precio de plan |
| E2-02 | `mrr-por-linea` | período | ídem |
| E2-09 | `adopcion-versiones` | (servicio, versión) | llamadas; declara derivación |
| E2-10 | `comparativa-partners` | partner | volumen, error, latencia; ceros visibles |
| E2-11 | `crecimiento-ecosistema` | período | primera llamada exitosa por partner |

**E2-06** no es fila de este modelo: no hay tabla que consultar.

---

## 4. Validaciones de consulta

- `resultados: []` en un mes sin llamadas → vacío, no 0 ms ni 0 % de uptime.
- p95 con `muestras < muestra_minima` → `null` + no fiable.
- 4xx y 5xx nunca se suman en un «error total» en E2-07.
- E2-09: `GROUP BY servicio, version_contrato`, nunca solo `version`.
- E2-08: tres componentes visibles; `alcance` dice que no es cobrado.
- E2-01/02: `cobertura: parcial` si falta precio de plan API.

---

## 5. Relación con el táctico

Las consultas tácticas `ot09_*` ya calculan p95, taxonomía y participación. OE2 **no las
parametriza**: tiene ventana comparada, `objetivo` BSC y permiso de Gerente/Finanzas. El
contraste de implementación debe cuadrar el **detalle del período**, no el envelope.
