import os
import azure.functions as func
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
import json
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="GA")
@app.route(route="GA")
def GA(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing GA4 data extraction.')

    # Cargar las credenciales desde la variable de entorno
    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not credentials_json:
        logging.error("La variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON no está establecida.")
        return func.HttpResponse(
            "Error: Las credenciales de Google no están configuradas.",
            status_code=500
        )
    try:
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
    except json.JSONDecodeError as e:
        logging.error(f"Error al parsear las credenciales JSON: {e}")
        return func.HttpResponse(
            "Error al parsear las credenciales de Google.",
            status_code=500
        )
    except Exception as e:
        logging.error(f"Error al cargar las credenciales: {e}")
        return func.HttpResponse(
            "Error al cargar las credenciales de Google.",
            status_code=500
        )

    # Crear el cliente de GA4
    try:
        client = BetaAnalyticsDataClient(credentials=credentials)
    except Exception as e:
        logging.error(f"Error al crear el cliente de GA4: {e}")
        return func.HttpResponse(
            "Error al inicializar el cliente de GA4.",
            status_code=500
        )

    # Obtener el ID de la propiedad desde la variable de entorno
    property_id = os.getenv("GA4_PROPERTY_ID")
    if not property_id:
        logging.error("La variable de entorno GA4_PROPERTY_ID no está establecida.")
        return func.HttpResponse(
            "Error: El ID de la propiedad de GA4 no está configurado.",
            status_code=500
        )

    # Crear la solicitud a GA4
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[{"name": "city"}],
        metrics=[{"name": "activeUsers"}]
    )

    # Ejecutar la solicitud
    try:
        response = client.run_report(request)
    except Exception as e:
        logging.error(f"Error al ejecutar la solicitud a GA4: {e}")
        return func.HttpResponse(
            "Error al obtener datos de GA4.",
            status_code=500
        )

    # Procesar y devolver los datos
    data = []
    for row in response.rows:
        record = {}
        for dimension_header, dimension_value in zip(response.dimension_headers, row.dimension_values):
            record[dimension_header.name] = dimension_value.value
        for metric_header, metric_value in zip(response.metric_headers, row.metric_values):
            record[metric_header.name] = metric_value.value
        data.append(record)

    return func.HttpResponse(
        json.dumps(data),
        status_code=200,
        mimetype="application/json"
    )
