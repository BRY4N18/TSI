"""Domain constants for gestión de tickets de soporte."""

ESTADO_ABIERTO = "Abierto"
ESTADO_PENDIENTE_DE_CLASIFICACION = "Pendiente_de_clasificacion"
ESTADO_EN_PROGRESO = "En_progreso"
ESTADO_ESCALADO = "Escalado"
ESTADO_RESUELTO = "Resuelto"
ESTADO_CERRADO = "Cerrado"
ESTADO_REABIERTO = "Reabierto"

SLA_EN_CURSO = "en curso"
SLA_EN_RIESGO = "en riesgo"
SLA_INCUMPLIDO = "incumplido"
SLA_CUMPLIDO = "cumplido"
# Ticket YA clasificado para el que no hay compromiso aplicable: el cliente no
# tiene suscripcion activa, o no existe regla vigente para su plan+tipo+prioridad.
# Existe para que esa ausencia sea VISIBLE. Antes quedaba en `null`, igual que un
# ticket sin clasificar, con una diferencia enorme: el sin clasificar tiene su
# propio estado y salta a la vista, y este se presentaba como un ticket normal
# que nadie estaba cronometrando.
SLA_SIN_COMPROMISO = "sin compromiso"

ROL_CLIENTE = "Cliente"
ROL_SOPORTE = "Soporte"
ROL_DESARROLLADOR_APIS = "DesarrolladorAPIs"
ROL_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"
ROL_ADMINISTRADOR = "Administrador"
ROL_SUPERVISOR_SOPORTE = "SupervisorSoporte"

CIERRE_AUTOMATICO_DIAS = 5
SLA_UMBRAL_RIESGO_PCT = 0.8
