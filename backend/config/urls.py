"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

from core.seguridad.salud_views import SaludView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Sonda de salud (PG-RES-004). Fuera de los `include` de modulo: no
    # pertenece a ningun dominio y debe responder aunque uno de ellos falle.
    path("api/v1/salud", SaludView.as_view(), name="salud"),
    path("api/v1/", include("apps.cuentas_clientes.views.urls")),
    path("api/v1/", include("apps.accidentes.views.urls")),
    path("api/v1/", include("apps.despacho.views.urls")),
    path("api/v1/", include("apps.seguimiento.views.urls")),
    path("api/v1/", include("apps.soporte_cliente.urls")),
    path("api/v1/", include("apps.red_operativa.views.urls")),
    path("api/v1/", include("apps.ventas_crm.urls")),
    path("api/v1/", include("apps.suscripciones.urls")),
    path("api/v1/", include("apps.informes_tacticos.urls")),
    path("api/v1/", include("apps.informes_estrategicos.urls")),
    path("api/v1/", include("apps.partners.views.urls")),
]
