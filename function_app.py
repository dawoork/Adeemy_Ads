import azure.functions as func
import logging
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.oauth2 import service_account
import os
import json
from azure.storage.blob import BlobServiceClient

def get_ga4_client():
    credentials_info = json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON'])
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    client = BetaAnalyticsDataClient(credentials=credentials)
    return client

def upload_to_blob_storage(data):
    blob_service_client = BlobServiceClient.from_connection_string(os.environ['BLOB_CONNECTION_STRING'])
    container_name = os.environ['BLOB_CONTAINER_NAME']
    blob_client = blob_service_client.get_blob_client(container=container_name, blob='ga4_data.json')
    blob_client.upload_blob(data, overwrite=True)


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="AdeemyFunctions")
@app.route(route="AdeemyFunctions")
def AdeemyFunctions(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Función HTTP de Python procesó una solicitud.')

    try:
        client = get_ga4_client()
        response = client.run_report(request={
            "property": f"properties/{os.environ['GA4_PROPERTY_ID']}",
            "dimensions": [{"name": "city"}],
            "metrics": [{"name": "activeUsers"}],
            "date_ranges": [{"start_date": "7daysAgo", "end_date": "today"}]
        })
        # Procesar la respuesta
        data = []
        for row in response.rows:
            data.append({
                "city": row.dimension_values[0].value,
                "activeUsers": row.metric_values[0].value
            })
        # Convertir datos a JSON
        data_json = json.dumps(data)
        # Subir datos a Blob Storage
        upload_to_blob_storage(data_json)
        return func.HttpResponse("Datos subidos a Blob Storage.", status_code=200)
    except Exception as e:
        logging.error(f"Error al obtener datos de GA4: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)
