# Quickstart — Informes Compuestos de Suscripciones y Facturación

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

---

## 1. Prerrequisitos

1. El modelo analítico cargado y sus flujos corriendo.
2. **Las fases 1 y 2 de Emergencias implementadas** — este módulo reutiliza su plomería.

```bash
docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q
```

---

## 2. Comprobación por escenario

### 2.1 Una suscripción cancelada no aporta MRR ⚠️ *(SC-002)*

**Es la comprobación de fondo del departamento.**

```sql
SELECT estado_derivado, count() FROM hecho_suscripcion FINAL GROUP BY estado_derivado
```

Comparar con el origen, donde **una suscripción `Cancelada` tiene `activo = true`**.

**Esperado:** aparece como `cancelada`, y **no suma al MRR**. Si el MRR incluye su precio, el estado
se derivó de la columna equivocada y **el ingreso recurrente está inflado**.

### 2.2 El MRR normaliza, y declara lo que no puede normalizar *(SC-003)*

**Esperado:** la cifra es la suma de los precios **mensualizados** de las suscripciones vigentes. Y
la suscripción **sin periodicidad** aparece en `sin_periodicidad`, **no** repartida como si fuera
mensual ni contada como cero.

Comprobar también que los cuatro componentes —nuevo, expansión, contracción, baja— **suman la
variación neta** (SC-008).

### 2.3 La vigencia invertida no produce números negativos ⚠️ *(SC-004)*

```sql
SELECT count() FROM hecho_suscripcion FINAL WHERE vigencia_inconsistente = 1
```

**Esperado:** 1 con los datos actuales. Y **ninguna métrica de duración devuelve un valor negativo**.

⚠️ **Esa fila no se corrige ni se descarta**: corregirla borraría la evidencia del defecto, y
descartarla perdería un ingreso real. Se aísla y se cuenta.

### 2.4 Una factura en disputa no es impaga *(SC-005)*

**Esperado:** no aparece entre las impagas ni suma días de mora. Disputar no es no pagar, y
mezclarlas convierte una discrepancia comercial en un problema de cobro.

### 2.5 Las notas de crédito restan *(SC-006)*

Pedir los ingresos de un período con una nota de crédito, y comparar con el mismo cálculo sobre
`monto_total` sin signo.

**Esperado:** el ingreso neto es **menor**. Si coinciden, la consulta está sumando importes sin signo
y **los ingresos están inflados**.

### 2.6 Una solicitud pendiente no se resolvió en cero *(SC-007)*

**Esperado:** las pendientes se cuentan en `pendientes` y **quedan fuera de la mediana**. Contarlas
como cero haría que las solicitudes olvidadas **mejoraran** el tiempo de resolución.

### 2.7 Nada sensible sale por la API ⚠️ *(SC-009)*

```sql
DESCRIBE TABLE dim_cliente
```

**Esperado:** ni token de pasarela, ni últimos dígitos, ni identificador fiscal. **No filtrados: no
existen.** Solo `tiene_metodo_pago` y `metodo_pago_caduca`.

Y ningún informe desglosa por administrador. Repetir con un usuario que tenga la autoridad: la
exención **no alcanza al dato sensible**.

### 2.8 La utilización de límites no inventa la dimensión que falta ⚠️

**Esperado:** la respuesta trae unidades y usuarios con sus límites, y **ninguna clave de llamadas
API — ni siquiera nula**. `nota_dimension_pendiente` lo declara en texto.

Un `llamadas: null` diría «este cliente no consume la API». No es lo mismo que «todavía no lo
medimos».

### 2.9 La autoridad repartida se respeta

Pedir los informes con el **Director Financiero** y con el **Director de Estrategia**.

**Esperado:** el Financiero accede a facturación, cobro y cartera; el de Estrategia, a los tres de
catálogo. **Ninguno de los dos cubre la materia del otro.**

### 2.10 Un plan de precio cero no desaparece *(SC-010)*

**Esperado:** cuenta en el reparto de clientes y aporta **cero** en ingreso, con ambas cifras
visibles. Un plan demo no es ni un éxito ni una ausencia.

---

## 3. Verificación de que nada se movió

```bash
cd backend && python -m pytest -q
```

**Esperado:** verde, y **las cifras de los tres departamentos anteriores sin cambios** (SC-011).

---

## 4. Trampas conocidas

- ⚠️ **Olvidar la versión final en `hecho_suscripcion`.** Es el único hecho acumulado de este
  módulo; los otros dos son de transacción, así que la costumbre lleva a no forzarla — y aquí eso
  **cuenta dos veces una suscripción actualizada e infla el MRR de forma intermitente**.
- **Leer `activo` para saber si está vigente.** Hay canceladas con esa columna en verdadero.
- **Sumar `monto_total` en vez de `monto_con_signo`.** Las notas de crédito dejarían de restar.
- **Tomar `motivocancelacion` como señal de cancelación.** Está poblado en suscripciones activas.
- **Tratar `idplan_programado = 0` como un plan.** Es un centinela: significa «ninguno».
- **Usar rangos arbitrarios para MRR o NRR.** Comparar dos ventanas móviles solapadas no es comparar;
  el endpoint resuelve al mes natural y lo declara.
- **Volúmenes de un dígito.** 4 suscripciones y 6 facturas: **los cinco indicadores BSC serán
  correctos y no representativos** hasta que crezca la cartera. Que dos de cuatro filas ya traigan un
  defecto es lo que debería preocupar, no la cifra.
