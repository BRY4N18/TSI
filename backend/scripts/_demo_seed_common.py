"""
Constantes compartidas por todos los seeds de datos demo.

Existe porque las credenciales demo estaban duplicadas con dos convenciones
distintas: `database/seed_usuarios.py` sembraba "Demo1234!" y los scripts de
`backend/scripts/` sembraban "password123". Segun que seed hubiera corrido
ultimo, la misma cuenta pedia una u otra contrasena, y `e2e/fixtures/auth.fixture.ts`
apuntaba a un tercer conjunto de usuarios que no existia en ningun entorno.

Vive en `backend/scripts/` a proposito: es la unica ruta presente tanto en el
repo del host (donde corren los seeds de `database/`) como dentro del contenedor
Django en `/app/scripts` (donde corren estos). Los seeds del host lo importan
agregando `backend/scripts` al sys.path.
"""

# Contrasena unica de todas las cuentas demo. Solo para entornos de desarrollo
# y pruebas; ningun entorno real debe sembrarse con este script.
DEMO_PASSWORD = "password123"

# Valor canonico de Dim_Credencial.estadocredencial. Debe coincidir con
# ESTADO_CREDENCIAL_ACTIVO en core/repositories/cuentas_clientes/credential_repository.py;
# el test tests/regression/test_credenciales_demo_consistentes.py verifica que no
# se separen.
ESTADO_CREDENCIAL_ACTIVO = "Activo"

# Dominio de los correos demo. `e2e/fixtures/auth.fixture.ts` debe usar el mismo.
DEMO_DOMAIN = "demo.tsi.com"

# ---------------------------------------------------------------------------
# Catalogo canonico de roles
# ---------------------------------------------------------------------------
# Fuente unica de `Dim_Rol`. Antes cada seed traia su propia lista y se pisaban:
# `database/seed_usuarios.py` definia idrol 4 = "Operador" y
# `seed_demo_usuarios_roles.py` creaba otro "Operador" en idrol 11, asi que el
# catalogo terminaba con dos filas del mismo nombre segun cual corriera ultimo.
# Como Dim_Rol es upsert por idrol, cualquier seed que reasigne un id existente
# renombra el rol de los usuarios ya vinculados.
#
# Los ids respetan los que ya estan en uso en el entorno; no reordenarlos sin
# migrar `Dim_Usuario_Rol`.
ROLES_DEMO = {
    1: ("Cliente", "Cliente que contrata el servicio"),
    2: ("Administrador", "Administrador general del sistema"),
    3: ("Soporte", "Atencion de tickets y reclamos (cola de soporte)"),
    4: ("Operador", "Operador de emergencias: accidentes, despacho y seguimiento"),
    # SRS L124: equipo tecnico de TSI que registra partners, asigna planes de
    # acceso y vigila consumo y errores. NO es quien consume la API: eso es
    # PartnerIntegracion (idrol 15). La descripcion anterior ("Consumo de
    # integraciones via API") describia al partner y confundia ambos actores.
    5: ("DesarrolladorAPIs", "Equipo tecnico de integraciones: registra partners, asigna planes y vigila consumo"),
    6: ("DirectorTecnologico", "Vision estrategica y reportes ejecutivos"),
    7: ("Unidad", "Unidad de emergencia en campo"),
    8: ("Despacho", "Servicio/operador de despacho"),
    9: ("Tecnico", "Tecnico de campo / evidencia"),
    10: ("SupervisorSoporte", "Receptor de escalado automatico SLA (RN-TIC-005)"),
    12: ("GerenteVentas", "Gerente de ventas: pipeline comercial y prospectos"),
    13: ("Proveedor", "Proveedor de flota de unidades de emergencia"),
    14: ("DirectorEstrategia", "Director de Estrategia: catalogo Dim_Plan (RF-SUSF-001)"),
    # SRS L121: "Area tecnica de un cliente integrador". Es el AUTOSERVICIO del
    # partner (CU-O49): emitir sus credenciales, pedir el paso a produccion y ver
    # su consumo. No se reutiliza `Cliente` (idrol 1) porque, aunque todo partner
    # pertenece a un cliente, son personas distintas de la misma organizacion con
    # permisos distintos: el Cliente titular gestiona plan, facturas y tickets; el
    # area tecnica solo gestiona credenciales. Tampoco es `DesarrolladorAPIs`
    # (idrol 5), que es el equipo de TSI que registra partners, no quien consume.
    15: ("PartnerIntegracion", "Area tecnica de un cliente integrador: credenciales y consumo propio (CU-O49)"),
}

# idrol 11 fue un "Operador" duplicado del 4. Se conserva la constante para poder
# desactivarlo explicitamente en la higiene de datos, no para volver a usarlo.
ROL_OPERADOR_DUPLICADO_OBSOLETO = 11

# Busqueda inversa nombre -> idrol, para que los seeds no hardcodeen numeros.
ROL_ID_POR_NOMBRE = {nombre: idrol for idrol, (nombre, _) in ROLES_DEMO.items()}


def filas_dim_rol(now_ms: int) -> list[dict]:
    """Catalogo completo listo para publicar en Dim_Rol_topic."""
    return [
        {
            "idrol": idrol,
            "rol": nombre,
            "descripcion": descripcion,
            "activo": True,
            "fecha_actualizacion": now_ms,
        }
        for idrol, (nombre, descripcion) in sorted(ROLES_DEMO.items())
    ]
