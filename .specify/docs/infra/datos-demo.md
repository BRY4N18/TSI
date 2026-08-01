# Datos demo y seeds

Convenciones que deben respetar todos los scripts que siembran datos en entornos de
desarrollo y prueba. Existe porque los seeds se escribieron por separado y llegaron a
contradecirse entre sí, borrando datos que otro seed había creado.

## Fuente única de constantes

`backend/scripts/_demo_seed_common.py` es la autoridad para todo lo compartido:

| Constante | Qué define |
|---|---|
| `DEMO_PASSWORD` | Contraseña única de todas las cuentas demo |
| `ESTADO_CREDENCIAL_ACTIVO` | Debe coincidir con `credential_repository.ESTADO_CREDENCIAL_ACTIVO` |
| `DEMO_DOMAIN` | Dominio de los correos demo; `e2e/fixtures/auth.fixture.ts` usa el mismo |
| `ROLES_DEMO` / `ROL_ID_POR_NOMBRE` | Catálogo canónico de `Dim_Rol` |

Vive en `backend/scripts/` porque es la única ruta presente **tanto** en el repo del host
(donde corren los seeds de `database/`) **como** dentro del contenedor Django en
`/app/scripts` (donde corren los de `backend/scripts/`). Los seeds del host lo importan
agregando esa carpeta al `sys.path`.

## Reglas

1. **Ningún seed hardcodea contraseñas, ids de rol ni valores de enum.** Todo sale del
   módulo compartido. Convivían dos contraseñas (`Demo1234!` y `password123`) y la misma
   cuenta pedía una u otra según cuál seed hubiera corrido último.

2. **Ningún seed hardcodea claves primarias de entidades que otro seed pueda crear.**
   Las tablas de Pinot son **upsert por clave primaria**: reusar un id no agrega un
   registro, reemplaza el que estuviera ahí. `seed_demo_director_estrategia.py`
   hardcodeaba `USER_ID = 12` y borró al Gerente de Ventas al ejecutarse. Usar
   `_siguiente_id(...)` o resolver por una clave natural (gmail, nombre de rol).

3. **Los vínculos se resuelven por clave natural, no por id fijo.** `seed_flota_demo.py`
   ligaba unidades a `idusuario=4` asumiendo que ese usuario tenía rol `Unidad`; al
   cambiar el catálogo de roles quedó ligada a un Operador, y esa unidad no podía iniciar
   sesión (CU-O30 `find_by_usuario` → 403). Ahora resuelve los usuarios **por nombre de
   rol**.

4. **Publicar el registro completo, nunca parcial.** Con upsert, un payload sin alguna
   columna la deja en el centinela de nulo de Pinot (`-2147483648` para INT). Así se
   crearon filas huérfanas en `Dim_Usuario_Cliente`.

5. **Todo seed debe ser idempotente.** Correrlo dos veces no debe cambiar el resultado ni
   duplicar filas.

## Scripts

| Script | Dónde corre | Qué siembra |
|---|---|---|
| `database/seed_usuarios.py` | host | Catálogo de roles, usuarios demo, credenciales |
| `database/seed_catalogos.py` | host | Catálogos geográficos y de dominio |
| `database/seed_soporte.py` | host | Cliente corporativo, plan, suscripción, tickets |
| `database/seed_vinculos.py` | host | `Dim_Usuario_Cliente`, `Dim_CondadoVecino`, preferencias del cliente |
| `database/seed_flota_demo.py` | host | Flota mínima ligada a usuarios con rol `Unidad` |
| `backend/scripts/seed_demo_*.py` | contenedor | Usuarios de rol específico (Operador, GerenteVentas, DirectorEstrategia, Proveedor) |

## Mantenimiento

| Script | Para qué |
|---|---|
| `database/higiene_datos.py` | Desactiva unidades de prueba y huérfanas, consolida roles duplicados, sanea descripciones. Acepta `--dry-run` |
| `database/migra_estadocredencial.py` | Unifica `estadocredencial` al valor canónico. Acepta `--dry-run` |
| `database/reset_despachos_demo.py` | Libera despachos activos y devuelve unidades a `Activa`, para que la flota demo no se agote tras varias corridas de flujo end-to-end. No cierra el caso — solo resetea el estado operativo de la flota. Acepta `--dry-run` |

Correr `higiene_datos.py` y `reset_despachos_demo.py` después de cada recorrido
end-to-end deja el entorno listo para el siguiente.

## Verificación automática

Dos tests de regresión impiden que estas convenciones se rompan en silencio:

- `backend/tests/regression/test_credenciales_demo_consistentes.py` — contraseña única,
  enum de `estadocredencial`, catálogo de roles sin nombres repetidos y fixture E2E
  apuntando a cuentas del dominio demo.
- `backend/tests/regression/test_doble_pinot_vs_esquemas.py` — el doble en memoria de
  `conftest.py` y `database/esquemas.json` describen el mismo conjunto de tablas.
