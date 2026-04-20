import os
import boto3
from botocore.exceptions import ClientError

def upload_sales_data() -> None:
    """Sube los datos del dominio de ventas a la capa Bronze."""
    bucket = os.getenv("BRONZE_BUCKET")
    if not bucket:
        raise ValueError("La variable de entorno BRONZE_BUCKET no está definida.")

    s3 = boto3.client("s3")
    base_path = os.path.join(os.getcwd(), "src", "data") # Asumimos que los CSV estarán aquí
    
    tablas = {
        "clientes.csv": "sales/clientes/clientes.csv",
        "catalogo.csv": "sales/catalogo/catalogo.csv",
        "pedidos.csv": "sales/pedidos/pedidos.csv"
    }

    for file_name, s3_key in tablas.items():
        local_path = os.path.join(base_path, file_name)
        if os.path.exists(local_path):
            try:
                s3.upload_file(local_path, bucket, s3_key)
                print(f"✅ Subido: {file_name} -> {s3_key}")
            except ClientError as e:
                print(f"❌ Error AWS subiendo {file_name}: {e}")
        else:
            print(f"⚠️ Archivo no encontrado: {local_path}")

if __name__ == "__main__":
    upload_sales_data()
