# Quickstart — Informes Tácticos Simples de Partners y API (Backend)

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
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Ver todos los partners |
| `maria.suarez.dev@demo.tsi.com` | Desarrollador de APIs | Gestor del módulo |
| `partner.demo@demo.tsi.com` | Partner de integración | **Comprobar el acotamiento** |
| `sofia.castro.operador@demo.tsi.com` | Operador | Comprobar el 403 |

> ⚠️ **Hacen falta dos partners con credenciales.** Con uno solo, filtrar y no filtrar dan el mismo
> resultado y el acotamiento pasa sin existir. La revisión anterior dejó *Integradora Andina*
> además del partner de demo.

**Datos que hay que garantizar antes de probar:**

- Un partner con credencial de **pruebas y de producción a la vez** (§3.3).
- Una credencial **revocada por el partner** y otra **desactivada en cascada** por suspensión, sobre
  el mismo partner (§3.4). La revisión anterior dejó exactamente ese caso en *Integradora Andina*.
- Un partner **suspendido** (§3.6).
- Una **versión del contrato retirada** además de las publicadas (§3.7).
- Un cliente **sin preferencias configuradas** (§3.8).

---

## 3. Comprobación por escenario

### 3.1 Los cinco responden

```bash
for r in partners credenciales cambios-acceso versiones-contrato alcance-datos; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/$r"; done
```

**Esperado:** cinco `200`. Sin filas, `200` con `data: []` — nunca `404`.

### 3.2 El secreto de autenticación no sale ⛔ *(SC-003)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/credenciales" | grep -o 'client_secret\|secret\|hash' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. Repetir sobre los otros cuatro.

**Verificar además en el código** que el repositorio **enumera las columnas que devuelve** en vez de
leerlas todas y descartar las prohibidas. Es la diferencia que importa: **una lista negra falla
abierta** —una columna sensible añadida mañana saldría sola—, **una lista blanca falla cerrada**.

### 3.3 Pruebas y producción coexisten

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/credenciales?partner=<ID>"
```

**Esperado:** aparecen **ambas**, cada una con su entorno. Activar producción no elimina el acceso de
pruebas.

### 3.4 Una credencial inactiva no dice por qué ⚠️ *(SC-004 — la comprobación de fondo)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/credenciales?activa=false"
```

**Esperado:** las credenciales inactivas aparecen con `activa: false` **y ningún campo de motivo**.
Si el listado afirmara un motivo, estaría **inventándolo**: ese dato no existe en el registro de la
credencial.

Ahora el contraste, que es lo que demuestra que la información sí está disponible:

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/cambios-acceso?partner=<ID>&limit=500"
```

**Esperado:** la revocación decidida por el partner y la desactivación en cascada aparecen **con
tipos de cambio distintos**. Si se agruparan, se estaría poniendo en la misma línea una decisión de
seguridad y un impago administrativo — y quien reactivara guiándose por eso resucitaría una
credencial comprometida.

### 3.5 La reactivación sin motivo es correcta

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/cambios-acceso?tipo_cambio=reactivacion"
```

**Esperado:** `motivo` **ausente**, y eso **no es un defecto**: el sistema exige motivo al cortar el
acceso, no al devolverlo. Contrastar con una suspensión, que sí lo trae.

### 3.6 El partner suspendido conserva acceso *(SC-005)*

Con el token de un partner **suspendido**, consultar `partners`, `credenciales` y `cambios-acceso`.

**Esperado:** `200` con sus datos. Es donde ve qué le pasó y qué debe regularizar; negárselo lo
dejaría a ciegas.

### 3.7 Las versiones retiradas se listan

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/versiones-contrato"
```

**Esperado:** la versión retirada **aparece** con su fecha de retiro. Omitirla escondería lo que hay
que mirar antes de retirar otra.

### 3.8 Sin alcance configurado no es acceso ilimitado *(SC-006)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/alcance-datos"
```

**Esperado:** el cliente sin preferencias aparece con `zonas_geograficas` **ausente**. **Nunca** con
una lista vacía presentada como «todas» ni con texto que sugiera acceso total.

### 3.9 El acotamiento por partner *(SC-001, SC-002)*

Con el token del **Partner**:

```bash
curl -s -H "Authorization: Bearer $TOKEN_PARTNER" "http://localhost:8000/api/v1/informes/partners-api/credenciales?limit=500"
```

**Esperado:** solo las suyas, `meta.acotado_a = "propios"`, conteo estrictamente menor que el del
gestor.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN_PARTNER" "http://localhost:8000/api/v1/informes/partners-api/credenciales?partner=<ID_DE_OTRO>"
```

**Esperado:** `403` **sin ninguna fila**.

Y `versiones-contrato` y `alcance-datos` responden **403** al partner: son de gestores.

> ⚠️ **Si el Partner recibe `403` incluso sin indicar partner**, comprobar si es el **administrador
> local** de su cuenta. La resolución cae en esa vía porque la tabla de vínculos no la escribe
> ningún código. **Es la limitación ya anotada, no un defecto de estos listados.**

### 3.10 Un filtro de enumeración inválido se rechaza con los valores buenos

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/partners-api/partners?estado=Activo"
```

**Esperado:** `400` nombrando los seis estados reales. Y si algún día se añade un estado al dominio,
**el filtro debe aceptarlo sin tocar este módulo** — los valores se importan, no se copian.

### 3.11 Nombres, no identificadores

**Esperado:** `cuenta` con la razón social, `partner` con su nombre, `ejecutado_por` con el nombre de
la persona. Nunca `idcliente`, `idpartner` ni `idusuario`.

---

## 4. Suites

```bash
cd backend && python -m pytest apps/partners -q
```

```bash
cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/red_operativa apps/soporte_cliente apps/informes_tacticos -q
```

**Esperado: verde sin cambios.** Este módulo **no modifica la capa transversal** ni el mecanismo de
propiedad existente. Si algo se mueve, se tocó algo que no debía tocarse.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Una credencial recién revocada puede seguir apareciendo activa.
  **No es un fallo.**
- **La credencial `tablero-interno` lleva el centinela de vigencia de producción siendo de pruebas.**
  Es una fila sembrada a mano, no un defecto del código de emisión; al ordenar por caducidad
  aparecerá al final.
- **Sin dos partners con credenciales, el acotamiento pasa cualquier prueba.**
- **Un `403` con un usuario que no sea administrador local es la limitación conocida**, no un defecto
  de estos listados.
