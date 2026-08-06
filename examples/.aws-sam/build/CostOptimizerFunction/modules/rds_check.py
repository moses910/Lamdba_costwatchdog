"""
RDS free-tier usage check — Section 8.
"""

import logging

logger = logging.getLogger(__name__)


def check_rds_free_tier(rds):
    """Check if RDS usage is within the free-tier 750-hour limit.

    Returns:
        list[str]: Summary lines.
    """
    logger.info("Section 8: Checking RDS free-tier usage...")
    summary = []

    try:
        rds_instances = rds.describe_db_instances()['DBInstances']
        active_rds = [
            r['DBInstanceIdentifier']
            for r in rds_instances
            if r['DBInstanceStatus'] == 'available'
        ]
        rds_hours = len(active_rds) * 24 * 30

        if rds_hours > 750:
            summary.append(
                f"⚠️ RDS usage likely exceeds Free Tier ({rds_hours} hours est.)."
            )
            logger.warning(
                f"RDS usage: {rds_hours} hours (exceeds 750 hour limit)"
            )
        else:
            summary.append(
                f"RDS usage within free tier ({rds_hours} hours est.)."
            )
            logger.info(f"RDS usage: {rds_hours} hours (within limits)")
    except Exception as e:
        logger.error(f"Error checking RDS usage: {e}")
        summary.append(f"⚠️ RDS usage check failed: {str(e)}")

    return summary
