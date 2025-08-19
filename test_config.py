"""
Test configuration and mock data for RSU Optimizer tests.
"""

import pandas as pd
from datetime import datetime

# Test RSU data
TEST_RSU_DATA = pd.DataFrame({
    'Company name': [
        'Test Company A',
        'Test Company B', 
        'Test Company C',
        'Test Company D'
    ],
    'Stock Code': ['TESTA', 'TESTB', 'TESTC', 'TESTD'],
    'Grant date': ['20/5/2019', '20/10/2020', '20/1/2021', '20/5/2022'],
    'Vesting date': ['8/20/2020', '1/20/2021', '1/20/2022', '1/20/2023'],
    'Number of units': [100, 150, 200, 250],
    'Section 102': [
        'Capital Gains Route',
        'Ordinary Income Route', 
        'Not under Section 102',
        'Capital Gains Route'
    ]
})

# Test allocation data
TEST_ALLOCATION_DATA = pd.DataFrame({
    'RSU Sale Allocated': [
        '100 units (Test Company A)',
        '150 units (Test Company B)',
        '200 units (Test Company C)',
        '250 units (Test Company D)'
    ],
    'Net': ['10,000 ₪', '15,000 ₪', '20,000 ₪', '25,000 ₪'],
    'Tax Rate': ['25%', '31%', '35%', '25%']
})

# Mock stock prices for testing
MOCK_STOCK_PRICES = {
    'TESTA': {'current': 200.0, 'grant': 100.0},
    'TESTB': {'current': 180.0, 'grant': 120.0},
    'TESTC': {'current': 160.0, 'grant': 140.0},
    'TESTD': {'current': 220.0, 'grant': 110.0}
}

# Expected tax calculations for testing
EXPECTED_TAX_CALCULATIONS = {
    'ordinary_income': {
        50000: 5000.0,      # 50,000 * 0.10
        112000: 11200.0,    # 112,000 * 0.10
        150000: 18520.0,    # 112,000 * 0.10 + 38,000 * 0.14
        200000: 28520.0,    # 112,000 * 0.10 + 76,000 * 0.14 + 12,000 * 0.20
        300000: 51280.0,    # Multiple brackets
        500000: 100280.0,   # Higher brackets
        800000: 200280.0    # Highest brackets
    },
    'capital_gains': {
        10000: 2500.0,      # 10,000 * 0.25
        50000: 12500.0,     # 50,000 * 0.25
        100000: 25000.0,    # 100,000 * 0.25
        500000: 125000.0    # 500,000 * 0.25
    }
}

# Test income levels for bracket testing
TEST_INCOME_LEVELS = [
    0,           # Zero income
    50000,       # First bracket
    112000,      # End of first bracket
    150000,      # Second bracket
    200000,      # Third bracket
    300000,      # Fourth bracket
    500000,      # Fifth bracket
    800000,      # Sixth bracket
    1200000      # Above all brackets
]

# Expected tax rates for each income level
EXPECTED_TAX_RATES = {
    0: 0.0,
    50000: 0.10,
    112000: 0.10,
    150000: 0.14,
    200000: 0.20,
    300000: 0.31,
    500000: 0.35,
    800000: 0.47,
    1200000: 0.47
}

# Test date formats
TEST_DATE_FORMATS = {
    'valid': [
        '2025-06-12',
        '12/06/2025', 
        '12-06-2025',
        '06/12/2025',  # US format
        '2025/06/12'
    ],
    'invalid': [
        'invalid-date',
        '25/13/2025',  # Invalid month
        '32/06/2025',  # Invalid day
        '2025.06.12',  # Unsupported format
        '12.06.2025',  # Unsupported format
        '2025 06 12',  # Unsupported format
        '06-12-2025'   # Unsupported format
    ]
}

# Test allocation strings
TEST_ALLOCATION_STRINGS = {
    'valid': [
        ('100 units (Company A)', (100, ['Company A'])),
        ('150 units (Company A, Company B)', (150, ['Company A', 'Company B'])),
        ('200 units (Company A, Company B, Company C)', (200, ['Company A', 'Company B', 'Company C'])),
        ('1 unit (Company)', (1, ['Company'])),
        ('1000 units (Company A,Company B)', (1000, ['Company A', 'Company B'])),  # No space after comma
    ],
    'invalid': [
        'invalid format',
        '100 units',
        '100 units (',
        '100 units Company A)',
        '',
        None
    ]
}

# Mock exchange rates for testing
MOCK_EXCHANGE_RATES = {
    'success': 3.75,
    'fallback': 3.8
}

# Test currency conversion amounts
TEST_CURRENCY_AMOUNTS = [
    (100, 375.0),
    (500, 1875.0),
    (1000, 3750.0),
    (0.01, 0.0375),
    (1.50, 5.625)
]
