# Modelo de Datos — Trafico Seguro Integral (TSI)

> **Nota de origen:** este documento se generó automáticamente a partir de `tablas.json` y `esquemas.json` (configuración real de Apache Pinot). Es un espejo fiel de esos dos archivos — si hay una diferencia entre este `.md` y los JSON, los JSON son la fuente de verdad y este archivo debe corregirse, nunca al revés.

## 1. Arquitectura General

El modelo de datos de TSI sigue un diseño **Fact-Dim (Hechos y Dimensiones)** implementado sobre **Apache Pinot** en modo **REALTIME** con ingestión de datos vía **Apache Kafka**. Cada tabla se alimenta de un tópico Kafka dedicado (`{NombreTabla}_topic`).

### Convenciones de nomenclatura (confirmadas contra los JSON reales)
- **Fact_***: Tablas de hechos — eventos transaccionales y métricas de negocio.
- **Dim_***: Tablas de dimensión — datos descriptivos y catálogos.
- Las palabras compuestas dentro del nombre **no llevan guion bajo entre sí** (ej. `Dim_EstadoRegion`, no `Dim_Estado_Region`) salvo un pequeño grupo de tablas que sí lo usan de forma consistente en el JSON real (`Dim_Estado_Conductor`, `Dim_Estado_Soporte`, `Dim_Elementos_Fisicos`, `Dim_Preferencias_Cliente`, `Dim_RolesServidorRoles`, `Dim_UsuariosServidorRolesServidor`, `Fact_Conductor_Accidente`, `Fact_Historial_Ticket`, `Fact_Solicitud_Cambio_Plan`, `Fact_ArchivosAdjuntosReclamos`) — se documentan tal cual aparecen en `tablas.json`, sin normalizar, para que este archivo sea 100% copiable al código.
- **activo** (BOOLEAN): Flag de borrado lógico, presente en la gran mayoría de las tablas.
- **fecha_actualizacion** (LONG, EPOCH ms): columna de tiempo usada por Pinot para upsert/segmentación en la mayoría de las tablas (algunas usan otra columna de tiempo propia del dominio, indicada en cada tabla).

### Total de tablas: 71
- **23 tablas de hechos (Fact)**
- **48 tablas de dimensión (Dim)**

### Tipos de datos
| Tipo | Uso |
|---|---|
| INT | Identificadores, contadores, FK |
| STRING | Textos, descripciones, nombres, URLs, JSON serializado |
| DOUBLE | Coordenadas GPS, montos, porcentajes, métricas |
| BOOLEAN | Flags (activo, condiciones) |
| LONG | Timestamps en milisegundos EPOCH |

---

## 2. Dominio: Gestion de Accidentes (Core Operativo)

