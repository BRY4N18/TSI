"""Rutas de Partners y API (CU-O48 a CU-O55)."""

from django.urls import path

from apps.partners.views.contrato_views import ContratoIntegracionView
from apps.partners.views.credencial_views import CredencialesView
from apps.partners.views.partner_views import (
    AsignarPlanAccesoView,
    ClientesElegiblesView,
    MiPartnerView,
    PartnerDetalleView,
    PartnersView,
)
from apps.partners.views.promocion_views import (
    ResolucionProduccionView,
    SolicitudProduccionView,
)

urlpatterns = [
    # --- CU-O48: registro y cupo ---
    path("partners", PartnersView.as_view(), name="partners"),
    # ANTES del patron numerico: `me` no es un `<int:idpartner>`, pero dejar
    # esta ruta despues invitaria a un 404 confuso si algun dia el converter
    # cambia. El orden explicito documenta la intencion.
    path("partners/me", MiPartnerView.as_view(), name="mi-partner"),
    path(
        "partners/clientes-elegibles",
        ClientesElegiblesView.as_view(),
        name="partners-clientes-elegibles",
    ),
    path("partners/<int:idpartner>", PartnerDetalleView.as_view(), name="partner-detalle"),
    path(
        "partners/<int:idpartner>/plan-acceso",
        AsignarPlanAccesoView.as_view(),
        name="partner-plan-acceso",
    ),
    # --- CU-O49: credenciales ---
    path(
        "partners/<int:idpartner>/credenciales",
        CredencialesView.as_view(),
        name="partner-credenciales",
    ),
    path(
        "partners/<int:idpartner>/solicitud-produccion",
        SolicitudProduccionView.as_view(),
        name="partner-solicitud-produccion",
    ),
    path(
        "partners/<int:idpartner>/solicitud-produccion/resolucion",
        ResolucionProduccionView.as_view(),
        name="partner-resolucion-produccion",
    ),
    # --- CU-O50: contrato de integracion versionado ---
    path(
        "contrato-integracion",
        ContratoIntegracionView.as_view(),
        name="contrato-integracion",
    ),
]
