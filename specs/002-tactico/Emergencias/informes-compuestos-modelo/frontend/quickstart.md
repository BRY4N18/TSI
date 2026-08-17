# Quickstart — Tres pantallas Z de gestión (Emergencias)

**Fecha:** 2026-08-16 · **Spec:** [`spec.md`](spec.md) · **Contrato UI:** [`contracts/ui-contract.md`](contracts/ui-contract.md)

Cada comprobación existe porque su fallo sería silencioso.

## Prerrequisitos

- Backend de los 13 publicados en servicio (`../backend/quickstart.md`).
- `accidentes-django` (:8000) y `accidentes-frontend` (:4200) **Up**.
- Usuario **Director de Operaciones** (`director.operaciones@demo.tsi.com` / `Tactico2026!`).
- Un Operador de demo para la exclusión.

## 1. El Director entra a Calidad, el Operador no

Abrir `http://localhost:4200/emergencias/gestion/calidad` como Director.

**Esperado:** patrón Z visible (`zona-heroe`, `zona-periodo`, `zona-visual`, `zona-lectura`). La
lectura nombra severidad y condado.

Como Operador, la misma URL → access-denied.

## 2. La completitud no es un 100 % eterno

Período con casos reales (p. ej. 2026).

**Esperado:** si hay incompletos, el héroe **no** es 100 % como única cifra. Los incompletos aparecen
en el visual. Un período 2019 → vacío, no 0 %.

## 3. Despacho: héroe, advertencia y sin capacidad

`/emergencias/gestion/despacho`

**Esperado:** héroe = primer intento. Visual = desviación con texto de que **no es un SLA**. Ratio:
un condado sin unidades se lee **sin capacidad**, no ratio 0.

## 4. Un fallo no tumba la pantalla

Forzar error de red en un solo informe (p. ej. `perdida-senal`).

**Esperado:** esa zona en error; héroe y visual siguen.

## 5. Evidencia y cierre no es un catálogo de ocho

`/emergencias/gestion/cierre`

**Esperado:** envejecimiento héroe, cobertura visual grande, resultados/retiros abajo a la derecha.
Los otros cuatro **plegados**. Recuento de bloques de la vista principal ≤ 8. Calificación ausente
no se ve como 0.

## 6. El workpanel viejo no cambió

`/emergencias/informes/registro` como Operador sigue siendo el workpanel. **No** hay tarjetas nuevas
ahí. El Director no necesita ese tablero para esta capa.

## 7. Nada sensible

Recorrer las tres: ninguna coordenada, ningún nombre de implicado, ningún mapa.

## Lo que este quickstart NO comprueba

- Exportar (no existe).
- Semáforo `cumple` de OE3 (otro módulo).
- Los 13 vigilados.
- Frontend de Red Operativa.
