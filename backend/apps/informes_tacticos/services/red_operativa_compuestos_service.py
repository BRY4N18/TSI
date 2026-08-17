"""Servicio de los informes compuestos de Red Operativa.

Mismo patrón que Emergencias, sobre el **mismo** `modelo_repository`. Que este
módulo no haya necesitado plomería propia es la comprobación de que el patrón
escala: si el segundo departamento hubiera necesitado la suya, los seis restantes
también, y los 108 informes del catálogo volverían a ser 108 soluciones
particulares.

⚠️ Lo propio de este departamento: la autoridad está repartida
---------------------------------------------------------------
No hay una jefatura única. El **Director de Expansión** gobierna el crecimiento y
la flota; el **Director Tecnológico**, los criterios de validación de región.
Cada uno accede sin acotamiento **a su materia, y no a la del otro** (FR-025).

Por eso cada informe declara su materia aquí, y no en la vista: es una propiedad
del informe —de qué habla— y no de cómo se sirve. Un informe nuevo sin materia
declarada no se puede publicar, que es el defecto correcto: obliga a decidir de
quién es antes de exponerlo.
"""

from __future__ import annotations

from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "red_operativa"

MATERIA_CRECIMIENTO = "crecimiento"
MATERIA_VALIDACION = "validacion"


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


#: Informe → consulta del catálogo.
CATALOGO: dict[str, str] = {
    # OT12 — flota
    "unidades-por-estado": "ot12_unidades_por_estado",
    "disponibilidad-declarada": "ot12_disponibilidad_declarada",
    "cobertura-flota-por-region": "ot12_cobertura_flota_por_region",
    "condados-cobertura-critica": "ot12_condados_cobertura_critica",
    "rotacion-flota": "ot12_rotacion_flota",
    "bajas-forzadas": "ot12_bajas_forzadas",
    "pendientes-primer-acceso": "ot12_pendientes_primer_acceso",
    "rendimiento-proveedor": "ot12_rendimiento_proveedor",
    # OT11 — regiones
    "tiempo-puesta-operacion": "ot11_tiempo_puesta_operacion",
    "mercados-activos": "ot11_mercados_activos",
    "tasa-aprobacion-primer-intento": "ot11_tasa_aprobacion_primer_intento",
    "motivos-rechazo": "ot11_motivos_rechazo",
    # OT13 — retirada
    "regiones-en-riesgo": "ot13_regiones_en_riesgo",
    "casos-activos-al-despublicar": "ot13_casos_activos_al_despublicar",
    "tiempo-perdida-a-despublicacion": "ot13_tiempo_perdida_a_despublicacion",
}

#: Materia de cada informe. **La autoridad se decide con esto** (FR-025).
#:
#: ⚠️ Solo dos informes son de validación: los que miden **cómo se valida una
#: región** —con qué tasa se aprueba a la primera y por qué se rechaza—. Lo demás
#: es crecimiento, incluida la retirada: decidir que un mercado se cierra es una
#: decisión de crecimiento, no un criterio de validación.
#:
#: La distinción importa porque es la que se equivoca sola. «Regiones en riesgo»
#: suena a validación —habla de regiones— y no lo es: habla de si el mercado
#: aguanta, que es de quien decide dónde crecer.
MATERIAS: dict[str, str] = {
    "tasa-aprobacion-primer-intento": MATERIA_VALIDACION,
    "motivos-rechazo": MATERIA_VALIDACION,
    **{
        informe: MATERIA_CRECIMIENTO
        for informe in CATALOGO
        if informe not in ("tasa-aprobacion-primer-intento", "motivos-rechazo")
    },
}

#: Parametros propios de cada informe, ademas del rango.
#:
#: ⚠️ `umbral_unidades` es **una convencion del informe, no una politica de la
#: empresa** (T033): el origen no define ningun umbral de cobertura minima. Por
#: eso viaja como parametro con un defecto explicito, y la respuesta lo devuelve
#: en `filtros` — quien lea «3 condados en estado critico» tiene que poder ver
#: contra que numero se midio. Sin eso, una cifra elegida por defecto pasaria por
#: una decision de la empresa.
PARAMETROS: dict[str, dict[str, int]] = {
    "condados-cobertura-critica": {"umbral_unidades": 5},
    "motivos-rechazo": {"top": 10},
    # ⚠️ `dias_objetivo` es la otra convencion del departamento: el sistema **no
    # guarda ningun plazo** para poner una region en operacion. Sin verlo en la
    # respuesta, «3 regiones fuera de objetivo» pasaria por el incumplimiento de
    # un acuerdo que nadie firmo.
    "tiempo-puesta-operacion": {"dias_objetivo": 30},
    "regiones-en-riesgo": {"umbral_unidades": 5},
}

#: Los que se publican como endpoint.
PUBLICADOS: frozenset[str] = frozenset(CATALOGO)


#: Nota que viaja **con la cifra** en los informes que la necesitan.
NOTAS: dict[str, dict[str, str]] = {
    "condados-cobertura-critica": {
        "nota_umbral": (
            "El umbral es una convencion de este informe: el sistema operativo no "
            "define ninguna cobertura minima."
        )
    },
    "tiempo-puesta-operacion": {
        "nota_objetivo": (
            "El objetivo en dias es una convencion de este informe: el sistema "
            "operativo no define ningun plazo de puesta en operacion."
        ),
        "nota_medida": (
            "Una region que aun no esta en produccion devuelve dias y "
            "cumple_objetivo ausentes: no incumplio un plazo, sigue dentro de el."
        ),
    },
    "tiempo-perdida-a-despublicacion": {
        "nota_historico": (
            "Un historico vacio aqui no significa que nunca haya pasado: significa "
            "que el modelo no lo vio. Ver medida_exacta_desde."
        )
    },
    "casos-activos-al-despublicar": {
        "nota_historico": (
            "Un resultado vacio aqui no significa que ninguna region se haya "
            "despublicado con casos abiertos: significa que el modelo no observo "
            "ninguna despublicacion. Ver medida_exacta_desde."
        )
    },
    "regiones-en-riesgo": {
        "nota_umbral": (
            "El umbral es una convencion de este informe: el sistema operativo no "
            "define ninguna cobertura minima por region."
        )
    },
    "tasa-aprobacion-primer-intento": {
        "nota_grano": (
            "Se cuentan intentos de validacion, no regiones: una region aprobada "
            "al tercer intento no cuenta como aprobada al primero."
        )
    },
    "cobertura-flota-por-region": {
        "nota_region": (
            "No existe relacion region-condado en el origen; mientras no exista, "
            "la cobertura no puede repartirse por region (decision #38)."
        )
    },
}


class RedOperativaCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def materia_de(self, informe: str) -> str | None:
        """La materia del informe, o `None` si no está declarada.

        Devolver `None` y no una materia por defecto es deliberado: un defecto
        haría que un informe nuevo quedara accesible para quien no le
        corresponde, en silencio.
        """
        return MATERIAS.get(informe)

    def calcular(
        self, informe: str, periodo: Periodo, *, extra: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        parametros: dict[str, Any] = {"desde": periodo.desde, "hasta": periodo.hasta}
        # El defecto declarado primero, y lo que llegue por encima.
        parametros.update(PARAMETROS.get(informe, {}))
        parametros.update(extra or {})
        return self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
