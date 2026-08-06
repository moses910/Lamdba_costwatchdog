"""
SNS notification helper.
"""

import logging
import boto3  # type: ignore

logger = logging.getLogger(__name__)


def publish_report(sns_topic_arn, report, subject="AWS Cost Optimization Report"):
    """Send a summary report to SNS if a topic ARN is configured.

    Args:
        sns_topic_arn: The SNS topic ARN to publish to.
        report: The report body (string).
        subject: The SNS message subject.
    """
    if not sns_topic_arn:
        logger.info("No SNS topic configured; skipping notification.")
        return

    try:
        sns = boto3.client('sns')
        sns.publish(TopicArn=sns_topic_arn, Message=report, Subject=subject)
        logger.info("SNS notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send SNS notification: {e}")
