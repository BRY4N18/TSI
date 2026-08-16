"""T036 — una página de demos puede traer **menos filas que el `limit`**.

Es la consecuencia declarada del filtro en dos pasos (research D3): el prefiltro
por día trae de más, y el servicio descarta con precisión de segundo las que
expiraron hoy más temprano.

Lo que esta prueba fija no es el número de filas, sino **quién es la autoridad**:
`has_next`, no el conteo. Un consumidor que asuma «si vienen menos de `limit`, se
acabó» se dejará demos vigentes sin ver — y no tendrá forma de saberlo, porque la
respuesta es válida en todo lo demás.
"""

from __future__ import annotations

import pytest

RUTA = "/api/v1/informes/ventas-crm/demos-activas"


@pytest.mark.api
class TestLaExpiradaHoyNoAparece:
    def test_no_esta_en_la_respuesta(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert "Demo Expirada" not in {f["empresa"] for f in cuerpo["data"]}

    def test_la_sin_fecha_tampoco(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert "Demo SinFecha" not in {f["empresa"] for f in cuerpo["data"]}

    def test_las_vigentes_si(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 4  # 3 formatos + la del otro gerente


@pytest.mark.api
class TestPaginaCorta:
    def test_una_pagina_puede_traer_menos_de_lo_pedido(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        # Con `limit=5` el prefiltro trae 5 candidatas (incluida la expirada
        # hoy), el refinamiento descarta una, y la página sale con 4.
        cuerpo = api_client.get(f"{RUTA}?limit=5", **admin_auth_headers).json()

        assert len(cuerpo["data"]) < 5

    def test_que_venga_corta_no_significa_fin_de_resultados(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        """`has_next` es la autoridad, no el conteo de filas."""
        cuerpo = api_client.get(f"{RUTA}?limit=2", **admin_auth_headers).json()

        # Se pidieron 2 y puede venir 1 o 2; lo que no puede es que `has_next`
        # mienta sobre si queda algo por ver.
        assert cuerpo["meta"]["pagination"]["has_next"] is True
        assert cuerpo["meta"]["pagination"]["cursor"] is not None

    def test_recorriendo_por_cursor_se_ven_todas_las_vigentes(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        """La garantía real: seguir el cursor no se deja ninguna."""
        from urllib.parse import quote

        vistas: list[str] = []
        cursor = None
        for _ in range(20):
            url = f"{RUTA}?limit=1"
            if cursor:
                url += f"&cursor={quote(cursor)}"
            cuerpo = api_client.get(url, **admin_auth_headers).json()
            vistas.extend(f["empresa"] for f in cuerpo["data"])
            cursor = cuerpo["meta"]["pagination"]["cursor"]
            if cursor is None:
                break

        assert cursor is None, "el recorrido no termino"
        assert set(vistas) == {"Demo Zeta", "Demo Offset", "Demo SinZona", "Demo Ajena"}
        assert len(vistas) == len(set(vistas)), "una demo se repitio entre paginas"

    def test_el_limit_declarado_en_meta_es_el_pedido_no_el_devuelto(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        # `limit` describe la petición; el conteo de `data` describe el resultado.
        cuerpo = api_client.get(f"{RUTA}?limit=5", **admin_auth_headers).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 5


@pytest.mark.django_db
class TestElCentinelaDeLaColumnaDeTexto:
    """El defecto que se vio al construir el frontend: un `500` en vez del listado.

    `demo_expiracion` vale la cadena `'null'` cuando el prospecto no tiene demo.
    Comparando texto —que es lo único seguro en esa columna— `'null'` ordena
    **después** de cualquier dígito, así que `demo_expiracion >= '2026-08-11'`
    lo dejaba pasar. La fila colada llegaba sin fecha utilizable y reventaba al
    componer el cursor de la página siguiente.

    Ninguna prueba lo detectó porque el fixture sembraba `None`, que no es lo que
    Pinot devuelve.
    """

    def test_el_centinela_no_aparece_como_demo_activa(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        respuesta = api_client.get(
            "/api/v1/informes/ventas-crm/demos-activas?limit=500",
            **admin_auth_headers,
        )

        assert respuesta.status_code == 200, respuesta.content
        empresas = {f["empresa"] for f in respuesta.json()["data"]}
        assert "Demo Centinela" not in empresas

    def test_el_listado_responde_200_con_el_centinela_sembrado(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        """Antes daba `500`: el cursor no se podía componer sobre esa fila."""
        respuesta = api_client.get(
            "/api/v1/informes/ventas-crm/demos-activas?limit=1",
            **admin_auth_headers,
        )

        assert respuesta.status_code == 200, respuesta.content

    def test_las_demos_reales_siguen_apareciendo(
        self, api_client, admin_auth_headers, demos_formato_mixto, reloj_congelado
    ):
        """Excluir el centinela no debe llevarse por delante las demos buenas."""
        respuesta = api_client.get(
            "/api/v1/informes/ventas-crm/demos-activas?limit=500",
            **admin_auth_headers,
        )

        empresas = {f["empresa"] for f in respuesta.json()["data"]}
        assert {"Demo Zeta", "Demo Offset", "Demo SinZona"} <= empresas
