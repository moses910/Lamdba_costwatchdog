import unittest
from unittest.mock import patch, MagicMock
import lambda_function

class TestLambdaFunction(unittest.TestCase):

    @patch('boto3.client')
    def test_lambda_handler_success(self, mock_boto3_client):
        # Mock the Cost Explorer client
        mock_ce = MagicMock()
        mock_ce.get_cost_and_usage.return_value = {
            'ResultsByTime': [
                {
                    'Groups': [
                        {
                            'Metrics': {
                                'BlendedCost': {'Amount': '100.0'}
                            }
                        }
                    ]
                }
            ]
        }

        # Mock SNS client
        mock_sns = MagicMock()

        mock_boto3_client.side_effect = [mock_ce, mock_sns]

        # Test event and context
        event = {}
        context = {}

        result = lambda_function.lambda_handler(event, context)

        self.assertEqual(result['statusCode'], 200)
        self.assertIn('Cost optimization check completed', result['body'])

    @patch('boto3.client')
    def test_lambda_handler_error(self, mock_boto3_client):
        mock_boto3_client.side_effect = Exception('Test error')

        event = {}
        context = {}

        result = lambda_function.lambda_handler(event, context)

        self.assertEqual(result['statusCode'], 500)
        self.assertIn('error', result['body'])

if __name__ == '__main__':
    unittest.main()