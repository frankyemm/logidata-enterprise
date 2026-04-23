from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, year, month, dayofmonth, hour, dayofweek

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init("sales_silver_to_gold", {})

SILVER_BUCKET = "s3://logidata-dev-silver/sales"
GOLD_BUCKET = "s3://logidata-dev-gold/sales"

def main() -> None:
    print("🚀 [SALES DOMAIN] Iniciando transformación Silver (Delta) -> Gold (Parquet)")

    # 1. Leer Silver (Aún es Delta Lake, mantenemos el ACID aquí)
    df_pedidos = spark.read.format("delta").load(f"{SILVER_BUCKET}/pedidos/")
    df_clientes = spark.read.format("delta").load(f"{SILVER_BUCKET}/clientes/")
    df_catalogo = spark.read.format("delta").load(f"{SILVER_BUCKET}/catalogo/")

    # 2. DIMENSIONES (Escribimos a Parquet plano para Redshift COPY)
    print("📦 Construyendo dimensiones...")
    dim_cliente = df_clientes.dropDuplicates().dropna(subset=["id_cliente"])
    dim_cliente.write.format("parquet").mode("overwrite").save(f"{GOLD_BUCKET}/dim_cliente/")

    dim_producto = df_catalogo.dropDuplicates().dropna(subset=["id_producto"])
    dim_producto.write.format("parquet").mode("overwrite").save(f"{GOLD_BUCKET}/dim_producto/")

    dim_tiempo = df_pedidos.select("fecha").dropna().distinct() \
        .withColumn("anio", year(col("fecha"))) \
        .withColumn("mes", month(col("fecha"))) \
        .withColumn("dia", dayofmonth(col("fecha"))) \
        .withColumn("hora", hour(col("fecha"))) \
        .withColumn("dia_semana", dayofweek(col("fecha")))
    dim_tiempo.write.format("parquet").mode("overwrite").save(f"{GOLD_BUCKET}/dim_tiempo/")

    # 3. HECHOS (FACT TABLE)
    print("📊 Construyendo tabla de hechos...")
    df_fact = df_pedidos.select(
        col("id_pedido"), col("id_cliente"), col("id_producto"), 
        col("fecha"), col("monto"), col("estado")
    )
    df_fact.write.format("parquet").mode("overwrite").save(f"{GOLD_BUCKET}/fact_pedidos/")

    print("🎯 Transformación a Gold completada exitosamente.")
    job.commit()

if __name__ == "__main__":
    main()
