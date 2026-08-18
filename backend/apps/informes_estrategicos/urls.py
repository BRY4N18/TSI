from django.urls import path

from apps.informes_estrategicos.views.oe1_views import Oe1View
from apps.informes_estrategicos.views.oe5_views import Oe5View
from apps.informes_estrategicos.views.oe2_views import Oe2View
from apps.informes_estrategicos.views.oe3_views import Oe3View
from apps.informes_estrategicos.views.oe4_views import Oe4View
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
    path(
        "informes-estrategicos/oe4/<str:informe>",
        Oe4View.as_view(),
        name="informes-estrategicos-oe4",
    ),
    path(
        "informes-estrategicos/oe2/<str:informe>",
        Oe2View.as_view(),
        name="informes-estrategicos-oe2",
    ),
    path(
        "informes-estrategicos/oe1/<str:informe>",
        Oe1View.as_view(),
        name="informes-estrategicos-oe1",
    ),
    path(
        "informes-estrategicos/oe5/<str:informe>",
        Oe5View.as_view(),
        name="informes-estrategicos-oe5",
    ),
]
