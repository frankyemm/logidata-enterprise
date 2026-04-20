import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_timestamp

# Configuración de Spark para soportar Delta Lake
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
# AWS Glue 4.0+ soporta Delta Lake nativamente si se le pasa el conf correcto en el Terraform
job = Job(glueContext)
job.init("sales_bronze_to_silver", {})

DB_NAME = "logidata_dev_bronze_db"
SILVER_BUCKET = "s3://logidata-dev-silver/sales"

def validate_data_quality(df, table_name: str) -> None:
    """Circuit Breaker: Detiene el pipeline si los datos son basura."""
    print(f"🧪 [DATA QUALITY] Evaluando {table_name}...")
    
    if df.count() == 0:
        raise ValueError(f"🚨 DQ ERROR: La tabla {table_name} está vacía.")

    # Validar llaves primarias
    pks = {"pedidos": "id_pedido", "clientes": "id_cliente", "catalogo": "id_producto"}
    if table_name in pks:
        nulos = df.filter(col(pks[table_name]).isNull()).count()
        if nulos > 0:
            raise ValueError(f"🚨 DQ ERROR: {nulos} registros con PK nula en {table_name}.")

    # Lógica de Negocio (Ej: Montos de pedidos válidos)
    if table_name == "pedidos":
        invalid_amounts = df.filter(col("monto") <= 0).count()
        if invalid_amounts > 0:
            raise ValueError(f"🚨 DQ ERROR: {invalid_amounts} pedidos con monto inválido.")

    print(f"✅ [DATA QUALITY] {table_name} pasó las pruebas.")

def process_table(table_name: str) -> None:
    print(f"🔄 Procesando {table_name}...")
    
    # 1. Leer de Bronze
    df = glueContext.create_dynamic_frame.from_catalog(database=DB_NAME, table_name=table_name).toDF()
    df_clean = df.dropDuplicates()

    # 2. Castear Fechas
    if "fecha" in df_clean.columns:
        df_clean = df_clean.withColumn("fecha", to_timestamp(col("fecha")))

    # 3. Data Quality Gate
    validate_data_quality(df_clean, table_name)

    # 4. Escribir a Silver en formato DELTA LAKE (Evolución de Esquemas habilitada)
    target_path = f"{SILVER_BUCKET}/{table_name}/"
    df_clean.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .save(target_path)
        
    print(f"💾 Guardado como Delta Table en {target_path}")

def main() -> None:
    # Dominio de Ventas (Sales)
    tables = ["clientes", "catalogo", "pedidos"]
    for t in tables:
        process_table(t)
    job.commit()

if __name__ == "__main__":
    main()
