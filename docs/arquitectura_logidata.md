# 🏛️  Arquitectura Corporativa - LogiData S.A.S.

## Topología de la Arquitectura (Data Mesh & Lakehouse)

El sistema implementa una **Arquitectura Lambda Híbrida** bajo el paradigma de **Data Mesh** (Malla de Datos). Las responsabilidades, el código y los pipelines están descentralizados por dominios de negocio (*Sales* y *Logistics*), gobernados por un orquestador central y desplegados mediante Infraestructura como Código modular.

```mermaid
flowchart TD
    %% Estilos
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:black;
    classDef storage fill:#3F8624,stroke:#232F3E,stroke-width:2px,color:white;
    classDef process fill:#00A4A6,stroke:#232F3E,stroke-width:2px,color:white;
    classDef onprem fill:#5A6B86,stroke:#232F3E,stroke-width:2px,color:white;
    classDef orchestration fill:#E83E8C,stroke:#232F3E,stroke-width:2px,color:white;
    classDef devops fill:#2088FF,stroke:#232F3E,stroke-width:2px,color:white;

    %% CI/CD & IaC
    subgraph DevOps ["Gobierno y DevSecOps"]
        GH[GitHub Actions\nCI/CD, Checkov, Ruff, Pytest]:::devops
        TF{Terraform Modules\nNetworking, IAM, Compute}:::onprem
    end

    %% Orquestación
    subgraph Orquestacion ["Plano de Control"]
        AIRFLOW((Apache Airflow\nDAG por Dominio)):::orchestration
    end

    %% DOMINIO: LOGÍSTICA (Streaming / Kappa)
    subgraph Logistics["Dominio: Logística (Real-Time)"]
        SIM[IoT Simulator]:::onprem
        KDS[Kinesis Data Stream]:::aws
        LAMBDA[AWS Lambda\nFiltro TEMP_CRITICA]:::process
        DYNAMO[(DynamoDB\nAlertas NoSQL)]:::aws
        
        SIM -- JSON Base64 --> KDS
        KDS -- Trigger --> LAMBDA
        LAMBDA -- PutItem --> DYNAMO
    end

    %% DOMINIO: VENTAS (Batch / Lakehouse)
    subgraph Sales ["Dominio: Ventas (Batch Lakehouse)"]
        CSV[Fuentes CSV]:::onprem
        BRONZE[(S3 Bronze\nRaw CSV AES-256)]:::storage
        CRAWLER[Glue Crawler\nData Catalog]:::process
        SILVER[(S3 Silver\nDelta Lake)]:::storage
        GOLD[(S3 Gold\nParquet Kimball)]:::storage
        
        CSV -- Boto3 Ingest --> BRONZE
        BRONZE -. Descubre Esquema .-> CRAWLER
        BRONZE -- PySpark + Data Quality --> SILVER
        SILVER -- PySpark Transform --> GOLD
    end

    %% Capa de Consumo (Data Warehouse & BI)
    subgraph Serving["Capa de Consumo (VPC Privada)"]
        RS_API[Redshift Data API\nServerless DDL/COPY]:::process
        REDSHIFT[(Redshift Serverless\nData Warehouse)]:::aws
        QS[Amazon QuickSight\nDashboards SPICE]:::aws
        
        GOLD -- COPY Command --> RS_API
        RS_API -- Execute SQL --> REDSHIFT
        REDSHIFT -- Custom SQL Query --> QS
        DYNAMO -. Live Map .-> QS
    end

    %% Conexiones de Gobierno
    GH -. Despliega Infraestructura .-> TF
    AIRFLOW -. Orquesta .-> CSV
    AIRFLOW -. Orquesta .-> CRAWLER
    AIRFLOW -. Dispara Spark .-> SILVER
    AIRFLOW -. Dispara Spark .-> GOLD
```

### Componentes Clave de la Arquitectura:
*   **Aislamiento de Red:** Redshift Serverless y PostgreSQL operan en subredes privadas (`publicly_accessible = false`). La interacción se realiza mediante la **API de Datos de Redshift**, eliminando la necesidad de exponer puertos en internet.
*   **Lakehouse Híbrido:** La capa *Silver* utiliza **Delta Lake** para garantizar transacciones ACID y evolución de esquemas (Time Travel). La capa *Gold* se materializa en **Parquet plano** para maximizar el rendimiento del comando `COPY` nativo de Redshift.
*   **Circuit Breakers (Data Quality):** Antes de mutar los datos en el Data Lake, PySpark ejecuta validaciones de integridad referencial y de negocio. Si fallan, Airflow aborta el pipeline, protegiendo el Data Warehouse.

