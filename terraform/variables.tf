variable "aws_region" {
  default = "ap-south-1"
}

variable "aws_account_id" {
  type = string
}

variable "dashboard_bucket_name" {
  type = string
}

variable "slack_webhook" {
  default = ""
}

variable "alert_email" {
  type = string
}
