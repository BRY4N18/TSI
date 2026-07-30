# OSRM — ruteo por calles reales

Motor de ruteo self-hosted usado por "Mapa de seguimiento" para trazar la ruta real por calles entre una unidad de emergencia y el accidente al que fue despachada (en vez de una línea recta). Decisión completa registrada en `.specify/docs/infra/infrastructure.md` §6.1.

## Primer uso (una sola vez, o al cambiar de región)

```bash
./build.sh
```

Esto descarga un extracto `.osm.pbf` recortado de Ciudad de México (BBBike, ~19MB) y genera los archivos `region.osrm*` en `data/` mediante el pipeline oficial de OSRM (`osrm-extract` → `osrm-partition` → `osrm-customize`). Los datos generados no se versionan en git (`data/` está en `.gitignore`).

Se usa [BBBike](https://download.bbbike.org/osm/bbbike/) en vez de Geofabrik porque Geofabrik solo ofrece el extracto de México completo (~600MB) — BBBike permite recortar por ciudad/área metropolitana, evitando bajar y procesar el país entero por una sola región operativa.

Para otra ciudad, buscar su extracto en el [listado de BBBike](https://download.bbbike.org/osm/bbbike/) o pasar la URL de un extracto de [Geofabrik](https://download.geofabrik.de/):

```bash
./build.sh https://download.geofabrik.de/<region>-latest.osm.pbf
```

## Levantar el servicio

Una vez generados los datos, el servicio `osrm` de `accidentes.yml` los sirve automáticamente:

```bash
docker compose -f docker/accidentes.yml up -d osrm
```

Django se conecta a `http://osrm:5000` por la red interna del compose (variable `OSRM_URL`) — el puerto de OSRM no se publica al host, solo Django lo consume.
