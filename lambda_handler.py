"""
AWS Cost Watchdog — Main Lambda Handler (Entry Point).

Orchestrates resource cleanup and monitoring across modules:
- modules.config: Configuration parameters
- modules.ec2_cleanup: Stopped instances, unattached EBS, EIPs, old snapshots, unused SGs
- modules.ec2_monitoring: EC2 free-tier, low CPU utilization, untagged resources
- modules.s3_cleanup: Empty S3 buckets, S3 free-tier
- modules.rds_check: RDS free-tier
- modules.lambda_check: Lambda free-tier
- modules.elb_cleanup: Unused load balancers
- modules.logs_retention: CloudWatch logs retention
- modules.cost_explorer: Monthly cost analysis
- modules.notifications: SNS reporting
"""

import datetime
import logging
import boto3  # type: ignore

from modules import config
from modules import ec2_cleanup
from modules import ec2_monitoring
from modules import s3_cleanup
from modules import rds_check
from modules import lambda_check
from modules import elb_cleanup
from modules import logs_retention
from modules import cost_explorer
from modules import notifications

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Main Lambda handler function."""
    logger.info("=" * 60)
    logger.info("Starting AWS Cost Optimization Job")
    logger.info("=" * 60)
    logger.info(f"DRY_RUN mode: {config.DRY_RUN}")
    logger.info(f"Snapshot retention: {config.SNAPSHOT_RETENTION_DAYS} days")
    logger.info(f"Low CPU threshold: {config.LOW_CPU_THRESHOLD}%")

    # Initialize boto3 clients once
    ec2 = boto3.client('ec2')
    s3 = boto3.client('s3')
    rds = boto3.client('rds')
    cloudwatch = boto3.client('cloudwatch')
    elbv2 = boto3.client('elbv2')
    logs = boto3.client('logs')
    ce = boto3.client('ce')

    summary = []
    total_savings = 0.0

    now = datetime.datetime.now(datetime.timezone.utc)
    start_30d = now - datetime.timedelta(days=30)
    start_7d = now - datetime.timedelta(days=7)

    # 1. Terminate stopped EC2 instances
    res_summary, savings = ec2_cleanup.terminate_stopped_instances(ec2, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 2. Delete unattached EBS volumes
    res_summary, savings = ec2_cleanup.delete_unattached_volumes(ec2, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 3. Release unused Elastic IPs
    res_summary, savings = ec2_cleanup.release_unused_eips(ec2, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 4. Delete empty S3 buckets
    res_summary, savings = s3_cleanup.delete_empty_buckets(s3, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 5. Check EC2 free-tier usage
    summary.extend(ec2_monitoring.check_ec2_free_tier(ec2))

    # 6. Check S3 free-tier storage
    summary.extend(s3_cleanup.check_s3_free_tier(s3, cloudwatch, start_30d, now))

    # 7. Check Lambda free-tier invocations
    summary.extend(lambda_check.check_lambda_free_tier(cloudwatch, start_30d, now))

    # 8. Check RDS free-tier usage
    summary.extend(rds_check.check_rds_free_tier(rds))

    # 9. Delete old EBS snapshots
    res_summary, savings = ec2_cleanup.delete_old_snapshots(
        ec2, config.SNAPSHOT_RETENTION_DAYS, config.DRY_RUN
    )
    summary.extend(res_summary)
    total_savings += savings

    # 10. Remove unused security groups
    res_summary, savings = ec2_cleanup.remove_unused_security_groups(ec2, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 11. Delete unused load balancers
    res_summary, savings = elb_cleanup.delete_unused_load_balancers(elbv2, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 12. Set CloudWatch log retention
    res_summary, savings = logs_retention.set_log_retention(logs, config.DRY_RUN)
    summary.extend(res_summary)
    total_savings += savings

    # 13. Identify low CPU utilization instances
    summary.extend(
        ec2_monitoring.find_low_utilization_instances(
            ec2, cloudwatch, config.LOW_CPU_THRESHOLD, start_7d, now
        )
    )

    # 14. Identify untagged resources
    summary.extend(
        ec2_monitoring.find_untagged_volumes(ec2, config.CLEANUP_UNTAGGED_AFTER_DAYS)
    )

    # 15. Cost analysis (monthly on days 1-3)
    ce_summary, savings = cost_explorer.analyze_costs(ce, now)
    summary.extend(ce_summary)
    total_savings += savings

    # Final summary report construction
    logger.info("=" * 60)
    logger.info("Job Complete - Generating Summary")
    logger.info("=" * 60)

    summary.append(f"\n💰 Estimated monthly savings: ${total_savings:.2f}")
    summary.append(f"🕐 Execution completed at: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    report = "\n".join(summary)
    logger.info("\n" + report)

    # Send SNS notification if configured
    notifications.publish_report(config.SNS_TOPIC_ARN, report, "AWS Cost Optimization Report")

    return {
        "statusCode": 200,
        "status": "completed",
        "summary": summary,
        "estimated_savings": total_savings,
        "dry_run": config.DRY_RUN,
        "timestamp": now.isoformat()
    }
