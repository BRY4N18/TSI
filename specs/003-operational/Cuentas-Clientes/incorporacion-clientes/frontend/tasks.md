# Tasks: Incorporación de Clientes — Frontend

**Prerequisites**: Backend OpenAPI incorporacion-clientes.

## Phase 1: Autorregistro (FR-UI-001)

- [X] T-FE-001 `autorregistro.page.ts` + ruta pública en `app.routes.ts`
- [X] T-FE-002 `IncorporacionClienteApiService.registrarCuenta` + spec
- [X] T-FE-003 Tipos TS desde OpenAPI en `models/incorporacion-cliente.contract.ts`

## Phase 2: Aprobación Admin (FR-UI-002, 003, 008)

- [X] T-FE-004 `aprobacion-solicitudes.page.ts` + ruta `/solicitudes`
- [X] T-FE-005 Acciones aprobar/rechazar/anular + reenvío invitación
- [X] T-FE-006 Sin enlaces a flujos O01/O12 retirados

## Phase 3: Wizard onboarding (FR-UI-004…007, 009, 010)

- [X] T-FE-007 `onboarding-wizard.page.ts` — etapas canónicas
- [X] T-FE-008 Logo en `perfil_corporativo`
- [X] T-FE-009 `OnboardingFacadeService` + guards (admin-local, pendiente, completado)
- [X] T-FE-010 Jasmine guards + facade specs

## Phase 4: Polish (FR-UI-012)

- [X] T-FE-011 Mensajes 403 cuenta no activa en wizard

**Checkpoint**: FR-UI-001…012 implementados.
