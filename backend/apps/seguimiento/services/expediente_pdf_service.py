"""PDF mínimo del expediente (RF-SEG-006)."""

from __future__ import annotations

from datetime import datetime, timezone

from apps.seguimiento.services.expediente_service import ExpedienteService


class ExpedientePdfService:
    def __init__(self, expediente: ExpedienteService | None = None):
        self.expediente = expediente or ExpedienteService()

    def generar_bytes(self, idaccidente: str, *, condados_permitidos: set[int] | None = None) -> bytes | None:
        data = self.expediente.obtener(
            idaccidente,
            condados_permitidos=condados_permitidos,
            requiere_cerrado=True,
        )
        if not data:
            return None
        return _minimal_pdf("\n".join(self._lineas(idaccidente, data)))

    def _lineas(self, idaccidente: str, data: dict) -> list[str]:
        """Cuerpo del expediente.

        Antes eran siete renglones de conteos ("Despachos: 2", "Notas: 5") que
        no decían qué pasó en el caso. Se mantiene el resumen y se añade el
        detalle que el cliente necesita para entender la atención: cuándo
        ocurrió, dónde, qué unidades acudieron y qué se registró en sitio.
        """
        acc = data["accidente"]
        lineas = [
            f"Expediente TSI — {idaccidente}",
            "",
            "RESUMEN",
            f"Estado: {data['estado_actual']}",
            f"Severidad: {_etiqueta_severidad(acc.get('idseveridad'))}",
            f"Fecha del accidente: {_fecha(acc.get('fechahoraaccidente'))}",
            f"Duracion de la atencion: {_duracion(acc.get('duracionminutos'))}",
            f"Heridos: {acc.get('numheridos') or 0}   "
            f"Fallecidos: {acc.get('numfallecidos') or 0}   "
            f"Vehiculos: {acc.get('numvehiculos') or 0}",
            "",
            "DESCRIPCION",
            str(acc.get("descripcion") or "Sin descripcion registrada."),
            "",
            f"UNIDADES DESPACHADAS ({len(data['despachos'])})",
        ]

        if data["despachos"]:
            for despacho in data["despachos"]:
                lineas.append(
                    f"- Despacho {despacho.get('iddespacho')}: "
                    f"unidad {despacho.get('idunidademergencia')}"
                    + (
                        f", llegada {_fecha(despacho.get('fechahorallegada'))}"
                        if despacho.get("fechahorallegada")
                        else ""
                    )
                )
        else:
            lineas.append("- Sin despachos registrados.")

        lineas += ["", f"NOTAS DE CAMPO ({len(data['notas'])})"]
        if data["notas"]:
            for nota in data["notas"]:
                lineas.append(f"- {nota.get('tiponota') or 'Nota'}: {nota.get('nota') or ''}")
        else:
            lineas.append("- Sin notas de campo.")

        lineas += [
            "",
            f"EVIDENCIA FOTOGRAFICA: {len(data['evidencias'])} archivo(s) adjunto(s).",
        ]
        return lineas


SEVERIDAD_LABEL = {1: "Leve", 2: "Moderado", 3: "Grave", 4: "Fatal"}


def _etiqueta_severidad(idseveridad) -> str:
    try:
        return SEVERIDAD_LABEL.get(int(idseveridad), f"Sev. {idseveridad}")
    except (TypeError, ValueError):
        return "No registrada"