### Dim_ElementoClimaticosAccidente
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_ElementoClimaticosAccidente_topic` · *PK:* `idelementoclimaticoaccidente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idelementoclimaticoaccidente (PK) | INT |  |
| idperiododia | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idestadoclima | INT |  |
| idusuario | INT |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_ElementoFisicoAccidente
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_ElementoFisicoAccidente_topic` · *PK:* `idelementosfisicosaccidente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idelementosfisicosaccidente (PK) | INT |  |
| idelementofisico | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idusuario | INT |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Elementos_Fisicos
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Elementos_Fisicos_topic` · *PK:* `idelementofisico`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idelementofisico (PK) | INT |  |
| elementofisico | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_EstadoDespacho
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_EstadoDespacho_topic` · *PK:* `idestadodespacho`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestadodespacho (PK) | INT |  |
| estadodespacho | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_EstadosClimas
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_EstadosClimas_topic` · *PK:* `idestadoclima`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestadoclima (PK) | INT |  |
| direccionviento | STRING |  |
| condicionclima | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| temperaturaf | DOUBLE |
| sensaciontermicaf | DOUBLE |
| humedadporcentaje | DOUBLE |
| presionpulgadas | DOUBLE |
| visibilidadmillas | DOUBLE |
| velocidadvientomph | DOUBLE |
| precipitacionpulgadas | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_EvidenciaFoto
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Dim_EvidenciaFoto_topic` · *PK:* `idevidenciafoto`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idevidenciafoto (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idusuario | INT |  |
| sincronizado | BOOLEAN |  |
| urlevidenciafoto | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Implicado
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Implicado_topic` · *PK:* `idimplicado`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idimplicado (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| tipoimplicado | STRING |  |
| genero | STRING |  |
| estadoimplicado | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| edad | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_NotaAccidente
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Dim_NotaAccidente_topic` · *PK:* `idnotaaccidentes`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idnotaaccidentes (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idusuario | INT |  |
| sincronizado | BOOLEAN |  |
| nota | STRING |  |
| tipo | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_OrigenDespacho
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_OrigenDespacho_topic` · *PK:* `idorigendespacho`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idorigendespacho (PK) | INT |  |
| origendespacho | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_PeriodosDias
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_PeriodosDias_topic` · *PK:* `idperiododia`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idperiododia (PK) | INT |  |
| amaneceranochecer | STRING |  |
| crepusculocivil | STRING |  |
| crepusculonautico | STRING |  |
| crepusculoastronomico | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_ReferenciaEstacion
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_ReferenciaEstacion_topic` · *PK:* `idreferenciaestacion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idreferenciaestacion (PK) | INT |  |
| codigoaeropuerto | STRING |  |
| zonahoraria | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Severidad
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Severidad_topic` · *PK:* `idseveridad`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idseveridad (PK) | INT |  |
| activo | BOOLEAN |  |
| descripcion | STRING |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| severidad | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_TipoEstadoAccidente
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_TipoEstadoAccidente_topic` · *PK:* `idtipoestadoincidente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idtipoestadoincidente (PK) | INT |  |
| tipoestadoincidente | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_TipoReportado
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_TipoReportado_topic` · *PK:* `idtiporeportado`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idtiporeportado (PK) | INT |  |
| tiporeportado | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Accidente
*Columna de tiempo (Pinot):* `fechahoraaccidente` · *Tópico Kafka:* `Fact_Accidente_topic` · *PK:* `idaccidente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idaccidente (PK) | STRING |  |
| idseveridad | INT | → `Dim_Severidad` |
| idcalle | INT | → `Dim_Calle` |
| idusuario | INT |  |
| idtiporeportado | INT | → `Dim_TipoReportado` |
| idreferenciaestacion | INT | → `Dim_ReferenciaEstacion` |
| idaccidenteorigen | STRING |  |
| horainicio | STRING |  |
| horafin | STRING |  |
| descripcion | STRING |  |
| codigopostal | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| duracionminutos | INT |
| numvehiculos | INT |
| numvictimas | INT |
| numheridos | INT |
| numfallecidos | INT |
| latitudinicio | DOUBLE |
| longitudinicio | DOUBLE |
| distanciamillas | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahoraaccidente | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_AccidenteTipoEstadoAccidente
*Columna de tiempo (Pinot):* `fechahoramodificado` · *Tópico Kafka:* `Fact_AccidenteTipoEstadoAccidente_topic` · *PK:* `idaccidentetipoestadoaccidente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idaccidentetipoestadoaccidente (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idtipoestadoincidente | INT |  |
| idusuario | INT |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahoramodificado | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Despacho
*Columna de tiempo (Pinot):* `fechahoradespacho` · *Tópico Kafka:* `Fact_Despacho_topic` · *PK:* `iddespacho`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| iddespacho (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idunidademergencia | INT | → `Dim_UnidadEmergencia` |
| idnotificaciondespacho | INT | → `Fact_NotificacionDespacho` |
| idorigendespacho | INT | → `Dim_OrigenDespacho` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahoradespacho | LONG | 1:MILLISECONDS:EPOCH |
| fechahorallegada | LONG | 1:MILLISECONDS:EPOCH |
| fechahoraretiro | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_HistorialDespachoUnidad
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Fact_HistorialDespachoUnidad_topic` · *PK:* `idhistorialdespachounidad`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idhistorialdespachounidad (PK) | INT |  |
| estadoanterior | STRING |  |
| estadonuevo | STRING |  |
| iddespacho | INT | → `Fact_Despacho` |
| idestadodespacho | INT | → `Dim_EstadoDespacho` |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_NotificacionDespacho
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Fact_NotificacionDespacho_topic` · *PK:* `idnotificaciondespacho`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idnotificaciondespacho (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idunidaddemergencia | INT |  |
| activo | BOOLEAN |  |
| estadonotificaciondespacho | STRING |  |
| motivo | STRING |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| numheridos | INT |
| numvehiculos | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 3. Dominio: Conductores y Vehiculos

### Dim_Conductor
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Conductor_topic` · *PK:* `idconductor`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idconductor (PK) | INT |  |
| apellidos | STRING |  |
| nombres | STRING |  |
| identificacion | STRING |  |
| genero | STRING |  |
| tipolicencia | STRING |  |
| estadolicencia | STRING |  |
| ciudadresidencia | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| aniosexperiencia | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Estado_Conductor
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Estado_Conductor_topic` · *PK:* `idestadoconductor`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestadoconductor (PK) | INT |  |
| estadosobriedad | BOOLEAN |  |
| nivelatencion | BOOLEAN |  |
| condicionfisica | BOOLEAN |  |
| usoseguridad | BOOLEAN |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Vehiculo
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Vehiculo_topic` · *PK:* `idvehiculo`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idvehiculo (PK) | INT |  |
| tipovehiculo | STRING |  |
| modelovehiculo | STRING |  |
| categoriausovehiculo | STRING |  |
| mercanciapeligrosa | BOOLEAN |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| ejes | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Conductor_Accidente
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Fact_Conductor_Accidente_topic` · *PK:* `idconductoraccidente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idconductoraccidente (PK) | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| idconductor | INT | → `Dim_Conductor` |
| idestadoconductor | INT | → `Dim_Estado_Conductor` |
| idvehiculo | INT | → `Dim_Vehiculo` |
| idusuario | INT |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 4. Dominio: Unidades de Emergencia

### Dim_EstadoUnidadEmergencia
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_EstadoUnidadEmergencia_topic` · *PK:* `idestadounidademergencia`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestadounidademergencia (PK) | INT |  |
| estadounidademergencia | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_HistorialUbicacionUnidadEmergencia
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Dim_HistorialUbicacionUnidadEmergencia_topic` · *PK:* `idhistorialunidademergencia`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idhistorialunidademergencia (PK) | INT |  |
| idunidademergencia | INT | → `Dim_UnidadEmergencia` |
| idaccidente | STRING | → `Fact_Accidente` |

**Métricas:**
| Columna | Tipo |
|---|---|
| latitud | DOUBLE |
| longitud | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_UnidadEmergencia
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_UnidadEmergencia_topic` · *PK:* `idunidademergencia`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idunidademergencia (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| tipopropiedad | STRING |  |
| placa | STRING |  |
| capacidad | STRING |  |
| zonacobertura | STRING |  |
| contactoproveedor | STRING |  |
| unidademergencia | STRING |  |
| tipounidademergencia | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| latitud | DOUBLE |
| longitud | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_BajaUnidad
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Fact_BajaUnidad_topic` · *PK:* `idbajaunidad`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idbajaunidad (PK) | INT |  |
| idunidademergencia | INT | → `Dim_UnidadEmergencia` |
| idusuario | INT |  |
| idaccidente | STRING | → `Fact_Accidente` |
| motivo | STRING |  |
| tipobaja | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_HistorialEstadoUnidad
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Fact_HistorialEstadoUnidad_topic` · *PK:* `idhistorialestadosunidadesemergencias`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idhistorialestadosunidadesemergencias (PK) | INT |  |
| estadoanterior | STRING |  |
| estadonuevo | STRING |  |
| idestadounidademergencia | INT | → `Dim_EstadoUnidadEmergencia` |
| idunidademergencia | INT | → `Dim_UnidadEmergencia` |
| idusuario | INT |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 5. Dominio: Configuracion de Red Operativa

### Dim_RegionOperativa
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_RegionOperativa_topic` · *PK:* `idregionoperativa`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idregionoperativa (PK) | INT |  |
| idestado | INT | → `Dim_Estado` |
| nombreregion | STRING |  |
| estadoregion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_RegionOperativaEstadoRegion
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_RegionOperativaEstadoRegion_topic` · *PK:* `idregionoperativaestadoregion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idregionoperativaestadoregion (PK) | INT |  |
| idregionoperativa | INT | → `Dim_RegionOperativa` |
| idestadoregion | INT | → `Dim_EstadoRegion` |
| nombreregion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_ValidacionRegion
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Dim_ValidacionRegion_topic` · *PK:* `idvalidacionregion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idvalidacionregion (PK) | INT |  |
| idregionoperativa | INT | → `Dim_RegionOperativa` |
| idusuario | INT |  |
| resultado | STRING |  |
| motivo | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 6. Dominio: Geografia (Jerarquia, dimension compartida)

### Dim_Calle
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Calle_topic` · *PK:* `idcalle`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idcalle (PK) | INT |  |
| calle | STRING |  |
| idciudad | INT | → `Dim_Ciudad` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Ciudad
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Ciudad_topic` · *PK:* `idciudad`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idciudad (PK) | INT |  |
| ciudad | STRING |  |
| idcondado | INT | → `Dim_Condado` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Condado
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Condado_topic` · *PK:* `idcondado`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idcondado (PK) | INT |  |
| condado | STRING |  |
| idestado | INT | → `Dim_Estado` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Estado
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Estado_topic` · *PK:* `idestado`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestado (PK) | INT |  |
| estado | STRING |  |
| idpais | INT | → `Dim_Pais` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_EstadoRegion
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_EstadoRegion_topic` · *PK:* `idestadoregion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestadoregion (PK) | INT |  |
| estadoregion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Pais
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Pais_topic` · *PK:* `idpais`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idpais (PK) | INT |  |
| pais | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 7. Dominio: Seguridad y Usuarios

### Dim_Credencial
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Credencial_topic` · *PK:* `idcredencial`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idcredencial (PK) | INT |  |
| idusuario | INT |  |
| contrasena | STRING |  |
| estadocredencial | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Rol
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Rol_topic` · *PK:* `idrol`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idrol (PK) | INT |  |
| rol | STRING |  |
| descripcion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_RolesServidor
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_RolesServidor_topic` · *PK:* `idrolservidor`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idrolservidor (PK) | INT |  |
| rolservidor | STRING |  |
| descripcion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_RolesServidorRoles
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_RolesServidorRoles_topic` · *PK:* `idrolservidor, idrol`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idrolservidor (PK) | INT |  |
| idrol (PK) | INT | → `Dim_Rol` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Usuario_Rol
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Usuario_Rol_topic` · *PK:* `idusuariorol`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idusuariorol (PK) | INT |  |
| idusuario | INT |  |
| idrol | INT | → `Dim_Rol` |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Usuarios
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Usuarios_topic` · *PK:* `idusuario`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idusuario (PK) | INT |  |
| apellidos | STRING |  |
| nombres | STRING |  |
| gmail | STRING |  |
| identificacion | STRING |  |
| genero | STRING |  |
| telefono | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechanacimiento | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_UsuariosServidor
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_UsuariosServidor_topic` · *PK:* `idusuarioservidor`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idusuarioservidor (PK) | INT |  |
| idusuario | INT |  |
| usuario | STRING |  |
| contrasena | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_UsuariosServidorRolesServidor
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_UsuariosServidorRolesServidor_topic` · *PK:* `idusuarioservidorrolservidor`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idusuarioservidorrolservidor (PK) | INT |  |
| idusuarioservidor | INT |  |
| idrolservidor | INT |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Session
*Columna de tiempo (Pinot):* `fechahorainiciosesion` · *Tópico Kafka:* `Fact_Session_topic` · *PK:* `idsession`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idsession (PK) | INT |  |
| idusuario | INT |  |
| navegador | STRING |  |
| token | STRING |  |
| estadosession | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahorainiciosesion | LONG | 1:MILLISECONDS:EPOCH |
| fechahoracierresesion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 8. Dominio: Cuentas y Onboarding

### Dim_Cliente
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Cliente_topic` · *PK:* `idcliente`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idcliente (PK) | INT |  |
| idprospecto | INT | → `Dim_Prospecto` |
| nombre | STRING |  |
| razon_social | STRING |  |
| tipo | STRING |  |
| nit_identificacion | STRING |  |
| plan_suscripcion | STRING |  |
| logo_url | STRING |  |
| estado_onboarding | STRING |  |
| admin_local_id | INT |  |
| estado | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_inicio_contrato | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Plan
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Plan_topic` · *PK:* `idplan`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idplan (PK) | INT |  |
| nombre | STRING |  |
| nivel | STRING |  |
| limites | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| precio | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Preferencias_Cliente
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Preferencias_Cliente_topic` · *PK:* `id_preferencia`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_preferencia (PK) | INT |  |
| id_cliente | INT | → `Dim_Cliente` |
| umbrales_alerta | STRING |  |
| frecuencia_reportes | STRING |  |
| formato_reportes | STRING |  |
| canales_notificacion | STRING |  |
| telefono_sms | STRING |  |
| zonas_geograficas | STRING |  |
| destinatarios_reportes | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Onboarding
*Columna de tiempo (Pinot):* `fecha_completado` · *Tópico Kafka:* `Fact_Onboarding_topic` · *PK:* `id_onboarding`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_onboarding (PK) | INT |  |
| id_cliente | INT | → `Dim_Cliente` |
| etapa | STRING |  |
| completado | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_completado | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 9. Dominio: Suscripciones y Facturacion

### Dim_MetodoPago
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_MetodoPago_topic` · *PK:* `idmetodopago`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idmetodopago (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| tipo | STRING |  |
| tokenpasarela | STRING |  |
| ultimosdigitos | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechaexpiracion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Factura
*Columna de tiempo (Pinot):* `fecha_emision` · *Tópico Kafka:* `Fact_Factura_topic` · *PK:* `id_factura`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_factura (PK) | INT |  |
| id_cliente | INT | → `Dim_Cliente` |
| id_suscripcion | INT | → `Fact_Suscripcion` |
| idmetodopago | INT | → `Dim_MetodoPago` |
| numero_factura | STRING |  |
| periodo | STRING |  |
| estado_pago | STRING |  |
| desglose_cargos | STRING |  |
| resultado_ultimo_reintento | STRING |  |
| id_factura_original | INT |  |
| es_nota_credito | BOOLEAN |  |
| motivo_anulacion | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| reintentos | INT |
| monto_base | DOUBLE |
| impuestos | DOUBLE |
| monto_total | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_emision | LONG | 1:MILLISECONDS:EPOCH |
| fecha_vencimiento | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Solicitud_Cambio_Plan
*Columna de tiempo (Pinot):* `fecha_solicitud` · *Tópico Kafka:* `Fact_Solicitud_Cambio_Plan_topic` · *PK:* `idsolicitud`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idsolicitud (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| idplanactual | INT |  |
| idplansolicitado | INT |  |
| estado | STRING |  |
| motivo | STRING |  |
| idadminaprobador | INT |  |
| motivo_rechazo | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_solicitud | LONG | 1:MILLISECONDS:EPOCH |
| fecha_resolucion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Suscripcion
*Columna de tiempo (Pinot):* `fecha_inicio` · *Tópico Kafka:* `Fact_Suscripcion_topic` · *PK:* `id_suscripcion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_suscripcion (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| idplan | INT | → `Dim_Plan` |
| estado | STRING |  |
| activo | BOOLEAN |  |
| renovacionautomatica | BOOLEAN |  |
| motivocancelacion | STRING |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| precio | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_inicio | LONG | 1:MILLISECONDS:EPOCH |
| fecha_fin | LONG | 1:MILLISECONDS:EPOCH |
| fechacancelacion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 10. Dominio: Ventas y CRM (Pipeline Comercial)

### Dim_Prospecto
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Prospecto_topic` · *PK:* `idprospecto`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idprospecto (PK) | INT |  |
| nombres | STRING |  |
| apellidos | STRING |  |
| gmail | STRING |  |
| empresa | STRING |  |
| tipo_organizacion | STRING |  |
| cargo | STRING |  |
| telefono | STRING |  |
| como_nos_conocio | STRING |  |
| etapa_actual | STRING |  |
| idusuario | INT |  |
| demo_expiracion | STRING |  |
| activo | BOOLEAN |  |
| motivo_inactividad | STRING |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| valor_estimado | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_registro | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Asignacion
*Columna de tiempo (Pinot):* `fechahoraasignacion` · *Tópico Kafka:* `Fact_Asignacion_topic` · *PK:* `idasignacion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idasignacion (PK) | INT |  |
| idprospecto | INT | → `Dim_Prospecto` |
| idusuariogerenteanterior | INT |  |
| idusuariogerenteactual | INT |  |
| tipoasignacion | STRING |  |
| motivo | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahoraasignacion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Interaccion_Demo
*Columna de tiempo (Pinot):* `timestamp_evento` · *Tópico Kafka:* `Fact_Interaccion_Demo_topic` · *PK:* `idinteraccion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idinteraccion (PK) | INT |  |
| idprospecto | INT | → `Dim_Prospecto` |
| tipo_evento | STRING |  |
| seccion | STRING |  |
| metadata | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| timestamp_evento | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_NotificacionVentas
*Columna de tiempo (Pinot):* `fechahoranotificacion` · *Tópico Kafka:* `Fact_NotificacionVentas_topic` · *PK:* `idnotificacion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idnotificacion (PK) | INT |  |
| id_prospecto | INT | → `Dim_Prospecto` |
| idinteraccion | INT |  |
| idusuariogerentenotificado | INT |  |
| regladisparada | STRING |  |
| canal | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahoranotificacion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Pipeline
*Columna de tiempo (Pinot):* `fecha_transicion` · *Tópico Kafka:* `Fact_Pipeline_topic` · *PK:* `id_transicion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_transicion (PK) | INT |  |
| id_prospecto | INT | → `Dim_Prospecto` |
| etapa_anterior | STRING |  |
| etapa_nueva | STRING |  |
| notas | STRING |  |
| motivo_perdida | STRING |  |
| gerente_id | INT |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_transicion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 11. Dominio: Portal de Partners y API

### Dim_CredencialAPI
*Columna de tiempo (Pinot):* `fecha_creacion` · *Tópico Kafka:* `Dim_CredencialAPI_topic` · *PK:* `idcredencial`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idcredencial (PK) | INT | → `Dim_Credencial` |
| idpartner | INT | → `Dim_Partner` |
| idcliente | INT | → `Dim_Cliente` |
| client_secret_hash | STRING |  |
| entorno | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_creacion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_EstadoIntegracion
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_EstadoIntegracion_topic` · *PK:* `idestadointegracion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idestadointegracion (PK) | INT |  |
| nombre | STRING |  |
| descripcion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Partner
*Columna de tiempo (Pinot):* `sandbox_activado` · *Tópico Kafka:* `Dim_Partner_topic` · *PK:* `idpartner`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idpartner (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| nombrepartner | STRING |  |
| planapi | STRING |  |
| contacto_tecnico_nombre | STRING |  |
| contacto_tecnico_gmail | STRING |  |
| fecha_suspension | STRING |  |
| motivo_suspension | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| limitellamadasmes | INT |
| limitellamadasminuto | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| sandbox_activado | LONG | 1:MILLISECONDS:EPOCH |
| sandbox_expiracion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_Servicio
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Servicio_topic` · *PK:* `id_servicio`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_servicio (PK) | INT |  |
| nombre | STRING |  |
| tipo | STRING |  |
| descripcion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_APIIntegracion
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Fact_APIIntegracion_topic` · *PK:* `idapiintegracion`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idapiintegracion (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| idservicio | INT | → `Dim_Servicio` |
| idestadointegracion | INT | → `Dim_EstadoIntegracion` |
| idpartner | INT | → `Dim_Partner` |
| entorno | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| llamadas | INT |
| errores | INT |
| latencia | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_HistorialAccesoPartner
*Columna de tiempo (Pinot):* `fecha_cambio` · *Tópico Kafka:* `Fact_HistorialAccesoPartner_topic` · *PK:* `idhistorial`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idhistorial (PK) | INT |  |
| idpartner | INT | → `Dim_Partner` |
| idcredencial | INT | → `Dim_Credencial` |
| tipo_cambio | STRING |  |
| ejecutado_por | STRING |  |
| motivo | STRING |  |
| estado_anterior | STRING |  |
| estado_nuevo | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_cambio | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_LogLlamadaAPI
*Columna de tiempo (Pinot):* `fechallamada` · *Tópico Kafka:* `Fact_LogLlamadaAPI_topic` · *PK:* `idlogllamadaapi`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idlogllamadaapi (PK) | INT |  |
| idpartner | INT | → `Dim_Partner` |
| idcredencialapi | INT | → `Dim_CredencialAPI` |
| endpoint | STRING |  |
| metodohttp | STRING |  |
| codigohttp | INT |  |
| iporigen | INT |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| latenciams | DOUBLE |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechallamada | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 12. Dominio: Soporte al Cliente

### Dim_Estado_Soporte
*Columna de tiempo (Pinot):* `fecha_actualizacion` · *Tópico Kafka:* `Dim_Estado_Soporte_topic` · *PK:* `id_estado_soporte`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_estado_soporte (PK) | INT |  |
| nombre | STRING |  |
| descripcion | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Dim_SLAConfig
*Columna de tiempo (Pinot):* `fechavigenciadesde` · *Tópico Kafka:* `Dim_SLAConfig_topic` · *PK:* `idslaconfig`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idslaconfig (PK) | INT |  |
| idplan | INT | → `Dim_Plan` |
| tipoincidencia | STRING |  |
| prioridad | STRING |  |
| activo | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| tiemporespuestamax | LONG |
| tiemporesolucionmax | LONG |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechavigenciadesde | LONG | 1:MILLISECONDS:EPOCH |
| fechavigenciahasta | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_ArchivosAdjuntosReclamos
*Columna de tiempo (Pinot):* `fechahorasubida` · *Tópico Kafka:* `Fact_ArchivosAdjuntosReclamos_topic` · *PK:* `idarchivoadjuntoreclamo`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| idarchivoadjuntoreclamo (PK) | INT |  |
| id_reclamo | INT | → `Fact_Reclamo` |
| urlarchivo | STRING |  |
| activo | BOOLEAN |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahorasubida | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Historial_Ticket
*Columna de tiempo (Pinot):* `fecha_accion` · *Tópico Kafka:* `Fact_Historial_Ticket_topic` · *PK:* `id_historial`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_historial (PK) | INT |  |
| id_reclamo | INT | → `Fact_Reclamo` |
| tipo_accion | STRING |  |
| mensaje | STRING |  |
| es_nota_interna | BOOLEAN |  |
| idusuario | INT |  |
| estado_anterior | STRING |  |
| estado_nuevo | STRING |  |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fecha_accion | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

### Fact_Reclamo
*Columna de tiempo (Pinot):* `fechahora` · *Tópico Kafka:* `Fact_Reclamo_topic` · *PK:* `id_reclamo`

| Columna | Tipo | FK sugerida (por nombre) |
|---|---|---|
| id_reclamo (PK) | INT |  |
| idcliente | INT | → `Dim_Cliente` |
| idestadosoporte | INT | → `Dim_Estado_Soporte` |
| idservicio | INT | → `Dim_Servicio` |
| idslaconfig | INT | → `Dim_SLAConfig` |
| tipo | STRING |  |
| activo | BOOLEAN |  |
| asunto | STRING |  |
| prioridad | STRING |  |
| descripcion | STRING |  |
| id_agente_asignado | INT |  |
| tipo_incidencia | STRING |  |
| sla_status | STRING |  |
| estado | STRING |  |
| cierreconfirmadocliente | BOOLEAN |  |

**Métricas:**
| Columna | Tipo |
|---|---|
| sla_primera_respuesta | LONG |
| sla_resolucion | LONG |
| tiempo_solucion | INT |

**Timestamps:**
| Columna | Tipo | Formato |
|---|---|---|
| fechahora | LONG | 1:MILLISECONDS:EPOCH |
| fechahoraconfirmacioncierre | LONG | 1:MILLISECONDS:EPOCH |
| fecha_actualizacion | LONG | 1:MILLISECONDS:EPOCH |

---

## 13. Arquitectura de Streaming

Cada tabla se alimenta vía **Apache Kafka** con las siguientes características (confirmadas en `tablas.json`):

- **Stream Type:** `kafka` (lowlevel consumer)
- **Broker:** `kafka:29092`
- **Consumer:** `org.apache.pinot.plugin.stream.kafka20.KafkaConsumerFactory`
- **Decoder:** `org.apache.pinot.plugin.stream.kafka.KafkaJSONMessageDecoder`
- **Offset Reset:** `smallest`
- **Load Mode:** `MMAP`
- **Upsert Mode:** `FULL`, columna de comparación variable por tabla (ver cada tabla arriba)
- **Replicas:** 1 por partición
- Cada tabla tiene su propio tópico Kafka con el formato `{NombreTabla}_topic`

---

## 14. Mapeo por Módulo del Sistema (Documentación operativa)

Correspondencia entre los dominios de este documento y los módulos documentados en `docs/architecture/` (`GestionCuentasClientes.md`, `GestionDeEmergencias.md`, `ConfiguracionRedOperativa.md`, `PortalPartnersAPI.md`, `SoporteCliente.md`, `SuscripcionesFacturacion.md`, `VentasCRM_Pre-venta.md`):

| Módulo (docs) | Dominios de este archivo |
|---|---|
| Gestión de Cuentas y Clientes | Seguridad y Usuarios, Cuentas y Onboarding |
| Gestión de Emergencias | Gestión de Accidentes (Core Operativo), Conductores y Vehículos, Unidades de Emergencia |
| Configuración de Red Operativa | Configuración de Red Operativa, Geografía (compartida) |
| Portal de Partners API | Portal de Partners y API |
| Soporte al Cliente | Soporte al Cliente |
| Suscripciones y Facturación | Suscripciones y Facturación |
| Ventas y CRM (Pre-venta) | Ventas y CRM (Pipeline Comercial) |

### Dimensiones compartidas entre módulos
| Dimensión | Tablas | Usada por |
|---|---|---|
| Geografía | Dim_Pais, Dim_EstadoRegion, Dim_Estado, Dim_Condado, Dim_Ciudad, Dim_Calle | Emergencias, Red Operativa |
| Cliente | Dim_Cliente | Cuentas, Facturación, Ventas-CRM, Partners API, Soporte |
| Plan | Dim_Plan | Cuentas, Facturación, Partners API |
| Servicio | Dim_Servicio | Partners API, Soporte |
| Sesión | Fact_Session | Cuentas (login), transversal a cualquier módulo autenticado |

---

## Resumen de Conteo (verificado contra tablas.json / esquemas.json)

| Tipo | Cantidad |
|---|---|
| Tablas de Hechos (Fact) | 23 |
| Tablas de Dimensión (Dim) | 48 |
| **Total** | **71** |
| Dominios documentados | 11 |