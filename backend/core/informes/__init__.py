"""Ayudantes transversales de los listados tacticos simples.

Los **64 listados de los 8 departamentos** comparten el mismo contrato HTTP
(`specs/002-tactico/contrato-informes-simples.md`): periodo opcional, paginacion
por cursor keyset y envelope `{data, meta:{pagination, filtros}}`. Ese contrato
vive aqui y no en la app de un departamento por dos razones:

1. **No se duplica ocho veces.** Los listados viven dentro de la app de cada
   departamento (`cuentas_clientes`, `ventas_crm`, ...). Si lo transversal
   viviera en una de ellas, las otras siete tendrian que importarla, creando una
   dependencia entre apps de departamento que hoy no existe.

2. **`apps/informes_tacticos/` no se toca.** Sus 19 informes agregados estan en
   produccion y su `periodo.py` exige el rango; el de aqui lo hace opcional. Son
   dos contratos distintos que conviven a proposito (research D1). La
   duplicacion de ~40 lineas es consciente: el precio de no ampliar la superficie
   de riesgo de 19 endpoints verificados.
"""
