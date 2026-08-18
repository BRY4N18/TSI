"""Roles de autoridad departamental (capa tactica).

Son los destinatarios de los informes tacticos. Viven aqui y no en el modulo de
permisos de cada app porque **son transversales**: siete departamentos los usan y
dos de ellos comparten el mismo rol (`DirectorTecnologico` es autoridad de
Partners y API, de Red Operativa y de la capa de accesos tecnicos de Cuentas).
Duplicar la cadena en siete `permissions.py` es como aparecen las divergencias de
un caracter que nadie detecta hasta que un permiso deja de conceder.

Fuente de la asignacion
-----------------------
`informestacticos/TSI-SRS-Especificacion-de-Requisitos.md` §5.1 define, por
departamento, un **responsable operativo** y una **autoridad superior**. El mapa
completo de que informe ve cada quien esta en
`specs/002-tactico/acceso-tactico.md`.

Dos reglas que este modulo NO puede hacer cumplir por si solo
-------------------------------------------------------------
1. **La autoridad accede sin el acotamiento por titularidad** que aplica al
   responsable operativo. Eso lo resuelve el resolutor de acotamiento, no una
   constante: aqui solo estan los nombres.

2. **La exencion no alcanza al dato sensible.** Coordenadas de accidentes,
   identidad de personas implicadas, secretos de autenticacion, medios de cobro y
   texto interno siguen excluidos de todo informe **para todos los roles**, tenga
   quien consulta el cargo que tenga. Son exclusiones constitucionales, no de
   acotamiento, y se resuelven enumerando columnas en el repositorio.

Nota sobre la autoridad repartida
---------------------------------
El SRS advierte que la autoridad "no siempre es una jefatura unica": en
Suscripciones y en Red Operativa esta repartida por materia, y en Cuentas y
Clientes el Director Tecnologico gobierna **solo** la capa de accesos tecnicos.
Por eso este modulo expone conjuntos por materia y no un simple
"autoridad del departamento X".
"""

from __future__ import annotations

# ── Autoridades departamentales ──────────────────────────────────────────────

ROL_DIRECTOR_MARKETING = "DirectorMarketing"
ROL_DIRECTOR_FINANCIERO = "DirectorFinanciero"
ROL_DIRECTOR_EXPANSION = "DirectorExpansion"
ROL_DIRECTOR_OPERACIONES = "DirectorOperaciones"
#: Autoridad de empresa. **No es un grupo que acumule directores**: cada director
#: entra a la capa estratégica por su departamento. El `Gerente` es quien ve los
#: seis OE porque responde por el tablero entero (CU-E01/E09/E10), no porque
#: herede los roles de debajo.
ROL_GERENTE = "Gerente"
ROL_GERENTE_EXITO_CLIENTE = "GerenteExitoCliente"
ROL_DIRECTOR_DATOS = "DirectorDatos"

# Ya existian como actores operativos; suman autoridad tactica sin perder su
# papel anterior (un usuario acumula roles via `Dim_Usuario_Rol`).
ROL_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"
ROL_DIRECTOR_ESTRATEGIA = "DirectorEstrategia"


# ── Autoridad por departamento y materia ─────────────────────────────────────

#: Ventas y CRM: autoridad unica sobre los cuatro listados.
AUTORIDAD_VENTAS_CRM = frozenset({ROL_DIRECTOR_MARKETING})

#: Suscripciones: repartida. Estrategia decide catalogo y precios...
AUTORIDAD_SUSCRIPCIONES_CATALOGO = frozenset({ROL_DIRECTOR_ESTRATEGIA})
#: ...y Financiero responde por el resultado economico.
AUTORIDAD_SUSCRIPCIONES_FINANZAS = frozenset({ROL_DIRECTOR_FINANCIERO})

