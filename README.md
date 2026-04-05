# 🧠 AWS Cost Optimiser Lambda

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)

An automated, serverless AWS cost optimisation tool that identifies and cleans up unused resources, monitors free-tier usage, and provides monthly cost analysis reports.

**🚀 Deployed via Lambda • 📊 Daily monitoring • 💰 Automatic cost savings**

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Safety Features](#-safety-features)
- [What It Does](#-what-it-does)
- [Example Output](#-example-output)
- [Deployment Options](#-deployment-options)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## ✨ Features

### **Automated Resource Cleanup**
- ✅ Terminates stopped EC2 instances
- ✅ Deletes unattached EBS volumes
- ✅ Releases unused Elastic IPs
- ✅ Removes empty S3 buckets
- ✅ Deletes old EBS snapshots (configurable retention)
- ✅ Cleans up unused security groups
- ✅ Removes unused load balancers

### **Free Tier Monitoring**
- 📊 EC2 usage tracking (750 hours/month limit)
- 📊 S3 storage monitoring (5 GB limit)
- 📊 Lambda invocations tracking (1M requests/month)
- 📊 RDS usage monitoring (750 hours/month)

### **Cost Intelligence**
- 💰 Monthly cost breakdown by service (runs 1st-3rd of each month)
- 💰 Top 5 cost drivers identification
- 💰 Estimated monthly savings calculation

### **Resource Optimization**
- 🔍 Identifies low CPU utilization instances
- 🔍 Sets CloudWatch log retention to 30 days
- 🔍 Flags untagged resources older than threshold

### **Safety & Reliability**
- 🛡️ **DRY_RUN mode** (enabled by default - test before deleting!)
- 🛡️ Comprehensive error handling
- 🛡️ Continues execution even if one check fails
- 🛡️ SNS notifications with detailed reports
- 🛡️ Detailed CloudWatch logging

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  EventBridge (Daily Schedule)   │
│     cron(0 2 * * ? *)           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│        AWS Lambda Function                  │
│  ┌────────────────────────────────────┐    │
│  │ 1. Scan & Clean EC2, EBS, EIPs     │    │
│  │ 2. Monitor S3, Lambda, RDS usage   │    │
│  │ 3. Check Free-Tier limits          │    │
│  │ 4. Analyze costs (monthly)         │    │
│  │ 5. Generate savings report         │    │
│  └────────────────────────────────────┘    │
└──────────────┬──────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   CloudWatch      SNS Topic
     Logs          (Email)
```

---

## 🚀 Quick Start

### Prerequisites
- AWS Account
- AWS CLI configured
- Python 3.9 or higher
- Appropriate IAM permissions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/moses910/Lamdba_costwatchdog.git
cd Lamdba_costwatchdog
```

### 2️⃣ Deploy Using PowerShell (Recommended for Windows)
```powershell
# Deploy SNS topic first
.\deploy-sns.ps1

# Deploy Lambda function
.\deploy.ps1
```

### 3️⃣ Or Deploy Manually

**Create Lambda Function:**
```bash
# Package the code
zip function.zip lambda_function.py

# Create function
aws lambda create-function \
  --function-name aws-cost-optimizer \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 300 \
  --memory-size 256 \
  --environment Variables="{DRY_RUN=true}"
```

**Set Up Daily Schedule:**
```bash
aws events put-rule \
  --name daily-cost-optimizer \
  --schedule-expression "cron(0 2 * * ? *)"

aws events put-targets \
  --rule daily-cost-optimizer \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:aws-cost-optimizer"

aws lambda add-permission \
  --function-name aws-cost-optimizer \
  --statement-id AllowEventBridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | **Set to `false` to enable actual deletions** |
| `SNS_TOPIC_ARN` | - | SNS topic ARN for email notifications |
| `SNAPSHOT_RETENTION_DAYS` | `30` | Days to keep EBS snapshots before deletion |
| `LOW_CPU_THRESHOLD` | `5.0` | CPU % threshold for low-utilization alerts |
| `CLEANUP_UNTAGGED_AFTER_DAYS` | `7` | Days before flagging untagged resources |

### Setting Environment Variables

**Via AWS Console:**
1. Go to Lambda → Functions → aws-cost-optimizer
2. Configuration → Environment variables
3. Add/Edit variables
4. Save

**Via AWS CLI:**
```bash
aws lambda update-function-configuration \
  --function-name aws-cost-optimizer \
  --environment Variables="{
    DRY_RUN=false,
    SNS_TOPIC_ARN=arn:aws:sns:REGION:ACCOUNT:cost-optimizer-alerts,
    SNAPSHOT_RETENTION_DAYS=30,
    LOW_CPU_THRESHOLD=5.0,
    CLEANUP_UNTAGGED_AFTER_DAYS=7
  }"
```

---

## 🛡️ Safety Features

### DRY_RUN Mode (Default: Enabled)

**ALWAYS test in DRY_RUN mode first!**

When `DRY_RUN=true`:
- ✅ Scans all resources
- ✅ Reports what **would** be deleted
- ✅ Sends notifications
- ❌ **Does NOT delete anything**

### Testing Workflow

1. **Deploy with `DRY_RUN=true`** (default)
2. **Run manually** via AWS Console or CLI
3. **Review CloudWatch Logs** and SNS notifications
4. **Verify** what would be deleted is safe
5. **Set `DRY_RUN=false`** only when confident
6. **Monitor** first few production runs closely

### Error Handling

- Each cleanup section runs independently
- Failures in one section don't stop other checks
- All errors logged to CloudWatch
- Failed operations reported in summary

---

## 🔍 What It Does

### Daily Operations

| # | Check | Action | Free Tier Limit |
|---|-------|--------|-----------------|
| 1 | Stopped EC2 instances | Terminate | - |
| 2 | Unattached EBS volumes | Delete | - |
| 3 | Unused Elastic IPs | Release | - |
| 4 | Empty S3 buckets | Delete | 5 GB |
| 5 | EC2 usage | Monitor | 750 hrs/month |
| 6 | S3 storage | Monitor | 5 GB |
| 7 | Lambda invocations | Monitor | 1M requests/month |
| 8 | RDS instances | Monitor | 750 hrs/month |
| 9 | Old EBS snapshots | Delete (>30 days) | - |
| 10 | Unused security groups | Delete | - |
| 11 | Unused load balancers | Delete | ~$18.25/month savings each |
| 12 | CloudWatch logs | Set 30-day retention | - |
| 13 | Low CPU instances | Flag for review | < 5% CPU |
| 14 | Untagged resources | Flag if >7 days old | - |

### Monthly Operations (Days 1-3)

| # | Check | Description |
|---|-------|-------------|
| 15 | Cost Explorer | Analyze spending by service, identify top cost drivers |

---

## 📊 Example Output

### DRY_RUN Mode (Testing)
```
[DRY RUN] Would terminate 2 stopped EC2 instances: ['i-abc123', 'i-def456']
[DRY RUN] Would delete 3 unused EBS volumes
[DRY RUN] Would release 1 unused Elastic IPs
No empty S3 buckets found.
EC2 usage within free-tier limits (120 hours est.).
S3 storage within free tier: 2.34 GB
Lambda invocations within free tier: 45,230
RDS usage within free tier (0 hours est.).
[DRY RUN] Would delete 5 old snapshots (>30 days)
No unused security groups found.
No unused load balancers found.
[DRY RUN] Would set 30-day retention on 8 log groups
⚠️ Low utilization instances (consider downsizing): ['i-xyz789 (2.3% CPU)']
No old untagged volumes found.
Cost Explorer skipped (runs monthly on days 1-3)

💰 Estimated monthly savings: $12.50
🕐 Execution completed at: 2025-12-27 22:15:00 UTC
```

### Production Mode (DRY_RUN=false)
```
✅ Terminated 2 stopped EC2 instances: ['i-abc123', 'i-def456']
✅ Deleted 3 unused EBS volumes
✅ Released 1 unused Elastic IPs
✅ Deleted 5 old snapshots (>30 days)
✅ Set 30-day retention on 8 log groups

💰 Estimated monthly savings: $12.50
```

---

## 📦 Deployment Options

### Option 1: PowerShell Scripts (Windows - Easiest)
```powershell
.\deploy-sns.ps1          # Set up SNS notifications
.\deploy.ps1              # Deploy Lambda function
```

### Option 2: CloudFormation (Infrastructure as Code)
```bash
# Coming soon - CloudFormation template in development
aws cloudformation create-stack \
  --stack-name aws-cost-optimizer \
  --template-body file://cloudformation-template.yaml
```

### Option 3: Terraform (Multi-cloud)
```bash
# Coming soon - Terraform configuration in development
```

### Option 4: Manual Deployment
See [Quick Start](#-quick-start) section above.

---

## 🔐 Security Best Practices

1. **Start with DRY_RUN=true** - Always test before enabling deletions
2. **Tag critical resources** - Add tags like `DoNotDelete=true` to protect important resources
3. **Review IAM permissions** - Use least privilege principle (see `lambda-iam-policy.json`)
4. **Enable CloudTrail** - Audit all Lambda actions
5. **Monitor SNS alerts** - Review reports regularly
6. **Test in non-production first** - Use a sandbox AWS account initially

---

## 📝 IAM Permissions Required

The Lambda function needs these permissions (see `lambda-iam-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*", "ec2:TerminateInstances", "ec2:DeleteVolume",
        "s3:ListAllMyBuckets", "s3:DeleteBucket",
        "rds:DescribeDBInstances",
        "cloudwatch:GetMetricStatistics",
        "elasticloadbalancing:*",
        "logs:DescribeLogGroups", "logs:PutRetentionPolicy",
        "ce:GetCostAndUsage",
        "sns:Publish",
        "ssm:GetParameter", "ssm:PutParameter"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas We Need Help With

- [ ] Terraform deployment templates
- [ ] Multi-region support
- [ ] Additional cleanup checks (NAT Gateways, CloudFront, etc.)
- [ ] Cost optimisation recommendations engine
- [ ] Dashboard/UI for visualisation
- [ ] Slack/Teams integration
- [ ] Unit tests and integration tests

### Development Setup

```bash
# Clone the repo
git clone https://github.com/moses910/Lamdba_costwatchdog.git
cd Lamdba_costwatchdog

# Install dependencies
pip install -r requirements.txt

# Run tests (coming soon)
# python -m pytest tests/
```

---

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK.** This tool deletes AWS resources.

**Before using in production:**
- ✅ Test thoroughly in DRY_RUN mode
- ✅ Use in a non-production AWS account first
- ✅ Review all logs and reports
- ✅ Ensure critical resources are tagged
- ✅ Have backups of important data
- ✅ Understand each cleanup action

**The authors are not responsible for:**
- Data loss
- Service disruptions
- Unexpected AWS charges
- Any damages resulting from the use of this tool

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Moses Mungai**  
Cloud Engineer & AI Developer

- 🌐 **Website**: [moses-mungai.com](https://sites.google.com/view/moses-mungai/home)
- 💼 **LinkedIn**: [Moses Mungai](https://www.linkedin.com/in/moses-mungai-624746160)
- 🐙 **GitHub**: [@moses910](https://github.com/moses910)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/moses910/Lamdba_costwatchdog/issues)
- **Discussions**: [GitHub Discussions](https://github.com/moses910/Lamdba_costwatchdog/discussions)
- **Questions**: Open an issue with the `question` label

---

## 🗺️ Roadmap

- [x] v1.0: Core cleanup and monitoring features
- [x] v1.1: DRY_RUN mode and error handling
- [x] v1.2: Monthly cost analysis with SSM tracking
- [ ] v1.3: CloudFormation and Terraform templates
- [ ] v1.4: Multi-region support
- [ ] v2.0: Web dashboard for visualization
- [ ] v2.1: Machine learning-based cost recommendations
- [ ] v2.2: Slack/Teams integration

---

## 🙏 Acknowledgments

- Inspired by AWS cost optimisation best practices
- Built for the AWS community
- Special thanks to all contributors

---

## ⭐ Star History

If you find this tool useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the AWS Community**
