# Multi-Cloud Edge Telemetry & Analytical Lakehouse
# Terraform Infrastructure as Code: Kinesis, S3 Medallion Lakehouse, Lambda, IAM & LocalStack Support

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = var.use_localstack ? "mock_access_key" : null
  secret_key                  = var.use_localstack ? "mock_secret_key" : null
  s3_use_path_style           = var.use_localstack
  skip_credentials_validation = var.use_localstack
  skip_metadata_api_check     = var.use_localstack
  skip_requesting_account_id  = var.use_localstack

  dynamic "endpoints" {
    for_each = var.use_localstack ? [1] : []
    content {
      s3       = var.localstack_endpoint
      kinesis  = var.localstack_endpoint
      lambda   = var.localstack_endpoint
      iam      = var.localstack_endpoint
      dynamodb = var.localstack_endpoint
    }
  }
}

# 1. Edge Ingestion Kinesis Stream
resource "aws_kinesis_stream" "edge_telemetry_stream" {
  name             = "${var.environment}-edge-telemetry-kinesis-stream"
  shard_count      = var.kinesis_shard_count
  retention_period = 48

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded"
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Environment = var.environment
    Project     = "EdgeTelemetryLakehouse"
    ManagedBy   = "Terraform"
  }
}

# 2. Medallion Storage Buckets (Bronze / Silver / Gold / Quarantine)
resource "aws_s3_bucket" "bronze_raw_lakehouse" {
  bucket        = "${var.environment}-lakehouse-bronze-raw-${var.aws_region}"
  force_destroy = true

  tags = {
    Layer       = "Bronze"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "silver_cleansed_lakehouse" {
  bucket        = "${var.environment}-lakehouse-silver-cleansed-${var.aws_region}"
  force_destroy = true

  tags = {
    Layer       = "Silver"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "gold_aggregated_lakehouse" {
  bucket        = "${var.environment}-lakehouse-gold-aggregated-${var.aws_region}"
  force_destroy = true

  tags = {
    Layer       = "Gold"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "quarantine_dead_letter" {
  bucket        = "${var.environment}-lakehouse-quarantine-dlq-${var.aws_region}"
  force_destroy = true

  tags = {
    Layer       = "Quarantine"
    Environment = var.environment
  }
}

# 3. Serverless Edge Micro-Batch Normalizer IAM Role
resource "aws_iam_role" "lambda_edge_normalizer_role" {
  name = "${var.environment}-edge-normalizer-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}
