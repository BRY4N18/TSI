# Estándares de API REST — TSI

**Ubicación de este archivo:** `docs/arquitectura/api-standards.md`
**Última actualización:** 2026-07-09

---

| Aspecto          | Convención                                                                     | Ejemplo                                                                        |
| ---------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| URL base         | `/api/v1/` + plural kebab-case                                                 | `/api/v1/accidentes`, `/api/v1/usuarios`                                       |
| Autenticación    | Bearer JWT (generado y validado por Django)                                    | `Authorization: Bearer <token>`                                                |
| Formato de éxito | `{ "data": {...}, "meta": { "pagination": {...} } }`                           | `GET /api/v1/accidentes?cursor=abc&limit=20`                                   |
| Formato de error | `{ "error": "error_code", "detail": "mensaje", "code": "ERROR_CODE" }`         | `{ "error": "not_found", "detail": "Accidente no encontrado", "code": "404" }` |
| Paginación       | Basada en cursor (no en página)                                                | `?cursor=eyJsYXN0X2lkIjoxMH0=&limit=20`                                        |
| Rate limiting    | DRF throttling por rol/usuario                                                 | 30 req/min operador, 100 req/min admin                                         |
| Idempotencia     | Endpoints de escritura soportan header `Idempotency-Key`                       | `Idempotency-Key: uuid-v4`                                                     |
| Versionado       | Path de URL (`/api/v1/`, `/api/v2/`)                                           | Breaking change → nuevo path                                                   |
| Métodos          | GET (leer), POST (crear), PUT (reemplazar), PATCH (parcial), DELETE (eliminar) | Semántica HTTP estándar                                                        |
| Content-Type     | `application/json` en requests y responses                                     | —                                                                              |
| Tiempo real      | Server-Sent Events (SSE), no WebSocket — ver `infrastructure.md` sección 3.1 | `GET /api/v1/despacho/tracking/{idaccidente}/stream` con `Accept: text/event-stream` |
