"""API v1 URL routes for red_operativa (alta-unidades)."""

from django.urls import path

from apps.red_operativa.views.informes_baja_views import BajasUnidadView
from apps.red_operativa.views.informes_flota_views import (
    CatalogosFlotaView,
    CatalogosRegionesView,
    FlotaView,
)
from apps.red_operativa.views.informes_region_views import (
    RegionesView,
    ValidacionesRegionView,
)
from apps.red_operativa.views.region_views import (
    RegionDespublicacionAutomaticaView,
    RegionDetalleView,
    RegionListView,
    RegionRechazoDefinitivoView,
    RegionReevaluacionView,
    RegionValidacionHistorialView,
    RegionValidacionView,
)
from apps.red_operativa.views.unidad_views import (
    UnidadBajaView,
    UnidadDetailView,
    UnidadImportacionLoteView,
    UnidadInvitacionReenviarView,
    UnidadListCreateView,
    UnidadReactivarView,
)

urlpatterns = [
    # ── Informes tácticos simples ───────────────────────────────────────────
    # Antes que las rutas operativas: Django resuelve por orden de declaración.
    path("informes/red-operativa/flota/catalogos", CatalogosFlotaView.as_view(),
         name="informes-red-flota-catalogos"),
    path("informes/red-operativa/flota", FlotaView.as_view(), name="informes-red-flota"),
    path(
        "informes/red-operativa/bajas-unidad/catalogos", CatalogosFlotaView.as_view(),
         name="informes-red-bajas-catalogos"),
    path("informes/red-operativa/bajas-unidad",
        BajasUnidadView.as_view(),
        name="informes-red-bajas-unidad",
    ),
    path(
        "informes/red-operativa/regiones",
        RegionesView.as_view(),
        name="informes-red-regiones",
    ),
    path(
        "informes/red-operativa/validaciones-region/catalogos", CatalogosRegionesView.as_view(),
         name="informes-red-validaciones-catalogos"),
    path("informes/red-operativa/validaciones-region",
        ValidacionesRegionView.as_view(),
        name="informes-red-validaciones-region",
    ),
    path(
        "red-operativa/regiones",
        RegionListView.as_view(),
        name="red-operativa-regiones",
    ),
    path(
        "red-operativa/regiones/validaciones",
        RegionValidacionView.as_view(),
        name="red-operativa-region-validaciones",
    ),
    path(
        "red-operativa/regiones/<int:idregionoperativa>",
        RegionDetalleView.as_view(),
        name="red-operativa-region-detalle",
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
        "red-operativa/unidades/<int:idunidademergencia>/invitacion/reenviar",
        UnidadInvitacionReenviarView.as_view(),
        name="red-operativa-unidad-invitacion-reenviar",
    ),
]
