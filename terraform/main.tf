provider "aws" {
  region = var.aws_region
}

# S3 Dashboard Bucket
resource "aws_s3_bucket" "dashboard" {
  bucket = var.dashboard_bucket_name
}

resource "aws_s3_bucket_website_configuration" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id
  index_document { suffix = "index.html" }
}

resource "aws_s3_bucket_public_access_block" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "dashboard" {
  bucket = aws_s3_bucket.dashboard.id
  depends_on = [aws_s3_bucket_public_access_block.dashboard]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.dashboard.arn}/*"
    }]
  })
}

# SNS Topic
resource "aws_sns_topic" "costguard" { name = "costguard-alerts" }

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.costguard.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda" {
  name = "costguard-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  name = "costguard-lambda-policy"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["ec2:Describe*", "ec2:StopInstances", "cloudwatch:GetMetricStatistics", "ce:GetCostAndUsage", "sns:Publish", "s3:PutObject", "s3:GetObject"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      }
    ]
  })
}

# Lambda Functions
locals {
  common_env = {
    AWS_ACCOUNT_ID   = var.aws_account_id
    SLACK_WEBHOOK    = var.slack_webhook
    SNS_TOPIC_ARN    = aws_sns_topic.costguard.arn
    DASHBOARD_BUCKET = aws_s3_bucket.dashboard.id
    AWS_REGION       = var.aws_region
  }
}

resource "aws_lambda_function" "waste_detector" {
  filename      = "../dist/waste_detector.zip"
  function_name = "costguard-waste-detector"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 300
  environment { variables = local.common_env }
}

# EventBridge Rules
resource "aws_cloudwatch_event_rule" "waste" {
  name                = "costguard-waste-daily"
  schedule_expression = "cron(0 8 * * ? *)"
}

resource "aws_cloudwatch_event_target" "waste" {
  rule      = aws_cloudwatch_event_rule.waste.name
  target_id = "waste_detector"
  arn       = aws_lambda_function.waste_detector.arn
}

resource "aws_lambda_permission" "waste" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.waste_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.waste.arn
}
