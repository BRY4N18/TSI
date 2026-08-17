from django.urls import path

from apps.informes_estrategicos.views.oe3_views import Oe3View
from apps.informes_estrategicos.views.oe6_views import Oe6View

urlpatterns = [
    path(
        "informes-estrategicos/oe6/<str:informe>",
        Oe6View.as_view(),
        name="informes-estrategicos-oe6",
    ),
    path(
        "informes-estrategicos/oe3/<str:informe>",
        Oe3View.as_view(),
        name="informes-estrategicos-oe3",
    ),
]
