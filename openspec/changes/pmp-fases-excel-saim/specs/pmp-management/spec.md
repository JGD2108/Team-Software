## Purpose

Proporcionar una base PMP verificable desde el Excel histórico, con métricas de horas-hombre, capacidad y cumplimiento que permitan dirigir la operación por área.

## ADDED Requirements

### Requirement: Carga inicial obligatoria y trazable del Excel PMP
El sistema SHALL aceptar `añadidos/JOSE.xlsx` como fuente inicial obligatoria de la Fase 1 y SHALL persistir las órdenes válidas con el origen de importación, la fila de procedencia y el historial de cambios. El sistema SHALL tratar `Especialidad` como el área PMP y SHALL usar `TiempoPlaneado` como la fuente de horas-hombre planeadas; no SHALL derivar métricas PMP ni fecha de creación a partir de fechas planeadas del archivo.

#### Scenario: Carga válida de JOSE.xlsx
- **WHEN** un administrador ejecuta la carga inicial de JOSE.xlsx
- **THEN** el sistema guarda las órdenes válidas, identifica su área desde Especialidad y conserva sus horas-hombre planeadas desde TiempoPlaneado

#### Scenario: Archivo inicial no permitido
- **WHEN** se intenta iniciar la Fase 1 con un archivo distinto de JOSE.xlsx
- **THEN** el sistema rechaza la carga como fuente inicial y comunica el motivo sin alterar los datos PMP existentes

### Requirement: Validación de datos sin pérdida de filas válidas
El sistema SHALL validar que cada orden tenga un área PMP reconocible, un estado permitido y un TiempoPlaneado numérico mayor que cero. SHALL informar número de fila, campo y motivo de cada inconsistencia, persistir las filas válidas y excluir de las métricas las filas inválidas. Las órdenes sin identificador externo utilizable SHALL reportarse como inconsistentes.

#### Scenario: Filas mixtas durante la importación
- **WHEN** JOSE.xlsx contiene órdenes válidas y filas con área, estado u horas-hombre inválidos
- **THEN** el sistema carga únicamente las órdenes válidas y presenta un reporte de las filas inválidas sin descartar las válidas

#### Scenario: TiempoPlaneado ausente o inválido
- **WHEN** una fila no contiene TiempoPlaneado numérico mayor que cero
- **THEN** el sistema la marca como inconsistente y no suma sus horas-hombre al tablero PMP

### Requirement: Reconciliación de la carga inicial
El sistema SHALL producir una reconciliación de la importación contra JOSE.xlsx que compare, para las filas válidas, órdenes, horas-hombre planeadas y distribución por área y estado. El resultado SHALL mostrar diferencias, si existen, antes de habilitar la sincronización SAIM.

#### Scenario: Reconciliación sin diferencias
- **WHEN** los totales persistidos coinciden con los totales válidos calculados desde JOSE.xlsx
- **THEN** el sistema informa que la Fase 1 está reconciliada y lista para validación de negocio

#### Scenario: Reconciliación con diferencia
- **WHEN** un total persistido no coincide con el total válido de JOSE.xlsx
- **THEN** el sistema muestra la diferencia por dimensión afectada y mantiene la sincronización SAIM deshabilitada

### Requirement: Tablero de cumplimiento y carga PMP
El sistema SHALL mostrar órdenes y horas-hombre planeadas totales, finalizadas y pendientes, así como el cumplimiento total y por área. El cumplimiento SHALL calcularse sobre órdenes PMP válidas y SHALL distinguir una meta cumplida únicamente cuando el resultado sea estrictamente mayor que 90 %; SHALL mostrar un semáforo y alertas cuando la meta no se cumpla.

#### Scenario: Cumplimiento igual a 90 por ciento
- **WHEN** el cumplimiento PMP calculado es exactamente 90 %
- **THEN** el tablero lo muestra como incumplido y activa la alerta correspondiente

#### Scenario: Filtrado por área PMP
- **WHEN** un usuario consulta el tablero para un área
- **THEN** el tablero muestra las órdenes, horas-hombre, pendientes y cumplimiento correspondientes a esa Especialidad

### Requirement: Capacidad, programación y brecha de personal
El sistema SHALL permitir administrar personal PMP por área y turno, junto con su programación semanal y horas disponibles. El tablero SHALL comparar la capacidad programada con las horas-hombre pendientes y SHALL mostrar la brecha y el personal equivalente requerido por área, turno y periodo consultado.

#### Scenario: Capacidad insuficiente
- **WHEN** las horas-hombre pendientes superan la capacidad programada de un área y turno
- **THEN** el sistema muestra la brecha de horas y el personal equivalente adicional requerido

#### Scenario: Capacidad suficiente
- **WHEN** la capacidad programada cubre las horas-hombre pendientes del área y turno
- **THEN** el sistema muestra una brecha no positiva y no solicita personal adicional

### Requirement: Retiro del registro manual de reportes
El sistema SHALL retirar de la interfaz el acceso al formulario de reportes manuales de falla y SHALL rechazar nuevas creaciones por sus interfaces de servicio. SHALL conservar y permitir consultar los registros históricos ya existentes según las reglas de acceso vigentes.

#### Scenario: Usuario intenta acceder al registro manual
- **WHEN** un usuario navega por la aplicación después de habilitar PMP
- **THEN** no encuentra una ruta ni acción para crear un reporte manual de falla

#### Scenario: Solicitud de creación manual heredada
- **WHEN** un cliente intenta crear un reporte manual mediante la interfaz de servicio anterior
- **THEN** el sistema rechaza la creación y no modifica los datos históricos
