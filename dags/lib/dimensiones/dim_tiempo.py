"""`dim_tiempo`: una fila por día. **Se genera, no se extrae.**

Ningún origen tiene una tabla de calendario, y no hace falta: el calendario es
conocido. Generarlo tiene además una propiedad que extraerlo no tendría — **no
faltan días**. Una dimensión de tiempo derivada de los hechos solo contendría los
días con actividad, y un informe que agrupe por mes mostraría 28 días en un mes
con dos festivos sin actividad, sin que nadie note la diferencia.

La franja horaria **no vive aquí**: depende de la hora del suceso, no de la
fecha, así que es atributo del hecho.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

NOMBRES_MES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

NOMBRES_DIA = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


def fila_de_dia(dia: date, ahora: datetime) -> dict[str, Any]:
    """Una fila de calendario. `dia_semana` es 1 = lunes."""
    return {
        "fecha": dia.isoformat(),
        "anio": dia.year,
        "trimestre": (dia.month - 1) // 3 + 1,
        "mes": dia.month,
        "nombre_mes": NOMBRES_MES[dia.month - 1],
        "semana_iso": dia.isocalendar().week,
        "dia_del_mes": dia.day,
        "dia_semana": dia.isoweekday(),
        "nombre_dia": NOMBRES_DIA[dia.weekday()],
        "es_fin_de_semana": 1 if dia.isoweekday() >= 6 else 0,
        "version": ahora.strftime("%Y-%m-%d %H:%M:%S"),
    }


def generar(desde: date, hasta: date, ahora: datetime) -> list[dict[str, Any]]:
    """Calendario de `desde` a `hasta`, ambos incluidos. **Sin días ausentes.**"""
    if hasta < desde:
        raise ValueError(f"rango invertido: {desde} > {hasta}")
    dias = (hasta - desde).days + 1
    return [fila_de_dia(desde + timedelta(days=i), ahora) for i in range(dias)]
