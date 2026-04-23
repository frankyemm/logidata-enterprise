# 🚛 LogiData Enterprise - Modern Data Platform

![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?style=flat-square&logo=amazon-aws)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=flat-square&logo=terraform)
![Apache Spark](https://img.shields.io/badge/Apache_Spark-Data_Processing-E25A1C?style=flat-square&logo=apache-spark)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-Lakehouse-02A8DF?style=flat-square)
![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-Orchestration-017CEE?style=flat-square&logo=apache-airflow)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python)

## 📌 Resumen Ejecutivo
**LogiData Enterprise** es una Plataforma de Datos Moderna (Modern Data Stack) construida desde cero (End-to-End) para resolver los desafíos analíticos y operativos de una empresa logística. 

El proyecto abandona las arquitecturas monolíticas tradicionales y adopta un paradigma de **Data Mesh (Malla de Datos)**, separando responsabilidades por dominios de negocio (*Ventas* y *Logística*). Toda la plataforma está aprovisionada mediante **Infraestructura como Código (IaC)**, asegurada bajo normativas corporativas (DevSecOps) y completamente automatizada vía CI/CD.

---

## 🏛️ Paradigmas y Patrones de Arquitectura

Este proyecto implementa los estándares más altos de la industria de datos actual:

1. **Data Mesh (Descentralización):** El código fuente, las pruebas (Unit Tests) y los pipelines de CI/CD están estrictamente aislados por subdominios (`src/domains/sales` y `src/domains/logistics`).
2. **Data Lakehouse Híbrido:** 
   * La capa *Silver* utiliza **Delta Lake** para habilitar transacciones ACID, control de concurrencia y evolución de esquemas (Schema Evolution). 
   * La capa *Gold* se materializa en **Apache Parquet plano** para maximizar el throughput del comando `COPY` en el Data Warehouse.
3. **Arquitectura Lambda Híbrida:**
   * **Rama Batch (Ventas):** Procesamiento de altos volúmenes de datos históricos usando AWS Glue (PySpark Serverless).
   * **Rama Streaming / Kappa (Logística):** Captura de eventos IoT de telemetría de camiones en tiempo real usando Amazon Kinesis, AWS Lambda y persistencia de alertas en NoSQL (DynamoDB).
4. **Shift-Left Security (DevSecOps):** La seguridad se audita desde el commit. Se aplican escáneres de análisis estático (SAST) sobre Python (`Bandit`) e Infraestructura (`Checkov`) antes de autorizar cualquier despliegue.

---

## 📁 Anatomía del Proyecto

El repositorio sigue una estructura de *Monorepo Corporativo*, integrando submódulos de Git para abstraer la infraestructura.

