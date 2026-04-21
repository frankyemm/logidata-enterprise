import os
import json
import base64
import boto3
from moto import mock_aws

# Configuramos el entorno ANTES de importar la lambda
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["DYNAMO_TABLE"] = "test-events-table"

from src.domains.logistics.lambda_iot import lambda_handler

@mock_aws
def test_lambda_filtra_temp_critica():
    """Test unitario: Verifica que la Lambda solo guarda eventos TEMP_CRITICA."""
    
    # 1. Setup: Crear tabla DynamoDB en memoria
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName=os.environ["DYNAMO_TABLE"],
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )

    # 2. Arrange: Crear evento falso de Kinesis
    evento_ok = {"vehiculo": "V1", "timestamp": "2026-01-01", "temperatura": 10, "latitud": 0, "longitud": 0, "evento": "OK"}
    evento_malo = {"vehiculo": "V2", "timestamp": "2026-01-01", "temperatura": 25, "latitud": 0, "longitud": 0, "evento": "TEMP_CRITICA"}
    
    b64_ok = base64.b64encode(json.dumps(evento_ok).encode("utf-8")).decode("utf-8")
    b64_malo = base64.b64encode(json.dumps(evento_malo).encode("utf-8")).decode("utf-8")

    event = {
        "Records":[
            {"kinesis": {"data": b64_ok}},
            {"kinesis": {"data": b64_malo}}
        ]
    }

    # 3. Act: Ejecutar la Lambda
    response = lambda_handler(event, None)

    # 4. Assert: Verificar resultados
    assert response["statusCode"] == 200
    assert "Procesados 2 registros" in response["body"]

    # Verificar que SOLO se guardó el evento malo en DynamoDB
    items = table.scan()["Items"]
    assert len(items) == 1
    assert items[0]["vehiculo"] == "V2"
