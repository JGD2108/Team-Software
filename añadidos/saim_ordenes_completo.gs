/**
 * Referencia entregada por el usuario: exporta todas las órdenes SAIM a Hoja8,
 * filtradas por FechaCreacion y con fechas ajustadas a Colombia.
 */
function fechayhoradefirmas() {
  const libro = SpreadsheetApp.openById("1alQngVlKuJn6xyBswZ9SOFu5i-HWKeVkdMVYIuHHs8Y");
  const hojaDestino = libro.getSheetByName("Hoja8");
  const fechaCorteFiltro = new Date("2024-01-01T00:00:00.000Z");
  const zonaHorariaColombia = "America/Bogota";
  const filasPorPagina = 10000;
  const limiteMaximoFilas = 25000;
  const limiteMaximoPaginas = Math.ceil(limiteMaximoFilas / filasPorPagina);
  const notify = (message, isError = false) => {
    try {
      // SpreadsheetApp.getUi().alert(message);
    } catch (e) {
      Logger.log(message);
      if (isError) {
        // MailApp.sendEmail("your_email@ejemplo.com", "Alerta de Script de Google Sheets", message);
      }
    }
  };
  const apiToken = PropertiesService.getScriptProperties().getProperty("MY_API_TOKEN");
  if (!apiToken) {
    notify("Error: No se encontró el token de API. Por favor, ejecuta la función 'setApiToken()' primero. La hoja no se modificará.", true);
    return;
  }

  const baseApiUrl = "https://saimweb.apping.com.co/backend/api/v1/ordenes";
  const options = {
    method: "get",
    muteHttpExceptions: true,
    headers: { Authorization: "Bearer " + apiToken, "Content-Type": "application/json" },
  };
  let todosLosRegistros = [];
  let apiFetchErrorOccurred = false;

  try {
    let paginaActual = 1;
    let totalFilasAPI = 0;
    let fetchedRowsCount = 0;
    do {
      const apiUrlConPaginacion = `${baseApiUrl}?rows=${filasPorPagina}&page=${paginaActual}`;
      Logger.log(`Obteniendo datos de la página ${paginaActual}: ${apiUrlConPaginacion}`);
      const respuesta = UrlFetchApp.fetch(apiUrlConPaginacion, options);
      const codigoEstado = respuesta.getResponseCode();
      const textoRespuesta = respuesta.getContentText();
      if (codigoEstado >= 200 && codigoEstado < 300) {
        const datosParseados = JSON.parse(textoRespuesta);
        const registrosDePagina = datosParseados.data;
        if (paginaActual === 1) totalFilasAPI = datosParseados.total;
        if (Array.isArray(registrosDePagina) && registrosDePagina.length > 0) {
          todosLosRegistros.push(...registrosDePagina);
          fetchedRowsCount += registrosDePagina.length;
          paginaActual++;
        } else {
          Logger.log("No se encontraron más registros en la página actual o la propiedad 'data' está vacía.");
          break;
        }
      } else {
        notify(`La API devolvió un error (Código: ${codigoEstado}) en la página ${paginaActual}. Deteniendo proceso. Los datos existentes en la hoja no se modificarán.`, true);
        Logger.log(`Error de la API en página ${paginaActual}: Código ${codigoEstado}. Respuesta: ${textoRespuesta}. No se modificará la hoja.`);
        apiFetchErrorOccurred = true;
        break;
      }
      if (totalFilasAPI > 0 && fetchedRowsCount >= totalFilasAPI) break;
      if (fetchedRowsCount >= limiteMaximoFilas || paginaActual > limiteMaximoPaginas) break;
      Utilities.sleep(50);
    } while (!apiFetchErrorOccurred);
    if (apiFetchErrorOccurred) return;

    const registrosFiltrados = todosLosRegistros.filter((registro) => {
      return registro.FechaCreacion && new Date(registro.FechaCreacion) > fechaCorteFiltro;
    });
    if (registrosFiltrados.length === 0) {
      notify("No se encontraron registros que cumplan con el criterio de filtro de fecha. La hoja no se modificará.");
      return;
    }
    const headers = Object.keys(registrosFiltrados[0]);
    const datosParaHoja = [headers];
    registrosFiltrados.forEach((registro) => {
      datosParaHoja.push(headers.map((header) => {
        let value = registro[header];
        if (header === "FechaModificacion" || header === "FechaCreacion" || header.includes("Fecha") || header.includes("fecha")) {
          try {
            const dateObj = new Date(value);
            if (!isNaN(dateObj.getTime())) value = Utilities.formatDate(dateObj, zonaHorariaColombia, "yyyy-MM-dd HH:mm:ss");
          } catch (e) { Logger.log(`Advertencia: fecha inválida en '${header}': ${e.message}`); }
        }
        if (typeof value === "object" && value !== null) {
          try { value = JSON.stringify(value); } catch (e) { value = String(value); }
        }
        return value;
      }));
    });
    if (hojaDestino) {
      hojaDestino.clearContents();
      hojaDestino.getRange(1, 1, datosParaHoja.length, datosParaHoja[0].length).setValues(datosParaHoja);
      notify(`Datos exportados exitosamente a la hoja 'Hoja8'. Total de filas: ${datosParaHoja.length - 1}`);
    } else {
      notify("Error: La hoja 'Hoja8' no se encontró. No se pudo exportar.", true);
    }
  } catch (e) {
    notify(`Error inesperado durante la ejecución del script: ${e.message}`, true);
    Logger.log(`Error: ${e.message}`);
  }
}

/** Guarda el token de SAIM en Script Properties. */
function setApiToken() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.prompt("Configurar Token de API", "Por favor, ingresa tu token de API:", ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() === ui.Button.OK) {
    const token = response.getResponseText();
    if (token) {
      PropertiesService.getScriptProperties().setProperty("MY_API_TOKEN", token);
      ui.alert("Token de API guardado exitosamente.");
    } else {
      ui.alert("No se ingresó ningún token. El token no fue guardado.");
    }
  } else {
    ui.alert("Configuración de token cancelada.");
  }
}
