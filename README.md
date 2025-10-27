🧠 AWS Free-Tier & Resource Cleanup Lambda
Overview

The AWS Daily Resource Cleanup Lambda automatically scans your AWS account once per day to:

Detect and terminate idle or unused services

Check if active resources have exceeded free-tier limits

Identify costly VPC components (NAT Gateways, Load Balancers, Endpoints, VPNs)

Optionally send a summary report to your email via Amazon SNS

This helps reduce unnecessary AWS spending and keep your account clean and cost-efficient.

🏗️ Architecture
+-----------------------------+
| AWS EventBridge (Daily Cron)|
+-------------+---------------+
              |
              v
+-----------------------------------------+
| AWS Lambda Function                    |
|-----------------------------------------|
| - Scans EC2, RDS, S3, Lambda usage      |
| - Deletes stopped/unused resources      |
| - Checks Free-Tier thresholds           |
| - Flags costly VPC components           |
| - Publishes summary via SNS (optional)  |
+-----------------------------------------+
              |
              v
+---------------------------+
| CloudWatch Logs / SNS     |
+---------------------------+

🧰 Features
Category	Checks / Actions
EC2	Terminates stopped instances; estimates total instance-hours vs free-tier (750 hrs)
EBS	Deletes unattached EBS volumes
Elastic IPs	Releases unassociated Elastic IPs
S3	Deletes empty buckets; checks total size vs 5 GB free-tier
Lambda	Monitors monthly invocations (1 M free)
RDS	Checks active instance hours vs 750 hrs free-tier
VPC Resources	Detects active NAT Gateways, Load Balancers, Endpoints, VPNs
Notifications	Sends daily summary to SNS/email (optional)
⚙️ Deployment Steps
1️⃣ Create the Lambda Function

Go to AWS Lambda → Create function

Choose:

Runtime: Python 3.12.3

Architecture: x86_64

Copy and paste the Lambda code
 into the function editor

Set the Timeout to 5 minutes

2️⃣ Configure IAM Role

Attach a custom role or inline policy with the following permissions:

{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": [
      "ec2:*",
      "s3:*",
      "rds:DescribeDBInstances",
      "cloudwatch:GetMetricStatistics",
      "lambda:ListFunctions",
      "sns:Publish",
      "logs:*",
      "elasticloadbalancing:*"
    ], "Resource": "*"}
  ]
}


⚠️ You may narrow these permissions to Describe*, List*, Delete*, and TerminateInstances for stricter security.

3️⃣ (Optional) Configure SNS Notifications

Create an SNS topic (e.g., aws-cleanup-daily-report)

Subscribe to your email address to it

Add the topic ARN to the Lambda’s environment variables:

Key	Value
SNS_TOPIC_ARN	arn:aws:sns:region:account-id:aws-cleanup-daily-report
4️⃣ Schedule Daily Execution

Create an EventBridge Rule:

Schedule expression:

cron(0 0 * * ? *)   # Runs daily at midnight UTC


Target: the Lambda function you just created

🧾 Outputs

CloudWatch Logs: All actions and findings are logged.

SNS Email (optional): A daily summary like:

✅ Terminated stopped EC2 instances: ['i-0abcd1234']
✅ Deleted unattached EBS volumes: ['vol-07efgh5678']
⚠️ Found 2 active NAT Gateways (each ~$0.045/hr)
⚠️ Lambda usage exceeded free-tier: 1,250,000 invocations

🧩 Optional: Dry Run Mode

To preview what the script would delete, set:

DRY_RUN = True


This will log actions only, without deleting or terminating any resources.

💰 Cost Impact Overview
Service	Free Tier	Action
EC2	750 hrs/month	Terminates stopped instances
S3	5 GB storage	Deletes empty buckets
Lambda	1M invocations/month	Logs usage warning
RDS	750 hrs/month: Checks usage
VPC Components	Pay-per-hour	Flags NAT, VPNs, Endpoints, ELBs
🧠 Future Enhancements

 Add AWS Cost Explorer API integration for cost breakdowns

 Include DynamoDB & CloudFront usage

 Add Slack or Teams webhook integration

 Store daily reports in S3 for cost trend tracking

🧑‍💻 Author

Moses Mungai
Cloud Engineer & AI Developer

🌐 LinkedIn https://www.linkedin.com/in/moses-mungai-624746160

💼 Website (https://sites.google.com/view/moses-mungai/home)
