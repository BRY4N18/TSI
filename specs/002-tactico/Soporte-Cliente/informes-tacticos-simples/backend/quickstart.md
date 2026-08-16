# Quickstart — Informes Tácticos Simples de Soporte al Cliente (Backend)

**Fecha:** 2026-08-14 · **Spec:** [`spec.md`](spec.md) · **Plan:** [`plan.md`](plan.md)

Cómo comprobar que los dos listados hacen lo que la spec dice. Esta guía **valida**, no implementa.

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
| `carlos.mendoza.admin@demo.tsi.com` | Administrador | Ver toda la cola |
| `ana.torres.cliente@demo.tsi.com` | Cliente | **Acotamiento del reportador** |
| `partner.demo@demo.tsi.com` | Partner de integración | **El otro reportador — SC-002** |
| `sofia.castro.operador@demo.tsi.com` | Operador | Comprobar el 403 |

> ⚠️ **Los dos reportadores deben pertenecer a cuentas distintas** y ambos tener tickets. Si comparten
> cuenta, SC-002 pasa sin demostrar nada.

**Datos que hay que garantizar antes de probar:**

- Un ticket **`sin compromiso`** (§3.2). La revisión anterior dejó el caso: un cliente sin
  suscripción activa que abre un ticket clasificado.
- Un ticket **sin clasificar**, para contrastar (§3.2).
- Un **escalado manual** y uno **automático por incumplimiento** (§3.3, §3.4).
- Un **aviso de plazo próximo** (`alerta_sla_riesgo`) sobre algún ticket, para comprobar que **no**
  aparece como escalado (§3.4).
- Si es posible, un usuario con rol de **Cliente y Agente a la vez** (§3.6).

---

## 3. Comprobación por escenario

### 3.1 Los dos responden

```bash
for r in tickets escalados; do echo "--- $r"; curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/$r"; done
```

**Esperado:** dos `200`. Sin filas, `200` con `data: []` — nunca `404`.

### 3.2 El ticket que nadie vigila *(SC-006 — el propósito del listado)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/tickets?situacion_compromiso=sin%20compromiso"
```

**Esperado:** aparece el ticket sin compromiso. **Si el listado lo omite o lo muestra como
`en curso`, está reintroduciendo el defecto que la corrección anterior resolvió**: es el único
estado en que un ticket puede quedarse indefinidamente sin que ningún proceso lo mire.

Contrastar con el ticket **sin clasificar**: debe aparecer con `situacion_compromiso` **ausente**,
no con un valor inventado.

### 3.3 El escalado automático es del sistema *(SC-005)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/escalados?tipo_escalado=automatico"
```

**Esperado:** `autor` **ausente** en todos, y `tipo_escalado` con valor `automatico`. Contrastar con
`?tipo_escalado=manual`: ahí `autor` trae el nombre del agente.

**Un escalado automático con el supervisor como autor es el defecto que se corrigió**: el supervisor
lo recibe, no lo ejecuta.

**Comprobación de coherencia**, que es la que de verdad importa: recorrer todos los escalados y
verificar que **ningún automático tiene autor** y **ningún manual carece de él**. Si las dos señales
se contradicen, el dato está corrupto.

### 3.4 Un aviso de plazo no es un escalado *(research D2)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/escalados?limit=500"
```

**Esperado:** el ticket que solo recibió un **aviso de plazo próximo** **no aparece**. Tampoco los
cierres automáticos por vencimiento.

Incluirlos inflaría el recuento de escalados con acciones que no cambiaron ni el agente ni el nivel.

### 3.5 El texto de los mensajes no sale *(SC-004, research D4)*

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/escalados" | grep -o 'mensaje\|es_nota_interna' || echo "LIMPIO"
```

**Esperado:** `LIMPIO`. No basta con que el filtro funcione: **la columna no debe consultarse**.
Verificar también en el código que el repositorio enumera columnas y no incluye el texto.

### 3.6 El acotamiento se decide por lo que NO se tiene *(SC-001, SC-002, SC-003)*

Con el token del **Cliente**:

```bash
curl -s -H "Authorization: Bearer $TOKEN_CLIENTE" "http://localhost:8000/api/v1/informes/soporte-cliente/tickets?limit=500"
```

**Esperado:** solo los de su cuenta, `meta.acotado_a = "propios"`, conteo estrictamente menor que el
del Administrador.

Con el token del **Partner**: **el mismo acotamiento**. Si el Partner ve los tickets del Cliente, el
acotamiento se está decidiendo por «ser Cliente» en vez de por «no atender tickets» — el fallo que
casi se cuela en la revisión anterior.

Con un usuario que sea **Cliente y Agente a la vez**: obtiene la **cola completa**, `acotado_a =
"todos"`. Tener un rol de atención saca del acotamiento.

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN_CLIENTE" "http://localhost:8000/api/v1/informes/soporte-cliente/tickets?cuenta=<ID_AJENA>"
```

**Esperado:** `403` **sin ninguna fila**.

> ⚠️ **Si el Cliente recibe `403` incluso sin indicar cuenta**, comprobar antes si es el
> **administrador local** de su organización. Hoy la pertenencia se resuelve por esa vía en todos los
> departamentos —la tabla de vínculos no la escribe ningún código—, así que un usuario que no lo sea
> no resuelve a ninguna cuenta. **Es una limitación conocida, no un defecto de estos endpoints.**

### 3.7 Los escalados son internos *(FR-008)*

Con el token del **Cliente** y con el del **Partner**: `escalados` responde **403** en ambos casos.

### 3.8 Nombres, no identificadores

**Esperado:** `cuenta` con la razón social, `agente_asignado` y `autor` con el nombre de la persona,
`servicio` con su nombre. Nunca `idcliente`, `idusuario` ni `idservicio`. El **número de ticket** sí
se muestra: es lenguaje de negocio.

### 3.9 Rango opcional donde corresponde *(FR-018)*

```bash
curl -s -w '\n%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/tickets?desde=2026-01-01&hasta=2026-08-14"
```

**Esperado:** `400` — es un listado de estado actual.

```bash
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/informes/soporte-cliente/escalados"
```

**Esperado:** `200` con el histórico completo.

---

## 4. Suites

```bash
cd backend && python -m pytest apps/soporte_cliente -q
```

```bash
cd backend && python -m pytest core/informes apps/cuentas_clientes apps/ventas_crm apps/suscripciones apps/red_operativa apps/informes_tacticos -q
```

**Esperado: verde sin cambios.** Este módulo **no modifica la capa transversal**, así que el segundo
comando debe pasar sin que nada se mueva. **Si algo se mueve, es que sí se tocó algo compartido** —
y este era precisamente el módulo que debía demostrar que no hacía falta.

---

## 5. Trampas del entorno

- **Retraso de ingesta 5–15 s.** Un ticket recién resuelto puede seguir apareciendo abierto. **No es
  un fallo.**
- **El doble en memoria sí puebla la tabla de vínculos**, cosa que el sistema real no hace. Las
  pruebas de acotamiento que se apoyen en el doble darán un resultado que en producción no ocurre;
  la comprobación de §3.6 debe hacerse contra el stack real.
- **Si el Partner y el Cliente comparten cuenta, SC-002 pasa sin demostrar nada.**
- **Un `403` con un usuario que no sea administrador local es la limitación conocida de D1**, no un
  defecto de estos listados.
