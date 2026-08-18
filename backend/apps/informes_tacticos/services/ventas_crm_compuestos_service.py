"""Servicio de los informes compuestos de Ventas y CRM.

Tercer departamento, y sigue sin necesitar plomería propia: el cargador de
consultas, el repositorio de lectura, la resolución de período y los permisos se
reutilizan tal cual.

⚠️ Lo propio de este departamento: el acotamiento por titularidad
------------------------------------------------------------------
El **Director de Marketing** ve el departamento entero, que es de lo que
responde. El **ejecutivo comercial** ve **sus propios prospectos** y no los de
los demás (FR-033, FR-034).

Es el primer departamento con acotamiento en los compuestos, y por eso la
respuesta declara `acotado_a`: quien lee «12 prospectos en pipeline» tiene que
saber si son los suyos o los de todos. Sin ese campo, un ejecutivo y su director
verían la misma pantalla con cifras distintas y ninguno sabría por qué.

⚠️ El acotamiento filtra por el **hecho**, no por la dimensión
---------------------------------------------------------------
`dim_prospecto` no guarda a quién pertenece un prospecto, y es deliberado: la
asignación tiene **instante propio** y un prospecto puede reasignarse, así que
vive en `hecho_asignacion_prospecto`. El acotamiento se aplica sobre ese hecho.

Guardar el dueño en la dimensión habría hecho que reasignar un prospecto
reescribiera la carga de todos los períodos anteriores — el mismo defecto que la
atribución histórica corrige en los otros departamentos (FR-015).
"""

from __future__ import annotations

from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "ventas_crm"

ACOTADO_TODOS = "todos"
ACOTADO_PROPIOS = "propios"


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


#: Informe → consulta del catálogo.
CATALOGO: dict[str, str] = {
    # OT02 — el embudo (CU-T03)
    "embudo-conversion": "ot02_embudo_conversion",
    "permanencia-por-etapa": "ot02_permanencia_por_etapa",
    "carga-por-ejecutivo": "ot02_carga_por_ejecutivo",
    "pipeline-ponderado": "ot02_pipeline_ponderado",
    "motivos-perdida": "ot02_motivos_perdida",
    # OT01 — los canales (CU-T04)
    "captacion-por-canal": "ot01_captacion_por_canal",
    "conversion-por-canal": "ot01_conversion_por_canal",
    "convertidos-por-canal": "ot01_convertidos_por_canal",
    # OT03 — la demo y la nutrición
    "intensidad-demo": "ot03_intensidad_demo",
    "secciones-visitadas": "ot03_secciones_visitadas",
    "efectividad-nutricion": "ot03_efectividad_nutricion",
    "latencia-reaccion": "ot03_latencia_reaccion",
    "reglas-disparo": "ot03_reglas_disparo",
}

#: Parametros propios, con su defecto. `top` recorta rankings; sin el, ClickHouse
#: rechazaria las dos consultas que lo declaran.
PARAMETROS: dict[str, dict[str, int]] = {
    "motivos-perdida": {"top": 10},
    "secciones-visitadas": {"top": 10},
}

#: Convención del pipeline ponderado. El sistema operativo no define pesos:
#: viajan en `meta.filtros` para que la cifra no se lea como politica.
PESOS_ETAPA_DEFECTO = (
    "Nuevo=0.1, Contactado=0.2, Calificado=0.4, Propuesta=0.6, Negociación=0.8"
)
NOTA_PESOS_ETAPA = (
    "pesos_etapa es una convencion del informe, no una politica de la empresa: "
    "el sistema operativo no define ninguna ponderacion."
)

PUBLICADOS: frozenset[str] = frozenset(CATALOGO)

#: El único informe que desglosa por ejecutivo (FR-028).
#:
#: ⚠️ Se identifica por su **rol**, que es su función, no por su identidad
#: personal. Y ningún otro informe del departamento desglosa por persona: un
#: ranking de quién cierra menos es una herramienta de vigilancia, y las
#: preguntas que interesan —dónde se atasca el embudo, qué canal funciona— se
#: responden sin nombrar a nadie.
DESGLOSA_POR_EJECUTIVO = frozenset({"carga-por-ejecutivo"})


class VentasCrmCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def calcular(
        self,
        informe: str,
        periodo: Periodo,
        *,
        idejecutivo: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        """Calcula el informe y devuelve **con qué alcance** se calculó.

        `idejecutivo` acota a los prospectos de esa persona. Devolver el alcance
        junto a los datos —y no dejarlo implícito— es lo que permite a la vista
        declararlo en la respuesta: una cifra acotada y una completa se ven
        idénticas, y solo el `meta` las distingue.
        """
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        parametros: dict[str, Any] = {"desde": periodo.desde, "hasta": periodo.hasta}
        parametros.update(PARAMETROS.get(informe, {}))
        parametros.update(extra or {})

        # ⚠️ `-1` y no `NULL` para «sin acotar»: el parámetro con tipo de
        # ClickHouse no admite ausencia, y la consulta compara
        # `{idejecutivo:Int32} = -1 OR idejecutivo = {idejecutivo:Int32}`.
        # Usar `0` habría chocado con un identificador real algún día.
        parametros["idejecutivo"] = idejecutivo if idejecutivo is not None else -1

        filas = self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
        alcance = ACOTADO_PROPIOS if idejecutivo is not None else ACOTADO_TODOS
        return filas, alcance
