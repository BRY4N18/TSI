

class TestLaGrafiaSeConserva:
    """⚠️ Agrupar y mostrar son dos cosas distintas.

    `normalizar` hacía `texto[0].upper() + texto[1:].lower()` y usaba el
    resultado para las dos: agrupaba bien —«REDES SOCIALES» y «redes sociales»
    convergían— pero en pantalla salían «Linkedin» y «Referido tsi», con el
    origen diciendo «LinkedIn» y «Referido TSI».
    """

    def test_los_nombres_propios_conservan_sus_mayusculas(self):
        from lib.dimensiones.dim_canal import normalizar

        assert normalizar("LinkedIn") == "LinkedIn"
        assert normalizar("Referido TSI") == "Referido TSI"

    def test_dos_escrituras_del_mismo_canal_comparten_clave(self):
        from lib.dimensiones.dim_canal import clave

        assert clave("REDES SOCIALES") == clave("redes sociales") == clave("Redes Sociales")

    def test_el_alias_sigue_juntando_las_variantes_declaradas(self):
        from lib.dimensiones.dim_canal import clave

        assert clave("Web / catalogo planes") == clave("Web / catálogo de planes")

    def test_el_grupo_se_muestra_con_la_grafia_mas_frecuente(self):
        from datetime import datetime

        from lib.dimensiones.dim_canal import construir

        prospectos = [
            {"como_nos_conocio": "LinkedIn"},
            {"como_nos_conocio": "LinkedIn"},
            {"como_nos_conocio": "linkedin"},
        ]
        filas = construir(prospectos, datetime(2026, 8, 19))
        assert [f["canal"] for f in filas] == ["LinkedIn"]

    def test_una_sola_fila_por_canal_aunque_haya_varias_escrituras(self):
        from datetime import datetime

        from lib.dimensiones.dim_canal import construir

        prospectos = [
            {"como_nos_conocio": "Redes sociales"},
            {"como_nos_conocio": "REDES SOCIALES"},
            {"como_nos_conocio": "  redes   sociales  "},
        ]
        assert len(construir(prospectos, datetime(2026, 8, 19))) == 1

    def test_la_eleccion_no_depende_del_orden_de_llegada(self):
        """El orden de Pinot no está garantizado: dos corridas, mismo nombre."""
        from datetime import datetime

        from lib.dimensiones.dim_canal import construir

        a = [{"como_nos_conocio": x} for x in ("linkedin", "LinkedIn", "LinkedIn")]
        b = [{"como_nos_conocio": x} for x in ("LinkedIn", "LinkedIn", "linkedin")]
        ahora = datetime(2026, 8, 19)
        assert construir(a, ahora) == construir(b, ahora)


class TestElProspectoEncuentraSuCanal:
    """⚠️ El cruce va por clave, no por la grafía publicada.

    `dim_canal` muestra **una** grafía por canal —la más frecuente— y el
    prospecto conserva la suya. Si el cruce fuera por texto, quien escribió
    «linkedin» no encontraría el canal «LinkedIn»: caería en la fila desconocida
    y **perdería su canal sin que nada fallara**. El informe de captación
    repartiría la inversión sobre un reparto equivocado.
    """

    def test_una_grafia_distinta_no_manda_el_prospecto_a_desconocido(self):
        from datetime import datetime

        from lib.dimensiones.dim_canal import construir as construir_canales
        from lib.dimensiones.dim_prospecto import construir as construir_prospectos
        from lib.dimensiones.desconocido import ID_DESCONOCIDO

        ahora = datetime(2026, 8, 19)
        prospectos = [
            {"idprospecto": 1, "como_nos_conocio": "LinkedIn"},
            {"idprospecto": 2, "como_nos_conocio": "LinkedIn"},
            # Mismo canal, escrito distinto: tiene que caer en el mismo idcanal.
            {"idprospecto": 3, "como_nos_conocio": "linkedin"},
        ]
        canales = construir_canales(prospectos, ahora)
        filas = construir_prospectos(prospectos, canales, ahora)

        ids = {f["idprospecto"]: f["idcanal"] for f in filas}
        assert ID_DESCONOCIDO not in ids.values(), "un prospecto perdió su canal"
        assert len(set(ids.values())) == 1, "el mismo canal se partió en dos"

    def test_el_alias_declarado_tambien_cruza(self):
        from datetime import datetime

        from lib.dimensiones.dim_canal import construir as construir_canales
        from lib.dimensiones.dim_prospecto import construir as construir_prospectos

        ahora = datetime(2026, 8, 19)
        prospectos = [
            {"idprospecto": 1, "como_nos_conocio": "Web / catálogo de planes"},
            {"idprospecto": 2, "como_nos_conocio": "Web / catalogo planes"},
        ]
        canales = construir_canales(prospectos, ahora)
        filas = construir_prospectos(prospectos, canales, ahora)

        assert len({f["idcanal"] for f in filas}) == 1

    def test_la_columna_denormalizada_lleva_la_grafia_no_la_clave(self):
        """⚠️ `ot01_captacion_por_canal` agrupa por `dim_prospecto.canal`.

        Si esa columna llevara la clave de agrupación —plegada a minúsculas—, el
        informe de captación mostraría «linkedin» y «referido tsi». Pasó al
        separar agrupación y presentación: el `idcanal` quedó bien y la columna
        visible se llevó la clave.
        """
        from datetime import datetime

        from lib.dimensiones.dim_canal import construir as construir_canales
        from lib.dimensiones.dim_prospecto import construir as construir_prospectos

        ahora = datetime(2026, 8, 19)
        prospectos = [
            {"idprospecto": 1, "como_nos_conocio": "LinkedIn"},
            {"idprospecto": 2, "como_nos_conocio": "linkedin"},
        ]
        canales = construir_canales(prospectos, ahora)
        filas = construir_prospectos(prospectos, canales, ahora)

        assert {f["canal"] for f in filas} == {"LinkedIn"}