#: Red Operativa: repartida. Expansion decide donde crecer...
AUTORIDAD_RED_OPERATIVA_CRECIMIENTO = frozenset({ROL_DIRECTOR_EXPANSION})
#: ...y Tecnologico fija los criterios de validacion de region.
AUTORIDAD_RED_OPERATIVA_VALIDACION = frozenset({ROL_DIRECTOR_TECNOLOGICO})

#: Partners y API: autoridad unica sobre los cinco listados.
AUTORIDAD_PARTNERS_API = frozenset({ROL_DIRECTOR_TECNOLOGICO})

#: Emergencias: autoridad unica sobre los cinco listados.
AUTORIDAD_EMERGENCIAS = frozenset({ROL_DIRECTOR_OPERACIONES})

#: OE6 (y solo OE6): el Director de Operaciones como autoridad del departamento
#: de Emergencias, más el Gerente que ve todos los OE. Cualquier otro rol —
#: incluidos Operador, Despacho y Unidad, que sí ven los listados tácticos—
#: queda fuera. La versión de empresa de su operación no es una ampliación de
#: su pantalla.
AUTORIDAD_ESTRATEGICA_OE6 = frozenset({ROL_DIRECTOR_OPERACIONES, ROL_GERENTE})

#: OE3 despacho y registro (E3-02, E3-03, E3-10, E3-11). Expansion no entra.
AUTORIDAD_OE3_DESPACHO = frozenset({ROL_DIRECTOR_OPERACIONES, ROL_GERENTE})
#: OE3 capacidad y flota (E3-07, E3-08, E3-13). Expansion sí, y Operaciones
#: también porque tocan despacho y flota.
AUTORIDAD_OE3_CAPACIDAD = frozenset(
    {ROL_DIRECTOR_EXPANSION, ROL_DIRECTOR_OPERACIONES, ROL_GERENTE}
)
#: Cualquier autoridad de OE3: para que un bloqueado responda 404 y no 403.
AUTORIDAD_OE3 = AUTORIDAD_OE3_DESPACHO | AUTORIDAD_OE3_CAPACIDAD

#: Soporte al Cliente: autoridad unica sobre los dos listados.
AUTORIDAD_SOPORTE = frozenset({ROL_GERENTE_EXITO_CLIENTE})

#: Analitica: se aplicara cuando ese modulo se especifique.
AUTORIDAD_ANALITICA = frozenset({ROL_DIRECTOR_DATOS})

#: OE4: DirectorDatos y Gerente ven los nueve. DirectorOperaciones solo
#: los del expediente (calidad e impacto), no los de inteligencia vendible.
AUTORIDAD_OE4 = frozenset({ROL_DIRECTOR_DATOS, ROL_GERENTE, ROL_DIRECTOR_OPERACIONES})
AUTORIDAD_OE4_INTELIGENCIA = frozenset({ROL_DIRECTOR_DATOS, ROL_GERENTE})
AUTORIDAD_OE4_EXPEDIENTE = frozenset(
    {ROL_DIRECTOR_DATOS, ROL_GERENTE, ROL_DIRECTOR_OPERACIONES}
)

#: OE2 consumo / ecosistema: Tecnología y Gerente. Finanzas no entra aquí.
AUTORIDAD_OE2_CONSUMO = frozenset({ROL_DIRECTOR_TECNOLOGICO, ROL_GERENTE})
#: OE2 dinero (E2-01, E2-02, E2-08): Finanzas y Gerente. Tecnología no entra.
AUTORIDAD_OE2_DINERO = frozenset({ROL_GERENTE, ROL_DIRECTOR_FINANCIERO})
#: Unión: un bloqueado responde 404 (no 403) a quien sí es autoridad de OE2.
AUTORIDAD_OE2 = AUTORIDAD_OE2_CONSUMO | AUTORIDAD_OE2_DINERO

