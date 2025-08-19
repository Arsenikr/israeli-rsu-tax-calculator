#!/usr/bin/env python3
"""
Test script to verify that Section 102 Capital Gains Route taxation is correctly implemented.

This test verifies the correct two-layer taxation:
1. Base value (grant price × units) is taxed as ordinary income (progressive)
2. Appreciation (current price - grant price) × units is taxed as capital gains (25%)
"""

import pandas as pd
from app import RSUOptimizer
from unittest.mock import patch


def test_section_102_capital_gains_route():
    """Test Section 102 Capital Gains Route with a concrete example."""
    print("🧮 Testing Section 102 Capital Gains Route Tax Calculation")
    print("=" * 60)
    
    optimizer = RSUOptimizer()
    
    # Create test data based on the example from the issue description
    # Grant price = 100₪, Market price = 150₪, Units = 10
    test_data = pd.DataFrame({
        'Company name': ['Test Company'],
        'Stock Code': ['TEST'],
        'Grant date': ['2023-01-01'],
        'Vesting date': ['2024-01-01'],
        'Number of units': [10],
        'Section 102': ['Capital Gains Route']
    })
    
    # Mock stock prices to return our test values (converted to USD for the mocks)
    # Grant price: 100₪ ÷ 3.8 = ~26.32 USD
    # Current price: 150₪ ÷ 3.8 = ~39.47 USD
    def mock_get_stock_price(ticker, date):
        if 'Grant date' in str(date) or '2023-01-01' in str(date):
            return 26.32  # Grant price in USD
        else:
            return 39.47  # Current price in USD
    
    def mock_get_usd_to_ils_rate():
        return 3.8
    
    # Test with different income levels to verify incremental tax calculation
    test_cases = [
        (0, "No existing income"),
        (50000, "50k existing income (10% bracket)"),
        (150000, "150k existing income (14% bracket)"),
        (300000, "300k existing income (20% bracket)")
    ]
    
    with patch.object(optimizer, 'get_stock_price', side_effect=mock_get_stock_price), \
         patch.object(optimizer, 'get_usd_to_ils_rate', side_effect=mock_get_usd_to_ils_rate):
        
        for current_income, description in test_cases:
            print(f"\n📊 Test Case: {description}")
            print("-" * 40)
            
            # Run optimization
            results = optimizer.optimize_rsu_sales(test_data, current_income, 500)
            
            if not results.empty:
                # Get the result row (not summary)
                result_row = results[results['Company'] != 'Summary'].iloc[0]
                
                # Extract values
                units_sold = result_row['Units to Sell']
                grant_price_nis = float(result_row['Grant Price (NIS)'].replace('₪', ''))
                current_price_nis = float(result_row['Current Price (NIS)'].replace('₪', ''))
                total_gain_str = result_row['Total Gain (NIS)'].replace('₪', '').replace(',', '')
                tax_str = result_row['Tax (NIS)'].replace('₪', '').replace(',', '')
                
                total_gain = float(total_gain_str)
                total_tax = float(tax_str)
                
                # Calculate expected values
                base_value = grant_price_nis * units_sold
                appreciation = (current_price_nis - grant_price_nis) * units_sold
                
                # Expected taxes
                expected_base_tax_before = optimizer.calculate_tax(current_income, 'ordinary_income')
                expected_base_tax_after = optimizer.calculate_tax(current_income + base_value, 'ordinary_income')
                expected_incremental_base_tax = expected_base_tax_after - expected_base_tax_before
                expected_appreciation_tax = appreciation * 0.25
                expected_total_tax = expected_incremental_base_tax + expected_appreciation_tax
                
                print(f"Units sold: {units_sold}")
                print(f"Grant price: {grant_price_nis:.2f}₪ per unit")
                print(f"Current price: {current_price_nis:.2f}₪ per unit")
                print(f"")
                print(f"📊 Component Breakdown:")
                print(f"  Base value: {base_value:.2f}₪ (taxed as ordinary income)")
                print(f"  Appreciation: {appreciation:.2f}₪ (taxed at 25%)")
                print(f"  Total gain: {total_gain:.2f}₪")
                print(f"")
                print(f"🧮 Tax Calculation:")
                print(f"  Current income tax before: {expected_base_tax_before:.2f}₪")
                print(f"  Current income tax after: {expected_base_tax_after:.2f}₪")
                print(f"  Incremental base tax: {expected_incremental_base_tax:.2f}₪")
                print(f"  Appreciation tax (25%): {expected_appreciation_tax:.2f}₪")
                print(f"  Expected total tax: {expected_total_tax:.2f}₪")
                print(f"  Actual total tax: {total_tax:.2f}₪")
                
                # Verify correctness
                if abs(total_tax - expected_total_tax) < 0.01:
                    print(f"  ✅ Tax calculation is CORRECT!")
                else:
                    print(f"  ❌ Tax calculation is INCORRECT!")
                    print(f"     Difference: {total_tax - expected_total_tax:.2f}₪")
                
                # Show effective tax rate
                effective_rate = (total_tax / total_gain) * 100 if total_gain > 0 else 0
                print(f"  Effective tax rate: {effective_rate:.1f}%")
                
            else:
                print("  ❌ No optimization results returned")


