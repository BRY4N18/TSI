# Implementation Plan: OE2 — Monetización del Ecosistema de APIs

**Branch**: `001-estrategico/OE2-monetizacion-api/backend` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE2-monetizacion-api/backend/spec.md`

---

## Summary

Diez de los once informes de OE2, cada uno una consulta sobre el modelo que Partners ya cargó.
**Cero tablas nuevas.** E2-06 no tiene endpoint.

El táctico de Partners desbloqueó el plan (2026-08-18). Lo que este módulo añade no es el hecho:
es la ventana comparada, el percentil con muestra mínima, el excedente **facturable** (no cobrado)
y la exclusión de cualquier rol partner.

**La investigación no mueve el recuento de la spec:** 10 construibles, 1 bloqueado, 2 parciales
(E2-01, E2-02). E2-08 sigue construible.

---

## Technical Context

**Language/Version**: Python 3.11 (Django) para HTTP · SQL de ClickHouse para las consultas

**Primary Dependencies**: Django + DRF · armazón `informes_estrategicos` (OE6/OE3/OE4) ·
`ModeloEstrategicoRepository`

**Storage**: ClickHouse `tsi_tactico`. **Sin ALTER.** Lectura de `hecho_llamada_api`,
`dim_partner`, `dim_plan`, `dim_version_contrato`, `hecho_factura` (excedente cobrado, no
facturable)

**Testing**: pytest. Contrato por endpoint, **exclusión de partner**, p95 ausente bajo muestra,
E2-06 = 404, OpenAPI sin secretos

**Target Platform**: `accidentes-django` · consultas en `dags/lib/consultas/estrategicos/oe2/`

**Project Type**: Servicio web de solo lectura — diez `GET`

**Performance Goals**: Regla 7 (filtro por `fecha`, partición mensual). El p95 corre sobre el
detalle; con el volumen actual (18 llamadas) es barato

**Constraints**:
- Período obligatorio
- Sin IP, hash de secreto, contacto técnico
- **Ningún partner en los diez**
- No usar agregado de consumo
- E2-01/E2-02: `cobertura: parcial` mientras falte precio de plan API
- E2-08 declara «facturable, no cobrado»

**Scale/Scope**: 10 publicados + 1 sin ruta · 4 partners / 18 llamadas en el origen demo ·
histórico acotado al log real

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Principio | Cómo se cumple | |
|---|---|:--:|
| **I. Idoneidad funcional como contrato** | Diez informes trazados a CU-E02/E04/E05 y al BSC. E2-06 se declara inmedible en vez de publicarse al 100 %. E2-08 se corrige respecto del catálogo (sí hay precio de excedente) | ✅ |
| **II. Fiabilidad operativa** | Lectura histórica. No está en el camino de despacho. Fallo del almacén → 503 | ⚪ *fuera de la cadena crítica* |
| **III. Eficiencia en tiempo real** | No toca despacho. Partición por mes | ✅ |
| **IV. Capacidad de interacción** | No aplica en esta capa. Frontend en `../frontend/` (implementado) | ⚪ |
| **V. Seguridad de la información** | Lista blanca de columnas. Sin secreto ni contacto. **Un partner no ve el ecosistema** (ventaja competitiva, no solo PII) | ✅ |
| **VI. Compatibilidad API-first** | OpenAPI bajo el envelope común. E2-09 es lo que permite retirar una versión sin romper integraciones a ciegas | ✅ |
| **VII. Mantenibilidad estructural** | Misma app `informes_estrategicos`. Cero DDL nuevo | ✅ |
| **VIII. Flexibilidad** | El ecosistema de partners es el vehículo de expansión; E2-11 lo mide. Sin eje de región | ✅ |
| **IX. Safety** | No aplica: ningún informe mueve ambulancias | ⚪ |

### Trade-off — Idoneidad vs Fiabilidad (E2-06)

- **En conflicto:** el catálogo pide uptime ≥99,9 %. El log no puede medirlo.
- **Qué se priorizó:** **Fiabilidad** (regla 2 del desempate; no hay Safety).
- **Lo aceptado:** 10 de 11. Un GET a disponibilidad responde 404.
- **Lo ganado:** nadie lee «100 %» porque no hubo filas de error.
- **Revisión:** cuando exista la misma fuente de monitoreo que desbloquea E3-01.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE2-monetizacion-api/
├── OE2-monetizacion-api.md
└── backend/
    ├── spec.md
    ├── plan.md                 # este archivo
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/informes-estrategicos-oe2.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                # lo crea /speckit-tasks, no este comando
```

### Source Code (repository root)

```text
backend/apps/informes_estrategicos/
├── services/oe2_service.py          # NUEVO — CATALOGO de 10, BLOQUEADOS de 1
├── views/oe2_views.py               # NUEVO
├── permissions.py                   # AMPLIAR — permiso por informe (dinero vs resto)
└── urls.py                          # AMPLIAR — oe4/<informe> ya existe; añadir oe2

dags/lib/consultas/estrategicos/oe2/ # 10 SQL; ningún e2_06_*.sql
```

**Structure Decision:** no hay app nueva. Igual que OE3 y OE4. El modelo de Partners **no se toca**.

---

## Constitution Re-Check (post-Phase 1)

Ningún gate cambió. El diseño refuerza V: la exclusión de partner es de **alcance competitivo**,
no solo de dato sensible, y el contrato OpenAPI no declara `disponibilidad-api`.

---

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, rechazada |
|---|---|---|
| **Permiso por informe** | Finanzas entra solo en tres rutas | *Un permiso de módulo*: el Tecnológico vería dinero o Finanzas vería latencias de todos |
| **E2-01/02 parciales** | El plan API no tiene `precio_lista` | *Ocultar los informes*: el volumen sí existe y el BSC los pide |
| **E2-06 sin ruta** | El log no mide minutos en silencio | *Publicar 100 %*: mentiría siempre |

---

## Risks

| Riesgo | Señal | Mitigación |
|---|---|---|
| Usar el agregado de consumo | Totales 40 vs 18 | Prueba de catálogo: ninguna consulta nombra tablas de agregado |
| Publicar p95 con 2 muestras | `percentil_fiable` ausente | Contrato + prueba: p95 `null` bajo `muestra_minima` |
| Un rol partner entra | 200 en comparativa | Prueba de **exclusión** con `PartnerIntegracion` |
| Confundir facturable con cobrado | E2-08 sin `alcance` | `alcance` obligatorio en E2-08 |
| Inventar E2-06 | Path en OpenAPI | El YAML no declara la ruta; GET → 404 |

---

## Lo que este plan deja para después

1. Precio y periodicidad del **plan de API** en `dim_plan` / `dim_partner` — completa E2-01 y E2-02.
2. Monitoreo de infraestructura — desbloquea E2-06 (y E3-01).
3. Frontend del tablero estratégico.
4. Semilla Pinot de `Gerente` si el entorno aún no la corrió.
