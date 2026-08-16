"""Servicio base de los informes compuestos de Emergencias.

Enlaza **nombre de informe → consulta del catálogo → respuesta**, y nada más. No
hay una función por informe a propósito: veintiséis funciones que solo cambian en
la cadena que pasan al repositorio son veintiséis sitios donde el día de mañana
una de ellas hará algo distinto que las otras — que es exactamente cómo el diseño
anterior llegó a tener dos caminos midiendo lo mismo con resultados diferentes.

Lo que sí hay es un **registro explícito**: un informe existe si está aquí. No se
deriva del nombre que llegue por la URL, porque entonces el conjunto de informes
publicados sería «los ficheros que haya en el disco», y añadir un fichero de
pruebas al catálogo lo publicaría sin que nadie lo decidiera.
"""

from __future__ import annotations

from typing import Any

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

DEPARTAMENTO = "emergencias"


class InformeDesconocido(KeyError):
    """El informe pedido no está en el registro publicado."""


#: Informe → consulta del catálogo que lo calcula.
#:
#: La clave es el nombre del informe; el valor, el fichero. Se separan porque el
#: nombre es un contrato con el frontend y el del fichero es un detalle del
#: catálogo: renombrar el segundo no debe romper el primero.
CATALOGO: dict[str, str] = {
    "distribucion-severidad": "ot21_distribucion_severidad",
    "distribucion-zona": "ot21_distribucion_zona",
    "completitud-campos-criticos": "ot21_completitud_campos_criticos",
    "descarte-fusion": "ot21_descarte_fusion",
    "ranking-ubicaciones": "ot21_ranking_ubicaciones",
    "impacto-humano": "ot21_impacto_humano",
    "asignacion-automatica-vs-manual": "ot22_asignacion_automatica_vs_manual",
    "tiempo-reportado-confirmado": "ot22_tiempo_reportado_a_confirmado",
    "tiempo-respuesta-por-severidad": "ot22_tiempo_respuesta_por_severidad",
    "rechazo-timeout-por-unidad": "ot22_rechazo_timeout_por_unidad",
    "carga-por-unidad": "ot22_carga_por_unidad",
    "abortos-perdidas": "ot23_abortos_perdidas",
    "ratio-demanda-capacidad": "ot22_ratio_demanda_capacidad",
    "primer-intento": "ot22_primer_intento",
    "perdida-senal": "ot23_perdida_senal",
    "desviacion-llegada": "ot23_desviacion_llegada",
    "cobertura-evidencia": "ot24_cobertura_evidencia",
    "latencia-sincronizacion": "ot24_latencia_sincronizacion",
    "completitud-enriquecimiento": "ot24_completitud_enriquecimiento",
    "volumen-evidencia-por-unidad": "ot24_volumen_evidencia_por_unidad",
    "escaladas-severidad": "ot24_escaladas_severidad",
    "distribucion-resultados": "ot25_distribucion_resultados",
    "envejecimiento-cartera": "ot25_envejecimiento_cartera",
    "retiros-forzados-por-proveedor": "ot25_retiros_forzados_por_proveedor",
    "tiempo-asignado-cierre": "ot25_tiempo_asignado_a_cierre",
    "cierres-forzados": "ot25_cierres_forzados",
}

#: Los que se **publican como endpoint**, que son menos que los del catálogo.
#:
#: ⚠️ Estar en el catálogo y estar publicado son cosas distintas, y confundirlas
#: es el error que este módulo existe para no cometer. El módulo «construye 10,
#: migra 3 y **vigila 13**»: de los seis informes OT21 que hay aquí, solo la
#: completitud se migra —porque el endpoint que la sirve hoy está mal—. Los otros
#: cinco ya los sirve `informes-tacticos-agregados` **correctamente**, y sus
#: consultas existen aquí para **contrastarlos** (T028), no para sustituirlos.
#:
#: Publicarlos sería crear dos endpoints que responden lo mismo leyendo de
#: almacenes distintos. Mientras coincidan nadie lo nota; el día que difieran hay
#: dos cifras verdaderas y ninguna forma de decidir cuál rige.
PUBLICADOS: frozenset[str] = frozenset({
    # US1 — migrado, corrige el defecto de la completitud.
    "completitud-campos-criticos",
    # US2 — dos migrados (corrigen defectos) y dos nuevos.
    "ratio-demanda-capacidad",   # migrado: la capacidad era la de hoy
    "perdida-senal",             # migrado: analizaba el 16,9 % de las posiciones
    "primer-intento",            # nuevo: indicador BSC
    "desviacion-llegada",        # nuevo
    # US3 — los ocho de OT24 y OT25. Todos nuevos: ninguno existia antes, asi
    # que aqui no hay endpoint anterior con el que puedan discrepar.
    "cobertura-evidencia",
    "latencia-sincronizacion",
    "completitud-enriquecimiento",
    "volumen-evidencia-por-unidad",
    "escaladas-severidad",
    "distribucion-resultados",
    "envejecimiento-cartera",
    "retiros-forzados-por-proveedor",
})


