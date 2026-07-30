# Decision Log — Autenticación y RBAC

## DL-AUT-001: Rate limiting diferido (RNF-AUT-005)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-07-09 |
| **Estado** | Diferido |
| **Requisito** | RNF-AUT-005 |
| **Decisión** | No implementar política obligatoria de rate limiting/bloqueo/CAPTCHA en esta fase. |
| **Contexto** | Clarificación aprobada en Session 2026-07-09: la política de intentos fallidos se difiere a diseño operativo/arquitectura posterior. |
| **Alternativas evaluadas** | (1) Throttling DRF por IP/usuario — rechazado por contradecir clarificación. (2) CAPTCHA en login — rechazado, fuera de alcance actual. |
| **Impacto** | El endpoint `POST /api/v1/auth/login` no aplica throttling específico de intentos fallidos. DRF throttling general de `api-standards.md` queda como referencia futura. |
| **Revisión** | Reevaluar cuando se defina política operativa de seguridad perimetral. |
