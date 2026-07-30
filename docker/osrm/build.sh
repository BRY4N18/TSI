#!/usr/bin/env bash
# Construye los datos de ruteo de OSRM una sola vez, a partir de un extracto
# OSM de la región operativa. El resultado (region.osrm*) se monta como
# volumen por el servicio `osrm` en accidentes.yml — no se versiona en git
# (ver .gitignore de esta carpeta).
#
# Uso:
#   ./build.sh [URL_DEL_EXTRACTO_OSM_PBF]
#
# Por defecto usa el extracto recortado de Ciudad de México de BBBike
# (~19MB, ciudad+área metropolitana), coherente con el centro por defecto
# del mapa de seguimiento (DEFAULT_CENTER en mapa-seguimiento.page.ts).
# Geofabrik solo ofrece el extracto de México completo (~600MB) — se prefiere
# BBBike aquí precisamente para no bajar/procesar el país entero por un solo
# área operativa. Cambiar la URL para otra región/ciudad.
set -euo pipefail

# Evita que Git Bash/MSYS traduzca rutas estilo Unix (ej. /opt/car.lua) a
# rutas de Windows al pasarlas como argumentos a `docker run`.
export MSYS_NO_PATHCONV=1

DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/data"
PBF_URL="${1:-https://download.bbbike.org/osm/bbbike/MexicoCity/MexicoCity.osm.pbf}"
PBF_FILE="$DATA_DIR/region.osm.pbf"

mkdir -p "$DATA_DIR"

echo "==> Descargando extracto OSM desde: $PBF_URL"
curl -L --fail -o "$PBF_FILE" "$PBF_URL"

echo "==> Preprocesando datos OSRM (extract → partition → customize)"
docker run --rm -t -v "$DATA_DIR:/data" osrm/osrm-backend \
  osrm-extract -p /opt/car.lua /data/region.osm.pbf

docker run --rm -t -v "$DATA_DIR:/data" osrm/osrm-backend \
  osrm-partition /data/region.osrm

docker run --rm -t -v "$DATA_DIR:/data" osrm/osrm-backend \
  osrm-customize /data/region.osrm

echo "==> Listo. Datos generados en $DATA_DIR — levantar con:"
echo "    docker compose -f accidentes.yml up -d osrm"
