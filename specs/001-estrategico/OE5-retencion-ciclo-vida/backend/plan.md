# Implementation Plan: OE5 — Retención, Satisfacción y Ciclo de Vida

**Branch**: `001-estrategico/OE5-retencion-ciclo-vida/backend` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE5-retencion-ciclo-vida/backend/spec.md`

---

## Summary

Nueve de los quince informes de OE5, cada uno una consulta sobre el modelo que Soporte,
Suscripciones, Cuentas y Partners ya cargaron. **Cero tablas nuevas.** E5-01 y E5-11 no tienen
endpoint. E5-09/10/13/14 no existen en OE5: son de OE1.

El táctico desbloqueó el plan (2026-08-18). OE1 ya publicó los cuatro compartidos. Lo que este
módulo añade es el SLA con denominador de cerrados-con-compromiso, el NRR descompuesto (la SQL
táctica deja expansión/contracción en 0), el riesgo con ≥2 señales, y el permiso partido
(Gerente-only en E5-12).

**La investigación no mueve el recuento de la spec:** 9 construibles, 2 bloqueados, 4
referencias. Los nueve salen `parcial` con 14 tickets / 4 suscripciones.

---

## Technical Context

**Language/Version**: Python 3.11 (Django) para HTTP · SQL de ClickHouse para las consultas

**Primary Dependencies**: Django + DRF · armazón `informes_estrategicos` (OE6–OE1) ·
`ModeloEstrategicoRepository`

**Storage**: ClickHouse `tsi_tactico`. **Sin ALTER.** Lectura de `hecho_ticket` (`FINAL`),
`hecho_accion_ticket`, `dim_sla_config` (`FINAL`), `dim_servicio` (`FINAL`),
`hecho_suscripcion` (`FINAL`), `hecho_factura`, `hecho_solicitud_cambio_plan`,
`dim_plan` (`FINAL`), `dim_cliente` (`FINAL`, **no recrear**), `hecho_sesion`,
`hecho_llamada_api`

**Testing**: pytest. Contrato por endpoint, **exclusión** (Financiero no ve SLA; Éxito Cliente
no ve NRR; nadie de Cuentas ve riesgo salvo Gerente), 404 de E5-01/11 y de las cuatro rutas
OE1, OpenAPI sin texto de ticket ni cobro, cobertura parcial, una sola señal ≠ riesgo

**Target Platform**: `accidentes-django` · consultas en `dags/lib/consultas/estrategicos/oe5/`

**Project Type**: Servicio web de solo lectura — nueve `GET`

**Performance Goals**: Regla 7 (filtro por `fecha`, partición mensual). Volumen demo irrisorio.

**Constraints**:
- Período obligatorio
- Sin texto de ticket, notas internas, ficha personal, medios de cobro
- Denominador SLA = cerrados con compromiso; sin compromiso se declara
- NRR descompone expansión, contracción y churn; precio congelado en la suscripción
- E5-12 exige ≥2 señales; `parcial` nombra la señal que falta
- E5-01/11 y las cuatro de OE1 sin ruta
- `cumple` siempre `null` (`[CALIBRAR]`)

**Scale/Scope**: 9 publicados + 2 sin ruta + 4 404-hacia-OE1 · 14 tickets / 4 suscripciones /
6 facturas / 4 clientes / 747 sesiones (origen 2026-08-16)

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Principio | Cómo se cumple | |
|---|---|:--:|
| **I. Idoneidad funcional como contrato** | Nueve informes trazados a CU-E07 y al BSC. Dos se declaran inmedibles, incluido el NPS. Dueño único de los cuatro de OE1 | ✅ |
| **II. Fiabilidad operativa** | Lectura histórica. Fallo del almacén → 503 | ⚪ *fuera de la cadena crítica* |
| **III. Eficiencia en tiempo real** | No toca despacho. Partición por mes | ✅ |
| **IV. Capacidad de interacción** | No aplica: frontend aplazado | ⚪ |
| **V. Seguridad de la información** | Lista blanca. Sin prosa de ticket ni cobro. E5-12 solo Gerente | ✅ |
| **VI. Compatibilidad API-first** | OpenAPI bajo envelope común | ✅ |
| **VII. Mantenibilidad estructural** | Misma app. Cero DDL. No reimplementa OE1 | ✅ |
| **VIII. Flexibilidad** | SLA no se desglosa por región (#38). Se declara; no se inventa geografía | ✅ *con hueco explícito* |
| **IX. Safety** | No aplica: ningún informe mueve ambulancias | ⚪ |

### Trade-off — Idoneidad vs Fiabilidad (E5-01/11) y vs Mantenibilidad (OE1)

- **En conflicto:** el catálogo pide NPS, reportes sin corrección, y cuatro informes que OE1 ya
  publica.
- **Qué se priorizó:** **Fiabilidad** (no hay NPS) y **Mantenibilidad** (una sola SQL de
  renovación). No hay Safety.
- **Lo aceptado:** 9 de 15. Dos GET → 404. Cuatro GET en OE5 → 404 con camino a OE1. El KPI
  principal de la perspectiva Cliente queda sin fuente.
- **Lo ganado:** nadie lee NPS = 0 ni dos tasas de renovación distintas.
- **Revisión:** encuesta de una pregunta al cerrar ticket; tabla de entregas de informes.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE5-retencion-ciclo-vida/
├── OE5-retencion-ciclo-vida.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/informes-estrategicos-oe5.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                # lo crea /speckit-tasks
```

