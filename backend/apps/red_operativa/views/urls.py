"""API v1 URL routes for red_operativa (alta-unidades)."""

from django.urls import path

from apps.red_operativa.views.region_views import (
    RegionDespublicacionAutomaticaView,
    RegionRechazoDefinitivoView,
    RegionReevaluacionView,
    RegionValidacionHistorialView,
    RegionValidacionView,
)
from apps.red_operativa.views.unidad_views import (
    UnidadBajaView,
    UnidadDetailView,
    UnidadDisponibilidadView,
    UnidadImportacionLoteView,
    UnidadListCreateView,
    UnidadReactivarView,
)

urlpatterns = [
    path(
        "red-operativa/regiones/validaciones",
        RegionValidacionView.as_view(),
        name="red-operativa-region-validaciones",
    ),
    path(
        "red-operativa/regiones/<int:idregionoperativa>/validaciones",
        RegionValidacionHistorialView.as_view(),
        name="red-operativa-region-validaciones-historial",
    ),
    path(
        "red-operativa/regiones/<int:idregionoperativa>/rechazo-definitivo",
        RegionRechazoDefinitivoView.as_view(),
        name="red-operativa-region-rechazo-definitivo",
    ),
    path(
        "red-operativa/regiones/<int:idregionoperativa>/reevaluacion",
        RegionReevaluacionView.as_view(),
        name="red-operativa-region-reevaluacion",
    ),
    path(
        "red-operativa/regiones/<int:idregionoperativa>/despublicacion-automatica",
        RegionDespublicacionAutomaticaView.as_view(),
        name="red-operativa-region-despublicacion-automatica",
    ),
    path("red-operativa/unidades", UnidadListCreateView.as_view(), name="red-operativa-unidades"),
    path(
        "red-operativa/unidades/importacion-lote",
        UnidadImportacionLoteView.as_view(),
        name="red-operativa-unidades-importacion-lote",
    ),
    path(
        "red-operativa/unidades/<int:idunidademergencia>",
        UnidadDetailView.as_view(),
        name="red-operativa-unidad-detail",
    ),
    path(
        "red-operativa/unidades/<int:idunidademergencia>/baja",
        UnidadBajaView.as_view(),
        name="red-operativa-unidad-baja",
    ),
    path(
        "red-operativa/unidades/<int:idunidademergencia>/reactivar",
        UnidadReactivarView.as_view(),
        name="red-operativa-unidad-reactivar",
    ),
    path(
        "red-operativa/unidades/<int:idunidademergencia>/disponibilidad",
        UnidadDisponibilidadView.as_view(),
        name="red-operativa-unidad-disponibilidad",
    ),
]
