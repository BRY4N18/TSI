# Quickstart — Informes Tácticos Simples de Emergencias (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Cómo comprobar que los cinco listados hacen lo que la spec dice. Esta guía **valida**, no implementa.

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
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Ver todos los casos |
| `sofia.castro.operador@demo.tsi.com` | Operador de Emergencias | Rol interno |
| `ana.torres.cliente@demo.tsi.com` | Cliente | **Acotamiento por zona** (condado 1) |
| `partner.demo@demo.tsi.com` | Partner de integración | Comprobar el 403 |

**Datos que hay que garantizar antes de probar:**

- **Casos en al menos dos condados distintos**, uno dentro y otro fuera de la zona contratada de Ana
  (§3.2). Sin eso, el acotamiento pasa sin demostrar nada.
- Un **caso cerrado**, uno **descartado por falsa alarma** y uno **fusionado** como duplicado (§3.3).
  La revisión anterior dejó los tres.
- Un **caso abierto** en la zona de Ana, para comprobar que no lo ve (§3.4).
- Un **despacho en tránsito** —sin llegada ni retiro— y uno con **retiro forzado** (§3.5).
- **Evidencia capturada sin conexión y sincronizada**, más **evidencia registrada en línea**, tanto
  foto como nota (§3.6). La revisión dejó los cuatro casos.
- **Evidencia sin sincronizar** (§3.7).
- Un **cierre sin calificación** y otro **sin observaciones** (§3.8).

---

## 3. Comprobación por escenario

### 3.1 Los cinco responden

```bash
for r in casos despachos evidencia-fotos notas-campo cierres; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/$r"; done
```

**Esperado:** cinco `200`. Sin filas, `200` con `data: []` — nunca `404`.

### 3.2 El acotamiento por zona contratada *(SC-001, SC-002)*

Con el token de **Ana (Cliente)**:

```bash
curl -s -H "Authorization: Bearer $TOKEN_ANA" "http://localhost:8000/api/v1/informes/emergencias/casos?limit=500"
```

**Esperado:** solo casos del **condado 1**, y `meta.acotado_a = "zonas_contratadas"`. Contrastar con
el Administrador: el conteo de Ana debe ser **estrictamente menor**.

**Y el caso límite que importa:** con un cliente **sin zonas contratadas**, el resultado debe ser
**vacío**, nunca el listado completo. De las dos lecturas posibles de «sin zonas», la otra daría
acceso total a quien no contrató nada.

### 3.3 Cerrado, descartado y fusionado se distinguen *(SC-004)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/casos?situacion=duplicado"
```

**Esperado:** el caso fusionado aparece con `duplicado_de` apuntando a su padre. Repetir con
`?situacion=descartado` y `?situacion=cerrado`: **tres conjuntos disjuntos**.

Y comprobar en la respuesta completa que **no existe ningún campo `estado`**: van `activo`,
`hora_fin` y `duplicado_de` por separado. Un estado calculado sería una inferencia apoyada en una
garantía que vive en otro módulo.

### 3.4 El cliente solo ve casos cerrados *(SC-003)*

Con el token de **Ana**, y existiendo un caso **abierto** en el condado 1:

**Esperado:** ese caso **no aparece**. La emergencia en curso es información operativa.

### 3.5 En tránsito y retiro forzado *(research D5)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/despachos?en_transito=true"
```

**Esperado:** solo despachos con hora de despacho y **sin** llegada ni retiro.

Y en el listado completo, el retiro forzado debe venir marcado, distinguible de uno normal.

**Comprobar también** que un caso con varios despachos los muestra **todos**, cada uno con sus horas.

### 3.6 La hora de captura no es la de subida ⚠️ *(SC-006, research D3)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/evidencia-fotos?caso=<CASO_CON_OFFLINE>"
```

**Esperado:** la foto capturada sin conexión muestra `hora_captura` y `hora_registro`
**distintas**; la tomada en línea, **iguales**. Ese contraste es la prueba de que no se está sellando
la hora de subida.

**Repetir con las notas**, que es donde el error es más probable:

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/notas-campo?caso=<CASO_CON_OFFLINE>"
```

**Esperado:** lo mismo. **Y aquí hay que insistir**: la nota no tiene marca de sincronización propia,
así que su hora de registro sale de otra columna. Si ambas horas coinciden **en la nota capturada sin
conexión**, se tomó la columna equivocada — y el error **sería invisible** en las notas registradas
en línea.

### 3.7 La evidencia que nunca llegó

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/evidencia-fotos?sincronizado=false"
```

**Esperado:** aparece la evidencia capturada y no sincronizada. Es el hueco que la revisión del
sistema dejó anotado expresamente: evidencia que se levantó y nunca llegó.

Repetir con `notas-campo`.

### 3.8 Una calificación ausente no es un cero ⚠️ *(research D6)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/cierres"
```

**Esperado:** el cierre sin calificar muestra `calificacion` **ausente**, **nunca `0`**. Y el cierre
sin observaciones las muestra ausentes, no como cadena vacía.

**Un cero aquí no es cosmético**: en una escala, cero es el peor valor, y un promedio que incluyera
los ceros de los casos sin calificar hundiría la media sin que nadie lo note.

### 3.9 Ni coordenadas ni identidad *(SC-005)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/casos" | grep -o 'latitud\|longitud\|conductor\|implicado\|identificacion' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. La ubicación va por nombre —calle, ciudad, condado—. **Un volcado de este
listado no debe ser un mapa de siniestralidad exportable.**

### 3.10 El caso sin ubicación resoluble aparece *(FR-026)*

**Esperado:** un caso cuya calle no resuelve **aparece** con la ubicación ausente. Omitirlo
escondería una anomalía real: ese caso además nunca podrá acotarse a ninguna zona.

### 3.11 Control de acceso

Con el token del **Partner de integración**: los cinco listados responden **403**. El acceso
programático a los datos tiene su propio camino.

Con el token de **Ana (Cliente)**: `despachos`, `evidencia-fotos`, `notas-campo` y `cierres`
responden **403**. Solo `casos` le está permitido, acotado.

### 3.12 Rango opcional donde corresponde *(FR-020)*

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/casos"
```

**Esperado:** `200` con el histórico completo paginado.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/emergencias/cierres?desde=2026-01-01&hasta=2026-08-14"
```

**Esperado:** `400` — el registro de cierre no tiene fecha propia, así que es de estado actual.

---

## 4. Suites

```bash
cd backend && python -m pytest apps/accidentes apps/seguimiento core/informes -q
```

```bash
cd backend && python -m pytest apps/informes_tacticos apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/red_operativa apps/soporte_cliente apps/partners -q
```

**Esperado: verde sin cambios.** El segundo comando es crítico: `core/informes/` gana un eje nuevo, y
**los 19 informes agregados no se tocan** pese a vivir en el mismo departamento.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Un caso recién cerrado puede seguir apareciendo activo. **No es un
  fallo.**
- **El doble en memoria no reproduce la asimetría de las notas.** La prueba de §3.6 debe hacerse
  contra el stack real, o mirando qué columna lee el repositorio.
- **Sin casos en dos condados, el acotamiento por zona pasa sin demostrar nada.**
- **El navegador de pruebas no da geolocalización**, así que la evidencia offline se sembró
  simulando el sensor. No afecta a estos listados, que solo leen lo ya registrado.
