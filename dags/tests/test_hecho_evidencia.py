"""T052 — el cargador de `hecho_evidencia`.

Tres cosas que este hecho tiene que resolver y que ninguna otra tabla resuelve:

1. **La unidad no viene en el origen.** Ni las fotos ni las notas la traen; traen
   `idusuario`, que está excluido. Se deriva del primer despacho que **llegó**.
2. **Las notas no tienen instante de sincronización** —la columna no existe en la
   fuente— así que su latencia es genuinamente desconocida y no se fabrica.
3. **Fotos y notas comparten grano**, y por eso comparten tabla.

Lógica pura: `construir` no consulta ni escribe. Es la única forma de probarlo
hoy, porque el origen tiene 3 fotos y 51 notas y con esos datos una atribución
rota y una fuente pobre se ven igual.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.desconocido import ID_DESCONOCIDO, SK_DESCONOCIDO  # noqa: E402
from lib.hechos.hecho_evidencia import construir  # noqa: E402

AHORA = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)
CASO = "ACC-1"

#: 2026-07-13 en epoch-ms, y una hora más tarde.
CAPTURA = 1784000000000
LLEGADA_TEMPRANA = 1783990000000
LLEGADA_TARDIA = 1783999000000


def _datos(**extra):
    base = {
        "fotos": [],
        "notas": [],
        "despachos": [],
        "dim_unidad": [
            {
                "sk_unidad": 10, "idunidademergencia": 7, "proveedor": "Proveedor A",
                "valido_desde": "2020-01-01 00:00:00", "valido_hasta": None,
            }
        ],
        "hecho_accidente": [
            {"idaccidente": CASO, "idseveridad": 3, "severidad": "Grave",
             "condado": "Cuauhtemoc"}
        ],
    }
    base.update(extra)
    return base


def _foto(idev=1, sincronia=None):
    return {"idevidenciafoto": idev, "idaccidente": CASO,
            "fechahora": CAPTURA, "fecha_sincronizacion": sincronia}


def _nota(idev=1, tipo="Condiciones del sitio"):
    return {"idnotaaccidentes": idev, "idaccidente": CASO,
            "fechahora": CAPTURA, "tipo": tipo}


class TestFotosYNotasCompartenTabla:
    def test_las_dos_producen_filas_del_mismo_grano(self):
        filas = construir(_datos(fotos=[_foto()], notas=[_nota()]), AHORA)

        assert {f["tipo"] for f in filas} == {"foto", "nota"}
        assert all(f["idaccidente"] == CASO for f in filas)

    def test_solo_las_notas_traen_categoria(self):
        """Una foto no tiene categoría de nota: ausente, no cadena vacía.

        No es que su categoría esté en blanco; es que no le corresponde una.
        Una cadena vacía la metería en un grupo «sin categoría» junto a las notas
        que sí deberían tener una y no la traen.
        """
        filas = {f["tipo"]: f for f in construir(_datos(fotos=[_foto()], notas=[_nota()]), AHORA)}

        assert filas["nota"]["categoria_nota"] == "Condiciones del sitio"
        assert filas["foto"]["categoria_nota"] is None


class TestLaAtribucionDeUnidad:
    def test_se_atribuye_a_la_unidad_del_primer_despacho_que_llego(self):
        filas = construir(
            _datos(
                fotos=[_foto()],
                despachos=[
                    {"idaccidente": CASO, "idunidademergencia": 7,
                     "fechahorallegada": LLEGADA_TEMPRANA},
                    {"idaccidente": CASO, "idunidademergencia": 9,
                     "fechahorallegada": LLEGADA_TARDIA},
                ],
            ),
            AHORA,
        )

        assert filas[0]["idunidademergencia"] == 7
        assert filas[0]["proveedor"] == "Proveedor A"

    def test_un_despacho_sin_llegada_no_atribuye_nada(self):
        """Rechazado, vencido o abortado: esa unidad nunca fue al sitio.

        Tomarlo como atribución colgaría la evidencia de una unidad que no
        estuvo, y el informe de volumen por unidad premiaría a la que menos
        trabaja.
        """
        filas = construir(
            _datos(
                fotos=[_foto()],
                despachos=[
                    {"idaccidente": CASO, "idunidademergencia": 9, "fechahorallegada": None},
                    {"idaccidente": CASO, "idunidademergencia": 7,
                     "fechahorallegada": LLEGADA_TEMPRANA},
                ],
            ),
            AHORA,
        )

        assert filas[0]["idunidademergencia"] == 7

    def test_un_caso_sin_ninguna_llegada_deja_la_evidencia_en_la_unidad_desconocida(self):
        """No se descarta. La evidencia existió.

        Descartarla sería la peor salida: bajaría el volumen de evidencia sin que
        nada indicara que faltan filas, y el informe de cobertura diría que se
        documentó menos de lo que se documentó.
        """
        filas = construir(_datos(fotos=[_foto()]), AHORA)

        assert len(filas) == 1
        assert filas[0]["idunidademergencia"] == ID_DESCONOCIDO
        assert filas[0]["sk_unidad"] == SK_DESCONOCIDO
        assert filas[0]["proveedor"] == "Desconocido"

    def test_la_version_de_la_unidad_es_la_vigente_al_capturar(self):
        # Atribución histórica, la misma que usan los otros hechos: si la unidad
        # cambia de proveedor mañana, esta evidencia sigue siendo del de hoy.
        datos = _datos(
            fotos=[_foto()],
            despachos=[{"idaccidente": CASO, "idunidademergencia": 7,
                        "fechahorallegada": LLEGADA_TEMPRANA}],
        )
        datos["dim_unidad"] = [
            {"sk_unidad": 10, "idunidademergencia": 7, "proveedor": "Proveedor de entonces",
             "valido_desde": "2020-01-01 00:00:00", "valido_hasta": "2026-08-01 00:00:00"},
            {"sk_unidad": 11, "idunidademergencia": 7, "proveedor": "Proveedor de ahora",
             "valido_desde": "2026-08-01 00:00:00", "valido_hasta": None},
        ]

        filas = construir(datos, AHORA)

        assert filas[0]["proveedor"] == "Proveedor de entonces"


class TestLaSincronizacion:
    def test_sin_sincronizar_la_latencia_es_ausente_y_no_cero(self):
        """Ausente significa «todavía no», no «en la época cero».

        Un cero diría que llegó instantáneamente —la mejor latencia posible— y es
        justo lo contrario: no ha llegado.
        """
        filas = construir(_datos(fotos=[_foto(sincronia=None)]), AHORA)

        assert filas[0]["fechahora_sincronia"] is None
        assert filas[0]["segundos_hasta_sincronia"] is None

    def test_con_sincronizacion_la_latencia_se_calcula(self):
        filas = construir(
            _datos(fotos=[_foto(sincronia=CAPTURA + 120_000)]), AHORA
        )

        assert filas[0]["segundos_hasta_sincronia"] == 120

    def test_una_nota_nunca_trae_latencia_porque_su_fuente_no_la_tiene(self):
        """`Dim_NotaAccidente` **no tiene** columna de sincronización.

        La latencia de las notas es genuinamente desconocida. Rellenarla con la
        fecha de carga diría que tardó justo lo que llevamos mirándola, y
        rellenarla con la de captura diría que fue instantánea.
        """
        filas = construir(_datos(notas=[_nota()]), AHORA)

        assert filas[0]["fechahora_sincronia"] is None
        assert filas[0]["segundos_hasta_sincronia"] is None


class TestLoQueNoEntraAlModelo:
    def test_ninguna_fila_lleva_identidad_de_persona_ni_el_enlace_al_material(self):
        filas = construir(_datos(fotos=[_foto()], notas=[_nota()]), AHORA)

        for fila in filas:
            for prohibida in ("idusuario", "urlevidenciafoto", "nota"):
                assert prohibida not in fila

    def test_la_consulta_de_notas_no_pide_el_texto(self):
        from lib.hechos.hecho_evidencia import CONSULTA_FOTOS, CONSULTA_NOTAS

        # Se comprueba el texto de la consulta además del resultado: el resultado
        # solo demuestra que hoy no llega, y la consulta demuestra que no se pide.
        assert " nota," not in CONSULTA_NOTAS and " nota\n" not in CONSULTA_NOTAS
        assert "urlevidenciafoto" not in CONSULTA_FOTOS
        assert "idusuario" not in CONSULTA_NOTAS and "idusuario" not in CONSULTA_FOTOS


class TestLosDatosDelCaso:
    def test_la_severidad_y_el_condado_se_copian_del_modelo(self):
        filas = construir(_datos(fotos=[_foto()]), AHORA)

        assert filas[0]["severidad"] == "Grave"
        assert filas[0]["condado"] == "Cuauhtemoc"

    def test_una_evidencia_de_un_caso_que_no_esta_en_el_modelo_no_se_pierde(self):
        # Sale sin severidad ni condado, que es información honesta. Descartarla
        # bajaría el volumen sin que nada lo indicara.
        datos = _datos(fotos=[_foto()])
        datos["hecho_accidente"] = []

        filas = construir(datos, AHORA)

        assert len(filas) == 1
        assert filas[0]["severidad"] is None


class TestSinInstanteDeCaptura:
    def test_una_evidencia_sin_captura_no_entra(self):
        # Es la única razón por la que una evidencia queda fuera: sin instante no
        # hay partición posible.
        filas = construir(
            _datos(fotos=[{"idevidenciafoto": 1, "idaccidente": CASO,
                           "fechahora": None, "fecha_sincronizacion": None}]),
            AHORA,
        )

        assert filas == []
