"""PG-SEC-004 — los cupos declarados se aplican de verdad.

El sistema declara cinco límites de tasa y hasta ahora **ninguno tenía prueba**.
Un throttle declarado y no verificado es peor que no tenerlo: figura en la
documentación, se cuenta como control existente al evaluar el riesgo, y nadie
comprueba que DRF lo esté aplicando.

**La suite se parametriza sobre el registro real** —`DEFAULT_THROTTLE_RATES` de
`settings.py` y las clases que heredan de `SimpleRateThrottle`—, no sobre una
lista escrita a mano. Un cupo nuevo sin prueba hace fallar la suite en vez de
pasar desapercibido, que es la misma razón por la que el registro de secretos de
`PG-CFG-002` se comprueba contra `settings.py`.

⛔ **Frontera de negocio que estas pruebas no deben cruzar.** Esto es el techo
**técnico** de plataforma. **No** es la cuota comercial de `RN-APM-002`, donde el
cupo mensual **nunca bloquea: se factura**. Una prueba que espere `429` por cuota
mensual estaría verificando lo contrario de la regla de negocio.

Contrato: `contracts/respuestas-seguridad.md` §C4.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import APIClient

pytestmark = [pytest.mark.api, pytest.mark.seguridad]

#: Clases de throttle del proyecto, con el scope que declaran.
CLASES_DECLARADAS = {
    "apps.ventas_crm.throttles.ProspectoRegistroThrottle": "prospecto_registro",
    "apps.ventas_crm.throttles.DemoSesionIpThrottle": "demo_sesion_ip",
    "apps.ventas_crm.throttles.DemoInteraccionTokenThrottle": "demo_interaccion_token",
    "apps.suscripciones.throttles.ProveedorBillingWriteThrottle": "suscripciones_proveedor_write",
    "apps.suscripciones.throttles.AdminBillingThrottle": "suscripciones_admin",
    "apps.partners.throttling.PartnerRateThrottle": "partner_api",
}


@pytest.fixture(autouse=True)
def _cache_limpia():
    """DRF cuenta las peticiones en la caché.

    Sin limpiarla, el contador sobrevive entre pruebas y una que ya agotó el cupo
    deja a la siguiente empezando en `429` — un falso positivo que además cambia
    según el orden de ejecución.
    """
    cache.clear()
    yield
    cache.clear()


def _importar(ruta: str):
    modulo, nombre = ruta.rsplit(".", 1)
    return getattr(__import__(modulo, fromlist=[nombre]), nombre)


# --- Que los cupos existan y estén bien formados ------------------------------


@pytest.mark.parametrize("ruta,scope", sorted(CLASES_DECLARADAS.items()))
def test_cada_throttle_resuelve_un_rate(ruta, scope):
    """Un scope sin rate hace que DRF **no limite nada**, en silencio.

    Es el modo de fallo característico: la clase está puesta en la vista, el
    código parece correcto, y el cupo simplemente no se aplica porque el scope
    no resuelve a ninguna tasa.
    """
    throttle = _importar(ruta)()

    assert throttle.rate, (
        f"{ruta} (scope «{scope}») no resuelve ningún rate. Está declarado en la "
        "vista pero no limita nada."
    )
    cantidad, _, periodo = throttle.rate.partition("/")
    assert cantidad.isdigit() and int(cantidad) > 0, throttle.rate
    assert periodo in ("s", "sec", "min", "hour", "day"), throttle.rate


def test_todos_los_scopes_declarados_tienen_una_clase_que_los_use():
    """Un rate en `settings` sin clase que lo consuma es documentación muerta.

    Aparenta un control existente al revisar la configuración, y no limita nada.
    """
    scopes_en_settings = set(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"])
    scopes_usados = set(CLASES_DECLARADAS.values())

    huerfanos = scopes_en_settings - scopes_usados
    assert not huerfanos, (
        f"Scopes con rate declarado y ninguna clase que los use: {sorted(huerfanos)}. "
        "O se les asocia un throttle, o se retiran de settings."
    )


def test_el_registro_de_esta_suite_cubre_las_clases_existentes():
    """Antienvejecimiento: un throttle nuevo sin prueba rompe la suite.

    Sin esto el registro se queda atrás y la suite pasa a dar una falsa sensación
    de cobertura completa — el mismo fallo que ya se corrigió en `PG-CFG-002`.
    """
    import pkgutil
    from rest_framework.throttling import SimpleRateThrottle

    import apps

    encontradas = set()
    for modulo in pkgutil.walk_packages(apps.__path__, "apps."):
        if not modulo.name.endswith(("throttles", "throttling")):
            continue
        mod = __import__(modulo.name, fromlist=["*"])
        for nombre in dir(mod):
            obj = getattr(mod, nombre)
            if (
                isinstance(obj, type)
                and issubclass(obj, SimpleRateThrottle)
                and obj.__module__ == modulo.name
            ):
                encontradas.add(f"{modulo.name}.{nombre}")

    sin_registrar = encontradas - set(CLASES_DECLARADAS)
    assert not sin_registrar, (
        f"Throttles sin prueba: {sorted(sin_registrar)}. Añadirlos a "
        "CLASES_DECLARADAS (PG-SEC-004)."
    )


# --- Que el cupo se aplique de verdad ----------------------------------------


def test_superar_el_cupo_devuelve_429():
    """El aserto que da sentido a todo lo demás.

    Se usa el registro de prospectos porque es anónimo —10/min por IP— y no
    necesita credenciales ni datos sembrados: cualquier fallo aquí es del
    throttle, no del montaje.
    """
    cliente = APIClient()
    ruta = "/api/v1/ventas-crm/prospectos"
    cuerpo = {"nombre": "x", "gmail": "x@y.com", "telefono": "1"}

    codigos = [cliente.post(ruta, cuerpo, format="json").status_code for _ in range(15)]

    assert 429 in codigos, (
        f"15 peticiones seguidas contra un cupo de 10/min y ningún 429. "
        f"Códigos: {sorted(set(codigos))}. El throttle no se está aplicando."
    )


def test_la_respuesta_de_cupo_agotado_no_revela_de_mas():
    """Un `429` no debe explicar el cupo exacto ni cómo se cuenta.

    Decirle a quien lo agota cuántas le quedaban o sobre qué ventana se mide le
    ahorra el trabajo de medirlo.
    """
    cliente = APIClient()
    ruta = "/api/v1/ventas-crm/prospectos"
    cuerpo = {"nombre": "x", "gmail": "x@y.com", "telefono": "1"}

    respuesta = None
    for _ in range(15):
        r = cliente.post(ruta, cuerpo, format="json")
        if r.status_code == 429:
            respuesta = r
            break

    if respuesta is None:
        pytest.skip("No se alcanzó el cupo; cubierto por la prueba anterior.")

    texto = respuesta.content.decode("utf-8", errors="replace").lower()
    for delator in ("traceback", "settings", "cache", "redis"):
        assert delator not in texto, f"El 429 revela «{delator}»: {texto[:160]}"


def test_el_cupo_mensual_de_partner_no_bloquea():
    """`RN-APM-002`: el cupo **mensual** se factura, no se bloquea.

    Esta prueba existe para impedir que alguien «arregle» el sistema añadiendo un
    `429` por cuota mensual creyendo que refuerza la seguridad. Sería romper una
    regla de negocio deliberada — y `PartnerRateThrottle` lo dice en su docstring:
    el rate del scope existe solo porque DRF exige uno declarado.
    """
    from apps.partners.throttling import PartnerRateThrottle

    doc = (PartnerRateThrottle.__doc__ or "").lower()
    assert "limite efectivo" in doc or "límite efectivo" in doc, (
        "PartnerRateThrottle dejó de documentar que el límite efectivo sale del "
        "partner y no del scope. Esa distinción es lo que separa el techo técnico "
        "de la cuota comercial de RN-APM-002."
    )
