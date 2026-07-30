<!-- SPECKIT START -->

Project Rules

For any development task, the agent MUST first read the file .specify/memory/constitution.md to understand the architecture and standards. The operational specifications of the forms are located in specs/operational/.

**Layered operational modules (`specs/003-operational`):** modules use `{module}/{backend|frontend}` with an index file named `{module}.md` (not README). Speckit `feature.json` points to **one active layer** (backend first, then frontend). **Phase B:** each `frontend/spec.md` holds FR-UI (Interaction Capability) with `Depends-on` backend — do not duplicate OpenAPI/data-model. Create new layered modules with `create-new-feature.ps1 -Layered`.

<!-- SPECKIT END -->
