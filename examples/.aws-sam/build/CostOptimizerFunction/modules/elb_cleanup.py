"""
Unused load balancer cleanup — Section 11.
"""

import logging

logger = logging.getLogger(__name__)


def delete_unused_load_balancers(elbv2, dry_run):
    """Delete ALB/NLB load balancers with no target groups.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 11: Checking for unused load balancers...")
    summary = []
    savings = 0

    try:
        load_balancers = elbv2.describe_load_balancers()['LoadBalancers']
        unused_lbs = []

        for lb in load_balancers:
            try:
                targets = elbv2.describe_target_groups(
                    LoadBalancerArn=lb['LoadBalancerArn']
                )
                if not targets['TargetGroups']:
                    unused_lbs.append(lb['LoadBalancerName'])
                    if not dry_run:
                        elbv2.delete_load_balancer(
                            LoadBalancerArn=lb['LoadBalancerArn']
                        )
                        savings += 18.25  # ~$18.25/month per ALB
            except Exception as e:
                logger.warning(
                    f"Could not check/delete load balancer "
                    f"{lb.get('LoadBalancerName', 'unknown')}: {e}"
                )

        if unused_lbs:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would delete {len(unused_lbs)} unused load balancers"
                )
                logger.info(
                    f"DRY RUN: Would delete {len(unused_lbs)} load balancers"
                )
            else:
                summary.append(
                    f"✅ Deleted {len(unused_lbs)} unused load balancers"
                )
                logger.info(f"Deleted {len(unused_lbs)} load balancers")
        else:
            summary.append("No unused load balancers found.")
            logger.info("No unused load balancers found")
    except Exception as e:
        logger.error(f"Error in load balancer cleanup: {e}")
        summary.append(f"⚠️ Load balancer cleanup failed: {str(e)}")

    return summary, savings
