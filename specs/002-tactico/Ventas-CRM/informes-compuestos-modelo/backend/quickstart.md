# Quickstart — Informes Compuestos de Ventas y CRM

**Fecha:** 2026-08-14 · **Plan:** [`plan.md`](plan.md)

---

## 1. Prerrequisitos

1. El modelo analítico cargado y sus flujos corriendo.
2. **Las fases 1 y 2 de Emergencias implementadas** — este módulo reutiliza su plomería y no crea
   ninguna propia.

```bash
docker exec -w /opt/airflow tactico-airflow-scheduler python -m pytest dags/tests -q
```

---

## 2. Comprobación por escenario

### 2.1 Convertido y perdido no se cuentan juntos ⚠️ *(SC-002)*

**Es la comprobación de fondo del departamento.**

```sql
SELECT desenlace, count() FROM dim_prospecto FINAL GROUP BY desenlace
```

**Esperado:** tres grupos —`convertido`, `perdido`, `en_curso`— con 2, 1 y 7 respectivamente sobre
los datos actuales.

Comparar con el origen, donde **2 convertidos y 1 perdido comparten `activo = false`**. Si el modelo
solo distingue dos grupos, el desenlace se derivó de la columna equivocada y **el informe de embudo
presentará el éxito y el fracaso como lo mismo**.

### 2.2 El prospecto estancado es el más lento, no el más rápido ⚠️ *(SC-004)*

1. Tomar un prospecto que lleve semanas en la misma etapa **sin transiciones**.
2. Pedir la permanencia por etapa.

**Esperado:** aparece con **la permanencia mayor**, y se cuenta en `abiertos`.

Si no aparece, la consulta solo mide etapas ya abandonadas — y **deja fuera exactamente a los
prospectos que el informe existe para encontrar**.

### 2.3 El embudo cuadra *(SC-003)*

Para cada etapa: los que entran son iguales a los que salen más los que permanecen.

**Esperado:** cuadra, con los retrocesos contados como transición y declarados.

### 2.4 La carga histórica no se reescribe *(SC-005)*

1. Pedir la carga por ejecutivo de un período pasado.
2. Reasignar un prospecto a otro ejecutivo.
3. Volver a pedir **el mismo período**.

**Esperado:** idéntico. ⚠️ **Aquí la atribución es exacta desde el primer día**, a diferencia de la
unidad y la región: `Fact_Asignacion` sí guarda el instante de cada cambio.

### 2.5 Los canales suman el total *(SC-006)*

**Esperado:** la suma de todos los canales, incluido `Desconocido`, es igual al total de prospectos
del período. Si es menor, los prospectos sin canal se están descartando.

### 2.6 Ningún dato personal sale por la API ⚠️ *(SC-007)*

```sql
DESCRIBE TABLE dim_prospecto
```

**Esperado:** ninguna columna de nombre, apellidos, correo, teléfono ni cargo. **No están filtradas:
no existen.**

Repetir con un usuario que tenga la autoridad departamental: la exención de acotamiento **no alcanza
al dato personal**.

### 2.7 El informe de canales no trae coste, ni vacío ⚠️

Pedir «convertidos por canal» y revisar la respuesta.

**Esperado:** ninguna clave `coste`, `importe` ni `inversion` — **ni siquiera con valor nulo**. Y
`nota_indicador` presente, declarando que es la parte medible del CAC.

Una columna de coste vacía es una invitación a rellenarla desde el frontend, y entonces el tablero
mostraría un CAC que el sistema no puede sostener.

### 2.8 Un aviso ignorado no mejora la latencia ⚠️

Con datos sintéticos: una notificación **sin ningún avance posterior** del prospecto.

**Esperado:** cuenta en `sin_reaccion` y **queda fuera de la mediana**. Si se contara como cero, los
avisos ignorados **mejorarían** el indicador — al revés de la realidad.

### 2.9 «No hubo demos» no es «hubo demos y no se usaron» *(SC-009)*

**Esperado:** con las fuentes vacías de hoy, los informes de OT03 devuelven `data: []`. Con demos
registradas pero sin interacciones, devuelven filas con valores en cero.

Son **conclusiones opuestas sobre el producto**, y el informe debe permitir distinguirlas.

### 2.10 Un ejecutivo solo ve lo suyo *(SC-008)*

**Esperado:** un ejecutivo comercial obtiene los informes acotados a sus prospectos, con `acotado_a`
en la meta. El Director de Marketing los ve todos.

---

## 3. Verificación de que nada se movió

```bash
cd backend && python -m pytest -q
```

**Esperado:** verde, y **las cifras de Emergencias y Red Operativa sin cambios** (SC-010).

---

## 4. Trampas conocidas

- **Leer `activo` para saber el desenlace.** Cubre convertido y perdido a la vez. El modelo expone
  `desenlace`; ninguna consulta debe volver a esa columna.
- **Medir el embudo sobre el estado actual.** No dice por dónde pasó el prospecto.
- **Olvidar el tramo abierto** en la permanencia. Deja fuera a los estancados.
- **Contar un aviso ignorado como latencia cero.** Mejora el indicador con los peores casos.
- **Tratar los pesos del pipeline como una política.** Son una convención del informe: el sistema no
  define ninguna.
- **Volúmenes de dos dígitos.** 10 prospectos y 24 transiciones: el embudo es correcto y **no es
  representativo**.
- **Dos fuentes vacías en OT03.** Es de entorno, no de diseño: sus repositorios sí publican a Kafka.
  Las pruebas van con datos sintéticos, porque con la fuente vacía **una consulta rota y un origen
  vacío se ven igual**.
