"""PDF mínimo del expediente (RF-SEG-006)."""

from __future__ import annotations

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
        acc = data["accidente"]
        lines = [
            f"Expediente TSI — {idaccidente}",
            f"Estado: {data['estado_actual']}",
            f"Descripcion: {acc.get('descripcion', '')}",
            f"Duracion min: {acc.get('duracionminutos', '')}",
            f"Despachos: {len(data['despachos'])}",
            f"Notas: {len(data['notas'])}",
            f"Evidencias: {len(data['evidencias'])}",
        ]
        text = "\n".join(lines)
        return _minimal_pdf(text)


def _minimal_pdf(text: str) -> bytes:
    """Genera PDF 1.4 mínimo con una página de texto."""
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 50 750 Td ({escaped}) Tj ET"
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        (
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
        ),
        f"4 0 obj<< /Length {len(stream_bytes)} >>stream\n".encode()
        + stream_bytes
        + b"\nendstream endobj\n",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]
    body = b"".join(objects)
    xref_positions = []
    pos = 0
    for obj in objects:
        xref_positions.append(pos)
        pos += len(obj)
    xref = ["xref", "0 6", "0000000000 65535 f "]
    for p in xref_positions:
        xref.append(f"{p:010d} 00000 n ")
    trailer = (
        "trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        f"{sum(len(o) for o in objects)}\n%%EOF"
    )
    return b"%PDF-1.4\n" + body + "\n".join(xref).encode() + b"\n" + trailer.encode()
