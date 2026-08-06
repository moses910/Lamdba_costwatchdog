"""
CloudWatch Logs retention management — Section 12.
"""

import logging

logger = logging.getLogger(__name__)


def set_log_retention(logs_client, dry_run, retention_days=30):
    """Set retention policy on CloudWatch log groups that have none or exceed the limit.

    Args:
        logs_client: boto3 CloudWatch Logs client.
        dry_run: If True, report but do not modify.
        retention_days: Target retention in days.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 12: Checking CloudWatch log retention...")
    summary = []
    savings = 0

    try:
        log_groups = logs_client.describe_log_groups()['logGroups']
        updated_logs = 0

        for lg in log_groups:
            if (
                'retentionInDays' not in lg
                or lg.get('retentionInDays', 0) > retention_days
            ):
                if not dry_run:
                    try:
                        logs_client.put_retention_policy(
                            logGroupName=lg['logGroupName'],
                            retentionInDays=retention_days,
                        )
                        updated_logs += 1
                    except Exception as e:
                        logger.warning(
                            f"Could not set retention for "
                            f"{lg['logGroupName']}: {e}"
                        )
                else:
                    updated_logs += 1

        if updated_logs > 0:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would set {retention_days}-day retention on "
                    f"{updated_logs} log groups"
                )
                logger.info(
                    f"DRY RUN: Would update {updated_logs} log groups"
                )
            else:
                summary.append(
                    f"✅ Set {retention_days}-day retention on "
                    f"{updated_logs} log groups"
                )
                logger.info(
                    f"Updated retention for {updated_logs} log groups"
                )
        else:
            summary.append("All log groups already have appropriate retention.")
            logger.info("All log groups have appropriate retention")
    except Exception as e:
        logger.error(f"Error in log retention update: {e}")
        summary.append(f"⚠️ Log retention update failed: {str(e)}")

    return summary, savings
