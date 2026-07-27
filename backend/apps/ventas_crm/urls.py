from django.urls import path
from apps.ventas_crm.views.prospecto_views import ProspectoListCreateView, ProspectoDetailView
from apps.ventas_crm.views.asignacion_views import AsignacionView
from apps.ventas_crm.views.pipeline_views import PipelineView
from apps.ventas_crm.views.conversion_views import ConversionView
from apps.ventas_crm.views.entrada_directa_views import EntradaDirectaView
from apps.ventas_crm.views.plan_views import PlanListView
from apps.ventas_crm.views.demo_views import DemoSesionView, DemoInteraccionView
from apps.ventas_crm.views.notificacion_views import NotificacionVentasListView

urlpatterns = [
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
