import os
import csv
import json
import time
import boto3

# Nombre del stream (ajustado a la nomenclatura de tu infraestructura actual)
STREAM_NAME = os.getenv("KINESIS_STREAM", "logidata-dev-iot-stream")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

def simulate():
    print(f"🚀 Iniciando simulador IoT hacia Kinesis Stream: {STREAM_NAME}...")
    
    # Navegamos dinámicamente: src/domains/logistics/ -> src/data/sensores.csv
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_path = os.path.join(base_path, "data", "sensores.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ ERROR: No se encontró el archivo {csv_path}")
        return

    kinesis = boto3.client('kinesis', region_name=REGION)
    
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            payload = json.dumps(row)
            try:
                response = kinesis.put_record(
                    StreamName=STREAM_NAME,
                    Data=payload,
                    PartitionKey=row['vehiculo']
                )
                print(f"📡 Enviado: {row['vehiculo']} - {row['evento']} - Seq: {response['SequenceNumber']}")
            except Exception as e:
                print(f"❌ Error enviando registro: {e}")
            
            # Simulamos el delay de la red celular de un camión real
            time.sleep(1) 

if __name__ == "__main__":
    simulate()
