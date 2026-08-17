"""T049–T052 — los dos indicadores BSC de Red Operativa y sus exclusiones.

Tres cosas que fallan sin fallar:

1. **Contar regiones en vez de intentos** daría 100 % a una región rechazada dos
   veces y aprobada a la tercera — el mejor resultado en el caso que peor fue.
2. **Agrupar los motivos sobre todas las validaciones** convertiría las
   aprobaciones sin motivo en una categoría, y hoy sería la causa de rechazo más
   frecuente del informe.
3. **Devolver `0` días** a una región que todavía no llegó a producción diría que
   incumplió un plazo dentro del cual sigue estando.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    PARTICION_DE_PRUEBA,
    ejecutar_red_operativa,
    requiere_modelo,
)

from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402

REGION = 9501


def _validacion(idv: int, *, resultado: str, intento: int, motivo: str | None = None,
                hora: str = "10:00:00", region: int = REGION) -> dict:
    return {
        "idvalidacion": idv,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} {hora}",
        "sk_region": 0,
        "idregionoperativa": region,
        "nombre_region": f"Region {region}",
        "resultado": resultado,
        "motivo": motivo,
        "numero_intento": intento,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def _insertar(filas: list[dict]) -> None:
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in filas)
    execute_clickhouse(f"INSERT INTO hecho_validacion_region FORMAT JSONEachRow\n{payload}")


@pytest.fixture
def limpio():
    execute_clickhouse(
        f"ALTER TABLE hecho_validacion_region DROP PARTITION {PARTICION_DE_PRUEBA}"
    )
    yield
    execute_clickhouse(
        f"ALTER TABLE hecho_validacion_region DROP PARTITION {PARTICION_DE_PRUEBA}"
    )


@requiere_modelo
class TestLaTasaAlPrimerIntento:
    """T049 — se cuentan intentos, no regiones (FR-017)."""

    def test_una_region_aprobada_al_tercero_no_cuenta_como_aprobada_al_primero(self, limpio):
        """⚠️ El caso que existe hoy en los datos reales.

        Con grano de región solo queda la aprobación final: los dos rechazos no
        dejan rastro y el indicador daría 100 %. Es el mejor resultado posible
        justamente en el caso que peor fue.
        """
        _insertar([
            _validacion(1, resultado="Rechazada", intento=1, motivo="Cobertura insuficiente"),
            _validacion(2, resultado="Rechazada", intento=2, motivo="Faltan mapas", hora="11:00:00"),
            _validacion(3, resultado="Aprobada", intento=3, hora="12:00:00"),
        ])

        fila = ejecutar_red_operativa("ot11_tasa_aprobacion_primer_intento")[0]

        assert fila["regiones_validadas"] == 1, "el denominador cuenta regiones, no intentos"
        assert fila["aprobadas_al_primero"] == 0, (
            "la región se dio por aprobada al primer intento: los dos rechazos "
            "previos desaparecieron de la cuenta"
        )
        assert fila["pct_aprobacion_primer_intento"] == 0.0

    def test_una_region_aprobada_a_la_primera_si_cuenta(self, limpio):
        # La comprobación simétrica: un indicador que diera siempre 0 pasaría la
        # prueba anterior y estaría igual de roto.
        _insertar([_validacion(1, resultado="Aprobada", intento=1)])

        assert ejecutar_red_operativa("ot11_tasa_aprobacion_primer_intento")[0][
            "pct_aprobacion_primer_intento"
        ] == 1.0

    def test_los_reintentos_no_entran_en_el_denominador(self, limpio):
        """Una región con tres intentos aporta **uno** al denominador.

        Si aportara tres, una sola región problemática hundiría el indicador
        tanto como tres regiones distintas que fallaron a la primera.
        """
        _insertar([
            _validacion(1, resultado="Rechazada", intento=1, motivo="X"),
            _validacion(2, resultado="Rechazada", intento=2, motivo="Y", hora="11:00:00"),
            _validacion(3, resultado="Aprobada", intento=3, hora="12:00:00"),
            _validacion(4, resultado="Aprobada", intento=1, region=REGION + 1, hora="13:00:00"),
        ])

        fila = ejecutar_red_operativa("ot11_tasa_aprobacion_primer_intento")[0]

        assert fila["regiones_validadas"] == 2
        assert fila["pct_aprobacion_primer_intento"] == 0.5

    def test_una_region_sin_validaciones_no_cuenta_como_fallo(self, limpio):
        # No ha intentado nada, así que no ha fallado. Contarla como 0 % haría
        # que el indicador empeorara al declarar regiones nuevas.
        _insertar([_validacion(1, resultado="Aprobada", intento=1)])

        assert ejecutar_red_operativa("ot11_tasa_aprobacion_primer_intento")[0][
            "regiones_validadas"
        ] == 1


@requiere_modelo
class TestLosMotivosDeRechazo:
    """T051 — solo sobre validaciones rechazadas (FR-018)."""

    def test_una_aprobacion_sin_motivo_no_aparece_como_categoria(self, limpio):
        """⚠️ Una aprobación no tiene motivo, y eso es correcto.

        Agrupando sobre todas las validaciones, ese nulo se convertiría en una
        categoría y con estos datos sería la **más frecuente** del informe. La
        categoría aparecería con nombre plausible y conteo creíble, y quien la
        leyera concluiría que hace falta mejorar el registro de motivos — una
        conclusión falsa: lo que pasa es que las aprobaciones se colaron en un
        informe de rechazos.
        """
        _insertar([
            _validacion(1, resultado="Rechazada", intento=1, motivo="Cobertura insuficiente"),
            _validacion(2, resultado="Aprobada", intento=2, hora="11:00:00"),
            _validacion(3, resultado="Aprobada", intento=1, region=REGION + 1, hora="12:00:00"),
        ])

        motivos = {f["motivo"]: f["rechazos"] for f in ejecutar_red_operativa(
            "ot11_motivos_rechazo", top=10
        )}

        assert motivos == {"Cobertura insuficiente": 1}, (
            f"aparecieron categorías de más: {sorted(motivos)}. Las aprobaciones "
            f"sin motivo se están contando como una causa de rechazo"
        )

    def test_un_rechazo_sin_motivo_si_es_una_categoria_y_se_etiqueta(self, limpio):
        """Alguien rechazó sin decir por qué. Eso sí hay que verlo.

        Es un hueco de registro que hay que cerrar, y esconderlo dejaría el
        informe de motivos aparentemente completo.
        """
        _insertar([
            _validacion(1, resultado="Rechazada", intento=1, motivo=None),
            _validacion(2, resultado="Rechazada", intento=2, motivo="Cobertura", hora="11:00:00"),
        ])

        motivos = {f["motivo"] for f in ejecutar_red_operativa("ot11_motivos_rechazo", top=10)}

        assert "Rechazada sin motivo registrado" in motivos

    def test_el_tope_limita_las_categorias(self, limpio):
        _insertar([
            _validacion(i, resultado="Rechazada", intento=i, motivo=f"Motivo {i}",
                        hora=f"{9 + i}:00:00")
            for i in range(1, 5)
        ])

        assert len(ejecutar_red_operativa("ot11_motivos_rechazo", top=2)) == 2


@requiere_modelo
class TestLaPuestaEnOperacion:
    """T050 — una región aún en validación devuelve ausente, no incumplimiento."""

    def test_una_region_que_no_llego_a_produccion_devuelve_ausente(self, limpio):
        """⚠️ No incumplió un plazo: sigue dentro de él (SC-007).

        Ni `0` días ni `cumple_objetivo = false`. Son cosas distintas y la
        diferencia decide qué se hace: una región que incumplió necesita
        explicación, una en curso necesita tiempo. Y un `0` además la pondría a
        la cabeza de las más rápidas, que es el orden por el que alguien buscaría
        buenas prácticas.
        """
        filas = ejecutar_red_operativa("ot11_tiempo_puesta_operacion", dias_objetivo=30)

        for fila in filas:
            if fila["estado_actual"] != "Producción" or fila["entro_en_produccion"] is None:
                assert fila["dias"] is None, (
                    f"'{fila['region']}' devuelve {fila['dias']} días sin haber "
                    f"entrado en producción de forma medible"
                )
                assert fila["cumple_objetivo"] is None, (
                    f"'{fila['region']}' se marca como incumplimiento sin haber "
                    f"llegado a producción"
                )

    def test_el_objetivo_aplicado_viaja_en_la_respuesta(self, limpio):
        """El sistema no guarda ningún plazo: el objetivo lo pone quien consulta.

        Sin verlo, «3 regiones fuera de objetivo» pasaría por el incumplimiento
        de un acuerdo que nadie firmó.
        """
        filas = ejecutar_red_operativa("ot11_tiempo_puesta_operacion", dias_objetivo=45)

        assert filas and all(f["dias_objetivo"] == 45 for f in filas)


@requiere_modelo
class TestSinIdentidadDelValidador:
    """T052 — ningún informe de OT11 devuelve quién validó (FR-021)."""

    DE_PERSONA = ("idusuario", "usuario", "validador", "aprobador", "revisor",
                  "responsable", "nombres", "apellidos")

    @pytest.mark.parametrize(
        "informe,extra",
        [
            ("ot11_tasa_aprobacion_primer_intento", {}),
            ("ot11_motivos_rechazo", {"top": 10}),
            ("ot11_mercados_activos", {}),
            ("ot11_tiempo_puesta_operacion", {"dias_objetivo": 30}),
        ],
    )
    def test_ninguna_columna_identifica_a_quien_valido(self, informe, extra, limpio):
        _insertar([_validacion(1, resultado="Rechazada", intento=1, motivo="X")])

        filas = ejecutar_red_operativa(informe, **extra)
        if not filas:
            pytest.skip(f"'{informe}' no devolvió filas")

        for columna in filas[0]:
            for prohibido in self.DE_PERSONA:
                assert prohibido not in columna.lower(), (
                    f"'{informe}' devuelve '{columna}': identidad del validador"
                )

    def test_el_hecho_tampoco_la_guarda(self):
        """La garantía está en el esquema, no en la consulta.

        Una consulta que no pide el dato lo deja fuera hoy; una tabla que no lo
        tiene lo deja fuera siempre.
        """
        from lib.clickhouse_http_client import query_clickhouse

        columnas = {
            c["name"].lower()
            for c in query_clickhouse(
                "SELECT name FROM system.columns WHERE database = currentDatabase() "
                "AND table = 'hecho_validacion_region'"
            )
        }

        assert columnas, "la tabla no existe"
        for prohibido in self.DE_PERSONA:
            assert not [c for c in columnas if prohibido in c], (
                f"hecho_validacion_region guarda algo con '{prohibido}'"
            )
