from apps.accidentes.tests.conftest import seed_accidente  # noqa: F401

# Los informes tácticos de Emergencias comparten siembra entre `accidentes` y
# `seguimiento` —el despacho apunta a un caso—, así que se importan de un solo
# sitio. Duplicar las constantes de un caso sembrado sería la forma más rápida
# de que las dos copias dejaran de coincidir.
from apps.accidentes.tests.informes_fixtures import *  # noqa: F401,F403,E402
