output "kinesis_stream_arn" {
  value       = aws_kinesis_stream.edge_telemetry_stream.arn
  description = "ARN of the edge telemetry Kinesis stream"
}

output "bronze_bucket_name" {
  value       = aws_s3_bucket.bronze_raw_lakehouse.id
  description = "S3 Bucket Name for Bronze Raw Ingestion"
}

output "silver_bucket_name" {
  value       = aws_s3_bucket.silver_cleansed_lakehouse.id
  description = "S3 Bucket Name for Silver Cleansed Layer"
}

output "gold_bucket_name" {
  value       = aws_s3_bucket.gold_aggregated_lakehouse.id
  description = "S3 Bucket Name for Gold Machine Health Aggregations"
}
