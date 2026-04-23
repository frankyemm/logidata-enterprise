import os
import boto3
import json
from moto import mock_aws
from unittest.mock import patch, mock_open
from src.domains.logistics.simulator import simulate

@mock_aws
def test_simulate_sends_records_to_kinesis():
    """
    Verifica que el simulador lee un CSV y envía los eventos a Kinesis.
    """
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    
    kinesis = boto3.client("kinesis", region_name="us-east-1")
    kinesis.create_stream(StreamName="test-iot-stream", ShardCount=1)
    
    csv_data = "vehiculo,timestamp,latitud,longitud,temperatura,evento\nV1,2026-01-01,0,0,25,TEMP_CRITICA\n"
    
    # EL FIX: Mockeamos también la constante STREAM_NAME dentro del módulo simulator
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=csv_data)), \
         patch("time.sleep", return_value=None), \
         patch("src.domains.logistics.simulator.STREAM_NAME", "test-iot-stream"):
        
        simulate()
        
    response = kinesis.describe_stream(StreamName="test-iot-stream")
    shard_id = response["StreamDescription"]["Shards"][0]["ShardId"]
    
    iterator = kinesis.get_shard_iterator(
        StreamName="test-iot-stream",
        ShardId=shard_id,
        ShardIteratorType="TRIM_HORIZON"
    )["ShardIterator"]
    
    records = kinesis.get_records(ShardIterator=iterator)["Records"]
    
    assert len(records) == 1, "No se insertó el registro en Kinesis"
    payload = json.loads(records[0]["Data"].decode("utf-8"))
    
    assert payload["vehiculo"] == "V1"
    assert payload["evento"] == "TEMP_CRITICA"