```text
logidata-enterprise/
├── airflow/                        # 🧠 ORQUESTACIÓN
│   └── dags/
│       └── sales_domain_dag.py     # DAG Topológico (Ingesta -> Crawler -> Spark B2S -> Spark S2G)
├── dashboards
│   └── quicksight_logidata.pdf     # Dashboard de QuickSight
├── docs/                           # 📚 DOCUMENTACIÓN TÉCNICA
│   ├── arquitectura_logidata.md    # Topología Cloud y diagramas Mermaid
│   └── modelo_datos_logidata.md    # ERDs (Kimball Star Schema) y diccionarios de datos
├── src/                            # ⚙️ LÓGICA DE NEGOCIO (DATA MESH)
│   ├── data/
│   │   ├── catalogo.csv            # Dataset de productos
│   │   ├── clientes.csv            # Dataset de clientes
│   │   ├── diccionario_datos.csv   # Diccionario de datos
│   │   ├── entregas.csv            # Dataset de entregas
│   │   ├── pedidos.csv             # Dataset de pedidos
│   │   └── sensores.csv            # Dataset de sensores
│   └── domains/
│       ├── logistics/              # DOMINIO: LOGÍSTICA (Streaming IoT)
│       │   ├── simulator.py        # Generador de telemetría IoT inyectando a Kinesis
│       │   └── lambda_iot.py       # Función Lambda (Decodificación Kinesis y filtrado NoSQL)
│       └── sales/                  # DOMINIO: VENTAS (Batch)
│           ├── ingest_sales.py     # Script Boto3: Extracción hacia capa Bronze
│           ├── bronze_to_silver_sales.py # PySpark: Casteo, DQ Circuit Breakers y Delta Lake
│           ├── silver_to_gold_sales.py   # PySpark: Kimball Star Schema Transformation
│           └── deploy_redshift_schema.py # Inyección de DDL/COPY vía Redshift Data API (Red Segura)
├── terraform/                      # ☁️ INFRAESTRUCTURA COMO CÓDIGO (IaC)
│   ├── environments/
│   │   ├── dev/                    # Entorno de Desarrollo (Aislado con Remote Backend)
│   │   └── prod/                   # Entorno de Producción (DRY concept)
│   └── modules/                    # 🔗 GIT SUBMODULE (Plantillas AWS reutilizables)
│       ├── networking/             # VPCs, Subnets Públicas/Privadas, Security Groups
│       ├── iam/                    # Roles y Políticas bajo Principio de Menor Privilegio (PoLP)
│       ├── storage/                # Data Lake Medallion (S3 AES-256 + Block Public Access)
│       ├── databases/              # Redshift Serverless, DynamoDB (On-Demand), Secrets Manager
│       └── compute/                # Glue Jobs, Lambda, Kinesis, Glue Crawlers
├── tests/                          # 🧪 CALIDAD DE SOFTWARE (UNIT TESTING)
│   ├── logistics/
│   │   ├── test_simulator.py       # Unit test: Mocking de open() y Kinesis
│   │   └── test_lambda_iot.py      # Unit test: Mocking de Kinesis y DynamoDB
│   └── sales/
│       └── test_ingest_sales.py    # Unit test: Mock de S3 y parches del OS File System
├── .github/workflows/              # 🤖 INTEGRACIÓN Y DESPLIEGUE CONTINUO
│   ├── ci-infra.yml                # CI: Terraform fmt, validate, Checkov
│   ├── cd-terraform.yml            # CD: Terraform apply automatizado en main
│   ├── ci-sales.yml                # CI Ventas: Ruff, Bandit, Pytest (Aislado)
│   └── ci-logistics.yml            # CI Logística: Ruff, Bandit, Pytest (Aislado)
└── requirements.txt                # Dependencias estrictas (Airflow, Boto3, Testing)
```

---

## 🛡️ Gobierno, Seguridad y Calidad de Datos

Esta plataforma fue diseñada asumiendo que los datos de origen pueden estar corruptos y que internet es un entorno hostil.

### 1. Privacidad de Datos y Red (Zero Trust)
* **Bases de Datos Ocultas:** El Data Warehouse (Redshift) opera bajo un esquema `publicly_accessible = false`. La comunicación se realiza exclusivamente a través de la **AWS Redshift Data API**, eliminando la necesidad de abrir puertos (`5439`) al internet público.
* **Gestión de Secretos:** No existen contraseñas en el código fuente, archivos de configuración ni en variables de entorno CI/CD. Terraform utiliza `random_password` para generar credenciales de alta entropía y las inyecta directamente en **AWS Secrets Manager**.
* **Cifrado Militar:** Todos los buckets de S3 del Data Lake tienen cifrado habilitado por defecto (`AES-256 / SSE-S3`) mediante IaC.

### 2. Data Quality (El patrón "Circuit Breaker")
En lugar de implementar validaciones a posteriori, la capa Silver (Pipeline de PySpark) actúa como un cortafuegos:
* Valida que los DataFrames no estén vacíos.
* Evalúa la integridad referencial (Rechaza PKs nulas, ej. `id_pedido`).
* Evalúa lógicas de negocio (Rechaza transacciones con montos negativos o en formato texto).
* *Resultado:* Si un archivo corrupto entra a la capa Bronze, el Job de AWS Glue arroja una excepción intencional, Airflow detiene la orquestación y la capa Gold (Data Warehouse) permanece inmaculada.

### 3. Testing Cloud-Native Local (QA Automatizado)
El código que interactúa con la nube es probado en los pipelines de GitHub Actions **sin generar costos en AWS**.
* **Dominio Ventas:** Unit tests para la ingesta usando `moto` (Mock de S3) y `pytest` (`tmp_path`, `patch`), aislando el sistema de archivos local y la red.
* **Dominio Logística:** Unit tests para el simulador IoT y la Lambda Serverless. Se levantan réplicas efímeras de Kinesis y DynamoDB en memoria, validando que el filtrado de alertas (`TEMP_CRITICA`) funciona de manera determinista.

