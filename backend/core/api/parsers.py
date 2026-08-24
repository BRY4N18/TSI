"""Parser JSON que garantiza un objeto en la raiz (PG-API-004).

**El problema que resuelve, medido y no supuesto.** 25 modulos de vistas hacen
`request.data.get(...)` o `request.data["..."]` sin comprobar el tipo. Con un
cuerpo `[1, 2, 3]` eso lanza `AttributeError` o `TypeError`, que **no son
excepciones de DRF**: `drf_exception_handler` devuelve `None` para ellas y la
peticion termina en **500**.

El 500 importa mas de lo que parece: es el unico camino que no pasa por
`custom_exception_handler`, y por tanto la unica respuesta del sistema sobre la
que no hay garantia de que muestra. Con `DEBUG=true` ensenaria el traceback.

**Por que central y no en cada vista.** Arreglar 25 ficheros a mano deja fuera el
numero 26, que se escribe la semana que viene. Aqui se rechaza antes de que
ninguna vista lo vea, con un `ParseError` que DRF ya traduce a **400**.

⚠️ **Se verifico que ninguna vista espera una lista en la raiz** antes de imponer
esto: todas tratan el cuerpo como objeto. Si alguna llegara a necesitarla, debe
declarar su propio `parser_classes` — explicitamente, no por omision.
"""

from __future__ import annotations

from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class ObjetoJSONParser(JSONParser):
    """JSON cuya raiz debe ser un objeto."""

    def parse(self, stream, media_type=None, parser_context=None):
        datos = super().parse(stream, media_type, parser_context)
        if datos is not None and not isinstance(datos, dict):
            raise ParseError("El cuerpo debe ser un objeto JSON.")
        return datos
