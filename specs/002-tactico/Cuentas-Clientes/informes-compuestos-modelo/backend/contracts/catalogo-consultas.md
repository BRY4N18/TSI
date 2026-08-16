# Contrato — Catálogo de consultas de Cuentas y Clientes

**Fecha:** 2026-08-14 · **Data model:** [`../data-model.md`](../data-model.md)

Cada informe es **un fichero SQL parametrizado** en `dags/lib/consultas/cuentas/`. Rigen las
convenciones del
[catálogo de Emergencias](../../../Emergencias/informes-compuestos-modelo/backend/contracts/catalogo-consultas.md) §1.

---

## 1. La regla de la versión final, por tabla ⚠️

| Tabla | ¿`FINAL`? |
|---|---|
| `dim_cliente`, `dim_plan`, `dim_rol`, `dim_usuario_rol`, `dim_usuario_organizacion`, `dim_etapa_onboarding` | **Obligatorio** |
| `hecho_onboarding`, `hecho_sesion` | **Prohibido** — transacción |

---

## 2. Cuatro reglas propias del departamento ⚠️

1. **El embudo se calcula contra `dim_etapa_onboarding`**, nunca sobre las etapas observadas. Una
   consulta que agrupe solo por las etapas presentes **oculta la etapa donde todos abandonan**.
2. **La duración de sesión solo sobre las que tienen cierre**, y las abiertas se cuentan aparte.
3. **La concurrencia se mide por solape de intervalos**, no contando inicios.
4. **Ninguna consulta devuelve token, nombre, correo, identificación, teléfono, género ni fecha de
   nacimiento.** Solo el informe de roles devuelve una clave de usuario.

Las cuatro se verifican con pruebas sobre el **texto** de las consultas.

---

## 3. Parámetros propios

| Parámetro | Informe | Por defecto |
|---|---|---|
| `dias_inactividad` | #4 cuentas en riesgo | `90` |
| `franjas` | #8 concurrencia | `madrugada,manana,tarde,noche` |
| `pares_incompatibles` | #9 roles | **vacío** — sin política, el informe devuelve vacío |
| `mes_cohorte` | #1 churn | mes natural |

⚠️ **`pares_incompatibles` vacío por defecto es deliberado.** El multi-rol es el mecanismo previsto
del sistema: un informe que marcara «más de un rol» estaría denunciando el funcionamiento normal.
**Sin política declarada por el negocio, no hay hallazgo.**

---

## 4. Los 9 ficheros

### OT17 — Ciclo de vida

| Fichero | Devuelve |
|---|---|
| `ot17_churn_por_cohorte.sql` | `cohorte_alta, clientes_iniciales, bajas, pct_churn, motivo` |
| `ot17_antiguedad_media.sql` | `tipo_cliente, plan, clientes, dias_mediana` |
| `ot17_usuarios_vs_tope.sql` | `idcliente, usuarios_conocidos, tope_plan, pct_ocupacion, pct_cobertura_pertenencia` |
| `ot17_cuentas_en_riesgo.sql` | `idcliente, ultima_sesion, dias_sin_actividad, sin_actividad_conocida` |

⚠️ **`ot17_churn_por_cohorte.sql`** agrupa por **cohorte de alta**. Agrupar por mes de baja mediría
cuándo se fue la gente, no qué cohortes retienen peor — y mezclaría cohortes de tamaños muy
distintos en el mismo número.

⚠️ **`ot17_usuarios_vs_tope.sql`** devuelve `pct_cobertura_pertenencia`. Sin ese número, «1 de 10
usuarios» se lee como **ocupación real** cuando hoy es **cobertura del dato**: solo el 9,5 % de los
usuarios tiene organización conocida.

⚠️ **`ot17_cuentas_en_riesgo.sql`** distingue `sin_actividad_conocida = 1` de un número alto de días.
**Nunca haber entrado y haber entrado hoy son lo contrario**, y un cero los confundiría.

### OT04 — Incorporación

| Fichero | Devuelve |
|---|---|
| `ot04_tiempo_onboarding.sql` | `periodo, clientes_completados, dias_mediana, en_proceso` |
| `ot04_embudo_abandono.sql` | `orden, etapa, clientes_que_llegaron, pct_supera, detenidos_aqui` |
| `ot04_tasa_aprobacion.sql` | `periodo, tipo_organizacion, solicitudes, aprobadas, rechazadas, pct` |

⚠️ **`ot04_embudo_abandono.sql`** parte de `dim_etapa_onboarding` y **cuenta ausencias**. Debe
devolver **todas las etapas del catálogo**, incluidas las que **nadie ha completado nunca** — que son
precisamente donde está el problema.

⚠️ **`ot04_tiempo_onboarding.sql`**: los clientes **aún en proceso** van en `en_proceso` y **fuera de
la mediana**.

### OT18 — Acceso

| Fichero | Devuelve |
|---|---|
| `ot18_concurrencia_sesiones.sql` | `fecha, franja, concurrencia_maxima, sesiones_iniciadas, duracion_mediana, sesiones_sin_cierre` |
| `ot18_roles_incompatibles.sql` | `idusuario, rol_a, rol_b, par_declarado` |

⚠️ **`ot18_concurrencia_sesiones.sql`** devuelve `sesiones_sin_cierre` junto a la duración. Con 513
inicios y 195 cierres, una mediana sin ese contexto describe **el 27 % de las sesiones** como si
fueran todas.

Una sesión que **cruza la medianoche** cuenta en ambas franjas, así que **la suma de franjas es mayor
que el total de sesiones**. El informe lo declara para que no parezca un error de conteo.

⚠️ **`ot18_roles_incompatibles.sql`** devuelve `idusuario`, **nunca su nombre**, y **nombra los dos
roles** de la combinación: el hallazgo es la combinación, no la persona.

---

## 5. Reglas de resultado

Las comunes, más dos propias:

| Regla | Detalle |
|---|---|
| **Declarar la cobertura del dato** | Los informes de pertenencia dicen qué porcentaje de usuarios la tiene conocida |
| **Declarar el solape de franjas** | La concurrencia avisa de que la suma de franjas excede el total |

---

## 6. Lo que ninguna consulta puede devolver

| Excluido | Aunque |
|---|---|
| **Token de sesión** | Está en la misma tabla que todo lo demás de la sesión |
| Nombre, correo, identificación, teléfono | El informe de roles señala a una persona |
| **Género y fecha de nacimiento** | Están en la tabla de usuarios |
| Identificador fiscal del cliente | Ya excluido por Suscripciones |
