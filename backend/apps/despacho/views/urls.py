from django.urls import path

from apps.despacho.views.asignacion_views import (
    AsignarManualView,
    CoordinarDespachoView,
    EscalarZonaView,
    UnidadesCandidatasView,
)
from apps.despacho.views.disponibilidad_views import (
    MiDisponibilidadView,
    UnidadDisponibilidadView,
    UnidadesEmergenciaListView,
    UnidadHistorialEstadoView,
)
from apps.despacho.views.mi_despacho_views import (
    MiDespachoConfirmarView,
    MiDespachoDetalleView,
    MiDespachoPendientesView,
    MiDespachoRechazarView,
)
from apps.despacho.views.monitoreo_views import (
    MonitoreoDespachoStreamView,
    MonitoreoDespachoView,
)
from apps.despacho.views.parametros_views import ParametrosDespachoView

urlpatterns = [
    path("mi-unidad-emergencia/disponibilidad", MiDisponibilidadView.as_view()),
    path("unidades-emergencia", UnidadesEmergenciaListView.as_view()),
    path(
        "unidades-emergencia/<int:idunidademergencia>/disponibilidad",
        UnidadDisponibilidadView.as_view(),
    ),
    path(
        "unidades-emergencia/<int:idunidademergencia>/historial-estado",
        UnidadHistorialEstadoView.as_view(),
    ),
    path("mi-despacho/pendientes", MiDespachoPendientesView.as_view()),
    path("mi-despacho/<int:idnotificaciondespacho>", MiDespachoDetalleView.as_view()),
    path(
        "mi-despacho/<int:idnotificaciondespacho>/confirmar",
        MiDespachoConfirmarView.as_view(),
    ),
    path(
        "mi-despacho/<int:idnotificaciondespacho>/rechazar",
        MiDespachoRechazarView.as_view(),
    ),
    path("accidentes/<str:idaccidente>/despacho", MonitoreoDespachoView.as_view()),
    path(
        "accidentes/<str:idaccidente>/despacho/stream",
        MonitoreoDespachoStreamView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/despacho/unidades-candidatas",
        UnidadesCandidatasView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/despacho/asignar-manual",
        AsignarManualView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/despacho/escalar-zona",
        EscalarZonaView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/despacho/coordinar",
        CoordinarDespachoView.as_view(),
    ),
    path("despacho/parametros", ParametrosDespachoView.as_view()),
]
