# Contrato UI — tres pantallas Z

**No redefine** el OpenAPI del backend. Mapea **zona → informe publicado → campos visibles**.

Prefijo: `GET /api/v1/informes-tacticos/cuentas/{informe}?desde=&hasta=`

| Id publicado | Materia |
|---|---|
| `churn-por-cohorte` | ciclo |
| `antiguedad-media` | ciclo |
| `usuarios-vs-tope` | ciclo |
| `cuentas-en-riesgo` | ciclo |
| `tiempo-onboarding` | incorporacion |
| `embudo-abandono` | incorporacion |
| `tasa-aprobacion` | incorporacion |
| `concurrencia-sesiones` | acceso |
| `roles-incompatibles` | acceso |

Roles: ciclo e incorporación = `Administrador`. Acceso = `DirectorTecnologico` \| `Administrador`.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`.

Envelope: `data.resultados`. Notas en `meta`.

## Prohibido en las tres

Token; nombre; correo; teléfono; género; fecha de nacimiento; mapas; botones de baja / cambio de rol / cierre de sesión; exportar; filtrar etapas con cero; pintar ocupación sin cobertura; titular concurrencia como recuento de logins; marcar multi-rol como hallazgo.

---

## Pantalla `ciclo` — Ciclo de vida

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `churn-por-cohorte` | `cohorte_alta`, `clientes_iniciales`, `bajas`, `pct_churn`, `motivo` | barras/filas por **cohorte de alta**; vacío → no 0 % |
| Período | — | `desde`, `hasta` | — |
| Visual | `usuarios-vs-tope` | `idcliente`, `usuarios_conocidos`, `tope_plan`, `pct_ocupacion`, `pct_cobertura_pertenencia`; `meta.nota_cobertura` | usuarios + tope + cobertura **juntos**; sin plan → sin dato |
| Lectura | `cuentas-en-riesgo` | `idcliente`, `dias_sin_actividad`, `sin_actividad_conocida` | conocida ≠ 0 días |
| Apoyo plegado | `antiguedad-media` | `tipo_cliente`, `plan`, `clientes`, `dias_mediana` | segundo plano |

Vista principal ≤ 8 bloques.

---

## Pantalla `incorporacion` — Incorporación

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `tiempo-onboarding` | `dias_mediana`, `clientes_completados`, `en_proceso` | en proceso **aparte**, no cero días |
| Período | — | `desde`, `hasta` | — |
| Visual | `embudo-abandono` | `orden`, `etapa`, `clientes_que_llegaron`, `pct_supera`, `detenidos_aqui`; `meta.nota_catalogo` | **todas** las etapas, ceros incluidos |
| Lectura | `tasa-aprobacion` | `tipo_organizacion`, `solicitudes`, `aprobadas`, `rechazadas`, `pct` | el rechazo cuenta en el denominador |

---

## Pantalla `acceso` — Acceso

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `concurrencia-sesiones` (mismo GET que visual) | `concurrencia_maxima`, `sesiones_iniciadas` | solape **y** inicios; no titular como logins |
| Período | — | `desde`, `hasta` | — |
| Visual | `concurrencia-sesiones` | `fecha`, `franja`, `concurrencia_maxima`; `meta.nota_solape` | cruce de medianoche declarado |
| Lectura | `roles-incompatibles` | `idusuario`, `rol_a`, `rol_b` | vacío si no hay política; nunca el nombre |
| Apoyo | mismo GET de concurrencia | `duracion_mediana`, `sesiones_sin_cierre` | abiertas **a la vista** |

Un solo GET de concurrencia para héroe, visual y apoyo de duración.

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | filas y métrica no nula | cifra / barras |
| sin_dato | métrica `null` (tope ausente) | «sin dato», nunca 0 % |
| vacio | `resultados: []` | vacío explícito |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue |

## Navegación

Tres entradas en el grupo Administración. No modificar «Informes de cuentas», «Gestión de cuenta» ni incorporación operativa.
