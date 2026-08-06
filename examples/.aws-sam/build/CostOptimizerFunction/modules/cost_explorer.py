"""
AWS Cost Explorer analysis module — Section 15.

Key refactoring fixes applied:
1. Runs monthly on days 1-3 with SSM deduplication parameter `/lambda/cost-analysis-last-run`.
2. Queries the exact previous calendar month (1st of prev month to 1st of current month).
3. Handles API pagination via NextPageToken.
4. Uses configurable cost metric via config.COST_METRIC (default: BlendedCost).
"""

import datetime
import logging
import boto3  # type: ignore
from modules import config

logger = logging.getLogger(__name__)

SSM_PARAMETER_NAME = '/lambda/cost-analysis-last-run'


def analyze_costs(ce_client, now):
    """Perform monthly AWS Cost Explorer analysis.

    Runs only on days 1-3 of the month. Uses SSM parameter to ensure
    it runs at most once per month.

    Args:
        ce_client: boto3 Cost Explorer client.
        now: Current UTC datetime.

    Returns:
        tuple: (summary_lines: list[str], cost_savings: float)
    """
    logger.info("Section 15: Checking if cost analysis should run...")
    summary = []
    savings = 0

    if not (1 <= now.day <= 3):
        summary.append("Cost Explorer skipped (runs monthly on days 1-3)")
        logger.info(f"Cost analysis skipped (today is day {now.day})")
        return summary, savings

    try:
        current_month = now.strftime('%Y-%m')

        # SSM deduplication check
        already_ran_this_month = False
        try:
            ssm = boto3.client('ssm')
            last_run = ssm.get_parameter(Name=SSM_PARAMETER_NAME)['Parameter']['Value']
            already_ran_this_month = (last_run == current_month)
        except Exception:
            # Parameter doesn't exist or SSM is not accessible
            already_ran_this_month = False

        if already_ran_this_month:
            summary.append(f"Cost analysis already completed for {current_month}")
            logger.info(f"Cost analysis already ran for {current_month}")
            return summary, savings

        logger.info("Running monthly cost analysis...")

        # Exact previous calendar month range
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_of_prev_month = first_of_this_month - datetime.timedelta(days=1)
        first_of_prev_month = last_of_prev_month.replace(day=1)

        # CE End date is exclusive
        time_period = {
            'Start': first_of_prev_month.strftime('%Y-%m-%d'),
            'End': first_of_this_month.strftime('%Y-%m-%d')
        }

        monthly_costs = {}
        next_token = None

        while True:
            kwargs = {
                'TimePeriod': time_period,
                'Granularity': 'MONTHLY',
                'Metrics': [config.COST_METRIC],
                'GroupBy': [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            }
            if next_token:
                kwargs['NextPageToken'] = next_token

            cost_response = ce_client.get_cost_and_usage(**kwargs)

            for result in cost_response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    cost = float(group['Metrics'][config.COST_METRIC]['Amount'])
                    monthly_costs[service] = monthly_costs.get(service, 0.0) + cost

            next_token = cost_response.get('NextPageToken')
            if not next_token:
                break

        top_costs = sorted(monthly_costs.items(), key=lambda x: x[1], reverse=True)[:5]
        summary.append(f"📊 Top 5 cost drivers: {dict(top_costs)}")

        total_monthly = sum(monthly_costs.values())
        summary.append(f"💵 Total monthly cost ({config.COST_METRIC}): ${total_monthly:.2f}")

        # Update SSM tracking parameter
        try:
            ssm.put_parameter(
                Name=SSM_PARAMETER_NAME,
                Value=current_month,
                Type='String',
                Overwrite=True
            )
            logger.info(f"Cost analysis completed and recorded for {current_month}")
        except Exception as e:
            logger.warning(f"Could not update SSM parameter: {e}")

    except Exception as e:
        logger.error(f"Error in cost analysis: {e}")
        summary.append(f"⚠️ Cost analysis failed: {str(e)}")

    return summary, savings
