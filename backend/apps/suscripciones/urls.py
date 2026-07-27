"""URL routing — Suscripciones y Facturación (/api/v1/suscripciones/...)."""

from django.urls import path

from apps.suscripciones.views.cambio_plan_views import (
    AprobarCambioPlanView,
    RechazarCambioPlanView,
    SolicitudCambioPlanListCreateView,
)
from apps.suscripciones.views.factura_views import FacturaDetailView, FacturaListView
from apps.suscripciones.views.metodo_pago_views import MetodoPagoListCreateView
from apps.suscripciones.views.plan_views import PlanDetailView, PlanListCreateView
from apps.suscripciones.views.suscripcion_views import (
    AltaSuscripcionView,
    CancelarSuscripcionView,
    MiSuscripcionView,
    ReintentarCobroView,
)

urlpatterns = [
    path("suscripciones", AltaSuscripcionView.as_view()),
    path("suscripciones/mia", MiSuscripcionView.as_view()),
    path("suscripciones/mia/cancelar", CancelarSuscripcionView.as_view()),
    path("suscripciones/mia/reintentar-cobro", ReintentarCobroView.as_view()),
    path("suscripciones/metodos-pago", MetodoPagoListCreateView.as_view()),
    path("suscripciones/solicitudes-cambio-plan", SolicitudCambioPlanListCreateView.as_view()),
    path(
        "suscripciones/solicitudes-cambio-plan/<int:idsolicitud>/aprobar",
        AprobarCambioPlanView.as_view(),
    ),
    path(
        "suscripciones/solicitudes-cambio-plan/<int:idsolicitud>/rechazar",
        RechazarCambioPlanView.as_view(),
    ),
    path("suscripciones/planes", PlanListCreateView.as_view()),
    path("suscripciones/planes/<int:idplan>", PlanDetailView.as_view()),
    path("suscripciones/facturas", FacturaListView.as_view()),
    path("suscripciones/facturas/<str:id_factura>", FacturaDetailView.as_view()),
]
