from django.urls import path

from apps.informes_tacticos.views.cuentas_compuestos_views import (
    CuentasCompuestoView,
)
from apps.informes_tacticos.views.partners_compuestos_views import (
    PartnersCompuestoView,
)
from apps.informes_tacticos.views.emergencias_compuestos_views import (
    EmergenciasCompuestoView,
)
from apps.informes_tacticos.views.red_operativa_compuestos_views import (
    RedOperativaCompuestoView,
)
from apps.informes_tacticos.views.suscripciones_compuestos_views import (
    SuscripcionesCompuestoView,
)
from apps.informes_tacticos.views.soporte_compuestos_views import (
    SoporteCompuestoView,
    SoporteCumplimientoPorPlanView,
)
from apps.informes_tacticos.views.ventas_crm_compuestos_views import (
    VentasCrmCompuestoView,
)

urlpatterns = [
    # Informes compuestos de Emergencias, sobre el modelo analítico. Una sola
    # ruta parametrizada: el conjunto publicado lo fija `PUBLICADOS` en el
    # servicio, no esta lista, para que no haya dos sitios que puedan discrepar.
    #
    # La ruta no lleva un segmento `compuestos/` porque el contrato no lo lleva:
    # para quien consume, esto es «el informe de Emergencias», y que por dentro
    # salga del modelo analítico no es asunto de la URL.
    path(
        "informes-tacticos/emergencias/<str:informe>",
        EmergenciasCompuestoView.as_view(),
        name="informes-tacticos-emergencias-compuesto",
    ),
    # Red Operativa. El nombre del informe va en la **ruta** y no en un
    # parámetro de consulta porque el permiso depende de él: la autoridad de
    # este departamento está repartida por materia, y un permiso no puede
    # depender de algo que se lee después de concederlo.
    path(
        "informes-tacticos/red-operativa/<str:informe>",
        RedOperativaCompuestoView.as_view(),
        name="informes-tacticos-red-operativa-compuesto",
    ),
    path(
        "informes-tacticos/ventas-crm/<str:informe>",
        VentasCrmCompuestoView.as_view(),
        name="informes-tacticos-ventas-crm-compuesto",
    ),
    path(
        "informes-tacticos/suscripciones/<str:informe>",
        SuscripcionesCompuestoView.as_view(),
        name="informes-tacticos-suscripciones-compuesto",
    ),
    path(
        "informes-tacticos/soporte/cumplimiento-sla/por-plan",
        SoporteCumplimientoPorPlanView.as_view(),
        name="informes-tacticos-soporte-cumplimiento-por-plan",
    ),
    path(
        "informes-tacticos/soporte/<str:informe>",
        SoporteCompuestoView.as_view(),
        name="informes-tacticos-soporte-compuesto",
    ),
    path(
        "informes-tacticos/cuentas/<str:informe>",
        CuentasCompuestoView.as_view(),
        name="informes-tacticos-cuentas-compuesto",
    ),
    path(
        "informes-tacticos/partners/<str:informe>",
        PartnersCompuestoView.as_view(),
        name="informes-tacticos-partners-compuesto",
    ),
]