class ParametroTramos:
    """Los cortes de antiguedad de la cartera: una lista de dias.

    Se valida entera aqui y no en la consulta porque el error tiene que llegar
    como un 400 con su explicacion. Una lista mal escrita que llegara al almacen
    fallaria con un error de conversion de tipos que no dice cual era el
    problema, y el usuario solo veria un 500.

    Se **ordena** antes de pasarla: la consulta asigna cada caso al ultimo corte
    que no supera su antiguedad, asi que una lista desordenada -`30,1,7`- lo
    mandaria al tramo equivocado **sin fallar**.
    """

    nombre = "tramos_dias"
    defecto = "1,3,7,30"
    maximo_cortes = 10

    def leer(self, crudo: str | None) -> str:
        if crudo is None:
            return self.defecto
        piezas = [p.strip() for p in str(crudo).split(",") if p.strip()]
        if not piezas:
            raise ValueError("'tramos_dias' no puede estar vacio.")
        if len(piezas) > self.maximo_cortes:
            raise ValueError(
                f"'tramos_dias' no admite mas de {self.maximo_cortes} cortes."
            )
        try:
            dias = sorted({int(p) for p in piezas})
        except ValueError:
            raise ValueError("'tramos_dias' debe ser una lista de enteros separados por coma.") from None
        if dias[0] < 0:
            raise ValueError("'tramos_dias' no admite valores negativos.")
        return ",".join(str(d) for d in dias)


class Parametro:
    """Un parámetro de consulta con su valor por defecto y sus límites.

    Los límites no son decoración. `top` sin tope es una forma de pedir el
    catálogo entero de calles; `ventana_dias` sin tope hace que la referencia
    barra todo el histórico en cada consulta. Un parámetro numérico sin cota
    superior es una consulta que alguien puede alargar desde la barra del
    navegador.
    """

    def __init__(self, nombre: str, defecto: int, minimo: int, maximo: int):
        self.nombre = nombre
        self.defecto = defecto
        self.minimo = minimo
        self.maximo = maximo

    def leer(self, crudo: str | None) -> int:
        if crudo is None:
            return self.defecto
        try:
            valor = int(crudo)
        except (TypeError, ValueError):
            raise ValueError(f"'{self.nombre}' debe ser un número entero.") from None
        if valor < self.minimo:
            raise ValueError(f"'{self.nombre}' no puede ser menor que {self.minimo}.")
        if valor > self.maximo:
            raise ValueError(f"'{self.nombre}' no puede ser mayor que {self.maximo}.")
        return valor


#: Parámetros propios de cada informe, además del rango de fechas.
#:
#: Los valores por defecto son los del contrato. Que estén aquí y no repartidos
#: por la vista es lo que permite que el informe declare lo que acepta: una
#: consulta que use `{umbral_seg:UInt32}` sin declararlo aquí falla al ejecutarse
#: por parámetro ausente, y no en silencio con un valor inventado.
PARAMETROS: dict[str, tuple[Parametro, ...]] = {
    "ranking-ubicaciones": (Parametro("top", defecto=10, minimo=1, maximo=100),),
    "perdida-senal": (Parametro("umbral_seg", defecto=60, minimo=1, maximo=86_400),),
    "desviacion-llegada": (
        Parametro("ventana_dias", defecto=90, minimo=7, maximo=730),
        Parametro("muestra_minima", defecto=5, minimo=1, maximo=1_000),
    ),
    "envejecimiento-cartera": (ParametroTramos(),),
}


class EmergenciasCompuestosService:
    def __init__(self, repositorio: ModeloRepository | None = None):
        self._repositorio = repositorio or ModeloRepository()

    def informes_publicados(self) -> list[str]:
        return sorted(PUBLICADOS)

    def parametros_de(self, informe: str) -> tuple[Parametro, ...]:
        return PARAMETROS.get(informe, ())

    def calcular(
        self,
        informe: str,
        periodo: Periodo,
        *,
        extra: dict[str, Any] | None = None,
        publicado: bool = True,
    ) -> list[dict[str, Any]]:
        """Calcula `informe`.

        `publicado=False` lo permite fuera del conjunto publicado, y lo usa **la
        prueba de contraste**: necesita ejecutar las consultas de los informes
        que se vigilan sin que eso los convierta en endpoints.
        """
        if publicado and informe not in PUBLICADOS:
            raise InformeDesconocido(informe)
        try:
            consulta = CATALOGO[informe]
        except KeyError as exc:
            raise InformeDesconocido(informe) from exc

        parametros: dict[str, Any] = {"desde": periodo.desde, "hasta": periodo.hasta}
        dados = extra or {}
        for parametro in self.parametros_de(informe):
            parametros[parametro.nombre] = dados.get(parametro.nombre, parametro.defecto)

        return self._repositorio.ejecutar(
            consulta, departamento=DEPARTAMENTO, parametros=parametros
        )
