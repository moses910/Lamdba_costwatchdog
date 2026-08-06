"""
Lambda free-tier usage check — Section 7.
"""

import logging

logger = logging.getLogger(__name__)


def check_lambda_free_tier(cloudwatch, start, now):
    """Check if Lambda invocations are within the free-tier 1M limit.

    Args:
        cloudwatch: boto3 CloudWatch client.
        start: Start datetime for the metrics window (30 days back).
        now: Current UTC datetime.

    Returns:
        list[str]: Summary lines.
    """
    logger.info("Section 7: Checking Lambda free-tier usage...")
    summary = []

    try:
        lambda_metrics = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            StartTime=start,
            EndTime=now,
            Period=2592000,  # 30 days in seconds
            Statistics=['Sum'],
        )
        datapoints = lambda_metrics.get('Datapoints', [])
        total_invocations = datapoints[0]['Sum'] if datapoints else 0

        if total_invocations > 1_000_000:
            summary.append(
                f"⚠️ Lambda invocations exceed free tier: "
                f"{total_invocations:,.0f}"
            )
            logger.warning(
                f"Lambda invocations: {total_invocations:,.0f} "
                f"(exceeds 1M limit)"
            )
        else:
            summary.append(
                f"Lambda invocations within free tier: "
                f"{total_invocations:,.0f}"
            )
            logger.info(
                f"Lambda invocations: {total_invocations:,.0f} (within limits)"
            )
    except Exception as e:
        logger.error(f"Error checking Lambda usage: {e}")
        summary.append(f"⚠️ Lambda usage check failed: {str(e)}")

    return summary
