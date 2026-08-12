## Purpose

Mantener el PMP validado actualizado desde SAIM de forma segura, auditable y resistente a fallas, sin duplicar la base histórica importada desde Excel.

## ADDED Requirements

### Requirement: Administración segura del token SAIM
El sistema SHALL permitir solo a administradores ingresar o renovar un token Bearer de SAIM. SHALL almacenarlo cifrado, SHALL confirmar su actualización sin volver a mostrar su valor y SHALL impedir que el token aparezca en respuestas, registros de auditoría, código fuente o repositorio.

#### Scenario: Renovación exitosa de token
- **WHEN** un administrador guarda un token Bearer válido
- **THEN** el sistema confirma la actualización sin devolver ni mostrar el token almacenado

#### Scenario: Usuario no administrador
- **WHEN** un usuario sin rol administrador intenta gestionar el token SAIM
- **THEN** el sistema deniega el acceso y no altera la credencial existente

### Requirement: Sincronización diaria protegida de órdenes PMP
Después de que la reconciliación de la Fase 1 sea aprobada, el sistema SHALL consultar diariamente la API `/backend/api/v1/ordenes` de SAIM a las 7:00 a. m. en `America/Bogota`, autenticada con Bearer. SHALL recorrer toda la paginación publicada y procesar exclusivamente las órdenes que cumplan la clasificación PMP confirmada.

#### Scenario: Sincronización paginada exitosa
- **WHEN** SAIM publica órdenes PMP en más de una página
- **THEN** el sistema consulta todas las páginas disponibles y registra el total de órdenes recibidas y válidas

#### Scenario: Sincronización antes de validar Fase 1
- **WHEN** la carga inicial no está reconciliada y aprobada
- **THEN** el sistema no ejecuta una sincronización que modifique el corte PMP

### Requirement: Mapeo y conservación de órdenes SAIM
El sistema SHALL registrar para cada orden PMP de SAIM su identificador externo, estado, área o especialidad, fecha de creación y horas-hombre planeadas una vez confirmado el campo exacto por la API. SHALL conservar las órdenes provenientes de Excel y vincular una orden SAIM equivalente por identificador externo en lugar de crear un duplicado.

#### Scenario: Orden SAIM equivalente a Excel
- **WHEN** SAIM entrega una orden con el mismo identificador externo que una orden importada desde JOSE.xlsx
- **THEN** el sistema vincula la orden existente con SAIM y conserva una sola orden PMP

#### Scenario: Orden PMP nueva desde SAIM
- **WHEN** SAIM entrega una orden PMP con identificador externo no existente
- **THEN** el sistema crea una orden nueva con origen SAIM y sus campos mapeados

### Requirement: Corte válido, snapshots y observabilidad de sincronización
El sistema SHALL crear una fotografía diaria del cumplimiento después de una sincronización exitosa. Ante token inválido, respuesta incompleta, error de paginación o error de SAIM, SHALL conservar sin cambios el último corte PMP válido y SHALL registrar el fallo. La interfaz SHALL mostrar la última sincronización, órdenes recibidas, registros PMP válidos y errores de consulta.

#### Scenario: Respuesta incompleta de SAIM
- **WHEN** una página esperada no contiene una respuesta válida o la consulta falla
- **THEN** el sistema marca la sincronización como fallida, preserva el último corte válido y muestra el error

#### Scenario: Fotografía diaria exitosa
- **WHEN** la sincronización completa finaliza correctamente
- **THEN** el sistema guarda una fotografía diaria de cumplimiento y actualiza el estado visible de la sincronización
