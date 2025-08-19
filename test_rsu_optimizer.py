import unittest
import pandas as pd
from unittest.mock import patch
from app import RSUOptimizer

class TestRSUOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = RSUOptimizer()

    @patch('app.RSUOptimizer.get_stock_price')
    @patch('app.RSUOptimizer.get_fx_rate')
    def test_section_102_capital_gain(self, mock_get_fx_rate, mock_get_stock_price):
        # Mock API calls
        mock_get_stock_price.side_effect = [150.0, 50.0]  # sale_price_usd, grant_price_usd
        mock_get_fx_rate.side_effect = [3.8, 3.5]  # sale_fx, grant_fx

        # Setup test data
        rsu_data = pd.DataFrame({
            'Company name': ['TestCorp'],
            'Stock Code': ['TC'],
            'Grant date': ['2022-01-01'],
            'Vesting date': ['2023-01-01'],
            'Number of units': [100],
            'Section 102': ['Capital Gains Route']
        })
        current_income = 100000
        target_bracket_limit = 269280

        # Run optimization
        results_df = self.optimizer.optimize_rsu_sales(rsu_data, current_income, target_bracket_limit)

        # Assertions
        self.assertEqual(len(results_df), 1)
        self.assertEqual(results_df.iloc[0]['Units to Sell'], 100)
        self.assertAlmostEqual(float(results_df.iloc[0]['Ordinary Total (NIS)'].replace(',', '')), 17500.00)
        self.assertAlmostEqual(float(results_df.iloc[0]['Capital Gain Total (NIS)'].replace(',', '')), 39500.00)
        self.assertAlmostEqual(float(results_df.iloc[0]['Income Tax (NIS)'].replace(',', '')), 2450.00)
        self.assertAlmostEqual(float(results_df.iloc[0]['Net Proceeds (NIS)'].replace(',', '')), 44675.00)

    @patch('app.RSUOptimizer.get_stock_price')
    @patch('app.RSUOptimizer.get_fx_rate')
    def test_non_section_102(self, mock_get_fx_rate, mock_get_stock_price):
        # Mock API calls
        mock_get_stock_price.side_effect = [150.0, 50.0, 100.0]  # sale_price_usd, grant_price_usd, vest_price_usd
        mock_get_fx_rate.side_effect = [3.8, 3.5, 3.6]  # sale_fx, grant_fx, vest_fx

        # Setup test data
        rsu_data = pd.DataFrame({
            'Company name': ['TestCorp'],
            'Stock Code': ['TC'],
            'Grant date': ['2022-01-01'],
            'Vesting date': ['2023-01-01'],
            'Number of units': [100],
            'Section 102': ['Not Capital Gains Route']
        })
        current_income = 100000
        target_bracket_limit = 269280

        # Run optimization
        results_df = self.optimizer.optimize_rsu_sales(rsu_data, current_income, target_bracket_limit)

        # Assertions
        self.assertEqual(len(results_df), 0) # No ordinary income to optimize

    @patch('app.RSUOptimizer.get_stock_price')
    @patch('app.RSUOptimizer.get_fx_rate')
    def test_negative_capital_gain(self, mock_get_fx_rate, mock_get_stock_price):
        # Mock API calls
        mock_get_stock_price.side_effect = [40.0, 50.0]  # sale_price_usd, grant_price_usd
        mock_get_fx_rate.side_effect = [3.8, 3.5]  # sale_fx, grant_fx

        # Setup test data
        rsu_data = pd.DataFrame({
            'Company name': ['TestCorp'],
            'Stock Code': ['TC'],
            'Grant date': ['2022-01-01'],
            'Vesting date': ['2023-01-01'],
            'Number of units': [100],
            'Section 102': ['Capital Gains Route']
        })
        current_income = 100000
        target_bracket_limit = 269280

        # Run optimization
        results_df = self.optimizer.optimize_rsu_sales(rsu_data, current_income, target_bracket_limit)

        # Assertions
        self.assertEqual(len(results_df), 1)
        self.assertEqual(results_df.iloc[0]['Units to Sell'], 100)
        self.assertAlmostEqual(float(results_df.iloc[0]['Ordinary Total (NIS)'].replace(',', '')), 15200.00)
        self.assertAlmostEqual(float(results_df.iloc[0]['Capital Gain Total (NIS)'].replace(',', '')), 0.00)
        self.assertAlmostEqual(float(results_df.iloc[0]['Income Tax (NIS)'].replace(',', '')), 2128.00)
        self.assertAlmostEqual(float(results_df.iloc[0]['Net Proceeds (NIS)'].replace(',', '')), 13072.00)

if __name__ == '__main__':
    unittest.main()
