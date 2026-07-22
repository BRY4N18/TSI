from django.urls import path

from apps.soporte_cliente.views import (
    ClasificarTicketManualView,
    ComentarTicketView,
    ConfirmarCierreTicketView,
    DashboardSoporteView,
    EscalarTicketView,
    ReabrirTicketView,
    ResolverTicketView,
    SLAConfigDetalleView,
    SLAConfigView,
    TicketDetalleView,
    TicketsView,
    TomarTicketView,
)

urlpatterns = [
    path("soporte/tickets", TicketsView.as_view()),
    path("soporte/tickets/<int:id_reclamo>", TicketDetalleView.as_view()),
    path("soporte/tickets/<int:id_reclamo>/clasificar", ClasificarTicketManualView.as_view()),
    path("soporte/tickets/<int:id_reclamo>/tomar", TomarTicketView.as_view()),
    path("soporte/tickets/<int:id_reclamo>/comentarios", ComentarTicketView.as_view()),
    path("soporte/tickets/<int:id_reclamo>/escalar", EscalarTicketView.as_view()),
    path("soporte/tickets/<int:id_reclamo>/resolver", ResolverTicketView.as_view()),
    path(
        "soporte/tickets/<int:id_reclamo>/confirmar-cierre",
        ConfirmarCierreTicketView.as_view(),
    ),
    path("soporte/tickets/<int:id_reclamo>/reabrir", ReabrirTicketView.as_view()),
    path("soporte/sla-config", SLAConfigView.as_view()),
    path("soporte/sla-config/<int:idslaconfig>", SLAConfigDetalleView.as_view()),
    path("soporte/dashboard", DashboardSoporteView.as_view()),
]
