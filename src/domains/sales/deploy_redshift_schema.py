import boto3
import time

client = boto3.client('redshift-data', region_name='us-east-1')

# Estas variables deben coincidir con tu Terraform
WORKGROUP_NAME = 'logidata-dev-workgroup'
DATABASE_NAME = 'analytics'

# TODO: Cuando despliegues, pon aquí el ARN del rol de Redshift de tu cuenta
IAM_ROLE_ARN = 'arn:aws:iam::427297225199:role/logidata-dev-redshift-role'

SQL_COMMANDS = f"""
DROP TABLE IF EXISTS fact_pedidos;
DROP TABLE IF EXISTS dim_cliente;
DROP TABLE IF EXISTS dim_producto;
DROP TABLE IF EXISTS dim_tiempo;

CREATE TABLE dim_cliente (id_cliente VARCHAR(10) PRIMARY KEY, nombre VARCHAR(100), zona VARCHAR(50), tipo_cliente VARCHAR(50));
CREATE TABLE dim_producto (id_producto VARCHAR(10) PRIMARY KEY, categoria VARCHAR(50), precio FLOAT8, tipo_entrega VARCHAR(50));
CREATE TABLE dim_tiempo (fecha TIMESTAMP PRIMARY KEY, anio INTEGER, mes INTEGER, dia INTEGER, hora INTEGER, dia_semana INTEGER);

-- Data Mesh: Tabla de hechos pura del dominio de Ventas (6 columnas)
CREATE TABLE fact_pedidos (
    id_pedido VARCHAR(10) PRIMARY KEY, 
    id_cliente VARCHAR(10) REFERENCES dim_cliente(id_cliente), 
    id_producto VARCHAR(10) REFERENCES dim_producto(id_producto), 
    fecha TIMESTAMP REFERENCES dim_tiempo(fecha), 
    monto FLOAT8, 
    estado VARCHAR(50)
);

COPY dim_cliente FROM 's3://logidata-dev-gold/sales/dim_cliente/' IAM_ROLE '{IAM_ROLE_ARN}' FORMAT AS PARQUET;
COPY dim_producto FROM 's3://logidata-dev-gold/sales/dim_producto/' IAM_ROLE '{IAM_ROLE_ARN}' FORMAT AS PARQUET;
COPY dim_tiempo FROM 's3://logidata-dev-gold/sales/dim_tiempo/' IAM_ROLE '{IAM_ROLE_ARN}' FORMAT AS PARQUET;
COPY fact_pedidos FROM 's3://logidata-dev-gold/sales/fact_pedidos/' IAM_ROLE '{IAM_ROLE_ARN}' FORMAT AS PARQUET;
"""

def execute_sql():
    print("🚀 Enviando DDL y COPY a Redshift vía Data API (Red Privada)...")
    response = client.execute_statement(
        WorkgroupName=WORKGROUP_NAME,
        Database=DATABASE_NAME,
        Sql=SQL_COMMANDS
    )
    query_id = response['Id']
    print(f"⏳ Ejecutando Query ID: {query_id}...")
    
    while True:
        status = client.describe_statement(Id=query_id)
        if status['Status'] in ['FINISHED', 'FAILED', 'ABORTED']:
            if status['Status'] == 'FINISHED':
                print("✅ [EXITO] Tablas creadas y cargadas en Redshift.")
            else:
                print(f"❌ [ERROR] {status['Error']}")
            break
        time.sleep(2)

if __name__ == "__main__":
    execute_sql()
