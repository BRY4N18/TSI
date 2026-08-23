"""Rutas de Partners y API (CU-O48 a CU-O55)."""

from django.urls import path

from apps.partners.views.contrato_views import ContratoIntegracionView
from apps.partners.views.informes_views import (
    CatalogosAccesoView,
    CatalogosContratoView,
    AlcanceDatosView,
    CambiosAccesoView,
    CredencialesView as InformesCredencialesView,
    # Se importa con alias porque `partner_views` exporta otra `PartnersView`:
    # sin alias, la importación posterior sustituía a esta en silencio y la ruta
    # de informes acababa sirviendo el listado operativo.
    PartnersView as InformesPartnersView,
    VersionesContratoView,
)
from apps.partners.views.datos_views import ConsultarAccidentesView
from apps.partners.views.metricas_views import (
    ConsolaLogsView,
    MetricasPartnerView,
    ReporteConsumoView,
)
from apps.partners.views.credencial_views import CredencialesView
from apps.partners.views.estado_acceso_views import ColaAccesoView, EstadoAccesoView
from apps.partners.views.facturacion_views import ExcepcionesFacturacionView
from apps.partners.views.revocacion_views import RevocarCredencialView
from apps.partners.views.suspension_views import (
    ReactivarPartnerView,
    SuspenderPartnerView,
)
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
    # ── Informes tácticos simples ───────────────────────────────────────────
    # Antes que las rutas operativas: Django resuelve por orden de declaración.
    path(
        # Catálogos de los desplegables. Uno por familia de listados: los tres
        # de acceso comparten el filtro «Partner»; los dos de contrato comparten
        # «Servicio» y «Cuenta». Cada uno hereda el permiso de su familia.
        "informes/partners-api/partners/catalogos",
        CatalogosAccesoView.as_view(),
        name="informes-partners-catalogos-acceso",
    ),
    path(
        "informes/partners-api/credenciales/catalogos",
        CatalogosAccesoView.as_view(),
        name="informes-partners-credenciales-catalogos",
    ),
    path(
        "informes/partners-api/cambios-acceso/catalogos",
        CatalogosAccesoView.as_view(),
        name="informes-partners-cambios-acceso-catalogos",
    ),
    path(
        "informes/partners-api/versiones-contrato/catalogos",
        CatalogosContratoView.as_view(),
        name="informes-partners-versiones-catalogos",
    ),
    path(
        "informes/partners-api/alcance-datos/catalogos",
        CatalogosContratoView.as_view(),
        name="informes-partners-alcance-catalogos",
    ),
    path(
        "informes/partners-api/partners",
        InformesPartnersView.as_view(),
        name="informes-partners",
    ),
    path(
        "informes/partners-api/credenciales",
        InformesCredencialesView.as_view(),
        name="informes-partners-credenciales",
    ),
    path(
        "informes/partners-api/cambios-acceso",
        CambiosAccesoView.as_view(),
        name="informes-partners-cambios-acceso",
    ),
    path(
        "informes/partners-api/versiones-contrato",
        VersionesContratoView.as_view(),
        name="informes-partners-versiones-contrato",
    ),
    path(
        "informes/partners-api/alcance-datos",
        AlcanceDatosView.as_view(),
        name="informes-partners-alcance-datos",
    ),
    # --- CU-O48: registro y cupo ---
    path("partners", PartnersView.as_view(), name="partners"),
    # ANTES del patron numerico: `me` no es un `<int:idpartner>`, pero dejar
    # esta ruta despues invitaria a un 404 confuso si algun dia el converter
    # cambia. El orden explicito documenta la intencion.
    path("partners/me", MiPartnerView.as_view(), name="mi-partner"),
    path(
        "partners/cola-acceso",
        ColaAccesoView.as_view(),
        name="partners-cola-acceso",
    ),
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
    # --- CU-O51: API de datos que consume el partner (#08) ---
    #
    # Grupo SEPARADO del resto a proposito: es la unica superficie que se
    # autentica con credencial de maquina en vez de JWT humano, y el prefijo
    # `/datos/` es lo que el middleware de registro usa para saber que medir.
    path(
        "datos/accidentes",
        ConsultarAccidentesView.as_view(),
        name="datos-accidentes",
    ),
    # --- CU-O52: lectura del consumo (pantallas, JWT humano) ---
    path(
        "partners/<int:idpartner>/metricas",
        MetricasPartnerView.as_view(),
        name="partner-metricas",
    ),
    # --- CU-O55: gestion de acceso (#09) ---
    #
    # `cola-acceso` se declara ARRIBA, junto a `me` y `clientes-elegibles`:
    # tiene que resolverse antes que `<int:idpartner>` o una ruta literal
    # quedaria a merced del converter numerico.
    path(
        "credenciales/<int:idcredencial>/revocar",
        RevocarCredencialView.as_view(),
        name="credencial-revocar",
    ),
    path(
        "partners/<int:idpartner>/suspender",
        SuspenderPartnerView.as_view(),
        name="partner-suspender",
    ),
    path(
        "partners/<int:idpartner>/reactivar",
        ReactivarPartnerView.as_view(),
        name="partner-reactivar",
    ),
    path(
        "partners/<int:idpartner>/estado-acceso",
        EstadoAccesoView.as_view(),
        name="partner-estado-acceso",
    ),
    path("logs-api", ConsolaLogsView.as_view(), name="consola-logs-api"),
    path("reportes-consumo", ReporteConsumoView.as_view(), name="reportes-consumo"),
    # --- CU-O54: excepciones de facturacion (BE-DELTA-04/05, abierto por el FE) ---
    path(
        "facturacion/excepciones",
        ExcepcionesFacturacionView.as_view(),
        name="facturacion-excepciones",
    ),
]
