import base64
import json
import os
import uuid
import boto3
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Procesa eventos de Kinesis, filtra alertas de temperatura y guarda en DynamoDB."""
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    table_name = os.getenv("DYNAMO_TABLE", "logidata-dev-events")
    table = dynamodb.Table(table_name)

    records_processed = 0

    for record in event.get("Records",[]):
        try:
            payload_b64 = record["kinesis"]["data"]
            payload_str = base64.b64decode(payload_b64).decode("utf-8")
            data = json.loads(payload_str)

            if data.get("evento") == "TEMP_CRITICA":
                table.put_item(
                    Item={
                        "id": str(uuid.uuid4()),
                        "vehiculo": data["vehiculo"],
                        "timestamp": data["timestamp"],
                        "temperatura": str(data["temperatura"]),
                        "latitud": str(data["latitud"]),
                        "longitud": str(data["longitud"]),
                    }
                )
            records_processed += 1
        except Exception as e:
            print(f"Error procesando registro: {e}")

    return {"statusCode": 200, "body": f"Procesados {records_processed} registros"}
