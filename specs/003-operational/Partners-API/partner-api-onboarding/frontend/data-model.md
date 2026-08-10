# Phase 1 — Data Model (view models) y FR-UI propuestos

**Nada de este documento define reglas de negocio.** Los tipos son la proyección hacia la UI de los
esquemas ya cerrados en [`../backend/contracts/partner-api-onboarding.openapi.yaml`](../backend/contracts/partner-api-onboarding.openapi.yaml).
Si algo aquí contradice ese contrato, manda el contrato.

---

## 1. Tipos de la capa de servicios

Van en `frontend/src/app/modules/partners/services/models/partner.types.ts`.

### Estado derivado

```ts
export type EstadoPartner =
  | 'Registrado'
  | 'Plan asignado'
  | 'Pruebas activo'
  | 'Pendiente de aprobación'
  | 'Producción activa'
  | 'Suspendido';
```

Son los seis valores de `backend/apps/partners/domain_constants.py`. **Calculado por el backend; la
UI nunca lo escribe.**

### Entorno

```ts
export type Entorno = 'Sandbox' | 'Producción';
```

El acento de `'Producción'` es parte del valor, no una etiqueta: así viaja en el contrato.

### Partner

```ts
export interface PartnerListItem {
  idpartner: number;
  idcliente: number;
  nombrepartner: string;
  planapi: string;          // '' = sin plan (centinela, NO null)
  limitellamadasmes: number;    // -1 = sin cupo
  limitellamadasminuto: number; // -1 = sin cupo
  activo: boolean;
  estado: EstadoPartner;
}

export interface PartnerDetalle extends PartnerListItem {
  contacto_tecnico_nombre: string;
  contacto_tecnico_gmail: string;
  fecha_suspension: string;   // '' = sin suspensión
  motivo_suspension: string;  // '' = sin suspensión
  credenciales: CredencialItem[];
  historial: EventoHistorial[];
}
```

> **Los centinelas cruzan hasta la UI y hay que tratarlos.** Pinot no almacena NULL en este
> proyecto: un partner sin plan trae `planapi: ''` y `limitellamadasmes: -1`, no `null`. Renderizar
> `-1` como si fuera un cupo sería un defecto visible. Regla: **`-1` se muestra como «Sin asignar»**
> y `''` como «Sin plan», nunca el valor crudo.

### Credencial

```ts
export interface CredencialItem {
  idcredencial: number;
  nombre_credencial: string;
  entorno: Entorno;
  activo: boolean;
  fecha_creacion: number;    // epoch ms
  fecha_expiracion: number;  // epoch ms; 253402300799000 = no expira nunca
}

/** ÚNICA forma en la que el secreto entra al frontend. No se persiste jamás. */
export interface CredencialEmitida extends CredencialItem {
  client_id: string;
  client_secret: string;
}
```

> `fecha_expiracion === 253402300799000` es el centinela «no expira nunca» (año 9999). La UI **debe**
> renderizarlo como «No expira», nunca como una fecha. Mostrar «31/12/9999» sería técnicamente
> correcto y funcionalmente absurdo.

### Contrato de integración

```ts
export interface VersionContrato {
  idversion: number;
  id_servicio: number;
  version: string;
  estado: 'vigente' | 'soportada' | 'retirada';
  spec_url: string;    // '' = sin documento publicado
  fecha_publicacion: number;
  fecha_retiro: number; // 0 = sin retiro planificado (centinela)
}
```

`fecha_retiro === 0` significa «sin retiro planificado» y se muestra como tal, nunca como
01/01/1970.

---

## 2. Constantes de presentación

`estado-partner.constants.ts` — un mapa único, para que ningún componente decida por su cuenta cómo
se ve un estado:

| Estado | Ícono Tabler | Token semántico | Qué comunica |
|---|---|---|---|
| Registrado | `user-plus` | `informacion` | Existe, pero aún no puede operar |
| Plan asignado | `license` | `informacion` | Ya tiene cupo; puede emitir pruebas |
| Pruebas activo | `flask` | `exito` | Integrando en sandbox |
| Pendiente de aprobación | `clock-hour-4` | `alerta-media` | **Requiere acción de un Administrador** |
| Producción activa | `circle-check` | `exito` | Operando en producción |
| Suspendido | `ban` | `alerta-critica` | Bloqueado; toda acción de habilitación dará 409 |

`entorno.constants.ts`:

| Entorno | Ícono Tabler | Etiqueta | Nota de vigencia |
|---|---|---|---|
| Sandbox | `flask` | «Pruebas» | Vigencia finita; se avisa antes de vencer |
| Producción | `server-bolt` | «Producción» | No expira |

---

## 3. FR-UI — ⚠️ migrados a `spec.md`

> **Esta sección ya no es la autoridad.** `/speckit-specify` (2026-08-09) formalizó
> **FR-UI-001…034** en [`spec.md`](./spec.md), que es donde hay que leerlos y mantenerlos.
> La tabla de abajo se conserva solo como registro de la propuesta original del plan y **su
> numeración no coincide** con la definitiva.
>
> Tres requisitos de esta lista quedaron **derogados o corregidos** por esa sesión:
> - el antiguo FR-UI-003 (`eye` + `pencil`) → **solo `eye`**: no hay PATCH de ficha en el backend;
> - el antiguo FR-UI-009 (aprobar → paso del secreto) → el Administrador **no ve secretos ajenos**;
> - se añadió el descubrimiento del propio partner (`BE-DELTA-01`), sin el cual el portal no carga.

### Consola de partners (Administrador · Desarrollador de APIs)

