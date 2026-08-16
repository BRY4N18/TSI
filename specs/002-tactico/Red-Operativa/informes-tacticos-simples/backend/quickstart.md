# Quickstart — Informes Tácticos Simples de Red Operativa (Backend)

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
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Ver toda la flota y las regiones |
| `ana.torres.cliente@demo.tsi.com` | Cliente / Proveedor | **Comprobar el acotamiento** |
| `roberto.paredes.director@demo.tsi.com` | Director Tecnológico | Regiones y validaciones |
| `sofia.castro.operador@demo.tsi.com` | Operador | Comprobar el 403 |

> **Dos proveedores con flota son imprescindibles.** Con uno solo, filtrar y no filtrar dan el
> mismo resultado y el acotamiento pasa cualquier prueba sin existir.

**Datos que hay que garantizar antes de probar:**

- Una unidad **en estado operativo distinto de Activa** —por ejemplo `Fuera de servicio`— pero
  **dada de alta**. Es el caso que demuestra por qué alta ≠ disponible (§3.2).
- Una **baja forzada** con su caso afectado, y una baja **normal** (§3.4). La revisión anterior dejó
  `LOTE-A1` dada de baja forzada durante una misión.
- Una unidad **sin condado asignado**, si es posible sembrarla (§3.5).
- Una región en **`En_Alerta`** y otra **`Despublicada`** (§3.6).
- Una región con **dos rechazos** de validación (§3.7).

---

## 3. Comprobación por escenario

### 3.1 Los cuatro responden

```bash
for r in flota bajas-unidad regiones validaciones-region; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/$r"; done
```

**Esperado:** cuatro `200`. Sin filas, `200` con `data: []` — nunca `404`.

### 3.2 Estar de alta no es estar disponible ⚠️ *(SC-003 — la comprobación de fondo)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/flota?dado_de_alta=true"
```

**Esperado:** la unidad que está `Fuera de servicio` **aparece igualmente**, porque sigue dada de
alta. Y `meta.alcance` vale `composicion_de_flota`.

**Si `meta.alcance` falta, el listado incumple FR-008.** No es un adorno: sin esa declaración, quien
consuma el endpoint sin leer el contrato interpretará "dado de alta" como "puede acudir", y esa
confusión cuesta una decisión de cobertura.

Comprobar también que **ningún campo de la respuesta** se llama disponibilidad, estado operativo ni
similar.

### 3.3 Ni posición ni contacto *(research D6)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/flota" | grep -o 'latitud\|longitud\|contactoproveedor' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. La posición de una unidad es dato sensible con control y auditoría propios;
para seguir una unidad existe el módulo de seguimiento.

### 3.4 La baja forzada dejó un caso sin unidad *(SC-004, research D5)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/bajas-unidad?tipo_baja=Forzada_con_reasignaci%C3%B3n"
```

**Esperado:** cada fila trae `caso_afectado` con el número del caso. Contrastar con
`?tipo_baja=Normal`: ahí `caso_afectado` debe estar **ausente**, no vacío ni cero.

**Si ambos tipos aparecieran sin distinguir**, un incidente operativo se estaría contando como
rotación de flota.

### 3.5 La unidad sin condado aparece *(FR-023)*

**Esperado:** la unidad sin condado **aparece** con la ubicación ausente. Omitirla escondería
exactamente la anomalía que importa: sin condado, esa unidad no puede encontrarse como candidata en
un despacho.

### 3.6 `En_Alerta` no es `Despublicada` *(research D4)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/regiones?estado_region=En_Alerta"
```

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/regiones?estado_region=Despublicada"
```

**Esperado:** conjuntos **disjuntos**, y la región despublicada **sí aparece** en el listado
completo. `En_Alerta` es una región que **opera** con cobertura degradada: agruparlas ocultaría la
ventana en la que OT13 puede actuar.

### 3.7 Se conservan todos los intentos de validación

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/validaciones-region?idregionoperativa=<ID>"
```

**Esperado:** los **dos** rechazos, cada uno con su motivo y su ejecutor. Que el segundo sustituya al
primero sería el defecto.

### 3.8 El acotamiento por proveedor *(SC-001, SC-002)*

Con el token del **proveedor**:

```bash
curl -s -H "Authorization: Bearer $TOKEN_PROVEEDOR" "http://localhost:8000/api/v1/informes/red-operativa/flota?limit=500"
```

**Esperado:** solo sus unidades, `meta.acotado_a = "propios"`, y conteo **estrictamente menor** que
el del Administrador.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN_PROVEEDOR" "http://localhost:8000/api/v1/informes/red-operativa/flota?proveedor=<ID_DE_OTRO>"
```

**Esperado:** `403` **sin ninguna fila**.

> **Ojo con el criterio de pertenencia** (research D1). El acceso se resuelve por ser
> **administrador local** de la cuenta proveedora. Un usuario de esa organización que **no** lo sea
> recibirá `403`, y **eso es correcto**: es el mismo criterio que aplica la pantalla operativa de
> alta de unidades. Si se prueba con un usuario equivocado, el `403` parecerá un fallo y no lo es.

### 3.9 Las regiones no se acotan, se restringen

Con el token del **proveedor**: `regiones` y `validaciones-region` responden **403**. Una región no
pertenece a ningún proveedor.

Con el token del **Director Tecnológico**: ambos responden `200`.

### 3.10 Nombres, no identificadores *(SC-005)*

**Esperado:** `condado` con el nombre del condado, `proveedor` con la razón social, `ejecutada_por`
con el nombre de la persona. Nunca `idcondado`, `idcliente` ni `idusuario`.

### 3.11 Rango opcional donde corresponde *(FR-017)*

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/flota?desde=2026-01-01&hasta=2026-08-14"
```

**Esperado:** `400` — es un listado de estado actual.

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/red-operativa/bajas-unidad"
```

**Esperado:** `200` con el histórico completo.

---

## 4. Suites

```bash
cd backend && python -m pytest apps/red_operativa core/informes -q
```

```bash
cd backend && python -m pytest apps/informes_tacticos apps/cuentas_clientes apps/ventas_crm apps/suscripciones -q
```

**Esperado: verde sin cambios.** El segundo comando es crítico en este módulo: `core/informes/`
recibe una **corrección** del acotamiento, no solo una ampliación. Si los módulos previos se mueven,
la parametrización cambió el comportamiento por defecto en vez de añadir una opción.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Una unidad recién dada de baja puede seguir apareciendo como alta.
  **No es un fallo.**
- **El doble en memoria no reproduce ninguna de las dos trampas del módulo**: ni la distinción entre
  existencia y disponibilidad, ni los criterios de pertenencia. Las pruebas de D1 y D2 deben mirar el
  código.
- **Sin dos proveedores con flota, el acotamiento pasa cualquier prueba.**
- **Un `403` con un usuario no administrador local es el comportamiento correcto**, no un defecto.
  Verificar siempre con qué usuario se está probando antes de dar por roto el acotamiento.
