output "postgres_endpoint" { value = module.databases.postgres_endpoint }
output "redshift_endpoint" { value = module.databases.redshift_endpoint }
output "datalake_buckets" { value = module.storage.bucket_ids }
