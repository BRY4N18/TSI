"""El modelo no contiene dato sensible (T029, Regla 8 del contrato de consumo).

Las exclusiones del §5 del contrato —coordenadas, identidad de personas, secretos
de autenticación, medios de cobro y texto interno— **no son de acotamiento sino
constitucionales**: no dependen de quién consulta, no las levanta ninguna
autoridad departamental, y por tanto la forma correcta de garantizarlas es que el
dato **no esté**.

Esta prueba mira el esquema, no las filas. Un dato sensible ausente hoy porque
nadie lo cargó volvería en cuanto alguien añadiera la columna; un dato sensible
que no existe como columna no puede volver por descuido.

El origen sí los tiene —`Fact_Accidente` trae latitud y longitud,
`Dim_UnidadEmergencia` también— así que la exclusión es una decisión activa de
cada carga, no una casualidad.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

TABLAS = (
    "dim_tiempo",
    "dim_geografia",
    "dim_severidad",
    "dim_origen_despacho",
    "dim_unidad",
    "hecho_accidente",
    "hecho_despacho",
    "hecho_estado_unidad",
    "hecho_ping_unidad",
)

#: Fragmentos que delatan una columna excluida. Se busca por patrón y no por
#: lista cerrada de nombres: lo que hay que impedir es que **aparezca** una
#: columna nueva de este tipo, y una lista cerrada solo cubre las ya conocidas.
PATRONES_PROHIBIDOS = (
    "%latitud%", "%longitud%", "%coord%", "%geoloc%",
    "%contacto%", "%telefono%", "%correo%", "%email%",
    "%password%", "%contrasena%", "%token%", "%secret%", "%api_key%", "%hash%",
    "%tarjeta%", "%cuenta_banc%", "%metodo_pago%", "%nit%",
    "%observacion%", "%nota%", "%descripcion_libre%", "%mensaje%",
)


def _columnas() -> list[dict]:
    tablas = ", ".join(f"'{t}'" for t in TABLAS)
    return query_clickhouse(
        "SELECT table, name FROM system.columns "
        f"WHERE database = currentDatabase() AND table IN ({tablas})"
    )


@requiere_modelo
class TestEsquemaDelModelo:
    def test_ninguna_columna_coincide_con_un_patron_prohibido(self):
        condicion = " OR ".join(f"name ILIKE '{p}'" for p in PATRONES_PROHIBIDOS)
        tablas = ", ".join(f"'{t}'" for t in TABLAS)
        sobrantes = query_clickhouse(
            "SELECT table, name FROM system.columns "
            f"WHERE database = currentDatabase() AND table IN ({tablas}) AND ({condicion})"
        )
        assert sobrantes == [], f"columnas sensibles en el modelo: {sobrantes}"

    def test_ninguna_tabla_guarda_identidad_de_persona(self):
        # `idusuario` está en el origen de casi todas las tablas de hecho y NO se
        # copia: analizar cuántos casos hubo no requiere saber quién los tocó
        columnas = [c["name"] for c in _columnas()]
        assert "idusuario" not in columnas
        assert "idconductor" not in columnas
        assert "idimplicado" not in columnas

    def test_la_comprobacion_recorre_las_siete_tablas(self):
        # Si una tabla no existiera, la prueba anterior pasaría sin mirarla
        presentes = {c["table"] for c in _columnas()}
        assert presentes == set(TABLAS)

    def test_la_geografia_se_expresa_por_nombre(self):
        # La exclusión de coordenadas no puede dejar el modelo sin ubicación:
        # se sustituye por nombres, no se elimina la capacidad de analizar
        assert contar(
            "SELECT count() AS n FROM system.columns "
            "WHERE database = currentDatabase() AND table = 'dim_geografia' "
            "AND name IN ('condado', 'ciudad', 'estado', 'pais')"
        ) == 4
