"""
Centralized configuration — all environment variables loaded once.
"""

import os

# SNS topic ARN for notifications (empty = skip notifications)
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')

# Snapshot retention threshold in days
SNAPSHOT_RETENTION_DAYS = int(os.getenv('SNAPSHOT_RETENTION_DAYS', '30'))

# CPU utilization threshold (%) for low-utilization alerts
LOW_CPU_THRESHOLD = float(os.getenv('LOW_CPU_THRESHOLD', '5.0'))

# Days before flagging untagged resources
CLEANUP_UNTAGGED_AFTER_DAYS = int(os.getenv('CLEANUP_UNTAGGED_AFTER_DAYS', '7'))

# Safety switch — defaults to true (no destructive actions)
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'

# Cost Explorer metric type (BlendedCost, UnblendedCost, AmortizedCost)
COST_METRIC = os.getenv('COST_METRIC', 'BlendedCost')
