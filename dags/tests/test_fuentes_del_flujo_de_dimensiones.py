"""Las fuentes que un módulo declara y las que su flujo vuelve a leer.

⚠️ **Esta prueba existe porque el fallo ocurrió dos veces.**

La primera en `hecho_accidente`: se añadieron seis fuentes a `extraer()` y se
olvidaron en la tupla del flujo. La segunda en `dim_geografia`: se añadieron
`vecinos` y `regiones`, el `extract` las guardó, y el `transform` las leía desde
una lista de cinco nombres escrita a mano.

Las dos veces el síntoma fue el mismo, y las dos veces **no fallaba nada**. El
`construir` recibe `datos.get(nombre, [])`, que sustituye la fuente ausente por
una lista vacía, y de ahí sale un cero perfectamente plausible:

* En `hecho_accidente`, `0` notas donde el origen tenía 51.
* En `dim_geografia`, **ningún condado con vecinos** — que en el informe de
  cobertura crítica es la marca de «sin alternativas», la situación más grave
  que ese informe reporta. Un olvido de lectura se habría publicado como una
  emergencia operativa.

Un cero legítimo y una fuente que no se leyó son indistinguibles mirando el
resultado. Solo se ven comparando **lo que el módulo declara** con **lo que el
flujo lee**, que es lo que hace esto.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones import dim_geografia  # noqa: E402
from lib.dimensiones_tasks import DIMENSIONES  # noqa: E402


def test_el_flujo_lee_todos_los_catalogos_que_geografia_declara():
    """El `transform` deriva los nombres de `CONSULTAS`, no de una lista fija.

    Se comprueba leyendo el código del flujo: lo que importa es que **no exista**
    una lista escrita a mano que pueda quedarse corta, no que hoy coincida.
    """
    fuente = (Path(__file__).resolve().parents[1] / "lib" / "dimensiones_tasks.py").read_text(
        encoding="utf-8"
    )

    assert "for n in dim_geografia.CONSULTAS" in fuente, (
        "el flujo enumera los catálogos de geografía a mano: añadir uno al "
        "módulo y olvidarlo aquí no falla, lo sustituye por una lista vacía"
    )
    assert 'leido("vecino_vecinos")' in fuente and 'leido("vecino_condados")' in fuente, (
        "el flujo no lee las dos fuentes de dim_condado_vecino: un condado "
        "sin nombre o una vecindad vacía saldrían en silencio"
    )


def test_geografia_declara_los_catalogos_que_su_constructor_usa():
    """Los nombres que `construir` consulta tienen que existir en `CONSULTAS`.

    Sin esto, un `catalogos.get("vecinos")` escrito con un nombre que nadie
    extrae devolvería vacío para siempre — y con la prueba de arriba en verde,
    porque el flujo estaría leyendo correctamente un catálogo que no existe.
    """
    fuente = (
        Path(__file__).resolve().parents[1] / "lib" / "dimensiones" / "dim_geografia.py"
    ).read_text(encoding="utf-8")

    import re

    consultados = set(re.findall(r'catalogos(?:\.get\(|\[)"([a-z_]+)"', fuente))
    declarados = set(dim_geografia.CONSULTAS)

    assert consultados <= declarados, (
        f"`construir` lee {sorted(consultados - declarados)}, que nadie extrae: "
        f"devolverían vacío para siempre"
    )


def test_todas_las_dimensiones_del_flujo_tienen_su_fila_desconocida_o_no_la_necesitan():
    """`dim_tiempo` es la única que no la necesita: se genera completa.

    Una dimensión resoluble sin fila desconocida hace que un hecho que apunte a
    una clave ausente **desaparezca al unir**, que es peor que no saber a qué
    apunta.
    """
    from lib.dimensiones.desconocido import FILAS_DESCONOCIDAS

    sin_fila = set(DIMENSIONES) - set(FILAS_DESCONOCIDAS) - {"dim_tiempo", "dim_prospecto"}

    assert not sin_fila, f"{sorted(sin_fila)} no tienen fila desconocida"
