# Contrato UI — tres pantallas Z de OE2

**No redefine** el OpenAPI. Mapea **zona → informe publicado → campos visibles**.

Prefijo: `GET /api/v1/informes-estrategicos/oe2/{informe}?desde=&hasta=&granularidad=&comparacion=`

| Id publicado | Pantalla |
|---|---|
| `integraciones-activas` | uso |
| `consumo-por-partner` | uso |
| `latencia-por-endpoint` | uso (apoyo) |
| `taxonomia-errores` | uso |
| `excedente-facturable` | dinero |
| `participacion-ingresos-api` | dinero (apoyo) |
| `mrr-por-linea` | dinero (apoyo) |
| `adopcion-versiones` | ecosistema |
| `comparativa-partners` | ecosistema |
| `crecimiento-ecosistema` | ecosistema |

**No publicado:** `disponibilidad-api`.

Roles: uso y ecosistema = `DirectorTecnologico` · `Gerente`. Dinero = esos · `DirectorFinanciero`. Partner = ninguno.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`, `zona-parcial`, `zona-comparacion`.

Envelope: `data` (array) + `meta`.

## Prohibido en las tres

IP; secreto; hash; contacto técnico; mapas; uptime; botón de facturar / retirar versión / revocar; exportar; `acotado_a`; total «errores»; agrupar solo por `version`; ítem de menú gris para Partner.

---

## Pantalla `uso` — Uso de la API

Guard: `oe2UsoEcosistemaGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `integraciones-activas` | numerador, denominador (acceso), %, meta ≥70 % si `meta.objetivo` | denominador ≠ catálogo entero |
| Período | — | `desde`, `hasta`, `granularidad`, `comparacion` | comparación ausente con motivo |
| Visual | `taxonomia-errores` | `clase_http`, `llamadas`, `denominador`, `pct` | 4xx ≠ 5xx; sin total |
| Lectura | `consumo-por-partner` | organización, `llamadas`, `cupo`, `pct_cupo` | ceros visibles |
| Apoyo plegado | `latencia-por-endpoint` | endpoint, p95, media, `muestras`, `percentil_fiable` | trío inseparable; no fiable visible |

---

## Pantalla `dinero` — Dinero de la API

Guard: `oe2DineroGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `excedente-facturable` | llamadas, cupo, precio, importe | los cuatro juntos |
| Período | — | igual que uso | — |
| Visual | mismo GET | filas `no_tarificable` | declarados, no omitidos |
| Lectura | `meta.alcance` | texto de facturable ≠ cobrado | MUST verse |
| Apoyo plegado | `participacion-ingresos-api`, `mrr-por-linea` | volumen + `meta.cobertura` + `meta.falta` | `zona-parcial` si parcial |

Un GET de excedente alimenta héroe y visual (D9 táctico equivalente).

---

## Pantalla `ecosistema`

Guard: `oe2UsoEcosistemaGuard`.

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `crecimiento-ecosistema` | partners nuevos (primera 2xx) | no altas de credencial |
| Período | — | igual que uso | — |
| Visual | `adopcion-versiones` | `servicio`, `version`, `llamadas`, `version_es_derivada` | dos `'v1'` = dos grupos |
| Lectura | `comparativa-partners` | organización, volumen, error, latencia | ceros visibles; sin contacto |

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | filas | cifra / barras |
| sin_dato | p95 `null` | «sin dato», nunca 0 ms |
| vacio | `data: []` | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |
| parcial | `meta.cobertura = parcial` | banner `zona-parcial` |

## Navegación

Tres entradas en el grupo **Estratégico**. No modificar «Consumo de la API» táctico (`/partners/gestion/consumo`), el portal del partner ni los listados.
