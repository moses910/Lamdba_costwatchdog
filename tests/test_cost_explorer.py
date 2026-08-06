"""
Unit tests for AWS Cost Watchdog modules and lambda_handler.
"""

import datetime
import unittest
from unittest.mock import patch, MagicMock

from modules import cost_explorer
from modules import config


class TestCostExplorer(unittest.TestCase):

    def test_cost_explorer_skipped_on_day_15(self):
        mock_ce = MagicMock()
        mid_month_date = datetime.datetime(2026, 8, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
        summary, savings = cost_explorer.analyze_costs(mock_ce, mid_month_date)

        self.assertEqual(savings, 0)
        self.assertIn("Cost Explorer skipped (runs monthly on days 1-3)", summary[0])
        mock_ce.get_cost_and_usage.assert_not_called()

    @patch('boto3.client')
    def test_cost_explorer_runs_on_day_1(self, mock_boto3_client):
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = Exception("ParameterNotFound")
        mock_boto3_client.return_value = mock_ssm

        mock_ce = MagicMock()
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'Groups': [
                        {
                            'Keys': ['Amazon EC2'],
                            'Metrics': {'BlendedCost': {'Amount': '150.50'}}
                        }
                    ]
                }
            ]
        }

        first_of_month = datetime.datetime(2026, 8, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        summary, savings = cost_explorer.analyze_costs(mock_ce, first_of_month)

        mock_ce.get_cost_and_usage.assert_called_once()
        self.assertTrue(any("Top 5 cost drivers" in line for line in summary))
        self.assertTrue(any("$150.50" in line for line in summary))


class TestLambdaHandler(unittest.TestCase):

    @patch('boto3.client')
    def test_lambda_handler_execution(self, mock_boto3_client):
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {'Reservations': []}
        mock_client.describe_volumes.return_value = {'Volumes': []}
        mock_client.describe_addresses.return_value = {'Addresses': []}
        mock_client.list_buckets.return_value = {'Buckets': []}
        mock_client.describe_snapshots.return_value = {'Snapshots': []}
        mock_client.describe_security_groups.return_value = {'SecurityGroups': []}
        mock_client.describe_load_balancers.return_value = {'LoadBalancers': []}
        mock_client.describe_log_groups.return_value = {'logGroups': []}
        mock_client.describe_db_instances.return_value = {'DBInstances': []}
        mock_client.get_metric_statistics.return_value = {'Datapoints': []}

        mock_boto3_client.return_value = mock_client

        from lambda_handler import lambda_handler
        result = lambda_handler({}, {})

        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['dry_run'])


if __name__ == '__main__':
    unittest.main()
