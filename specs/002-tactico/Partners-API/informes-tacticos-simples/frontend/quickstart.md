# Quickstart — Cinco listados, dos audiencias (Partners y API)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso. Las más fáciles de olvidar: el Director
Tecnológico con `403` (FR-014a) y el Partner con un enlace a versiones que el guard cierra.

## Prerrequisitos

- Backend de los cinco listados en servicio, **con FR-014a cerrado** (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuarios:

| Correo | Clave | Rol | Para qué |
|---|---|---|---|
| `maria.suarez.dev@demo.tsi.com` | `password123` | DesarrolladorAPIs | Cinco listados, bandeja de credenciales |
| `director.tecnologico@demo.tsi.com` | `Tactico2026!` | DirectorTecnologico | FR-014a: entra a los cinco, `acotado_a: todos` |
| `carlos.mendoza.admin@demo.tsi.com` | `password123` | Administrador | Igual que gestor |
| `partner.demo@demo.tsi.com` | `password123` | PartnerIntegracion | Tres listados, aviso `propios` |
| `sofia.castro.operador@demo.tsi.com` | `password123` | Operador | Exclusión |

## 1. El Director entra a los cinco; el Partner ve tres

Abrir `http://localhost:4200/partners/informes` como Director Tecnológico.

**Esperado:** el menú muestra **Informes de partners** (no «Estado de mi acceso»). El índice tiene
**cinco** enlaces. Abrir versiones y alcance → 200, sin aviso de acotamiento.

Como Partner, la misma URL.

**Esperado:** el menú muestra **Estado de mi acceso**. El índice tiene **tres** enlaces. No hay
versiones ni alcance, ni en gris. `/partners/informes/versiones-contrato` → access-denied, no tabla
vacía.

## 2. El aviso de alcance acompaña al vacío

Como Partner, filtrar credenciales hasta no obtener filas (p. ej. `caduca_en_dias=0` si no hay
ninguna que caduque hoy, o un entorno que el partner no tenga).

**Esperado:** vacío de dominio **y** aviso de que solo ve los suyos. No un «no hay credenciales» que
parezca del sistema entero.

Como Desarrollador de APIs, el mismo listado **sin** aviso permanente.

## 3. Inactiva no dice por qué; la bitácora sí

Como gestor, abrir credenciales de un partner con una revocada y otra apagada por cascada (siembra
de las pruebas de backend; si el demo no las tiene, el tipo en bitácora igual no se agrupa).

**Esperado:**

- En credenciales: columna `activa`, **ninguna** de motivo, **ningún** secreto.
- En cambios de acceso: `revocacion_credencial` y `desactivacion_por_cascada` se leen distintos.
- El selector de fechas **solo** está en cambios de acceso.
- El filtro de entorno ofrece `Sandbox` y `Producción` (con tilde). Elegir uno no produce `400`.

## 4. Ausente no es ilimitado ni 1970

Alcance de datos: un cliente sin preferencias → zonas **ausentes**, no «todas».
Partners no suspendido → fecha/motivo de suspensión ausentes.
Reactivación en bitácora → motivo ausente.
Versión retirada → **aparece**, con fecha de retiro.

## 5. 400 no es tabla vacía; 403 no es vacío

Como gestor, forzar un `estado` inventado en partners (si la UI no lo permite, la prueba
automática basta; en navegador, un enum bien hecho **no** llega a `400`).

**Esperado:** si llega `400`, se lee el `detail` y **no** hay Reintentar. Un Operador en
`/partners/informes` → negativa, no lista vacía.

## 6. Consola, portal y logs no cambiaron

`/partners/consola` y `/partners/portal` siguen siendo las superficies operativas. **No** hay un
sexto listado de llamadas rechazadas: eso sigue en `/partners/consola/logs`. El Partner **no** ve
la consola; el gestor **no** ve el portal.

## 7. Paginación opaca

Un listado con más de una página: siguiente y anterior. **Cero** «página 3 de N» y **cero**
«120 registros».

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Motivo de inactividad en la fila de la credencial (prohibido).
- Abrir al Director la consola operativa (fuera de alcance).
- Informes compuestos de Partners (spec-only).
- Recorrer el `quickstart` de backend contra Pinot real (T044 de backend, distinto).
