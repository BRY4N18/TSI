from django.urls import path

from apps.accidentes.views.accidente_views import (
    AccidenteDetailView,
    AccidenteListCreateView,
    GeocodificacionInversaView,
)
from apps.accidentes.views.accion_views import (
    ConfirmarReporteView,
    DescartarCasoView,
    EscalarSeveridadView,
    FusionarReportesView,
)
from apps.accidentes.views.evidencia_views import (
    EvidenciaListView,
    RegistrarNotaCampoView,
    SincronizarEvidenciaView,
    SubirEvidenciaFotoView,
)
from apps.accidentes.views.ubicacion_catalogo_views import (
    CalleListView,
    CiudadListView,
    CondadoListView,
    EstadoListView,
    PaisListView,
)

urlpatterns = [
    path("accidentes/paises", PaisListView.as_view()),
    path("accidentes/estados", EstadoListView.as_view()),
    path("accidentes/condados", CondadoListView.as_view()),
    path("accidentes/ciudades", CiudadListView.as_view()),
    path("accidentes/calles", CalleListView.as_view()),
    path("accidentes/geocodificacion-inversa", GeocodificacionInversaView.as_view()),
    path("accidentes", AccidenteListCreateView.as_view()),
    path("accidentes/<str:idaccidente>", AccidenteDetailView.as_view()),
    path("accidentes/<str:idaccidente>/confirmar-reporte", ConfirmarReporteView.as_view()),
    path("accidentes/<str:idaccidente>/descartar", DescartarCasoView.as_view()),
    path("accidentes/<str:idaccidente>/fusionar", FusionarReportesView.as_view()),
    path("accidentes/<str:idaccidente>/escalar-severidad", EscalarSeveridadView.as_view()),
    path("accidentes/<str:idaccidente>/evidencias", EvidenciaListView.as_view()),
    path("accidentes/<str:idaccidente>/evidencias/fotos", SubirEvidenciaFotoView.as_view()),
    path("accidentes/<str:idaccidente>/evidencias/notas", RegistrarNotaCampoView.as_view()),
    path(
        "accidentes/<str:idaccidente>/evidencias/sincronizar",
        SincronizarEvidenciaView.as_view(),
    ),
]
