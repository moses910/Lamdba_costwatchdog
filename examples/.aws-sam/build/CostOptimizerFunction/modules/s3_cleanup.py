"""
S3 cleanup & free-tier monitoring — Sections 4, 6.

Functions:
    delete_empty_buckets
    check_s3_free_tier
"""

import logging

logger = logging.getLogger(__name__)


# --- Section 4 ---
def delete_empty_buckets(s3, dry_run):
    """Delete S3 buckets that contain zero objects.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 4: Checking for empty S3 buckets...")
    summary = []
    savings = 0

    try:
        buckets = s3.list_buckets().get('Buckets', [])
        empty_buckets = []

        for bucket in buckets:
            name = bucket['Name']
            try:
                objs = s3.list_objects_v2(Bucket=name)
                if objs.get('KeyCount', 0) == 0:
                    empty_buckets.append(name)
                    if not dry_run:
                        s3.delete_bucket(Bucket=name)
            except Exception as e:
                logger.warning(f"Could not check/delete bucket {name}: {e}")

        if empty_buckets:
            if dry_run:
                summary.append(
                    f"[DRY RUN] Would delete {len(empty_buckets)} empty S3 buckets"
                )
                logger.info(f"DRY RUN: Would delete buckets: {empty_buckets}")
            else:
                summary.append(
                    f"✅ Deleted {len(empty_buckets)} empty S3 buckets"
                )
                logger.info(f"Deleted {len(empty_buckets)} buckets")
        else:
            summary.append("No empty S3 buckets found.")
            logger.info("No empty S3 buckets found")
    except Exception as e:
        logger.error(f"Error in S3 bucket cleanup: {e}")
        summary.append(f"⚠️ S3 bucket cleanup failed: {str(e)}")

    return summary, savings


# --- Section 6 ---
def check_s3_free_tier(s3, cloudwatch, start, now):
    """Check total S3 storage against the 5 GB free-tier limit.

    Args:
        s3: boto3 S3 client.
        cloudwatch: boto3 CloudWatch client.
        start: Start datetime for the metrics window.
        now: Current UTC datetime.

    Returns:
        list[str]: Summary lines.
    """
    logger.info("Section 6: Checking S3 free-tier usage...")
    summary = []

    try:
        total_storage_gb = 0
        buckets = s3.list_buckets().get('Buckets', [])

        for bucket in buckets:
            name = bucket['Name']
            try:
                metrics = cloudwatch.get_metric_statistics(
                    Namespace='AWS/S3',
                    MetricName='BucketSizeBytes',
                    Dimensions=[
                        {'Name': 'BucketName', 'Value': name},
                        {'Name': 'StorageType', 'Value': 'StandardStorage'},
                    ],
                    StartTime=start,
                    EndTime=now,
                    Period=86400,
                    Statistics=['Average'],
                )
                if metrics['Datapoints']:
                    bytes_used = metrics['Datapoints'][-1]['Average']
                    total_storage_gb += bytes_used / (1024 ** 3)
            except Exception as e:
                logger.warning(f"Could not get S3 metrics for {name}: {e}")

        if total_storage_gb > 5:
            summary.append(
                f"⚠️ S3 storage exceeds free tier: {total_storage_gb:.2f} GB"
            )
            logger.warning(
                f"S3 storage: {total_storage_gb:.2f} GB (exceeds 5 GB limit)"
            )
        else:
            summary.append(
                f"S3 storage within free tier: {total_storage_gb:.2f} GB"
            )
            logger.info(
                f"S3 storage: {total_storage_gb:.2f} GB (within limits)"
            )
    except Exception as e:
        logger.error(f"Error checking S3 usage: {e}")
        summary.append(f"⚠️ S3 usage check failed: {str(e)}")

    return summary
