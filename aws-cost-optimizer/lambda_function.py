import boto3
import json
from datetime import datetime, timedelta

def lambda_handler(event, context):
    """
    AWS Lambda function for cost optimization monitoring.
    """
    # Initialize AWS clients
    ce_client = boto3.client('ce')
    sns_client = boto3.client('sns')

    # Get cost data for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    try:
        # Get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost']
        )

        # Process the data (simplified example)
        total_cost = 0
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                total_cost += cost

        # Check for cost optimization opportunities
        optimization_alerts = check_cost_optimization_opportunities()

        # Send SNS notification if needed
        if optimization_alerts:
            message = f"Cost Optimization Alert: {optimization_alerts}"
            sns_client.publish(
                TopicArn='arn:aws:sns:us-east-1:123456789012:cost-optimization-alerts',
                Message=message,
                Subject='AWS Cost Optimization Alert'
            )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost optimization check completed',
                'total_cost': total_cost,
                'alerts': optimization_alerts
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def check_cost_optimization_opportunities():
    """
    Check for cost optimization opportunities.
    This is a placeholder - implement actual checks.
    """
    # Example checks:
    # - Unused EC2 instances
    # - Underutilized RDS instances
    # - Idle load balancers
    # - etc.

    alerts = []

    # Placeholder logic
    # In a real implementation, you'd query various AWS services
    # to identify optimization opportunities

    return alerts