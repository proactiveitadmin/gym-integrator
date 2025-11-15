
param(
  [string]$Endpoint = "http://localhost:4566",
  [string]$Region = "eu-central-1"
)
$ErrorActionPreference = "Stop"
Write-Host "Creating SQS queues..." -ForegroundColor Cyan
aws --endpoint-url $Endpoint --region $Region sqs create-queue --queue-name inbound-events | Out-Null
aws --endpoint-url $Endpoint --region $Region sqs create-queue --queue-name outbound-messages | Out-Null

Write-Host "Creating DynamoDB tables..." -ForegroundColor Cyan
aws --endpoint-url $Endpoint --region $Region dynamodb create-table --table-name Conversations `
  --attribute-definitions AttributeName=pk,AttributeType=S `
  --key-schema AttributeName=pk,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST | Out-Null

aws --endpoint-url $Endpoint --region $Region dynamodb create-table --table-name Messages `
  --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S `
  --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE `
  --billing-mode PAY_PER_REQUEST | Out-Null

aws --endpoint-url $Endpoint --region $Region dynamodb create-table --table-name Campaigns `
  --attribute-definitions AttributeName=pk,AttributeType=S `
  --key-schema AttributeName=pk,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST | Out-Null

Write-Host "Done." -ForegroundColor Green
