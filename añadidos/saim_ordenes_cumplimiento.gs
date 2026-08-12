/**
 * Referencia entregada por el usuario: exporta órdenes SAIM a BASEAPI y BD_SAIM.
 * Esta es la copia canónica; el mismo bloque fue compartido dos veces.
 */
function exportarDatosDeApiConPaginacion() {
  const libro = SpreadsheetApp.openById("1alQngVlKuJn6xyBswZ9SOFu5i-HWKeVkdMVYIuHHs8Y");
  let hojaDestino = libro.getSheetByName("BASEAPI");
  let hojaCumplimiento = libro.getSheetByName("BD_SAIM");
  const fechaCorteFiltro = new Date("2024-01-01T00:00:00.000Z");
  const zonaHorariaColombia = "America/Bogota";
  const filasPorPagina = 10000;
  const limiteMaximoFilas = 40000;
  const limiteMaximoPaginas = Math.ceil(limiteMaximoFilas / filasPorPagina);
  const encabezadosDeseados = [
    "Orden", "Titulo", "Descripcion", "FechaCreacion", "Activo", "DescripcionActivo", "Especialidad", "Etapa",
    "SolicitudTipo", "Usuario_Autor", "Usuario_Supervisor", "Usuario_Solicitante", "OrdenTipo", "Prioridad",
    "Solicitud", "FirmaResponsable", "FirmaSupervisor", "FirmaSolicitante",
  ];
  const encabezadosCumplimiento = [
    "Orden", "Estado", "Especialidad", "Fecha Creación", "Activo", "Nombre de Activo", "Título",
    "Firma Responsable", "Firma Supervisor", "Firma Coordinador",
  ];
  const apiToken = PropertiesService.getScriptProperties().getProperty("MY_API_TOKEN");
  if (!apiToken) {
    Logger.log("Error: No se encontró el token de API. BASEAPI y BD_SAIM no se modificarán.");
    return;
  }
  const baseApiUrl = "https://saimweb.apping.com.co/backend/api/v1/ordenes";
  const options = { method: "get", muteHttpExceptions: true, headers: { Authorization: "Bearer " + apiToken, "Content-Type": "application/json" } };
  let todosLosRegistros = [];
  let apiFetchErrorOccurred = false;
  try {
    let paginaActual = 1;
    let totalFilasAPI = 0;
    do {
      const apiUrlConPaginacion = `${baseApiUrl}?rows=${filasPorPagina}&page=${paginaActual}`;
      const respuesta = UrlFetchApp.fetch(apiUrlConPaginacion, options);
      const codigoEstado = respuesta.getResponseCode();
      if (codigoEstado < 200 || codigoEstado >= 300) {
        Logger.log(`Error de API en página ${paginaActual}: ${codigoEstado}. Las hojas no se modificarán.`);
        apiFetchErrorOccurred = true;
        break;
      }
      const datosParseados = JSON.parse(respuesta.getContentText());
      const registrosDePagina = datosParseados.data;
      if (paginaActual === 1) totalFilasAPI = datosParseados.total;
      if (!Array.isArray(registrosDePagina) || registrosDePagina.length === 0) break;
      todosLosRegistros.push(...registrosDePagina);
      paginaActual++;
      if (todosLosRegistros.length >= limiteMaximoFilas || paginaActual > limiteMaximoPaginas) break;
      Utilities.sleep(10);
    } while (todosLosRegistros.length < totalFilasAPI && paginaActual <= limiteMaximoPaginas && !apiFetchErrorOccurred);
    if (apiFetchErrorOccurred) return;

    const filasFiltradasParaHoja = todosLosRegistros.flatMap((item) => {
      const fecha = item.FechaCreacion ? new Date(item.FechaCreacion.replace(" ", "T")) : null;
      if (!fecha || fecha <= fechaCorteFiltro) return [];
      const fechaCreacion = Utilities.formatDate(fecha, zonaHorariaColombia, "dd-MM-yyyy");
      return [[
        (item.IdT || "").toString().toUpperCase(), (item.Titulo || "").toString().toUpperCase(),
        (item.Descripcion || "").toString().toUpperCase(), fechaCreacion,
        (item.IdTActivo || "").toString().toUpperCase(), (item.DescripcionActivo || "").toString().toUpperCase(),
        (item.IdTEspecialidad || "").toString().toUpperCase(), (item.IdTEtapa || "").toString().toUpperCase(),
        (item.IdTSolicitudTipo || "").toString().toUpperCase(), (item.Usuario_Autor || "").toString().toUpperCase(),
        (item.Usuario_Aprobador1 || "").toString().toUpperCase(), (item.Usuario_Aprobador2 || "").toString().toUpperCase(),
        (item.IdTOrdenTipo || "").toString().toUpperCase(), (item.IdTPrioridad || "").toString().toUpperCase(),
        (item.IdTSolicitud || "").toString().toUpperCase(), (item.FirmaResponsable || "0").toString().toUpperCase(),
        (item.FirmaAprobador1 || "0").toString().toUpperCase(), (item.FirmaAprobador2 || "0").toString().toUpperCase(),
      ]];
    });
    if (filasFiltradasParaHoja.length === 0) return;
    if (!hojaDestino) hojaDestino = libro.insertSheet("BASEAPI");
    if (!hojaCumplimiento) hojaCumplimiento = libro.insertSheet("BD_SAIM");
    hojaDestino.clearContents();
    hojaDestino.appendRow(encabezadosDeseados);
    hojaCumplimiento.clearContents();
    hojaCumplimiento.appendRow(encabezadosCumplimiento);
    hojaDestino.getRange(2, 1, filasFiltradasParaHoja.length, filasFiltradasParaHoja[0].length).setValues(filasFiltradasParaHoja);
    const ArrayCUMPLIMIENTO = filasFiltradasParaHoja.map((fila) => [fila[0], fila[7], fila[6], fila[3], fila[4], fila[5], fila[1], fila[15], fila[16], fila[17]]);
    hojaCumplimiento.getRange(2, 1, ArrayCUMPLIMIENTO.length, ArrayCUMPLIMIENTO[0].length).setValues(ArrayCUMPLIMIENTO);
    Logger.log(`Exportación de órdenes completada. ${filasFiltradasParaHoja.length} registros filtrados.`);
  } catch (e) {
    Logger.log("Error inesperado: " + e.toString() + ". Las hojas no se modificarán.");
  }
}