---

## 🚀 Guía de Despliegue y Ejecución Operativa

### Requisitos Previos
* Cuenta de AWS activa (y credenciales inyectadas en los Secrets del repositorio de GitHub).
* Terraform >= 1.5
* Python 3.10+ y entorno virtual activado.

### Paso 1: Ejecución de Pruebas (Opcional - Local)
Para verificar la integridad del código sin afectar AWS:
```bash
pip install -r requirements.txt
pytest tests/
```

### Paso 2: Despliegue de la Infraestructura (CD Automático)
1. Cualquier push a la rama `main` que involucre la carpeta `terraform/` disparará el workflow `cd-terraform.yml`.
2. GitHub Actions inicializa el **Backend Remoto en S3** (para prevenir pérdida de estado).
3. Ejecuta `terraform apply` sin intervención humana, creando la VPC, roles, S3, Glue, Kinesis, Lambda, DynamoDB y Redshift Serverless.

### Paso 3: Orquestación (Apache Airflow)
Dada la restricción de costos de servicios como AWS MWAA (~$500/mes), el orquestador se ejecuta en *standalone* para fines de este proyecto, actuando como director externo de la API de AWS.
```bash
# Exportar el rol de AWS Default y directorio
export AIRFLOW_CONN_AWS_DEFAULT="aws://?region_name=us-east-1"
export AIRFLOW_HOME=$(pwd)/airflow

# Arrancar el orquestador
airflow standalone
```
1. Navegar a `http://localhost:8080`.
2. Encender y ejecutar el DAG `sales_domain_pipeline`.
3. El DAG ejecutará secuencialmente: Ingesta Local -> Glue Crawler -> Glue Job (Delta Silver) -> Glue Job (Parquet Gold).

### Paso 4: Carga al Data Warehouse (Data API)
Una vez que Airflow termine (todo en verde), inyectamos el modelo dimensional en Redshift.
1. Editar `src/domains/sales/deploy_redshift_schema.py` para reemplazar la constante `IAM_ROLE_ARN` con el ARN generado por Terraform para Redshift.
2. Ejecutar el script:
```bash
python3 src/domains/sales/deploy_redshift_schema.py
```
*(El script destruirá tablas temporales, aplicará el DDL Kimball, y ejecutará el comando `COPY` para absorber los terabytes virtuales de S3 Gold).*

### Paso 5: Simulación Streaming IoT (Logística)
Para probar la arquitectura Kappa:
```bash
python3 src/domains/logistics/simulator.py
# Enviará cargas JSON en Base64 al Data Stream de Kinesis, disparando la Lambda.
```

### Paso 6: Apagado y FinOps (Cero Deuda de Costos)
Una vez terminado el análisis en las herramientas de BI (QuickSight):
```bash
# Vaciar data lake
aws s3 rm s3://logidata-v2-dev-bronze --recursive
aws s3 rm s3://logidata-v2-dev-silver --recursive
aws s3 rm s3://logidata-v2-dev-gold --recursive

# Destruir infraestructura
cd terraform/environments/dev
terraform destroy -auto-approve
```

---

## 🔮 Roadmap / Evolución a Nivel Enterprise Fortune-500
Aunque el proyecto posee estándares altísimos, en un escenario de escalabilidad masiva se recomiendan las siguientes iteraciones:
1. **Orquestación Nube Nativa:** Migrar Airflow local a Amazon MWAA o desplegar KubernetesPodOperators en Amazon EKS.
2. **Cuarentena (Dead Letter Tables):** Modificar el *Circuit Breaker* en PySpark para que no detenga el pipeline entero, sino que desvíe los registros defectuosos a una tabla de cuarentena en S3 para su posterior auditoría.
3. **Resiliencia IoT:** Incorporar una Dead Letter Queue (DLQ) mediante Amazon SQS para los registros de Kinesis que la Lambda falle en procesar.

***
*Arquitectura diseñada y desplegada como demostración técnica de habilidades avanzadas en Data Engineering, Cloud Architecture y DevSecOps.*