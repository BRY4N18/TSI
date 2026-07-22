from django.urls import path

from apps.seguimiento.views.cierre_views import (
    CancelarCasoView,
    CerrarCasoView,
    ForzarRetiroView,
)
from apps.seguimiento.views.cliente_expediente_views import (
    ClienteExpedienteDetalleView,
    ClienteExpedientePdfView,
    ClienteExpedientesView,
)
from apps.seguimiento.views.historial_views import (
    ExpedienteOperadorView,
    HistorialEmergenciasView,
)
from apps.seguimiento.views.mapa_views import (
    MapaSeguimientoView,
    SeguimientoAccidenteView,
    SeguimientoStreamView,
)
from apps.seguimiento.views.mi_seguimiento_views import (
    AbortarMisionView,
    MiSeguimientoActualView,
    RegistrarLlegadaView,
    RegistrarPosicionGpsView,
)
from apps.seguimiento.views.ruta_views import RutaSeguimientoView

urlpatterns = [
    path("seguimiento/mapa", MapaSeguimientoView.as_view()),
    path("seguimiento/ruta", RutaSeguimientoView.as_view()),
    path("seguimiento/stream", SeguimientoStreamView.as_view()),
    path("accidentes/<str:idaccidente>/seguimiento", SeguimientoAccidenteView.as_view()),
    path("mi-seguimiento/actual", MiSeguimientoActualView.as_view()),
    path("mi-seguimiento/posicion", RegistrarPosicionGpsView.as_view()),
    path(
        "mi-seguimiento/despachos/<int:iddespacho>/llegada",
        RegistrarLlegadaView.as_view(),
    ),
    path(
        "mi-seguimiento/despachos/<int:iddespacho>/abortar",
        AbortarMisionView.as_view(),
    ),
    path("accidentes/<str:idaccidente>/cerrar", CerrarCasoView.as_view()),
    path("accidentes/<str:idaccidente>/cancelar", CancelarCasoView.as_view()),
    path("despachos/<int:iddespacho>/forzar-retiro", ForzarRetiroView.as_view()),
    path("emergencias/historial", HistorialEmergenciasView.as_view()),
    path(
        "emergencias/historial/<str:idaccidente>/expediente",
        ExpedienteOperadorView.as_view(),
    ),
    path("cliente/expedientes", ClienteExpedientesView.as_view()),
    path(
        "cliente/expedientes/<str:idaccidente>",
        ClienteExpedienteDetalleView.as_view(),
    ),
    path(
        "cliente/expedientes/<str:idaccidente>/pdf",
        ClienteExpedientePdfView.as_view(),
    ),
]
