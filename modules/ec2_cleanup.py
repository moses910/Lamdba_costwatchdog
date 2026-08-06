"""
EC2 resource cleanup — Sections 1, 2, 3, 9, 10.

Functions:
    terminate_stopped_instances
    delete_unattached_volumes
    release_unused_eips
    delete_old_snapshots
    remove_unused_security_groups
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


# --- Section 1 ---
def terminate_stopped_instances(ec2, dry_run):
    """Terminate EC2 instances in the 'stopped' state.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 1: Checking for stopped EC2 instances...")
    summary = []
    savings = 0

    try:
        instances = ec2.describe_instances()
        stopped = []
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] == 'stopped':
                    stopped.append(instance['InstanceId'])

        if stopped:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would terminate {len(stopped)} stopped EC2 instances: {stopped}"
                )
                logger.info(f"DRY RUN: Would terminate instances: {stopped}")
            else:
                ec2.terminate_instances(InstanceIds=stopped)
                summary.append(
                    f"✅ Terminated {len(stopped)} stopped EC2 instances: {stopped}"
                )
                logger.info(f"Terminated instances: {stopped}")
        else:
            summary.append("No stopped EC2 instances found.")
            logger.info("No stopped instances found")
    except Exception as e:
        logger.error(f"Error in EC2 instance cleanup: {e}")
        summary.append(f"⚠️ EC2 instance cleanup failed: {str(e)}")

    return summary, savings


# --- Section 2 ---
def delete_unattached_volumes(ec2, dry_run):
    """Delete EBS volumes in 'available' (unattached) state.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 2: Checking for unattached EBS volumes...")
    summary = []
    savings = 0

    try:
        volumes = ec2.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        unused_volumes = [v['VolumeId'] for v in volumes['Volumes']]

        if unused_volumes:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would delete {len(unused_volumes)} unused EBS volumes"
                )
                logger.info(f"DRY RUN: Would delete volumes: {unused_volumes}")
            else:
                deleted_count = 0
                for vid in unused_volumes:
                    try:
                        ec2.delete_volume(VolumeId=vid)
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete volume {vid}: {e}")
                summary.append(f"✅ Deleted {deleted_count} unused EBS volumes")
                logger.info(f"Deleted {deleted_count} volumes")
        else:
            summary.append("No unattached EBS volumes found.")
            logger.info("No unattached volumes found")
    except Exception as e:
        logger.error(f"Error in EBS volume cleanup: {e}")
        summary.append(f"⚠️ EBS volume cleanup failed: {str(e)}")

    return summary, savings


# --- Section 3 ---
def release_unused_eips(ec2, dry_run):
    """Release Elastic IPs not associated with any instance.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 3: Checking for unused Elastic IPs...")
    summary = []
    savings = 0

    try:
        addresses = ec2.describe_addresses()['Addresses']
        unattached_eips = [
            a['AllocationId'] for a in addresses if 'InstanceId' not in a
        ]

        if unattached_eips:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would release {len(unattached_eips)} unused Elastic IPs"
                )
                logger.info(f"DRY RUN: Would release EIPs: {unattached_eips}")
            else:
                released_count = 0
                for alloc in unattached_eips:
                    try:
                        ec2.release_address(AllocationId=alloc)
                        released_count += 1
                    except Exception as e:
                        logger.warning(f"Could not release EIP {alloc}: {e}")
                summary.append(f"✅ Released {released_count} unused Elastic IPs")
                logger.info(f"Released {released_count} EIPs")
        else:
            summary.append("No unattached Elastic IPs found.")
            logger.info("No unattached EIPs found")
    except Exception as e:
        logger.error(f"Error in Elastic IP cleanup: {e}")
        summary.append(f"⚠️ Elastic IP cleanup failed: {str(e)}")

    return summary, savings


# --- Section 9 ---
def delete_old_snapshots(ec2, retention_days, dry_run):
    """Delete EBS snapshots older than the retention threshold.

    Args:
        ec2: boto3 EC2 client.
        retention_days: Number of days to retain snapshots.
        dry_run: If True, report but do not delete.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info(f"Section 9: Checking for snapshots older than {retention_days} days...")
    summary = []
    savings = 0

    try:
        snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
        old_snapshots = []

        for snap in snapshots:
            age = _get_resource_age(snap['StartTime'])
            if age > retention_days:
                old_snapshots.append(snap['SnapshotId'])
                if not dry_run:
                    try:
                        ec2.delete_snapshot(SnapshotId=snap['SnapshotId'])
                    except Exception as e:
                        logger.warning(
                            f"Could not delete snapshot {snap['SnapshotId']}: {e}"
                        )

        if old_snapshots:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would delete {len(old_snapshots)} old snapshots "
                    f"(>{retention_days} days)"
                )
                logger.info(f"DRY RUN: Would delete {len(old_snapshots)} snapshots")
            else:
                summary.append(
                    f"✅ Deleted {len(old_snapshots)} old snapshots "
                    f"(>{retention_days} days)"
                )
                savings += len(old_snapshots) * 0.05  # ~$0.05 per GB-month
                logger.info(f"Deleted {len(old_snapshots)} snapshots")
        else:
            summary.append(f"No snapshots older than {retention_days} days found.")
            logger.info("No old snapshots found")
    except Exception as e:
        logger.error(f"Error in snapshot cleanup: {e}")
        summary.append(f"⚠️ Snapshot cleanup failed: {str(e)}")

    return summary, savings


# --- Section 10 ---
def remove_unused_security_groups(ec2, dry_run):
    """Delete security groups not attached to any non-terminated instance.

    Skips the 'default' security group which cannot be deleted.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 10: Checking for unused security groups...")
    summary = []
    savings = 0

    try:
        security_groups = ec2.describe_security_groups()['SecurityGroups']
        instances = ec2.describe_instances()
        used_sgs = set()

        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] != 'terminated':
                    for sg in instance['SecurityGroups']:
                        used_sgs.add(sg['GroupId'])

        unused_sgs = []
        for sg in security_groups:
            if sg['GroupName'] != 'default' and sg['GroupId'] not in used_sgs:
                unused_sgs.append(sg['GroupId'])
                if not dry_run:
                    try:
                        ec2.delete_security_group(GroupId=sg['GroupId'])
                    except Exception as e:
                        logger.warning(
                            f"Could not delete security group {sg['GroupId']}: {e}"
                        )

        if unused_sgs:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would delete {len(unused_sgs)} unused security groups"
                )
                logger.info(f"DRY RUN: Would delete {len(unused_sgs)} security groups")
            else:
                summary.append(f"✅ Deleted {len(unused_sgs)} unused security groups")
                logger.info(f"Deleted {len(unused_sgs)} security groups")
        else:
            summary.append("No unused security groups found.")
            logger.info("No unused security groups found")
    except Exception as e:
        logger.error(f"Error in security group cleanup: {e}")
        summary.append(f"⚠️ Security group cleanup failed: {str(e)}")

    return summary, savings
