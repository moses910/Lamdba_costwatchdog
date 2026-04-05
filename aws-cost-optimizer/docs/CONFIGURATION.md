# Configuration Guide

## Environment Variables

Set the following environment variables in your Lambda function:

- `SNS_TOPIC_ARN`: ARN of the SNS topic for alerts
- `COST_THRESHOLD`: Cost threshold for alerts (optional)

## Cost Analysis Settings

The function analyzes costs over the last 30 days by default. You can modify the time period in the code.

## Alert Configuration

Alerts are sent via SNS when cost optimization opportunities are detected. Configure the SNS topic subscribers to receive notifications.