def test_comparison_with_pure_ordinary_income():
    """Compare Section 102 Capital Gains Route vs pure ordinary income treatment."""
    print(f"\n🔄 Comparison: Section 102 Capital Gains Route vs Pure Ordinary Income")
    print("=" * 70)
    
    optimizer = RSUOptimizer()
    
    # Same example: 100₪ grant, 150₪ current, 10 units, 50k existing income
    current_income = 50000
    grant_price_nis = 100.0
    current_price_nis = 150.0
    units = 10
    
    base_value = grant_price_nis * units  # 1,000₪
    appreciation = (current_price_nis - grant_price_nis) * units  # 500₪
    total_gain = base_value + appreciation  # 1,500₪
    
    # Section 102 Capital Gains Route calculation
    base_tax_before = optimizer.calculate_tax(current_income, 'ordinary_income')
    base_tax_after = optimizer.calculate_tax(current_income + base_value, 'ordinary_income')
    incremental_base_tax = base_tax_after - base_tax_before
    appreciation_tax = appreciation * 0.25
    section_102_total_tax = incremental_base_tax + appreciation_tax
    
    # Pure ordinary income treatment
    pure_ordinary_tax = optimizer.calculate_tax(current_income + total_gain, 'ordinary_income') - optimizer.calculate_tax(current_income, 'ordinary_income')
    
    print(f"💰 Investment Details:")
    print(f"  Grant price: {grant_price_nis:.0f}₪ × {units} units = {base_value:.0f}₪")
    print(f"  Current price: {current_price_nis:.0f}₪ × {units} units = {current_price_nis * units:.0f}₪")
    print(f"  Total gain: {total_gain:.0f}₪")
    print(f"  Existing income: {current_income:,.0f}₪")
    
    print(f"\n🎯 Section 102 Capital Gains Route:")
    print(f"  Base value tax: {incremental_base_tax:.2f}₪ (progressive on {base_value:.0f}₪)")
    print(f"  Appreciation tax: {appreciation_tax:.2f}₪ (25% on {appreciation:.0f}₪)")
    print(f"  Total tax: {section_102_total_tax:.2f}₪")
    print(f"  Effective rate: {(section_102_total_tax / total_gain * 100):.1f}%")
    
    print(f"\n📈 Pure Ordinary Income Treatment:")
    print(f"  Income tax: {pure_ordinary_tax:.2f}₪ (progressive on {total_gain:.0f}₪)")
    print(f"  Effective rate: {(pure_ordinary_tax / total_gain * 100):.1f}%")
    
    print(f"\n💡 Tax Savings with Section 102:")
    savings = pure_ordinary_tax - section_102_total_tax
    print(f"  Savings: {savings:.2f}₪")
    print(f"  Savings rate: {(savings / pure_ordinary_tax * 100):.1f}%")
    
    if savings > 0:
        print(f"  ✅ Section 102 Capital Gains Route is MORE tax efficient!")
    else:
        print(f"  ❌ Pure ordinary income would be more efficient (rare case)")


if __name__ == "__main__":
    test_section_102_capital_gains_route()
    test_comparison_with_pure_ordinary_income()
    print(f"\n🎯 All tests completed!")
