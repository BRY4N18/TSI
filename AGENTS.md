<!-- SPECKIT START -->

Project Rules

For any development task, the agent MUST first read the file .specify/memory/constitution.md to understand the architecture and standards. The operational specifications of the forms are located in specs/operational/.

**Layered operational modules (`specs/003-operational`):** modules use `{module}/{backend|frontend}` with an index file named `{module}.md` (not README). Speckit `feature.json` points to **one active layer** (backend first, then frontend). **Phase B:** each `frontend/spec.md` holds FR-UI (Interaction Capability) with `Depends-on` backend — do not duplicate OpenAPI/data-model. Create new layered modules with `create-new-feature.ps1 -Layered`.

<!-- SPECKIT END -->

## Regla de documentación obligatoria

**Todo cambio de código debe quedar documentado en el documento que le corresponda**, en el
mismo trabajo que lo introduce. No es opcional ni depende de que alguien lo pida: en SDD la
fuente de verdad son las specs, y un cambio sin su contraparte documental deja la spec
mintiendo a quien la lea después.

Dónde escribir, según la naturaleza del cambio:

| Cambio | Documento |
|---|---|
| Corrección fuera del ciclo `/plan`→`/tasks` (bug detectado al probar, refactor) | `.specify/docs/changelog.md` |
| Requisito funcional o de UI (`FR-*`, `RF-*`) | `specs/.../spec.md` |
| Cualquier forma de request/response | `specs/.../contracts/*.openapi.yaml` |
| Modelo de datos, tablas nuevas o columnas | `specs/.../data-model.md` |
| Criterio de aceptación afectado | `specs/.../traceability.md` |
| Regla global de diseño | `.specify/docs/design/design-system.md` |

Reglas de resolución:

- El `design-system.md` es la **autoridad** en diseño: un `spec.md` de módulo no puede
  relajar una regla global. Si contradice, se corrige el spec del módulo.
- Si al implementar se descubre que la spec estaba equivocada, **se corrige la spec y se
  anota por qué** — nunca adaptar el código a una spec incorrecta en silencio.
- Las entradas de `changelog.md` llevan código de hallazgo (`D1`, `B2`, `F3`…), causa,
  efecto verificado y archivo tocado, y se referencian desde el `traceability.md` afectado.
