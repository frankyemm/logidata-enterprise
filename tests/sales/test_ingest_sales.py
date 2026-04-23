import os
import boto3
from moto import mock_aws
from unittest.mock import patch
from src.domains.sales.ingest_sales import upload_sales_data

@mock_aws
def test_upload_sales_data_success(tmp_path):
    """
    Verifica que el script de ingesta lee los CSV locales y los sube 
    correctamente a las rutas particionadas en S3 (Bronze).
    """
    # 1. SETUP: Variables de entorno y S3 en memoria
    os.environ["BRONZE_BUCKET"] = "test-bronze-bucket"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="test-bronze-bucket")

    # 2. ARRANGE: Crear estructura de carpetas y CSVs falsos en un directorio temporal
    data_dir = tmp_path / "src" / "data"
    data_dir.mkdir(parents=True)
    
    (data_dir / "clientes.csv").write_text("id,nombre\n1,TestCliente")
    (data_dir / "catalogo.csv").write_text("id,producto\n1,TestProducto")
    (data_dir / "pedidos.csv").write_text("id,monto\n1,100")

    # 3. ACT: Engañamos a os.getcwd() para que lea nuestro directorio temporal y ejecutamos
    with patch("os.getcwd", return_value=str(tmp_path)):
        upload_sales_data()

    # 4. ASSERT: Verificamos que los 3 archivos llegaron al bucket S3 simulado
    objects = s3.list_objects_v2(Bucket="test-bronze-bucket")
    assert "Contents" in objects, "No se subió ningún archivo a S3"
    
    claves_subidas = [obj["Key"] for obj in objects["Contents"]]
    
    assert "sales/clientes/clientes.csv" in claves_subidas
    assert "sales/catalogo/catalogo.csv" in claves_subidas
    assert "sales/pedidos/pedidos.csv" in claves_subidas
