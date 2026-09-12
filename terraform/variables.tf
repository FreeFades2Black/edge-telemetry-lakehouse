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

variable "factory_edge_gateways" {
  type = map(object({
    ip              = string
    plant_location  = string
    primary_machine = string
    facility_id     = string
    connection_type = string
  }))
  default = {
    "dmg-sptn-gw01" = {
      ip              = "10.240.40.14"
      plant_location  = "SPARTANBURG_SC_USA"
      primary_machine = "DMG_MORI_5AXIS_CNC"
      facility_id     = "SPTN-PLANT-04"
      connection_type = "ssh"
    }
    "bmw-greer-gw01" = {
      ip              = "10.240.10.11"
      plant_location  = "GREER_SC_USA"
      primary_machine = "BMW_AMR_ROBOT_KUKA"
      facility_id     = "BMW-GREER-ASSEMBLY"
      connection_type = "ssh"
    }
    "mich-gvl-gw01" = {
      ip              = "10.240.20.12"
      plant_location  = "GREENVILLE_SC_USA"
      primary_machine = "MICHELIN_CURING_PRESS"
      facility_id     = "MICH-MARC-01"
      connection_type = "ssh"
    }
    "gev-gvl-gw01" = {
      ip              = "10.240.30.13"
      plant_location  = "GREENVILLE_SC_USA"
      primary_machine = "GE_HA_GAS_TURBINE"
      facility_id     = "GEV-CAMPUS-02"
      connection_type = "ssh"
    }
    "omarchy" = {
      ip              = "127.0.0.1"
      plant_location  = "GREENVILLE_SC_USA"
      primary_machine = "GE_HA_GAS_TURBINE"
      facility_id     = "OMARCHY-EDGE-LAB-01"
      connection_type = "local"
    }
  }
  description = "Industrial Edge Gateway inventory topology mapped into Ansible"
}

