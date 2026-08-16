"""US1 — El listado de casos (L1).

**T019 es la prueba central del módulo**, y `dos_condados` es lo que la hace
real: con casos en un solo condado, un cliente acotado y otro sin acotar
obtienen exactamente lo mismo.

**T022 protege una exclusión constitucional.** Las coordenadas del accidente no
salen, y la exención de la autoridad departamental **no las levanta**: es una
exclusión de dato sensible, no de acotamiento.
"""

from __future__ import annotations

import re

import pytest

from apps.accidentes.tests.informes_fixtures import (
    CASO_ABIERTO,
    CASO_AJENO,
    CASO_CERRADO,
    CASO_DESCARTADO,
    CASO_FUSIONADO,
    CASO_SIN_UBICACION,
    CONDADO_AJENO,
    CONDADO_CONTRATADO,
    LAT_PROHIBIDA,
    LON_PROHIBIDA,
    SEVERIDAD_ALTA,
)

pytestmark = pytest.mark.django_db

URL = "/api/v1/informes/emergencias/casos"


def _data(resp):
    assert resp.status_code == 200, resp.content
    return resp.json()["data"]


def _casos(resp):
    return {f["numero_caso"] for f in _data(resp)}


# ── T019 — acotamiento por zona contratada ──────────────────────────────────


def test_el_cliente_solo_ve_los_casos_de_su_condado_contratado(
    client, emergencias_sembradas, cliente_informes_headers
):
    cuerpo = client.get(f"{URL}?limit=500", **cliente_informes_headers).json()

    casos = {f["numero_caso"] for f in cuerpo["data"]}
    assert CASO_CERRADO in casos
    assert CASO_AJENO not in casos
    assert cuerpo["meta"]["acotado_a"] == "zonas_contratadas"


def test_el_rol_interno_ve_los_dos_condados(
    client, emergencias_sembradas, operador_informes_headers
):
    cuerpo = client.get(f"{URL}?limit=500", **operador_informes_headers).json()

    casos = {f["numero_caso"] for f in cuerpo["data"]}
    assert {CASO_CERRADO, CASO_AJENO} <= casos
    assert cuerpo["meta"]["acotado_a"] == "todos"


def test_el_conteo_del_cliente_es_estrictamente_menor(
    client, emergencias_sembradas, cliente_informes_headers,
    operador_informes_headers
):
    del_cliente = _casos(client.get(f"{URL}?limit=500", **cliente_informes_headers))
    del_interno = _casos(client.get(f"{URL}?limit=500", **operador_informes_headers))

    assert del_cliente
    assert len(del_cliente) < len(del_interno)


def test_el_acotado_a_declara_el_eje_y_no_dice_propios(
    client, emergencias_sembradas, cliente_informes_headers
):
    """Los accidentes de una zona contratada **no son del cliente**.

    Decir `propios` afirmaría que el listado abarca todo lo que le pertenece,
    cuando abarca lo que ocurrió donde contrató cobertura.
    """
    cuerpo = client.get(URL, **cliente_informes_headers).json()

    assert cuerpo["meta"]["acotado_a"] == "zonas_contratadas"
    assert cuerpo["meta"]["acotado_a"] != "propios"


# ── T010 en su forma de extremo a extremo — sin zonas es CERO, no TODO ──────


def test_un_cliente_sin_zonas_contratadas_obtiene_cero_casos(
    client, emergencias_sembradas, cliente_sin_zonas_headers
):
    """De las dos lecturas posibles de «sin zonas», la contraria daría el mapa
    de siniestralidad completo a quien no contrató nada."""
    resp = client.get(f"{URL}?limit=500", **cliente_sin_zonas_headers)

    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_pedir_un_condado_ajeno_no_amplia_nada(
    client, emergencias_sembradas, cliente_informes_headers
):
    """La intersección con lo contratado lo deja vacío, no lo abre."""
    filas = _data(
        client.get(f"{URL}?condado={CONDADO_AJENO}&limit=500",
                   **cliente_informes_headers)
    )
    assert filas == []


def test_el_interno_si_puede_filtrar_por_cualquier_condado(
    client, emergencias_sembradas, operador_informes_headers
):
    casos = _casos(
        client.get(f"{URL}?condado={CONDADO_AJENO}&limit=500",
                   **operador_informes_headers)
    )
    assert casos == {CASO_AJENO}


# ── T020 — el cliente no ve casos abiertos ──────────────────────────────────


def test_el_cliente_no_ve_los_casos_abiertos_de_su_propia_zona(
    client, emergencias_sembradas, cliente_informes_headers
):
    """La emergencia en curso es información operativa, no del cliente.

    El caso abierto está **en su condado contratado**: si apareciera, el filtro
    de situación no se estaría imponiendo.
    """
    casos = _casos(client.get(f"{URL}?limit=500", **cliente_informes_headers))

    assert CASO_ABIERTO not in casos
    assert CASO_CERRADO in casos