def _fecha(epoch_ms) -> str:
    """Epoch en milisegundos → fecha legible; vacío si no hay dato."""
    if epoch_ms in (None, ""):
        return "No registrada"
    try:
        momento = datetime.fromtimestamp(int(epoch_ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return "No registrada"
    return momento.strftime("%d/%m/%Y %H:%M UTC")


def _duracion(minutos) -> str:
    if minutos in (None, ""):
        return "No registrada"
    try:
        total = int(minutos)
    except (TypeError, ValueError):
        return "No registrada"
    horas, resto = divmod(total, 60)
    return f"{horas} h {resto} min" if horas else f"{resto} min"


_CABECERA = b"%PDF-1.4\n"

#: Geometría de la página (Carta, en puntos) y márgenes del texto.
_ANCHO_PAGINA = 612
_ALTO_PAGINA = 792
_MARGEN_X = 50
_MARGEN_SUPERIOR = 750
_MARGEN_INFERIOR = 50
_TAMANO_FUENTE = 12
_INTERLINEADO = 16

#: Ancho medio de Helvetica ≈ 0.5 em; con eso se calcula cuántos caracteres
#: caben antes de salirse por el borde derecho.
_MAX_CARACTERES_LINEA = int((_ANCHO_PAGINA - 2 * _MARGEN_X) / (_TAMANO_FUENTE * 0.5))

_LINEAS_POR_PAGINA = int((_MARGEN_SUPERIOR - _MARGEN_INFERIOR) / _INTERLINEADO) + 1


def _escapar(texto: str) -> str:
    """Escapa los tres caracteres con significado dentro de un string PDF."""
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _envolver(linea: str) -> list[str]:
    """Parte una línea larga en varias que quepan en el ancho útil."""
    if len(linea) <= _MAX_CARACTERES_LINEA:
        return [linea]
    partes: list[str] = []
    actual = ""
    for palabra in linea.split(" "):
        # Una sola palabra más larga que la línea se corta a lo bruto: es
        # preferible a dejarla salirse de la página.
        while len(palabra) > _MAX_CARACTERES_LINEA:
            if actual:
                partes.append(actual)
                actual = ""
            partes.append(palabra[:_MAX_CARACTERES_LINEA])
            palabra = palabra[_MAX_CARACTERES_LINEA:]
        if not actual:
            actual = palabra
        elif len(actual) + 1 + len(palabra) <= _MAX_CARACTERES_LINEA:
            actual = f"{actual} {palabra}"
        else:
            partes.append(actual)
            actual = palabra
    if actual:
        partes.append(actual)
    return partes


def _contenido_pagina(lineas: list[str]) -> bytes:
    """Operadores de texto de una página, **una línea por renglón**.

    ⚠️ Un `\\n` dentro de un string PDF **no** salta de renglón: es un carácter
    más. La versión anterior metía las siete líneas del expediente en un único
    `(...) Tj`, así que todo se pintaba encima del mismo renglón y lo que
    sobraba se salía por el borde derecho — el "se recorta" del hallazgo #21.
    El salto real lo dan `TL` (interlineado) y `T*` (siguiente renglón).
    """
    partes = [
        f"BT /F1 {_TAMANO_FUENTE} Tf {_INTERLINEADO} TL "
        f"{_MARGEN_X} {_MARGEN_SUPERIOR} Td"
    ]
    for linea in lineas:
        partes.append(f"({_escapar(linea)}) Tj T*")
    partes.append("ET")
    return "\n".join(partes).encode("latin-1", errors="replace")


def _minimal_pdf(text: str) -> bytes:
    """Genera un PDF 1.4 válido, paginado, con el texto dado.

    Corrige dos defectos que producían los dos síntomas reportados en el
    hallazgo #21 ("sale una página en blanco o se recorta"):

    1. **Todo el texto en un renglón.** Ver `_contenido_pagina`.
    2. **Tabla `xref` desplazada.** Los desplazamientos se calculaban desde el
       inicio del *cuerpo*, ignorando los 9 bytes de la cabecera `%PDF-1.4\\n`,
       y `startxref` apuntaba al final del cuerpo en vez de a la posición real
       de la tabla. Todos los offsets quedaban 9 bytes cortos; los lectores
       estrictos no encontraban los objetos y mostraban la **página en blanco**.
    """
    lineas: list[str] = []
    for cruda in text.split("\n"):
        lineas.extend(_envolver(cruda))
    if not lineas:
        lineas = [""]

    paginas = [
        lineas[i : i + _LINEAS_POR_PAGINA] for i in range(0, len(lineas), _LINEAS_POR_PAGINA)
    ]

    # Numeración: 1 catálogo, 2 árbol de páginas, 3 fuente, y luego un par
    # (página, contenido) por cada página.
    id_primera_pagina = 4
    ids_pagina = [id_primera_pagina + 2 * i for i in range(len(paginas))]
    kids = " ".join(f"{i} 0 R" for i in ids_pagina)

    objetos: list[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(paginas)} >>\nendobj\n".encode(),
        b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        b"/Encoding /WinAnsiEncoding >>\nendobj\n",
    ]

    for indice, contenido_lineas in enumerate(paginas):
        id_pagina = ids_pagina[indice]
        id_contenido = id_pagina + 1
        objetos.append(
            (
                f"{id_pagina} 0 obj\n<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {_ANCHO_PAGINA} {_ALTO_PAGINA}] "
                f"/Contents {id_contenido} 0 R "
                f"/Resources << /Font << /F1 3 0 R >> >> >>\nendobj\n"
            ).encode()
        )
        flujo = _contenido_pagina(contenido_lineas)
        objetos.append(
            f"{id_contenido} 0 obj\n<< /Length {len(flujo)} >>\nstream\n".encode()
            + flujo
            + b"\nendstream\nendobj\n"
        )

    # Desplazamientos ABSOLUTOS: arrancan después de la cabecera, no en 0.
    desplazamientos: list[int] = []
    posicion = len(_CABECERA)
    for objeto in objetos:
        desplazamientos.append(posicion)
        posicion += len(objeto)

    cuerpo = b"".join(objetos)
    inicio_xref = len(_CABECERA) + len(cuerpo)

    total = len(objetos) + 1  # +1 por la entrada libre del objeto 0
    filas = ["xref", f"0 {total}", "0000000000 65535 f "]
    filas.extend(f"{d:010d} 00000 n " for d in desplazamientos)
    tabla_xref = ("\n".join(filas) + "\n").encode()

    cola = (
        f"trailer\n<< /Size {total} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n"
    ).encode()

    return _CABECERA + cuerpo + tabla_xref + cola
