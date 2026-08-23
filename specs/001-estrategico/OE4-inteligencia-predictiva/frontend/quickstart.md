# Quickstart — Cuatro pantallas Z de OE4

## Prerrequisitos

- Backend OE4 (`../backend/quickstart.md`). Nueve GET.
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.

| Rol | Para qué |
|---|---|
| `DirectorDatos` | Las cuatro |
| `DirectorOperaciones` | Calidad, Impacto |
| `Gerente` | Las cuatro |
| `DirectorExpansion` / Partner | Exclusión |

## 1. Datos entra a Calidad; Partner no

`/estrategico/oe4/calidad`: índice + cuatro componentes. Sin semáforo. Operaciones sí entra.

## 2. Vacío no es calidad 0 %

Período sin accidentes → vacío, no 0 %.

## 3. Ranking con ceros

Campos con 0 ausencias siguen listados.

## 4. Concentración sin mapa

`/estrategico/oe4/concentracion`: ranking por nombre. Operaciones no ve el enlace. Clima parcial.

## 5. Impacto: no-dato ≠ cero

`/estrategico/oe4/impacto`: `casos_con_dato`; duración y distancia con denominadores distintos.

## 6. Cobertura: umbral a la vista

`/estrategico/oe4/cobertura`: `sin_masa_critica`. Operaciones no entra.

## 7. Sin bloqueados

Ninguna pantalla menciona precisión del modelo, preposición ni latencia de ingesta.

## 8. Rebuild

```powershell
docker compose -f docker/accidentes.yml up -d --build django frontend
```
