variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS Deployment Region"
}

variable "environment" {
  type        = string
  default     = "prod"
  description = "Deployment environment (dev, staging, prod)"
}

variable "kinesis_shard_count" {
  type        = number
  default     = 2
  description = "Number of provisioned Kinesis shards for edge telemetry"
}

variable "use_localstack" {
  type        = bool
  default     = false
  description = "Toggle LocalStack emulation for zero-cost local sandbox testing"
}

variable "localstack_endpoint" {
  type        = string
  default     = "http://localhost:4566"
  description = "LocalStack endpoint URL"
}