#: OE1 finanzas (E1-01, E1-02, E1-06): Financiero y Gerente.
AUTORIDAD_OE1_FINANZAS = frozenset({ROL_DIRECTOR_FINANCIERO, ROL_GERENTE})
#: OE1 estrategia (E1-12). E1-03 suma Finanzas ∪ Estrategia en el permiso.
AUTORIDAD_OE1_ESTRATEGIA = frozenset({ROL_DIRECTOR_ESTRATEGIA, ROL_GERENTE})
#: OE1 captación (E1-04, E1-13): Marketing y Gerente.
AUTORIDAD_OE1_MARKETING = frozenset({ROL_DIRECTOR_MARKETING, ROL_GERENTE})
#: OE1 ciclo de vida (E1-09, E1-10, E1-11): solo Gerente. Cuentas no tiene autoridad de negocio.
AUTORIDAD_OE1_CICLO = frozenset({ROL_GERENTE})
#: Unión: un bloqueado responde 404 (no 403) a quien sí es autoridad de OE1.
AUTORIDAD_OE1 = (
    AUTORIDAD_OE1_FINANZAS
    | AUTORIDAD_OE1_ESTRATEGIA
    | AUTORIDAD_OE1_MARKETING
    | AUTORIDAD_OE1_CICLO
)

#: OE5 soporte (E5-04, E5-05, E5-06, E5-08): Éxito Cliente y Gerente.
AUTORIDAD_OE5_SOPORTE = frozenset({ROL_GERENTE_EXITO_CLIENTE, ROL_GERENTE})
#: OE5 finanzas (E5-02): Financiero y Gerente.
AUTORIDAD_OE5_FINANZAS = frozenset({ROL_DIRECTOR_FINANCIERO, ROL_GERENTE})
#: OE5 estrategia (E5-03, E5-07, E5-15).
AUTORIDAD_OE5_ESTRATEGIA = frozenset({ROL_DIRECTOR_ESTRATEGIA, ROL_GERENTE})
#: OE5 riesgo (E5-12): solo Gerente. Cruza cuatro departamentos.
AUTORIDAD_OE5_RIESGO = frozenset({ROL_GERENTE})
#: Unión: un bloqueado responde 404 (no 403) a quien sí es autoridad de OE5.
AUTORIDAD_OE5 = (
    AUTORIDAD_OE5_SOPORTE
    | AUTORIDAD_OE5_FINANZAS
    | AUTORIDAD_OE5_ESTRATEGIA
    | AUTORIDAD_OE5_RIESGO
)

#: Cuentas y Clientes: **solo** la capa de accesos tecnicos (§5.1). Los otros
#: siete listados del departamento no tienen autoridad por encima del
#: Administrador — no es un olvido, es lo que dice el SRS.
AUTORIDAD_CUENTAS_ACCESOS_TECNICOS = frozenset({ROL_DIRECTOR_TECNOLOGICO})


#: Todas las autoridades departamentales, para comprobaciones genericas.
TODAS_LAS_AUTORIDADES = frozenset(
    AUTORIDAD_VENTAS_CRM
    | AUTORIDAD_SUSCRIPCIONES_CATALOGO
    | AUTORIDAD_SUSCRIPCIONES_FINANZAS
    | AUTORIDAD_RED_OPERATIVA_CRECIMIENTO
    | AUTORIDAD_RED_OPERATIVA_VALIDACION
    | AUTORIDAD_PARTNERS_API
    | AUTORIDAD_EMERGENCIAS
    | AUTORIDAD_SOPORTE
    | AUTORIDAD_ANALITICA
)


def es_autoridad(roles, autoridad: frozenset[str]) -> bool:
    """True si el solicitante tiene la autoridad indicada.

    Se pasa el conjunto concreto —no "el departamento"— porque en Suscripciones y
    Red Operativa la autoridad esta repartida por materia, y en Cuentas y Clientes
    alcanza a un solo listado. Un `es_autoridad_de(departamento)` invitaria a
    conceder de mas justo en los tres casos donde el SRS pide lo contrario.
    """
    return bool(roles) and bool(set(roles) & autoridad)
