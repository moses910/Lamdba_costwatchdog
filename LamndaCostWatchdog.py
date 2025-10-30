import boto3  # type: ignore
import datetime
import logging
import os
import json
from collections import defaultdict

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:15159149893:aws-daily-cleanup-report')
SNAPSHOT_RETENTION_DAYS = int(os.getenv('SNAPSHOT_RETENTION_DAYS', '30'))
LOW_CPU_THRESHOLD = float(os.getenv('LOW_CPU_THRESHOLD', '5.0'))
CLEANUP_UNTAGGED_AFTER_DAYS = int(os.getenv('CLEANUP_UNTAGGED_AFTER_DAYS', '7'))

def publish_sns(message, subject="AWS Daily Cleanup Report"):
    """Send summary to SNS if topic ARN is configured"""
    if SNS_TOPIC_ARN:
        sns = boto3.client('sns')
        sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
    else:
        logger.info("No SNS topic configured; skipping notification.")

def get_resource_age(creation_date):
    """Calculate resource age in days"""
    if isinstance(creation_date, str):
        creation_date = datetime.datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
    return (datetime.datetime.now(datetime.timezone.utc) - creation_date).days

def lambda_handler(event, context):
    logger.info("Starting enhanced AWS cost optimization job...")

    ec2 = boto3.client('ec2')
    s3 = boto3.client('s3')
    rds = boto3.client('rds')
    cloudwatch = boto3.client('cloudwatch')
    lambda_client = boto3.client('lambda')
    elbv2 = boto3.client('elbv2')
    logs = boto3.client('logs')
    ce = boto3.client('ce')

    summary = []
    cost_savings = 0

    # --- 1. Terminate stopped EC2 instances ---
    instances = ec2.describe_instances()
    stopped = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            state = instance['State']['Name']
            instance_id = instance['InstanceId']
            if state == 'stopped':
                stopped.append(instance_id)

    if stopped:
        ec2.terminate_instances(InstanceIds=stopped)
        summary.append(f"Terminated stopped EC2 instances: {stopped}")
    else:
        summary.append("No stopped EC2 instances found.")

    # --- 2. Delete unattached EBS volumes ---
    volumes = ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
    unused_volumes = [v['VolumeId'] for v in volumes['Volumes']]
    if unused_volumes:
        for vid in unused_volumes:
            ec2.delete_volume(VolumeId=vid)
        summary.append(f"Deleted unused EBS volumes: {unused_volumes}")
    else:
        summary.append("No unattached EBS volumes found.")

    # --- 3. Release unused Elastic IPs ---
    addresses = ec2.describe_addresses()['Addresses']
    unattached_eips = [a['AllocationId'] for a in addresses if 'InstanceId' not in a]
    if unattached_eips:
        for alloc in unattached_eips:
            ec2.release_address(AllocationId=alloc)
        summary.append(f"Released unused Elastic IPs: {unattached_eips}")
    else:
        summary.append("No unattached Elastic IPs found.")

    # --- 4. Delete empty S3 buckets ---
    buckets = s3.list_buckets().get('Buckets', [])
    for bucket in buckets:
        name = bucket['Name']
        try:
            objs = s3.list_objects_v2(Bucket=name)
            if objs.get('KeyCount', 0) == 0:
                s3.delete_bucket(Bucket=name)
                summary.append(f"Deleted empty S3 bucket: {name}")
        except Exception as e:
            logger.warning(f"Could not check/delete bucket {name}: {e}")

    # --- 5. Check EC2 usage (Free Tier 750 hours per month) ---
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(days=30)
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        StartTime=start,
        EndTime=now,
        Period=86400,
        Statistics=['Average']
    )

    # Count running hours for EC2 micro instances
    running_instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    instance_hours = len(running_instances['Reservations']) * 24 * 30
    if instance_hours > 750:
        summary.append(f"⚠️ EC2 usage likely exceeds Free Tier (estimated {instance_hours} hours).")
    else:
        summary.append(f"EC2 usage within free-tier limits ({instance_hours} hours est.).")

    # --- 6. Check S3 usage (Free Tier 5 GB) ---
    total_storage_gb = 0
    for bucket in buckets:
        name = bucket['Name']
        try:
            metrics = cloudwatch.get_metric_statistics(
                Namespace='AWS/S3',
                MetricName='BucketSizeBytes',
                Dimensions=[
                    {'Name': 'BucketName', 'Value': name},
                    {'Name': 'StorageType', 'Value': 'StandardStorage'}
                ],
                StartTime=start,
                EndTime=now,
                Period=86400,
                Statistics=['Average']
            )
            if metrics['Datapoints']:
                bytes_used = metrics['Datapoints'][-1]['Average']
                total_storage_gb += bytes_used / (1024 ** 3)
        except Exception as e:
            logger.warning(f"Could not get S3 metrics for {name}: {e}")

    if total_storage_gb > 5:
        summary.append(f"⚠️ S3 storage exceeds free tier: {total_storage_gb:.2f} GB")
    else:
        summary.append(f"S3 storage within free tier: {total_storage_gb:.2f} GB")

    # --- 7. Check Lambda usage (Free Tier: 1M requests) ---
    metrics = cloudwatch.get_metric_statistics(
        Namespace='AWS/Lambda',
        MetricName='Invocations',
        StartTime=start,
        EndTime=now,
        Period=86400,
        Statistics=['Sum']
    )
    total_invocations = sum(dp['Sum'] for dp in metrics.get('Datapoints', []))
    if total_invocations > 1_000_000:
        summary.append(f"⚠️ Lambda usage exceeded free tier: {int(total_invocations)} invocations.")
    else:
        summary.append(f"Lambda usage within free tier: {int(total_invocations)} invocations.")

    # --- 8. Check RDS free-tier usage (750 hours/month) ---
    rds_instances = rds.describe_db_instances()['DBInstances']
    active_rds = [r['DBInstanceIdentifier'] for r in rds_instances if r['DBInstanceStatus'] == 'available']
    rds_hours = len(active_rds) * 24 * 30
    if rds_hours > 750:
        summary.append(f"⚠️ RDS usage likely exceeds Free Tier ({rds_hours} hours est.).")
    else:
        summary.append(f"RDS usage within free tier ({rds_hours} hours est.).")

    # --- 9. Delete old EBS snapshots ---
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
    old_snapshots = []
    for snap in snapshots:
        age = get_resource_age(snap['StartTime'])
        if age > SNAPSHOT_RETENTION_DAYS:
            old_snapshots.append(snap['SnapshotId'])
            try:
                ec2.delete_snapshot(SnapshotId=snap['SnapshotId'])
            except Exception as e:
                logger.warning(f"Could not delete snapshot {snap['SnapshotId']}: {e}")
    
    if old_snapshots:
        summary.append(f"Deleted {len(old_snapshots)} old snapshots (>{SNAPSHOT_RETENTION_DAYS} days)")
        cost_savings += len(old_snapshots) * 0.05  # ~$0.05 per GB-month

    # --- 10. Remove unused security groups ---
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
            try:
                ec2.delete_security_group(GroupId=sg['GroupId'])
                unused_sgs.append(sg['GroupId'])
            except Exception as e:
                logger.warning(f"Could not delete security group {sg['GroupId']}: {e}")
    
    if unused_sgs:
        summary.append(f"Deleted {len(unused_sgs)} unused security groups")

    # --- 11. Delete unused load balancers ---
    load_balancers = elbv2.describe_load_balancers()['LoadBalancers']
    unused_lbs = []
    for lb in load_balancers:
        targets = elbv2.describe_target_groups(LoadBalancerArn=lb['LoadBalancerArn'])
        if not targets['TargetGroups']:
            try:
                elbv2.delete_load_balancer(LoadBalancerArn=lb['LoadBalancerArn'])
                unused_lbs.append(lb['LoadBalancerName'])
                cost_savings += 18.25  # ~$18.25/month per ALB
            except Exception as e:
                logger.warning(f"Could not delete load balancer {lb['LoadBalancerName']}: {e}")
    
    if unused_lbs:
        summary.append(f"Deleted {len(unused_lbs)} unused load balancers")

    # --- 12. Set CloudWatch log retention ---
    log_groups = logs.describe_log_groups()['logGroups']
    updated_logs = 0
    for lg in log_groups:
        if 'retentionInDays' not in lg or lg.get('retentionInDays', 0) > 30:
            try:
                logs.put_retention_policy(logGroupName=lg['logGroupName'], retentionInDays=30)
                updated_logs += 1
            except Exception as e:
                logger.warning(f"Could not set retention for {lg['logGroupName']}: {e}")
    
    if updated_logs > 0:
        summary.append(f"Set 30-day retention on {updated_logs} log groups")

    # --- 13. Identify low-utilization instances ---
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(days=7)
    low_cpu_instances = []
    
    running_instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    for reservation in running_instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            try:
                metrics = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start,
                    EndTime=now,
                    Period=86400,
                    Statistics=['Average']
                )
                if metrics['Datapoints']:
                    avg_cpu = sum(dp['Average'] for dp in metrics['Datapoints']) / len(metrics['Datapoints'])
                    if avg_cpu < LOW_CPU_THRESHOLD:
                        low_cpu_instances.append(f"{instance_id} ({avg_cpu:.1f}% CPU)")
            except Exception as e:
                logger.warning(f"Could not get CPU metrics for {instance_id}: {e}")
    
    if low_cpu_instances:
        summary.append(f"⚠️ Low utilization instances (consider downsizing): {low_cpu_instances}")

    # --- 14. Delete untagged resources older than threshold ---
    untagged_volumes = []
    volumes = ec2.describe_volumes()['Volumes']
    for vol in volumes:
        if not vol.get('Tags') and get_resource_age(vol['CreateTime']) > CLEANUP_UNTAGGED_AFTER_DAYS:
            if vol['State'] == 'available':
                untagged_volumes.append(vol['VolumeId'])
    
    if untagged_volumes:
        summary.append(f"⚠️ Found {len(untagged_volumes)} untagged volumes older than {CLEANUP_UNTAGGED_AFTER_DAYS} days")

    # --- 15. Cost analysis ---
    try:
        cost_response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': (now - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': now.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        monthly_costs = {}
        for result in cost_response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['BlendedCost']['Amount'])
                monthly_costs[service] = cost
        
        top_costs = sorted(monthly_costs.items(), key=lambda x: x[1], reverse=True)[:5]
        summary.append(f"Top 5 cost drivers: {dict(top_costs)}")
        
        total_monthly = sum(monthly_costs.values())
        summary.append(f"Total monthly cost: ${total_monthly:.2f}")
        
    except Exception as e:
        logger.warning(f"Could not retrieve cost data: {e}")

    # --- Summary ---
    summary.append(f"\n💰 Estimated monthly savings: ${cost_savings:.2f}")
    report = "\n".join(summary)
    logger.info("\n" + report)

    publish_sns(report, "AWS Cost Optimization Report")
    return {"status": "completed", "summary": summary, "estimated_savings": cost_savings}
