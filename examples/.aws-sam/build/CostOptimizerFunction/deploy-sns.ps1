# Deploy SNS stack for Lambda notifications
param(
    [Parameter(Mandatory=$true)]
    [string]$EmailAddress,
    [string]$StackName = "lambda-cleanup-sns",
    [string]$Region = "us-east-1"
)

Write-Host "Deploying SNS stack for email: $EmailAddress" -ForegroundColor Green

# Deploy CloudFormation stack
aws cloudformation deploy `
    --template-file sns-template.yaml `
    --stack-name $StackName `
    --parameter-overrides EmailAddress=$EmailAddress `
    --region $Region

# Get the SNS Topic ARN
$TopicArn = aws cloudformation describe-stacks `
    --stack-name $StackName `
    --region $Region `
    --query "Stacks[0].Outputs[?OutputKey=='SnsTopicArn'].OutputValue" `
    --output text

Write-Host "SNS Topic ARN: $TopicArn" -ForegroundColor Yellow
Write-Host "Add this to your Lambda environment variable: SNS_TOPIC_ARN=$TopicArn" -ForegroundColor Cyan
Write-Host "Check your email and confirm the subscription!" -ForegroundColor Green