| ID | Requisito | Traza |
|---|---|---|
| **FR-UI-001** | La lista muestra `nombrepartner`, plan, cupo mensual, estado (badge) y entorno activo, paginada por cursor con «Cargar más» | CA-PON-004, Decisión 9 |
| **FR-UI-002** | La lista filtra por estado, y ofrece el CTA «Registrar partner» siempre visible en la cabecera | design-system § 5 |
| **FR-UI-003** | Cada fila expone `eye` (Ver) y, para el gestor, `pencil` (Editar). Nunca `pencil` deshabilitado | design-system § 5 |
| **FR-UI-004** | El registro pide `nombrepartner`, contacto técnico (nombre y gmail) y **elige el cliente por nombre legible**, nunca tecleando `idcliente` | CA-PON-001, design-system § 5 |
| **FR-UI-005** | Un `409 partner_duplicado` se presenta señalando el partner que ya existe, con enlace a su detalle — no como error genérico | CA-PON-002 |
| **FR-UI-006** | Un `422 sin_suscripcion` explica que el cliente no tiene suscripción vigente y que eso se resuelve fuera de este módulo | CA-PON-003 |
| **FR-UI-007** | «Asignar plan de acceso» muestra el cupo **derivado** que quedará congelado, y advierte que un cambio posterior del plan del cliente no lo alterará | CA-PON-004 |
| **FR-UI-008** | La cola de solicitudes lista los partners en «Pendiente de aprobación», ordenados por antigüedad de la solicitud | CA-PON-009, Decisión 8 |
| **FR-UI-009** | Aprobar exige confirmación en 2 pasos y, al completarse, **navega al paso de secreto emitido** (la aprobación emite credencial de producción) | CA-PON-010, RF-PON-008 |
| **FR-UI-010** | Rechazar exige un motivo en texto libre con `minlength`, advirtiendo que se envía al contacto técnico | CA-PON-010, Decisión 3 |
| **FR-UI-011** | Las acciones de resolución **solo existen** para el rol Administrador; el Desarrollador de APIs no las ve ni alcanza su ruta | RF-PON-008 |

### Portal del partner (PartnerIntegracion)

| ID | Requisito | Traza |
|---|---|---|
| **FR-UI-012** | «Mi integración» muestra estado derivado, plan, cupo y contacto técnico, sin ningún control que edite el estado | Decisión 4 |
| **FR-UI-013** | Las credenciales se agrupan **bajo encabezados por entorno**, con ícono y etiqueta; el color no es el único distintivo | RN-PON-008, Decisión 5 |
| **FR-UI-014** | Emitir credencial pide un `nombre_credencial` y valida en cliente que no colisione con otra **activa del mismo entorno** | CA-PON-006 |
| **FR-UI-015** | Un `409 nombre_duplicado` se muestra como error del campo nombre, no como error global | CA-PON-006 |
| **FR-UI-016** | Si el partner no tiene plan, el CTA de emisión se sustituye por el copy que explica que un administrador debe asignarlo | CA-PON-007, `research.md` copy |
| **FR-UI-017** | El secreto se muestra **una sola vez**, en página dedicada, con copia explícita y confirmación de guardado que habilita la salida | CA-PON-005, Decisión 2 |
| **FR-UI-018** | La emisión envía `Idempotency-Key`, reutilizando la misma clave si el usuario reintenta tras un fallo de red | Decisión 7 |
| **FR-UI-019** | Una credencial vencida se distingue de una activa y ofrece regenerar por autoservicio, sin intervención de un gestor | CA-PON-008 |
| **FR-UI-020** | `fecha_expiracion` igual al centinela se muestra como «No expira»; nunca como fecha del año 9999 | Sección 1 |
| **FR-UI-021** | Solicitar producción solo está disponible en «Pruebas activo»; en cualquier otro estado se explica la ruta obligatoria en vez de fallar con 409 | CA-PON-009, RN-PON-004 |
| **FR-UI-022** | El contrato de integración se consulta **por servicio**, mostrando la vigente y las soportadas con su fecha de retiro | CA-PON-013 |

### Transversales

| ID | Requisito | Traza |
|---|---|---|
| **FR-UI-023** | Toda vista con datos asíncronos implementa loading / vacío / error con los componentes compartidos `app-list-*` | Decisión 10 |
| **FR-UI-024** | Ninguna respuesta ni vista expone `client_secret_hash` ni el secreto fuera del paso dedicado | CA-PON-005 |
| **FR-UI-025** | Ningún PK se pide al usuario ni se muestra como campo principal; los IDs viajan solo en el payload | design-system § 5 |
| **FR-UI-026** | El sidebar del partner y el del gestor son **distintos y no se fusionan** (departamentos distintos) | design-system § 5, Decisión 6 |
| **FR-UI-027** | Un partner con `activo: false` ve su estado «Suspendido» y las acciones de habilitación no se ofrecen | CA-PON-012, RN-PON-013 |

---

## 4. Transiciones de estado visibles en la UI

La UI **refleja** estas transiciones; no las provoca por su cuenta.

```
Registrado ──(asignar plan)──▶ Plan asignado ──(emitir credencial)──▶ Pruebas activo
                                                                            │
                                                        (solicitar producción)
                                                                            ▼
                                                            Pendiente de aprobación
                                                             │                  │
                                                     (aprobar)                (rechazar)
                                                             ▼                  │
                                                   Producción activa            │
                                                                                ▼
                                                                        Pruebas activo
```

Dos cosas que la UI debe comunicar y son fáciles de perder:

1. **El rechazo devuelve a «Pruebas activo», no a «Registrado».** El acceso de pruebas sigue vivo
   porque es donde el partner debe corregir. Y **no hay tope de reintentos**.
2. **Aprobar no desactiva las credenciales de pruebas.** Ambos entornos coexisten (RN-PON-008); una
   UI que sugiriera «ya pasaste a producción, lo de pruebas se acabó» estaría mintiendo.