def test_el_cliente_no_puede_pedir_los_casos_en_curso(
    client, emergencias_sembradas, cliente_informes_headers
):
    """Pedir `situacion=en_curso` no levanta la restricción del eje."""
    casos = _casos(
        client.get(f"{URL}?situacion=en_curso&limit=500",
                   **cliente_informes_headers)
    )
    assert CASO_ABIERTO not in casos


def test_meta_declara_la_situacion_impuesta(
    client, emergencias_sembradas, cliente_informes_headers
):
    """Un cliente debe poder ver en `meta` por qué no le llegan los abiertos."""
    cuerpo = client.get(URL, **cliente_informes_headers).json()

    assert cuerpo["meta"]["filtros"]["situacion"] == "cerrado"


# ── T021 — las tres formas de quedar inactivo se distinguen ─────────────────


def test_cerrado_descartado_y_fusionado_son_conjuntos_disjuntos(
    client, emergencias_sembradas, operador_informes_headers
):
    """Un recuento de «casos inactivos» sin distinguir sumaría emergencias
    atendidas, falsas alarmas y duplicados como si fueran lo mismo."""
    cerrados = _casos(
        client.get(f"{URL}?situacion=cerrado&limit=500", **operador_informes_headers)
    )
    descartados = _casos(
        client.get(f"{URL}?situacion=descartado&limit=500",
                   **operador_informes_headers)
    )
    duplicados = _casos(
        client.get(f"{URL}?situacion=duplicado&limit=500",
                   **operador_informes_headers)
    )

    assert CASO_CERRADO in cerrados
    assert CASO_DESCARTADO in descartados
    assert CASO_FUSIONADO in duplicados

    assert not (cerrados & descartados)
    assert not (cerrados & duplicados)
    assert not (descartados & duplicados)


def test_el_fusionado_indica_de_que_caso_es_duplicado(
    client, emergencias_sembradas, operador_informes_headers
):
    """Y **no se omite**: el sistema garantiza que no se borra."""
    filas = _data(
        client.get(f"{URL}?situacion=duplicado&limit=500",
                   **operador_informes_headers)
    )
    fusionado = next(f for f in filas if f["numero_caso"] == CASO_FUSIONADO)

    assert fusionado["duplicado_de"] == CASO_CERRADO


def test_la_respuesta_no_contiene_ningun_campo_estado(
    client, emergencias_sembradas, operador_informes_headers
):
    """Los tres hechos viajan por separado; **no hay estado calculado**.

    Inferirlo ataría este listado a una regla de exclusividad que vive en el
    módulo de fusión, y empezaría a mentir el día que cambiara.
    """
    for fila in _data(client.get(f"{URL}?limit=500", **operador_informes_headers)):
        assert "estado" not in fila
        assert "situacion" not in fila
        assert {"activo", "hora_fin", "duplicado_de"} <= set(fila)


def test_los_tres_hechos_llegan_sin_interpretar(
    client, emergencias_sembradas, operador_informes_headers
):
    por_caso = {
        f["numero_caso"]: f
        for f in _data(client.get(f"{URL}?limit=500", **operador_informes_headers))
    }

    cerrado = por_caso[CASO_CERRADO]
    assert cerrado["activo"] is False
    assert cerrado["hora_fin"] == "09:30"
    assert cerrado["duplicado_de"] is None

    # ⚠️ `''` es el centinela de ausencia, no un valor. Una guarda por nulidad
    # sería siempre cierta y clasificaría todos los casos como cerrados.
    descartado = por_caso[CASO_DESCARTADO]
    assert descartado["activo"] is False
    assert descartado["hora_fin"] is None
    assert descartado["duplicado_de"] is None


def test_borrador_no_es_una_situacion_admitida():
    """⚠️ La spec lo pedía y **no se puede dar** con lo que el caso registra.

    `BORRADOR` es un estado formal que vive en el histórico. Un caso en borrador
    es `activo = true` sin hora de fin — idéntico a cualquier otro en curso—, así
    que implementarlo devolvería **todos los casos activos** etiquetados como
    detenidos en borrador: la forma correcta con el contenido equivocado.
    """
    from core.repositories.accidentes.informes_casos_repository import SITUACIONES

    assert "borrador" not in SITUACIONES


def test_una_situacion_desconocida_da_400(
    client, emergencias_sembradas, operador_informes_headers
):
    resp = client.get(f"{URL}?situacion=borrador", **operador_informes_headers)
    assert resp.status_code == 400, resp.content


# ── T022 — ni coordenadas ni identidad ──────────────────────────────────────


