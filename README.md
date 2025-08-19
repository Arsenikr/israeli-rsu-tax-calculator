# RSU Sell Optimizer for Israeli Taxpayers

This tool helps Israeli taxpayers optimize RSU (Restricted Stock Unit) sales by analyzing tax brackets, Section 102 eligibility, and real-time stock prices.

## Features

- Real-time stock price updates
- Automatic currency conversion (USD to NIS)
- Tax bracket analysis for Israeli taxpayers
- Section 102 route optimization
- Interactive CSV upload and processing
- Detailed tax breakdown and optimization recommendations

## Setup

1. Install Python 3.11+
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. In the web interface:
   - Enter your current taxable income (in NIS)
   - Upload your RSU data CSV file
   - Select Section 102 route for each RSU grant
   - Click "Optimize Sales" to get recommendations

## CSV Format

The RSU data CSV should have the following columns:
- Company name
- Stock Code
- Grant date
- Vesting date
- Number of units

Note: The grant price is automatically fetched from historical stock data using the Grant date.

## Note

This tool uses real-time stock prices and currency conversion rates. Make sure you have a stable internet connection.
