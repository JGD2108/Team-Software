/**
 * Referencia entregada por el usuario: exporta solicitudes SAIM a BASEST.
 */
function exportarDatosDeApiConPaginacionst() {
  const libro = SpreadsheetApp.openById("1alQngVlKuJn6xyBswZ9SOFu5i-HWKeVkdMVYIuHHs8Y");
  let hojaDestino = libro.getSheetByName("BASEST");
  const fechaCorteFiltro = new Date("2023-01-01T00:00:00.000Z");
  const zonaHorariaColombia = "America/Bogota";
  const filasPorPagina = 10000;
  const limiteMaximoFilas = 40000;
  const limiteMaximoPaginas = Math.ceil(limiteMaximoFilas / filasPorPagina);
  const encabezadosFinales = [
    "Solicitud", "Titulo", "Descripcion", "FechaCreacion", "Activo", "DescripcionActivo",
    "Ordenes", "Especialidad", "Prioridad", "SolicitudTipo", "Estado", "Usuario_Autor",
    "Usuario_Supervisor", "Usuario_Solicitante", "FirmaSupervisor", "FirmaSolicitante",
  ];
  const mapeoColumnasAPI = {
    Solicitud: "IdT", Titulo: "Titulo", Descripcion: "Descripcion", FechaCreacion: "FechaCreacion",
    Activo: "IdTActivo", DescripcionActivo: "DescripcionActivo", Ordenes: "IdTOrden",
    Especialidad: "IdTEspecialidad", Prioridad: "IdTPrioridad", SolicitudTipo: "IdTSolicitudTipo",
    Estado: "Estado", Usuario_Autor: "Usuario_Autor", Usuario_Supervisor: "Usuario_Aprobador1",
    Usuario_Solicitante: "Usuario_Aprobador2", FirmaSupervisor: "FirmaAprobador1", FirmaSolicitante: "FirmaAprobador2",
  };
  const apiToken = PropertiesService.getScriptProperties().getProperty("MY_API_TOKEN");
  if (!apiToken) {
    Logger.log("Error: No se encontró el token de API. La hoja 'BASEST' no se modificará.");
    return;
  }
  const options = { method: "get", muteHttpExceptions: true, headers: { Authorization: "Bearer " + apiToken, "Content-Type": "application/json" } };
  const baseApiUrl = "https://saimweb.apping.com.co/backend/api/v1/solicitudes";
  let todosLosRegistros = [];
  let apiFetchErrorOccurred = false;
  try {
    let paginaActual = 1;
    let totalFilasAPI = 0;
    do {
      const respuesta = UrlFetchApp.fetch(`${baseApiUrl}?rows=${filasPorPagina}&page=${paginaActual}`, options);
      if (respuesta.getResponseCode() < 200 || respuesta.getResponseCode() >= 300) {
        Logger.log(`Error de API: ${respuesta.getResponseCode()}. No se modifica BASEST.`);
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
      Utilities.sleep(50);
    } while (todosLosRegistros.length < totalFilasAPI && paginaActual <= limiteMaximoPaginas && !apiFetchErrorOccurred);
    if (apiFetchErrorOccurred) return;

    const filasParaHoja = todosLosRegistros.flatMap((item) => {
      const fecha = item.FechaCreacion ? new Date(item.FechaCreacion.replace(" ", "T")) : null;
      if (!fecha || fecha <= fechaCorteFiltro) return [];
      return [encabezadosFinales.map((encabezado) => {
        if (encabezado === "FechaCreacion") return Utilities.formatDate(fecha, zonaHorariaColombia, "dd-MM-yyyy");
        const valor = item[mapeoColumnasAPI[encabezado]];
        return valor === undefined || valor === null ? "" : valor.toString().toUpperCase();
      })];
    });
    if (filasParaHoja.length === 0) return;
    if (!hojaDestino) hojaDestino = libro.insertSheet("BASEST");
    hojaDestino.clearContents();
    hojaDestino.appendRow(encabezadosFinales);
    hojaDestino.getRange(2, 1, filasParaHoja.length, filasParaHoja[0].length).setValues(filasParaHoja);
    Logger.log(`Exportación de solicitudes completada. ${filasParaHoja.length} registros filtrados.`);
  } catch (e) {
    Logger.log("Error inesperado en la conexión o procesamiento: " + e.toString() + ". BASEST no se modificará.");
  }
}
