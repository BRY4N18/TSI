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

#: Soporte al Cliente: autoridad unica sobre los dos listados.
AUTORIDAD_SOPORTE = frozenset({ROL_GERENTE_EXITO_CLIENTE})

#: Analitica: se aplicara cuando ese modulo se especifique.
AUTORIDAD_ANALITICA = frozenset({ROL_DIRECTOR_DATOS})

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
