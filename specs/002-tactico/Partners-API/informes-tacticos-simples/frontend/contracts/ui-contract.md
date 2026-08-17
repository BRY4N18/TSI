# Contrato UI — cinco listados, dos audiencias

**No redefine** [`../backend/contracts/informes-tacticos-simples.openapi.yaml`](../backend/contracts/informes-tacticos-simples.openapi.yaml).
Mapea **pantalla → columnas visibles → filtros → quién entra**.

Prefijo de lectura: `GET /api/v1/informes/partners-api/{listado}`

Ruta de aplicación: `/partners/informes` (índice) y `/partners/informes/{id}`.

| Listado | Roles que entran | Roles que **no** entran (ni ven el enlace) |
|---|---|---|
| `partners`, `credenciales`, `cambios-acceso` | PartnerIntegracion, DesarrolladorAPIs, Administrador, DirectorTecnologico | Operador y resto ajeno |
| `versiones-contrato`, `alcance-datos` | DesarrolladorAPIs, Administrador, DirectorTecnologico | PartnerIntegracion, Operador, resto ajeno |

El índice lo ven los cuatro del primero. Filtra enlaces: el Partner obtiene **tres**. Un ítem
deshabilitado de contrato en su índice **no** cumple este contrato — no se ofrece.

## Prohibido en los cinco

Secreto de autenticación (claro, hash, pista). Columna de motivo en credenciales. Agrupar
`revocacion_credencial` con `desactivacion_por_cascada`. Recuento total. Números de página.
Exportar. Gráficas. CTA operativo. Fusionar consola y portal en un solo texto de menú.

`data-testid` canónicos del contrato común: estados de listado, `indice-informes`,
`enlace-{id}`.

---

## `partners` — estado actual · audiencia acceso

| Columnas | Filtros | Lectura obligatoria |
|---|---|---|
| `cuenta`, `nombre_partner` (principal), `estado_acceso`, `plan_api`, `limite_llamadas_mes`, `limite_llamadas_minuto`, `contacto_tecnico`, `fecha_suspension`, `motivo_suspension` | `estado` (seis del dominio), `plan` (texto), `partner` (**solo gestión**) | Sin rango de fechas. Suspendido: fecha y motivo presentes. No suspendido: ambos **ausentes**. `0` de cupo es cero, no ausencia |

Vacío: «No hay partners con esos criterios.» Con `propios`, el aviso de alcance acompaña.

## `credenciales` — estado actual · audiencia acceso · bandeja

| Columnas | Filtros | Lectura obligatoria |
|---|---|---|
| `partner`, `nombre_credencial` (principal), `entorno`, `activa`, `fecha_creacion`, `fecha_expiracion`, `dias_para_caducar` | `entorno` (`Sandbox` \| `Producción`), `activa` (booleano), `caduca_en_dias` (número ≥ 0), `partner` (**solo gestión**) | **`activa` dice si; no hay motivo.** Pruebas y producción coexisten. Sin rango de fechas. Sin secreto |

Vacío: «No hay credenciales con esos criterios.»

## `cambios-acceso` — hechos del período · audiencia acceso

| Columnas | Filtros | Lectura obligatoria |
|---|---|---|
| `partner`, `credencial`, `tipo_cambio`, `estado_anterior`, `estado_nuevo`, `motivo`, `ejecutado_por`, `fecha` | rango `desde`/`hasta`, `tipo_cambio` (cada `CAMBIO_*` por separado), `partner` (**solo gestión**) | Revocación y cascada **distintos**. Reactivación: motivo **ausente** es correcto |

Vacío: «No hay cambios de acceso en este período.»

## `versiones-contrato` — estado actual · audiencia contrato

| Columnas | Filtros | Lectura obligatoria |
|---|---|---|
| `servicio`, `version` (principal), `estado`, `spec_url`, `fecha_publicacion`, `fecha_retiro` | `estado` (`vigente` \| `soportada` \| `retirada`), `servicio` (número) | Las **retiradas se listan**. `fecha_retiro` ausente si sigue publicada. Sin rango de fechas. Sin filtro `partner` |

Vacío: «No hay versiones de contrato con esos criterios.»

## `alcance-datos` — estado actual · audiencia contrato

| Columnas | Filtros | Lectura obligatoria |
|---|---|---|
| `cuenta` (principal), `zonas_geograficas` (lista), `frecuencia_reportes`, `formato_reportes`, `canales_notificacion` (lista), `destinatarios_reportes` (lista) | `cuenta` (número), `frecuencia` (texto) | Zonas nulas → **ausente**, nunca «todas las zonas» / ilimitado. Sin rango de fechas |

Vacío: «No hay alcances de datos con esos criterios.»

---

## Estados de la pantalla

| Estado | Cuándo | Qué se ve |
|---|---|---|
| carga | petición en vuelo | skeleton de la capa compartida |
| dato | `data` con filas | tabla / tarjetas |
| vacio | `data: []` | `mensajeVacio` + aviso `acotado_a` si ≠ `todos` |
| peticion (`400`) | filtro o límite inválido | `detail` del backend; **sin** Reintentar |
| permiso (`403`) | rol o partner ajeno | negativa; **no** tabla vacía |
| servidor / red | 5xx o red | Reintentar sí |

## Navegación

Dos entradas de sidebar, grupo Partners y API, **misma ruta**, textos y roles de research D3. No
modificar enlaces de consola ni de portal. No añadir «Informes» a un grupo que el otro público vea
con el texto equivocado.
