# CI/CD Pipeline Setup Guide

## Prerequisites
- GitHub repository
- AWS CLI configured locally
- AWS Lambda function already created

## Setup Steps

### 1. GitHub Secrets Configuration
Add these secrets to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### 2. AWS IAM Policy
Create an IAM user with this policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration"
            ],
            "Resource": "arn:aws:lambda:us-east-1:*:function:LambdaCostWatchdog"
        }
    ]
}
```

### 3. Local Testing
Run the deployment script:
```powershell
.\deploy.ps1
```

### 4. Automatic Deployment
- Push changes to `main` branch
- Pipeline triggers automatically
- Lambda function updates with new code

## Pipeline Features
- ✅ Deploys on code changes
- ✅ Updates to Python 3.12 runtime
- ✅ Minimal permissions required
- ✅ Fast deployment (~30 seconds)