from django.urls import path
from apps.ventas_crm.views.prospecto_views import ProspectoListCreateView, ProspectoDetailView
from apps.ventas_crm.views.asignacion_views import AsignacionView
from apps.ventas_crm.views.pipeline_views import PipelineView
from apps.ventas_crm.views.conversion_views import ConversionView
from apps.ventas_crm.views.entrada_directa_views import EntradaDirectaView
from apps.ventas_crm.views.plan_views import PlanListView
from apps.ventas_crm.views.demo_views import DemoSesionView, DemoInteraccionView
from apps.ventas_crm.views.notificacion_views import NotificacionVentasListView
from apps.ventas_crm.views.informes_cartera_views import ProspectosView
from apps.ventas_crm.views.informes_asignacion_views import ReasignacionesView
from apps.ventas_crm.views.informes_nutricion_views import (
    DemosActivasView,
    NotificacionesEnviadasView,
)

urlpatterns = [
    # ── Informes tácticos simples ───────────────────────────────────────────
    # Antes que las rutas operativas de `ventas-crm/...`: Django resuelve por
    # orden de declaración y el prefijo vecino ya tiene rutas paramétricas.
    path(
        "informes/ventas-crm/prospectos",
        ProspectosView.as_view(),
        name="informes-ventas-prospectos",
    ),
    path(
        "informes/ventas-crm/reasignaciones",
        ReasignacionesView.as_view(),
        name="informes-ventas-reasignaciones",
    ),
    path(
        "informes/ventas-crm/demos-activas",
        DemosActivasView.as_view(),
        name="informes-ventas-demos-activas",
    ),
    path(
        "informes/ventas-crm/notificaciones-enviadas",
        NotificacionesEnviadasView.as_view(),
        name="informes-ventas-notificaciones-enviadas",
    ),
    path("ventas-crm/planes", PlanListView.as_view()),
    path("ventas-crm/prospectos", ProspectoListCreateView.as_view()),
    path("ventas-crm/prospectos/<int:idprospecto>", ProspectoDetailView.as_view()),
    path("ventas-crm/prospectos/<int:idprospecto>/asignacion", AsignacionView.as_view()),
    path("ventas-crm/prospectos/<int:idprospecto>/pipeline", PipelineView.as_view()),
    path("ventas-crm/prospectos/<int:idprospecto>/conversion", ConversionView.as_view()),
    path("ventas-crm/clientes/entrada-directa", EntradaDirectaView.as_view()),
    path("ventas-crm/demo/sesiones", DemoSesionView.as_view()),
    path("ventas-crm/demo/interacciones", DemoInteraccionView.as_view()),
    path("ventas-crm/notificaciones", NotificacionVentasListView.as_view()),
]
