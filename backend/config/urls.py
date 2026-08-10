"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.cuentas_clientes.views.urls")),
    path("api/v1/", include("apps.accidentes.views.urls")),
    path("api/v1/", include("apps.despacho.views.urls")),
    path("api/v1/", include("apps.seguimiento.views.urls")),
    path("api/v1/", include("apps.soporte_cliente.urls")),
    path("api/v1/", include("apps.red_operativa.views.urls")),
    path("api/v1/", include("apps.ventas_crm.urls")),
    path("api/v1/", include("apps.suscripciones.urls")),
    path("api/v1/", include("apps.informes_tacticos.urls")),
    path("api/v1/", include("apps.partners.views.urls")),
]
