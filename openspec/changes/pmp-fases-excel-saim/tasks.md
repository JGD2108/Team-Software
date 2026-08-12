## 1. Modelo de datos y bases PMP

- [ ] 1.1 Crear las entidades y migraciones para áreas PMP, órdenes, importaciones, errores por fila, historial de cambios, personal, programación semanal, snapshots, configuración SAIM y ejecuciones de sincronización.
- [x] 1.2 Establecer restricciones e índices para identificar una orden PMP por identificador externo y vincular los orígenes Excel y SAIM sin duplicados.
- [ ] 1.3 Implementar servicios de auditoría e historial para cargas, cambios de órdenes y ejecuciones PMP sin registrar secretos.

## 2. Fase 1: importación y reconciliación de JOSE.xlsx

- [x] 2.1 Implementar el importador exclusivo de `añadidos/JOSE.xlsx` con mapeo posicional de sus columnas, incluida Especialidad como área y TiempoPlaneado como minutos planeados.
- [x] 2.2 Implementar validación por fila de identificador externo, área, estado y TiempoPlaneado positivo, con persistencia de válidas y reporte de inconsistencias.
- [x] 2.3 Implementar deduplicación de órdenes Excel y trazabilidad de fila/origen sin perder el registro de inconsistencias.
- [x] 2.4 Implementar la reconciliación de órdenes, horas planeadas y totales por área y estado contra las filas válidas de JOSE.xlsx.
- [x] 2.5 Exponer endpoints administrativos para ejecutar, consultar y aprobar la carga inicial, bloqueando SAIM mientras la reconciliación no esté aprobada.

## 3. Tablero y capacidad PMP

- [x] 3.1 Implementar el servicio de métricas PMP para órdenes y horas totales, finalizadas y pendientes, cumplimiento por área y global, con condición de meta estrictamente mayor que 90 %.
- [x] 3.2 Implementar administración de personal, turnos, horas disponibles y programación semanal por área PMP.
- [x] 3.3 Implementar cálculos de capacidad, brecha de horas y personal equivalente requerido por área, turno y periodo.
- [x] 3.4 Exponer endpoints del tablero PMP, filtros por área y datos de semáforo/alertas.
- [x] 3.5 Crear la interfaz PMP para carga, reconciliación, KPI, avance por área, alertas, programación y capacidad.

## 4. Retiro del registro manual

- [x] 4.1 Eliminar de la navegación y pantallas la creación de reportes manuales de falla, sin eliminar sus vistas históricas autorizadas.
- [x] 4.2 Deshabilitar o retirar el endpoint de creación manual y verificar que no pueda crear datos nuevos.

## 5. Fase 2: credenciales e integración SAIM

- [ ] 5.1 Implementar almacenamiento cifrado del token Bearer con clave de configuración externa, rotación administrativa y respuestas que nunca revelen el secreto.
- [ ] 5.2 Crear la pantalla administrativa que indique el estado y fecha de actualización del token, permita reemplazarlo y restrinja el acceso a administradores.
- [ ] 5.3 Implementar cliente SAIM para `/backend/api/v1/ordenes` con Bearer, zona `America/Bogota`, paginación completa, límites seguros y redacción de secretos en errores.
- [ ] 5.4 Confirmar con una respuesta autenticada el criterio de clasificación PMP y el campo de horas-hombre planeadas; configurar y validar ese mapeo antes de habilitar la sincronización continua.
- [ ] 5.5 Implementar upsert transaccional de órdenes PMP SAIM, enlace por identificador externo con Excel y conservación del último corte válido ante errores.
- [ ] 5.6 Implementar snapshots diarios, ejecución programada a las 7:00 a. m. Colombia, ejecución administrativa controlada y estado observable de sincronización.
- [ ] 5.7 Mostrar en la interfaz última sincronización, órdenes recibidas, registros PMP válidos y errores de consulta.

## 6. Pruebas y validación de entrega

- [x] 6.1 Crear pruebas de importación y reconciliación de JOSE.xlsx para totales globales y por área, estado y TiempoPlaneado.
- [x] 6.2 Crear pruebas para filas inválidas, identificadores ausentes/repetidos, exclusión de horas inválidas y condición de cumplimiento exactamente 90 %.
- [x] 6.3 Crear pruebas de capacidad, pendientes, alertas y cálculo de personal equivalente.
- [ ] 6.4 Crear pruebas SAIM para token inválido, respuesta incompleta, paginación, fallo sin alterar el último corte válido y orden equivalente a Excel sin duplicación.
- [x] 6.5 Crear pruebas de autorización y regresión que confirmen que el formulario y endpoint manual no permiten nuevas creaciones y que los históricos persisten.
- [ ] 6.6 Ejecutar las pruebas backend y la compilación frontend, y documentar la reconciliación aprobada antes de habilitar SAIM.
