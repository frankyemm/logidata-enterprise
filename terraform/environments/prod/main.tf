terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "my_ip" { type = string }

locals {
  project_prefix = "logidata"
  environment    = "prod"
}

# 1. Llamamos al módulo de Red
module "networking" {
  source         = "../../modules/networking"
  project_prefix = local.project_prefix
  environment    = local.environment
  my_ip          = var.my_ip
}

# 2. Llamamos al módulo de Storage
module "storage" {
  source         = "../../modules/storage"
  project_prefix = local.project_prefix
  environment    = local.environment
}

# 3. Llamamos al módulo de Seguridad (IAM)
module "iam" {
  source         = "../../modules/iam"
  project_prefix = local.project_prefix
  environment    = local.environment
  # Fíjate cómo le pasamos los buckets del módulo storage de forma dinámica:
  datalake_bucket_arns = values(module.storage.bucket_arns)
}

# 4. Llamamos al módulo de Bases de Datos
module "databases" {
  source         = "../../modules/databases"
  project_prefix = local.project_prefix
  environment    = local.environment
  db_password    = var.db_password
  # Extraemos red y seguridad de los otros módulos:
  vpc_id               = module.networking.vpc_id
  subnet_ids           = module.networking.subnet_ids
  db_security_group_id = module.networking.db_security_group_id
  redshift_role_arn    = module.iam.redshift_role_arn
}

# Kinesis Data Stream (Para el dominio IoT)
resource "aws_kinesis_stream" "iot_stream" {
  name             = "${local.project_prefix}-${local.environment}-iot-stream"
  shard_count      = 1
  retention_period = 24
}

# 5. Llamamos al módulo de Cómputo (El cerebro)
module "compute" {
  source            = "../../modules/compute"
  project_prefix    = local.project_prefix
  environment       = local.environment
  glue_role_arn     = module.iam.glue_role_arn
  lambda_role_arn   = module.iam.lambda_role_arn
  bronze_bucket_id  = module.storage.bucket_ids["bronze"]
  iot_stream_arn    = aws_kinesis_stream.iot_stream.arn
  dynamo_table_name = module.databases.dynamodb_table_name
  # Inyectamos las rutas resolviéndolas desde el directorio actual (dev o prod)
  script_sales_b2s_path        = "${path.root}/../../../src/domains/sales/bronze_to_silver_sales.py"
  script_sales_s2g_path        = "${path.root}/../../../src/domains/sales/silver_to_gold_sales.py"
  script_logistics_lambda_path = "${path.root}/../../../src/domains/logistics/lambda_iot.py"
}
