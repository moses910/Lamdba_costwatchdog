# Update Lambda IAM role with missing permissions
param(
    [string]$RoleName = "LambdaCostWatchdog-role-1echupi5",
    [string]$PolicyName = "LambdaCostWatchdogPolicy"
)

Write-Host "Updating Lambda IAM role permissions..." -ForegroundColor Green

# Create/update the inline policy
aws iam put-role-policy `
    --role-name $RoleName `
    --policy-name $PolicyName `
    --policy-document file://lambda-iam-policy.json

Write-Host "IAM policy updated successfully!" -ForegroundColor Green
Write-Host "The Lambda function now has permissions for:" -ForegroundColor Yellow
Write-Host "  ✅ CloudWatch Logs retention policy" -ForegroundColor Cyan
Write-Host "  ✅ Cost Explorer API access" -ForegroundColor Cyan