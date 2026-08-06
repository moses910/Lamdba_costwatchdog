"""
EC2 monitoring & free-tier checks — Sections 5, 13, 14.

Functions:
    check_ec2_free_tier
    find_low_utilization_instances
    find_untagged_volumes
"""

import datetime
import logging

logger = logging.getLogger(__name__)


def _get_resource_age(creation_date):
    """Calculate resource age in days."""
    if isinstance(creation_date, str):
        creation_date = datetime.datetime.fromisoformat(
            creation_date.replace('Z', '+00:00')
        )
    return (datetime.datetime.now(datetime.timezone.utc) - creation_date).days


# --- Section 5 ---
def check_ec2_free_tier(ec2):
    """Check if EC2 usage is within the free-tier 750-hour limit.

    Returns:
        list[str]: Summary lines.
    """
    logger.info("Section 5: Checking EC2 free-tier usage...")
    summary = []

    try:
        running_instances = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        instance_count = sum(
            len(r['Instances']) for r in running_instances['Reservations']
        )
        instance_hours = instance_count * 24 * 30

        if instance_hours > 750:
            summary.append(
                f"⚠️ EC2 usage likely exceeds Free Tier "
                f"(estimated {instance_hours} hours)."
            )
            logger.warning(
                f"EC2 usage: {instance_hours} hours (exceeds 750 hour limit)"
            )
        else:
            summary.append(
                f"EC2 usage within free-tier limits ({instance_hours} hours est.)."
            )
            logger.info(f"EC2 usage: {instance_hours} hours (within limits)")
    except Exception as e:
        logger.error(f"Error checking EC2 usage: {e}")
        summary.append(f"⚠️ EC2 usage check failed: {str(e)}")

    return summary


# --- Section 13 ---
def find_low_utilization_instances(ec2, cloudwatch, threshold, start, now):
    """Identify running instances with average CPU below the threshold.

    Args:
        ec2: boto3 EC2 client.
        cloudwatch: boto3 CloudWatch client.
        threshold: CPU utilization percentage threshold.
        start: Start datetime for the metrics window.
        now: Current UTC datetime.

    Returns:
        list[str]: Summary lines.
    """
    logger.info(f"Section 13: Checking for instances with CPU < {threshold}%...")
    summary = []

    try:
        running_instances = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        low_cpu_instances = []

        for reservation in running_instances['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                try:
                    metrics = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[
                            {'Name': 'InstanceId', 'Value': instance_id}
                        ],
                        StartTime=start,
                        EndTime=now,
                        Period=86400,
                        Statistics=['Average'],
                    )
                    if metrics['Datapoints']:
                        avg_cpu = sum(
                            dp['Average'] for dp in metrics['Datapoints']
                        ) / len(metrics['Datapoints'])
                        if avg_cpu < threshold:
                            low_cpu_instances.append(
                                f"{instance_id} ({avg_cpu:.1f}% CPU)"
                            )
                except Exception as e:
                    logger.warning(
                        f"Could not get CPU metrics for {instance_id}: {e}"
                    )

        if low_cpu_instances:
            summary.append(
                f"⚠️ Low utilization instances (consider downsizing): "
                f"{low_cpu_instances}"
            )
            logger.warning(
                f"Found {len(low_cpu_instances)} low-utilization instances"
            )
        else:
            summary.append("No low-utilization instances detected.")
            logger.info("No low-utilization instances detected")
    except Exception as e:
        logger.error(f"Error in utilization check: {e}")
        summary.append(f"⚠️ Utilization check failed: {str(e)}")

    return summary


# --- Section 14 ---
def find_untagged_volumes(ec2, cleanup_days):
    """Find untagged, available EBS volumes older than the cleanup threshold.

    Args:
        ec2: boto3 EC2 client.
        cleanup_days: Age threshold in days for flagging.

    Returns:
        list[str]: Summary lines.
    """
    logger.info(
        f"Section 14: Checking for untagged volumes older than "
        f"{cleanup_days} days..."
    )
    summary = []

    try:
        volumes = ec2.describe_volumes()['Volumes']
        untagged_volumes = []

        for vol in volumes:
            if (
                not vol.get('Tags')
                and _get_resource_age(vol['CreateTime']) > cleanup_days
                and vol['State'] == 'available'
            ):
                untagged_volumes.append(vol['VolumeId'])

        if untagged_volumes:
            summary.append(
                f"⚠️ Found {len(untagged_volumes)} untagged volumes "
                f"older than {cleanup_days} days"
            )
            logger.warning(f"Found {len(untagged_volumes)} old untagged volumes")
        else:
            summary.append("No old untagged volumes found.")
            logger.info("No old untagged volumes found")
    except Exception as e:
        logger.error(f"Error checking untagged resources: {e}")
        summary.append(f"⚠️ Untagged resource check failed: {str(e)}")

    return summary
