# Contrato UI — tres pantallas Z, dos audiencias

**No redefine** [`../backend/contracts/informes-compuestos-red-operativa.openapi.yaml`](../backend/contracts/informes-compuestos-red-operativa.openapi.yaml).
Mapea **zona de pantalla → informe publicado → campos que la zona está obligada a mostrar**.

Prefijo de lectura: `GET /api/v1/informes-tacticos/red-operativa/{informe}?desde=&hasta=`

| Pantalla | Roles que entran | Roles que **no** entran (ni ven el enlace) |
|---|---|---|
| `flota`, `mercados` | `DirectorExpansion`, `Administrador` | `DirectorTecnologico`, Cliente, Proveedor, Operador |
| `validacion` | `DirectorTecnologico`, `Administrador` | `DirectorExpansion`, Cliente, Proveedor, Operador |

Cualquier otro: la pantalla no existe para ellos (403 / access-denied). Un ítem deshabilitado **no**
cumple este contrato.

## Prohibido en las tres

Coordenadas, identidad de personas (incluido quien validó), contacto de proveedor, mapas, botones de
alta/baja/validar/despublicar, exportar, un tablero único de departamento.

`data-testid` canónicos: `zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`, `zona-apoyo`.

Los quince slugs publicados MUST aparecer en exactamente una zona de exactamente una pantalla.

---

## Pantalla `flota` — Flota y cobertura · materia `crecimiento`

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `condados-cobertura-critica` | recuento de condados bajo umbral; `condado`, `unidades`, `umbral_aplicado`, `sin_alternativas`, `unidades_vecinas` | **sin alternativas** cuando `sin_alternativas`; umbral y `nota_umbral` visibles (convención, no política) |
| Período | — | `desde`, `hasta` | — |
| Visual | `unidades-por-estado` | `estado`, `unidades` / `transiciones` | **En Misión** aparece si el período lo tiene. No filtrar por catálogo de tres estados |
| Lectura | `disponibilidad-declarada` | `unidad`, `pct_disponibilidad` | `null` → **ausente**, nunca 0 %. 0 % real (medida y no disponible) se distingue |
| Apoyo plegado | `cobertura-flota-por-region`, `pendientes-primer-acceso`, `rendimiento-proveedor`, `rotacion-flota`, `bajas-forzadas` | lo que cada contrato ya devuelve | `nota_region` junto a cobertura; «Sin región asignada» no se maquilla como fallo de layout |

Vista principal ≤ 8 bloques (héroe, período, visual, lectura, apoyo como **un** bloque plegado).

---

## Pantalla `mercados` — Mercados y retirada · materia `crecimiento`

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `mercados-activos` | `estado_ciclo_vida`, `regiones`, `pct` | el estado es de **ciclo de vida**, no geografía |
| Período | — | `desde`, `hasta` | — |
| Visual | `tiempo-puesta-operacion` | `region`, `dias`, `cumple_objetivo`, `dias_objetivo` | `dias`/`cumple_objetivo` nulos → **ausente**, no 0 ni incumplimiento. `nota_objetivo`: convención, no plazo firmado |
| Lectura | `regiones-en-riesgo` | `region`, `unidades`, `umbral_aplicado`, `unidades_faltantes` | umbral y nota visibles. Si el backend declara el hueco región↔condado, **junto a la cifra** |
| Apoyo plegado | `casos-activos-al-despublicar`, `tiempo-perdida-a-despublicacion` | filas si hay; si `data: []`, igual | **`medida_exacta_desde` visible**. Vacío ≠ «nunca pasó». Una región aún publicada sin flota no se pinta como despublicada en 0 días |

---

## Pantalla `validacion` — Criterios de validación · materia `validacion`

| Zona Z | Informe | Campos visibles | Lectura obligatoria |
|---|---|---|---|
| Héroe | `tasa-aprobacion-primer-intento` | `pct_aprobacion_primer_intento`, `regiones_validadas`, `aprobadas_al_primero` | `null` → sin dato, no 0 % |
| Período | — | `desde`, `hasta` | — |
| Visual | `motivos-rechazo` | `motivo`, `rechazos`, `pct` | solo rechazos; no inventar categoría «sin motivo» a partir de aprobaciones |
| Lectura | — | texto fijo: se cuentan **intentos**, no regiones | `nota_grano` si el envelope la trae |

Sin zona de apoyo. Sin desglose por validador.

---

## Estados por zona

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | esqueleto **solo en esa zona** |
| dato | `data` con filas y métrica no nula | cifra / barras |
| sin_dato | métrica `null` con período que sí tiene contexto | «sin dato» / «ausente», nunca 0 |
| vacio | `data: []` | vacío explícito; en despublicación, con `medida_exacta_desde` |
| error | 4xx/5xx / red | mensaje en la zona; el resto sigue. Un 403 en materia ajena no se «recupera» pintando ceros |

## Navegación

Tres entradas de sidebar, grupo Red operativa, **roles del guard de esa pantalla**. No modificar el
enlace de listados. No añadir un índice que liste las tres a quien solo gobierna una.
