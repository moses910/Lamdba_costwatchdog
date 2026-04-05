# Installation Guide

## Prerequisites

- AWS Account
- AWS CLI configured
- Python 3.8+

## AWS Setup

1. Create an IAM role for the Lambda function with the following permissions:
   - `ce:GetCostAndUsage`
   - `sns:Publish`

2. Create an SNS topic for alerts (optional)

## Deployment

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Package the Lambda function:
   ```bash
   zip -r lambda-function.zip .
   ```

4. Deploy to AWS Lambda using AWS CLI or Console

## EventBridge Setup (Optional)

To run the function on a schedule, create an EventBridge rule that triggers the Lambda function daily.