### Source Code (repository root)

```text
backend/apps/informes_estrategicos/
├── services/oe5_service.py
├── views/oe5_views.py
├── permissions.py              # AMPLIAR — mapa por informe
└── urls.py                     # AMPLIAR — oe5/<informe>

dags/lib/consultas/estrategicos/oe5/   # 9 SQL; ningún e5_01/09/10/11/13/14
```

**Structure Decision:** no hay app nueva. El modelo táctico **no se toca**. Los cuatro de OE1
**no se copian**.

---

## Constitution Re-Check (post-Phase 1)

Ningún gate cambió. El diseño refuerza V al dejar E5-12 solo en Gerente, y VII al no
reimplementar E1-06/09/10/11.

---

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, rechazada |
|---|---|---|
| **Permiso por informe** | Cuatro cargos + Gerente-only en riesgo | *Un permiso de módulo*: Finanzas vería tickets o Soporte vería NRR |
| **Dos rutas sin SQL** | NPS y entregas no existen | *Publicar 0*: mentiría el BSC de Cliente |
| **Cuatro 404 hacia OE1** | Una sola definición de renovación/churn/onboarding | *Segunda SQL*: dos cifras para el mismo KPI |
| **Cobertura parcial forzada** | n=14 no es un indicador | *Ocultar los informes*: el BSC los pide |

---

## Risks

| Riesgo | Señal | Mitigación |
|---|---|---|
| Meter tickets sin compromiso en el SLA | 95 % inflado o hundido | Denominador = `tiene_compromiso = 1`; prueba de exclusión |
| Copiar OT07 con expansión = 0 | NRR sin descomponer | E5-02 calcula expansión/contracción desde movimientos aprobados |
| Usar `dim_plan.precio` en E5-03 | Historia reescrita al cambiar tarifa | `delta_precio` / `precio_mensualizado` congelados |
| Marcar riesgo con una señal | Cuatro alarmas ruidosas | Prueba: una señal → no marcado |
| Usar `calificacion` de cierre como NPS | Path o columna en YAML | El YAML no declara E5-01; prueba de exclusión |
| Segunda SQL de renovación | Fichero `e5_09_*` | Catálogo: cero `e5_09/10/13/14` |

---

## Lo que este plan deja para después

1. Encuesta de una pregunta al cerrar ticket — desbloquea E5-01 (NPS).
2. Tabla de programación/entrega de informes — desbloquea E5-11.
3. Frontend del tablero estratégico.
4. Volumen real (14 tickets siguen siendo anecdóticos).
5. Autoridad de negocio de Cuentas (E5-15 tramo cuenta; hoy solo Gerente).
