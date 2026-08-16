from django.urls import path

from apps.accidentes.views.informes_views import (
    CasosView,
    CierresView,
    EvidenciaFotosView,
    NotasCampoView,
)

from apps.accidentes.views.accidente_views import (
    AccidenteDetailView,
    AccidenteListCreateView,
    GeocodificacionInversaView,
)
from apps.accidentes.views.accion_views import (
    ConfirmarReporteView,
    DescartarCasoView,
    DeshacerDescarteView,
    DeshacerFusionView,
    FusionarReportesView,
)
from apps.accidentes.views.evidencia_views import (
    EvidenciaListView,
    RegistrarNotaCampoView,
    SincronizarEvidenciaView,
    SubirEvidenciaFotoView,
)
from apps.accidentes.views.enriquecimiento_views import (
    CatalogoElementosFisicosView,
    CatalogoEstadosClimasView,
    CatalogoEstadosConductorView,
    CatalogoPeriodosDiasView,
    EnriquecimientoAccidenteView,
    EnriquecimientoClimaView,
    EnriquecimientoConductorDetailView,
    EnriquecimientoConductoresView,
    EnriquecimientoElementoFisicoDetailView,
    EnriquecimientoElementosFisicosView,
    EnriquecimientoImplicadoDetailView,
    EnriquecimientoImplicadosView,
)
from apps.accidentes.views.catalogo_registro_views import (
    ReferenciaEstacionListView,
    TipoReportadoListView,
    UnidadesEmergenciaCatalogoView,
)
from apps.accidentes.views.ubicacion_catalogo_views import (
    CalleListView,
    CiudadListView,
    CondadoListView,
    EstadoListView,
    PaisListView,
)

urlpatterns = [
    # ── Informes tácticos simples ───────────────────────────────────────────
    path("informes/emergencias/casos", CasosView.as_view(),
         name="informes-emergencias-casos"),
    path("informes/emergencias/evidencia-fotos", EvidenciaFotosView.as_view(),
         name="informes-emergencias-evidencia-fotos"),
    path("informes/emergencias/notas-campo", NotasCampoView.as_view(),
         name="informes-emergencias-notas-campo"),
    path("informes/emergencias/cierres", CierresView.as_view(),
         name="informes-emergencias-cierres"),

    path("catalogos/periodos-dias", CatalogoPeriodosDiasView.as_view()),
    path("catalogos/estados-climas", CatalogoEstadosClimasView.as_view()),
    path("catalogos/elementos-fisicos", CatalogoElementosFisicosView.as_view()),
    path("catalogos/estados-conductor", CatalogoEstadosConductorView.as_view()),
    path("accidentes/paises", PaisListView.as_view()),
    path("accidentes/estados", EstadoListView.as_view()),
    path("accidentes/condados", CondadoListView.as_view()),
    path("accidentes/ciudades", CiudadListView.as_view()),
    path("accidentes/calles", CalleListView.as_view()),
    path("accidentes/tipos-reportado", TipoReportadoListView.as_view()),
    path("accidentes/referencias-estacion", ReferenciaEstacionListView.as_view()),
    path("accidentes/unidades-emergencia", UnidadesEmergenciaCatalogoView.as_view()),
    path("accidentes/geocodificacion-inversa", GeocodificacionInversaView.as_view()),
    path("accidentes", AccidenteListCreateView.as_view()),
    path("accidentes/<str:idaccidente>", AccidenteDetailView.as_view()),
    path("accidentes/<str:idaccidente>/confirmar-reporte", ConfirmarReporteView.as_view()),
    path("accidentes/<str:idaccidente>/descartar", DescartarCasoView.as_view()),
    path(
        "accidentes/<str:idaccidente>/deshacer-descarte",
        DeshacerDescarteView.as_view(),
    ),
    path("accidentes/<str:idaccidente>/fusionar", FusionarReportesView.as_view()),
    path(
        "accidentes/<str:idaccidente>/deshacer-fusion",
        DeshacerFusionView.as_view(),
    ),
    path("accidentes/<str:idaccidente>/evidencias", EvidenciaListView.as_view()),
    path("accidentes/<str:idaccidente>/evidencias/fotos", SubirEvidenciaFotoView.as_view()),
    path("accidentes/<str:idaccidente>/evidencias/notas", RegistrarNotaCampoView.as_view()),
    path(
        "accidentes/<str:idaccidente>/evidencias/sincronizar",
        SincronizarEvidenciaView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento",
        EnriquecimientoAccidenteView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/clima",
        EnriquecimientoClimaView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/elementos-fisicos",
        EnriquecimientoElementosFisicosView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/elementos-fisicos/<int:idelementosfisicosaccidente>",
        EnriquecimientoElementoFisicoDetailView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/conductores",
        EnriquecimientoConductoresView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/conductores/<int:idconductoraccidente>",
        EnriquecimientoConductorDetailView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/implicados",
        EnriquecimientoImplicadosView.as_view(),
    ),
    path(
        "accidentes/<str:idaccidente>/enriquecimiento/implicados/<int:idimplicado>",
        EnriquecimientoImplicadoDetailView.as_view(),
    ),
]
