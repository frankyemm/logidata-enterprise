import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_timestamp

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init("sales_bronze_to_silver", {})

SILVER_BUCKET = "s3://logidata-dev-silver/sales"
BRONZE_PREFIX = "s3://logidata-dev-bronze/sales"

def validate_data_quality(df, table_name: str) -> None:
    print(f"🧪 [DATA QUALITY] Evaluando {table_name}...")
    if df.count() == 0:
        raise ValueError(f"🚨 DQ ERROR: La tabla {table_name} está vacía.")
        
    pks = {"pedidos": "id_pedido", "clientes": "id_cliente", "catalogo": "id_producto"}
    if table_name in pks:
        nulos = df.filter(col(pks[table_name]).isNull()).count()
        if nulos > 0:
            raise ValueError(f"🚨 DQ ERROR: {nulos} registros con PK nula en {table_name}.")
            
    if table_name == "pedidos":
        invalid_amounts = df.filter(col("monto") <= 0).count()
        if invalid_amounts > 0:
            raise ValueError(f"🚨 DQ ERROR: {invalid_amounts} pedidos con monto inválido.")
    print(f"✅ [DATA QUALITY] {table_name} pasó las pruebas.")

def process_table(table_name: str) -> None:
    print(f"🔄 Procesando {table_name}...")
    
    # EL FIX: Ignoramos el Catálogo de Glue que adivinó mal el CSV.
    # Leemos nativamente de S3 forzando el header.
    source_path = f"{BRONZE_PREFIX}/{table_name}/"
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(source_path)
    
    df_clean = df.dropDuplicates()

    if "fecha" in df_clean.columns:
        df_clean = df_clean.withColumn("fecha", to_timestamp(col("fecha")))

    validate_data_quality(df_clean, table_name)

    target_path = f"{SILVER_BUCKET}/{table_name}/"
    df_clean.write \
        .format("delta") \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .save(target_path)
        
    print(f"💾 Guardado como Delta Table en {target_path}")

def main() -> None:
    tables = ["clientes", "catalogo", "pedidos"]
    for t in tables:
        process_table(t)
    job.commit()

if __name__ == "__main__":
    main()
