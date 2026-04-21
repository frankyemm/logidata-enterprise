from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator
from airflow.operators.bash import BashOperator

# Argumentos corporativos: Reintentos y SLAs
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False, # En prod, esto enviaría un correo o Slack
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'sales_domain_pipeline',
    default_args=default_args,
    description='Pipeline del Dominio de Ventas: Ingesta -> Delta Silver -> Delta Gold',
    schedule='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['sales', 'data-mesh', 'lakehouse'],
) as dag:

    # 1. Ingesta (Simulada desde script Python)
    ingest_sales = BashOperator(
        task_id='ingest_sales_to_bronze',
        # Llamamos al script del dominio específico
        bash_command='python3 /opt/airflow/src/domains/sales/ingest_sales.py',
    )

    # 2. Descubrimiento de Metadatos
    run_sales_crawler = GlueCrawlerOperator(
        task_id='run_sales_bronze_crawler',
        config={'Name': 'logidata-dev-bronze-crawler'},
        aws_conn_id='aws_default',
        region_name='us-east-1',
        wait_for_completion=True,
    )

    # 3. Transformación a Silver (Data Quality & Delta Lake)
    bronze_to_silver_sales = GlueJobOperator(
        task_id='glue_bronze_to_silver_sales',
        job_name='logidata-dev-sales-bronze-to-silver',
        aws_conn_id='aws_default',
        region_name='us-east-1',
        wait_for_completion=True,
    )

    # 4. Transformación a Gold (Modelo Dimensional en Delta)
    silver_to_gold_sales = GlueJobOperator(
        task_id='glue_silver_to_gold_sales',
        job_name='logidata-dev-sales-silver-to-gold',
        aws_conn_id='aws_default',
        region_name='us-east-1',
        wait_for_completion=True,
    )

    # DAG Topology (Strict Dependencies)
    ingest_sales >> run_sales_crawler >> bronze_to_silver_sales >> silver_to_gold_sales

