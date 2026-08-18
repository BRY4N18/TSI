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
    "hecho_evidencia",
    "hecho_baja_unidad",
    "hecho_validacion_region",
    "dim_prospecto",
    "dim_canal",
    "hecho_transicion_embudo",
    "hecho_asignacion_prospecto",
    "hecho_interaccion_demo",
    "hecho_notificacion_ventas",
    "dim_plan",
    "dim_cliente",
    "hecho_suscripcion",
    "hecho_factura",
    "hecho_solicitud_cambio_plan",
    "dim_sla_config",
    "dim_servicio",
    "dim_estado_soporte",
    "hecho_ticket",
    "hecho_accion_ticket",
    "dim_usuario_organizacion",
    "dim_etapa_onboarding",
    "dim_rol",
    "dim_usuario_rol",
    "hecho_sesion",
    "hecho_onboarding",
    "dim_partner",
    "dim_credencial_api",
    "dim_version_contrato",
    "hecho_llamada_api",
    "hecho_cambio_acceso",
)

#: `idusuario` es clave, no identidad. Solo en las tablas de Cuentas que
#: analizan pertenencia, sesión y roles (D6). El resto del modelo no la copia.
CLAVE_USUARIO = frozenset({
    "hecho_sesion",
    "dim_usuario_organizacion",
    "dim_usuario_rol",
})

#: Columnas que coinciden con un patrón prohibido y **no son** dato sensible.
#:
#: La excepción se declara una a una y con su razón, en vez de estrechar el
#: patrón. `%nota%` tiene que seguir cazando `observaciones`, `nota_interna` y
#: cualquier columna de texto que aparezca mañana; lo que no debe cazar es
#: `num_notas`, que es **cuántas** notas tiene un caso y no dice ninguna.
#:
#: La diferencia entre las dos es exactamente la que este modelo defiende: contar
#: no es leer. Saber que un caso tiene tres notas no revela nada de su contenido.
EXCEPCIONES = {
    ("hecho_accidente", "num_notas"),
    ("hecho_evidencia", "categoria_nota"),
    ("hecho_factura", "es_nota_credito"),
    # Flags y fecha de caducidad: hay método y cuándo caduca, nunca cuál.
    ("dim_cliente", "tiene_metodo_pago"),
    ("dim_cliente", "metodo_pago_caduca"),
}

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
    @classmethod
    def setup_class(cls):
        # Las tablas que este modulo acaba de anadir tienen que existir antes
        # de recorrer el esquema: si no, la prueba de «todas las tablas
        # esperadas» fallaria por un CREATE que nadie ejecuto, no por un
        # dato sensible.
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()

    def test_ninguna_columna_coincide_con_un_patron_prohibido(self):
        condicion = " OR ".join(f"name ILIKE '{p}'" for p in PATRONES_PROHIBIDOS)
        tablas = ", ".join(f"'{t}'" for t in TABLAS)
        sobrantes = query_clickhouse(
            "SELECT table, name FROM system.columns "
            f"WHERE database = currentDatabase() AND table IN ({tablas}) AND ({condicion})"
        )
        sobrantes = [
            c for c in sobrantes if (c["table"], c["name"]) not in EXCEPCIONES
        ]
        assert sobrantes == [], f"columnas sensibles en el modelo: {sobrantes}"

    def test_las_excepciones_son_recuentos_o_categorias_y_no_texto(self):
        """Una excepción mal puesta desactivaría el patrón para esa columna.

        Se comprueba el **tipo**: un recuento es numérico, y una categoría es una
        etiqueta de un conjunto cerrado, no texto libre. Si alguien añadiera aquí
        `observaciones` para acallar el fallo, esta prueba lo vería — que es lo
        que hace que la lista de excepciones sea segura.
        """
        tipos = {
            (c["table"], c["name"]): c["type"]
            for c in query_clickhouse(
                "SELECT table, name, type FROM system.columns "
                "WHERE database = currentDatabase()"
            )
        }
        for clave in EXCEPCIONES:
            tipo = tipos.get(clave)
            if tipo is None:
                continue
            if clave == ("dim_cliente", "metodo_pago_caduca"):
                assert "Date" in tipo, (
                    f"{clave} está exceptuada y es de tipo {tipo}: debe ser la "
                    "fecha de caducidad, no el medio"
                )
                continue
            assert "Int" in tipo or clave[1].startswith("categoria_"), (
                f"{clave} está exceptuada y es de tipo {tipo}: una excepción "
                f"solo vale para recuentos y categorías cerradas"
            )

    def test_ninguna_tabla_guarda_identidad_de_persona(self):
        # `idusuario` está en el origen de casi todas las tablas de hecho y NO se
        # copia salvo donde Cuentas lo necesita como clave (sesión, pertenencia,
        # roles). Analizar cuántos casos hubo no requiere saber quién los tocó.
        columnas = _columnas()
        nombres = [c["name"] for c in columnas]
        claves = {c["table"] for c in columnas if c["name"] == "idusuario"}
        assert claves <= CLAVE_USUARIO, f"idusuario fuera de clave: {claves - CLAVE_USUARIO}"
        assert "idconductor" not in nombres
        assert "idimplicado" not in nombres

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
