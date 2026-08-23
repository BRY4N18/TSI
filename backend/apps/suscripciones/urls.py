"""URL routing — Suscripciones y Facturación (/api/v1/suscripciones/...)."""

from django.urls import path

from apps.suscripciones.views.cambio_plan_views import (
    AprobarCambioPlanView,
    RechazarCambioPlanView,
    SolicitudCambioPlanListCreateView,
)
from apps.suscripciones.views.factura_views import FacturaDetailView, FacturaListView
from apps.suscripciones.views.informes_cambio_plan_views import (
    SolicitudesCambioPlanView,
)
from apps.suscripciones.views.informes_facturacion_views import (
    FacturasView,
    MetodosPagoView,
)
from apps.suscripciones.views.informes_suscripcion_views import SuscripcionesView
from apps.suscripciones.views.informes_base import (
    CatalogosCatalogoView,
    CatalogosFinanzasView,
)
from apps.suscripciones.views.metodo_pago_views import MetodoPagoListCreateView
from apps.suscripciones.views.plan_views import (
    PlanDetailView,
    PlanListCreateView,
    SeveridadCatalogoView,
)
from apps.suscripciones.views.suscripcion_views import (
    AltaSuscripcionView,
    CancelarSuscripcionView,
    MiSuscripcionView,
    ReintentarCobroView,
)

urlpatterns = [
    # ── Informes tácticos simples ───────────────────────────────────────────
    # Antes que las rutas operativas: Django resuelve por orden de declaración.
    path(
        "informes/suscripciones-facturacion/suscripciones/catalogos",
        CatalogosCatalogoView.as_view(),
        name="informes-suscripciones-catalogos",
    ),
    path(
        "informes/suscripciones-facturacion/suscripciones",
        SuscripcionesView.as_view(),
        name="informes-susc-suscripciones",
    ),
    path(
        "informes/suscripciones-facturacion/facturas/catalogos",
        CatalogosFinanzasView.as_view(),
        name="informes-suscripciones-facturas-catalogos",
    ),
    path(
        "informes/suscripciones-facturacion/facturas",
        FacturasView.as_view(),
        name="informes-susc-facturas",
    ),
    path(
        "informes/suscripciones-facturacion/metodos-pago/catalogos",
        CatalogosFinanzasView.as_view(),
        name="informes-suscripciones-metodos-catalogos",
    ),
    path(
        "informes/suscripciones-facturacion/metodos-pago",
        MetodosPagoView.as_view(),
        name="informes-susc-metodos-pago",
    ),
    path(
        "informes/suscripciones-facturacion/solicitudes-cambio-plan/catalogos",
        CatalogosCatalogoView.as_view(),
        name="informes-suscripciones-solicitudes-catalogos",
    ),
    path(
        "informes/suscripciones-facturacion/solicitudes-cambio-plan",
        SolicitudesCambioPlanView.as_view(),
        name="informes-susc-solicitudes-cambio-plan",
    ),
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
    path("suscripciones/severidades", SeveridadCatalogoView.as_view()),
    path("suscripciones/planes", PlanListCreateView.as_view()),
    path("suscripciones/planes/<int:idplan>", PlanDetailView.as_view()),
    path("suscripciones/facturas", FacturaListView.as_view()),
    path("suscripciones/facturas/<str:id_factura>", FacturaDetailView.as_view()),
]
