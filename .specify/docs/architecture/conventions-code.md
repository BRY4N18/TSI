# Convenciones de Código — TSI

**Ubicación de este archivo:** `docs/arquitectura/convenciones-codigo.md`
**Última actualización:** 2026-07-20

> Convenciones de estilo y nombrado. Si tu IDE ya las aplica vía linter configurado (`.eslintrc`, `ruff.toml`), este archivo es solo referencia humana — la fuente de verdad real es la configuración del linter.

---

| Lenguaje         | Convención                                                                                                                          | Herramienta               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| Python           | PEP 8, `snake_case` para variables/funciones, `UPPER_CASE` para constantes, `PascalCase` para clases                                | Ruff (linter + formatter) |
| TypeScript       | Angular Style Guide oficial, `camelCase` para variables/funciones, `PascalCase` para clases/componentes, `kebab-case` para archivos | ESLint + Prettier         |
| HTML/CSS         | `kebab-case` para atributos y clases                                                                                                | Prettier                  |
| Commits          | Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`                                                      | Estándar                  |
| Archivos Django  | Un app por dominio de negocio, nombres en plural o snake_case (`cuentas_clientes/`, `soporte_cliente/`, `accidentes/`, `marketplace_proveedores/`) — ver `project-structure.md` para la lista completa de las 12 apps | — |
| Archivos Angular | Un archivo por componente/servicio, sufijo por tipo (`*.component.ts`, `*.service.ts`, `*.module.ts`)                               | Angular CLI               |