def test_la_respuesta_no_contiene_coordenadas(
    client, emergencias_sembradas, operador_informes_headers
):
    resp = client.get(f"{URL}?limit=500", **operador_informes_headers)
    cuerpo = resp.content.decode("utf-8")

    assert str(LAT_PROHIBIDA) not in cuerpo
    assert str(LON_PROHIBIDA) not in cuerpo
    for fila in _data(resp):
        assert "latitud" not in " ".join(fila.keys()).lower()
        assert "longitud" not in " ".join(fila.keys()).lower()


def test_la_autoridad_del_departamento_tampoco_ve_coordenadas(
    client, emergencias_sembradas, director_operaciones_headers
):
    """Su exención es de **acotamiento**, no de dato sensible (FR-014b).

    Es la distinción que hace que un cargo no pueda levantar una exclusión
    constitucional por el camino de un informe.
    """
    resp = client.get(f"{URL}?limit=500", **director_operaciones_headers)
    cuerpo = resp.content.decode("utf-8")

    assert resp.json()["meta"]["acotado_a"] == "todos"
    assert str(LAT_PROHIBIDA) not in cuerpo
    assert str(LON_PROHIBIDA) not in cuerpo


def test_el_repositorio_enumera_las_columnas_en_vez_de_pedirlas_todas():
    from core.repositories.accidentes import informes_casos_repository as repo

    fuente = open(repo.__file__, encoding="utf-8").read()
    consultas = re.findall(r'"(SELECT [^"]+)"', fuente)

    assert consultas
    for consulta in consultas:
        assert "SELECT *" not in consulta, consulta

    for prohibida in ("latitudinicio", "longitudinicio", "descripcion"):
        assert prohibida not in repo.COLUMNAS_CASO


def test_ningun_listado_lee_las_tablas_de_personas():
    """Conductores, implicados y vehículos no se consultan desde aquí."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[4]
    modulos = [
        raiz / "core" / "repositories" / "accidentes" / "informes_casos_repository.py",
        raiz / "core" / "repositories" / "accidentes" / "informes_evidencia_repository.py",
        raiz / "core" / "repositories" / "accidentes" / "informes_cierres_repository.py",
        raiz / "core" / "repositories" / "seguimiento" / "informes_despachos_repository.py",
    ]
    for modulo in modulos:
        fuente = modulo.read_text(encoding="utf-8")
        for tabla in ("Dim_Conductor", "Dim_Implicado", "Dim_Vehiculo",
                      "Fact_Conductor_Accidente"):
            assert tabla not in fuente, f"{modulo.name} lee {tabla}"


# ── T023 — un caso sin ubicación resoluble aparece ──────────────────────────


def test_un_caso_sin_ubicacion_aparece_con_la_ubicacion_ausente(
    client, emergencias_sembradas, operador_informes_headers
):
    """No se omite: es una anomalía que la supervisión necesita ver — y además
    nunca podrá acotarse a ninguna zona."""
    por_caso = {
        f["numero_caso"]: f
        for f in _data(client.get(f"{URL}?limit=500", **operador_informes_headers))
    }

    assert CASO_SIN_UBICACION in por_caso
    fila = por_caso[CASO_SIN_UBICACION]
    assert fila["calle"] is None
    assert fila["ciudad"] is None
    assert fila["condado"] is None


def test_el_caso_sin_ubicacion_no_llega_a_ningun_cliente(
    client, emergencias_sembradas, cliente_informes_headers
):
    """No tiene calle, así que no está en ninguna zona contratada."""
    casos = _casos(client.get(f"{URL}?limit=500", **cliente_informes_headers))
    assert CASO_SIN_UBICACION not in casos


# ── Nombres, filtros y permisos ─────────────────────────────────────────────


def test_devuelve_nombres_y_no_identificadores(
    client, emergencias_sembradas, operador_informes_headers
):
    fila = _data(
        client.get(f"{URL}?condado={CONDADO_CONTRATADO}&limit=500",
                   **operador_informes_headers)
    )[0]

    assert fila["severidad"] in ("Grave", "Leve")
    assert fila["condado"] == "Valle Norte"
    assert fila["tipo_reportado"] == "Colisión"
    for interno in ("idseveridad", "idcalle", "idtiporeportado", "idusuario"):
        assert interno not in fila


def test_filtrar_por_severidad(
    client, emergencias_sembradas, operador_informes_headers
):
    filas = _data(
        client.get(f"{URL}?severidad={SEVERIDAD_ALTA}&limit=500",
                   **operador_informes_headers)
    )
    assert filas
    assert {f["severidad"] for f in filas} == {"Grave"}


def test_el_partner_recibe_403(
    client, emergencias_sembradas, partner_informes_headers
):
    """El acceso programático a estos datos tiene su propio camino, con su
    alcance y su auditoría. Dejarlo entrar aquí duplicaría ese control con otro
    que no lo audita."""
    resp = client.get(URL, **partner_informes_headers)

    assert resp.status_code == 403, resp.content
    assert "data" not in resp.json()


def test_sin_autenticar_es_401(client, emergencias_sembradas):
    assert client.get(URL).status_code == 401
