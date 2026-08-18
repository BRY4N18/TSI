# Implementation Plan: OE1 — Posicionamiento y Captación Digital

**Branch**: `001-estrategico/OE1-posicionamiento-captacion/backend` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-estrategico/OE1-posicionamiento-captacion/backend/spec.md`

---

## Summary

Diez de los trece informes de OE1, cada uno una consulta sobre el modelo que Suscripciones,
Ventas y Cuentas ya cargaron. **Cero tablas nuevas.** E1-05, E1-07 y E1-08 no tienen endpoint.

El táctico desbloqueó el plan (2026-08-18). Lo que este módulo añade es la ventana comparada, el
MRR con periodicidad ya mensualizada, la cobertura parcial por muestra de demostración, y el
permiso partido (incluido Gerente-only en onboarding/churn).

**La investigación no mueve el recuento de la spec:** 10 construibles, 3 bloqueados. Los diez
salen `parcial` con 4 suscripciones / 4 clientes / 10 prospectos.

---

## Technical Context

**Language/Version**: Python 3.11 (Django) para HTTP · SQL de ClickHouse para las consultas

**Primary Dependencies**: Django + DRF · armazón `informes_estrategicos` (OE6/OE3/OE4/OE2) ·
`ModeloEstrategicoRepository`

**Storage**: ClickHouse `tsi_tactico`. **Sin ALTER.** Lectura de `hecho_suscripcion` (`FINAL`),
`hecho_factura`, `dim_plan` (`FINAL`), `dim_cliente` (`FINAL`, **no recrear**),
`hecho_transicion_embudo`, `hecho_asignacion_prospecto`, `dim_prospecto` (`FINAL`),
`hecho_onboarding`, `dim_etapa_onboarding` (`FINAL`)

**Testing**: pytest. Contrato por endpoint, **exclusión** (Marketing no ve MRR; Financiero no ve
embudo; nadie de Cuentas ve onboarding salvo Gerente), 404 de los tres bloqueados, OpenAPI sin
medios de cobro, cobertura parcial

**Target Platform**: `accidentes-django` · consultas en `dags/lib/consultas/estrategicos/oe1/`

**Project Type**: Servicio web de solo lectura — diez `GET`

**Performance Goals**: Regla 7 (filtro por `fecha`, partición mensual). Volumen demo irrisorio.

**Constraints**:
- Período obligatorio
- Sin medios de cobro, IDs de pago, ficha personal, eje de país
- MRR usa `precio_mensualizado`; criterio vigente al **cierre**
- `cobertura: parcial` bajo muestra mínima
- E1-05/07/08 sin ruta
- Los cuatro compartidos con OE5 no se duplican

**Scale/Scope**: 10 publicados + 3 sin ruta · 4 suscripciones / 6 facturas / 4 clientes / 3
onboardings / 10 prospectos en origen 2026-08-16

---

## Constitution Check

*GATE: debe pasar antes de Phase 0. Re-evaluado tras Phase 1.*

| Principio | Cómo se cumple | |
|---|---|:--:|
| **I. Idoneidad funcional como contrato** | Diez informes trazados a CU-E02/E03/E07 y al BSC. Tres se declaran inmedibles. Dueño único de los cuatro compartidos con OE5 | ✅ |
| **II. Fiabilidad operativa** | Lectura histórica. Fallo del almacén → 503 | ⚪ *fuera de la cadena crítica* |
| **III. Eficiencia en tiempo real** | No toca despacho. Partición por mes | ✅ |
| **IV. Capacidad de interacción** | No aplica: frontend aplazado | ⚪ |
| **V. Seguridad de la información** | Lista blanca. Sin cobro ni persona. Permiso partido; onboarding/churn solo Gerente | ✅ |
| **VI. Compatibilidad API-first** | OpenAPI bajo envelope común | ✅ |
| **VII. Mantenibilidad estructural** | Misma app. Cero DDL. No recrea `dim_cliente` | ✅ |
| **VIII. Flexibilidad** | El objetivo es internacional y **no mide mercados**. Se declara; no se inventa geografía | ✅ *con hueco explícito* |
| **IX. Safety** | No aplica: ningún informe mueve ambulancias | ⚪ |

### Trade-off — Idoneidad vs Fiabilidad (E1-05/07/08)

- **En conflicto:** el catálogo pide CAC y +3 mercados/año. El origen no tiene costos ni país.
- **Qué se priorizó:** **Fiabilidad** (regla 2; no hay Safety).
- **Lo aceptado:** 10 de 13. Tres GET → 404. Dos KPI del BSC quedan sin fuente.
- **Lo ganado:** nadie lee CAC = 0 ni «un mercado».
- **Revisión:** columna de país en alta de cliente + fuente de inversión de marketing.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-estrategico/OE1-posicionamiento-captacion/
├── OE1-posicionamiento-captacion.md
└── backend/
    ├── spec.md
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    ├── contracts/informes-estrategicos-oe1.openapi.yaml
    ├── checklists/requirements.md
    └── tasks.md                # lo crea /speckit-tasks
```

### Source Code (repository root)

```text
backend/apps/informes_estrategicos/
├── services/oe1_service.py
├── views/oe1_views.py
├── permissions.py              # AMPLIAR — mapa por informe
└── urls.py                     # AMPLIAR — oe1/<informe>

dags/lib/consultas/estrategicos/oe1/   # 10 SQL; ningún e1_05/07/08
```

**Structure Decision:** no hay app nueva. El modelo táctico **no se toca**. `dim_cliente` **no se
recrea**.

---

## Constitution Re-Check (post-Phase 1)

Ningún gate cambió. El diseño refuerza VIII al **no** inventar un eje de mercado, y V al dejar
E1-09/10/11 solo en Gerente.

---

## Complexity Tracking

| Violación | Por qué es necesaria | Alternativa más simple, rechazada |
|---|---|---|
| **Permiso por informe** | Cuatro cargos + Gerente-only | *Un permiso de módulo*: Marketing vería MRR o Cuentas vería churn de empresa |
| **Tres rutas sin SQL** | CAC y geografía no existen | *Publicar 0*: mentiría el BSC |
| **Cobertura parcial forzada** | n=4 no es un indicador | *Ocultar los informes*: el BSC los pide y el volumen sí existe |

---

## Risks

| Riesgo | Señal | Mitigación |
|---|---|---|
| Sumar `precio` sin mensualizar | MRR ×12 en anuales | Usar `precio_mensualizado`; prueba con una anual |
| Recrear `dim_cliente` | Segundo CREATE | Prohibido en research D1 |
| Agrupar por país | Columna inventada | OpenAPI sin eje de mercado; 404 de E1-07/08 |
| Publicar CAC = 0 | Path en YAML | El YAML no declara las tres rutas |
| Embudo de solo completadas | 100 % de onboarding | JOIN al catálogo `dim_etapa_onboarding` |
| Segunda SQL en OE5 | Duplicado | Dueño documentado; OE5 referencia |

---

## Lo que este plan deja para después

1. País/estado en el alta de cliente — desbloquea E1-07 y E1-08.
2. Fuente de inversión de marketing — desbloquea E1-05.
3. Frontend del tablero estratégico.
4. Volumen real (el demo sigue siendo anecdótico).
5. Implementación de OE5 **consumiendo** estos cuatro, no copiándolos.
