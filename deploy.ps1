# PowerShell deployment script for local testing
param(
    [string]$FunctionName = "LambdaCostWatchdog",
    [string]$Region = "us-east-1"
)

Write-Host "Deploying Lambda function: $FunctionName" -ForegroundColor Green

# Create deployment package
Compress-Archive -Path "LamndaCostWatchdog.py" -DestinationPath "function.zip" -Force

# Update Lambda function code
aws lambda update-function-code `
    --function-name $FunctionName `
    --zip-file fileb://function.zip `
    --region $Region

# Update runtime to Python 3.12
aws lambda update-function-configuration `
    --function-name $FunctionName `
    --runtime python3.12 `
    --region $Region

# Clean up
Remove-Item "function.zip" -Force

Write-Host "Deployment completed!" -ForegroundColor Green