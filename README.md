# RSU Sell Optimizer for Israeli Taxpayers

This tool helps Israeli taxpayers optimize RSU (Restricted Stock Unit) sales by analyzing tax brackets, Section 102 eligibility, and real-time stock prices.

## Features

* Real-time stock price updates
* Automatic USD→NIS conversion
* Progressive income tax bracket analysis for Israel
* Section 102 route handling, including the 24-month trustee holding rule
* Interactive CSV upload, validation, and processing
* Optimization to stay within a chosen income-tax bracket while minimizing total tax
* Detailed per-grant breakdown and consolidated summary

## Online App

You can access the hosted version here: [https://il-rsu-tax-calculator.streamlit.app/](https://il-rsu-tax-calculator.streamlit.app/)
**Note:** Access requires an invite from `arsenikr@gmail.com`.

## Local Deployment

1. Install Python 3.11 or newer.

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   streamlit run app.py
   ```

## Usage

In the UI:

* Enter your current taxable income in NIS
* Upload your RSU CSV file (an example `RSU.csv` file is included in the repo)
* Choose Section 102 route per grant (if not supplied, defaults to Capital Gains Route)
* Pick a target bracket ceiling
* Click **Optimize Sales**

## CSV Format

Columns:

* Company name
* Stock Code
* Grant date *(format: YYYY-MM-DD)*
* Vesting date *(format: YYYY-MM-DD)*
* Number of units

Note: The grant price is fetched from historical data around the grant date. FX is fetched for the relevant dates.

### Example `RSU.csv`

```csv
Company name,Stock Code,Grant date,Vesting date,Number of units
Palo Alto Networks,PANW,2019-05-20,2020-08-20,XXXX
```

Replace `XXXX` with the actual number of units granted. You may also add more rows if you have multiple grants.

## Israeli Tax Logic Used

* **Section 102 (trustee, capital‑gains track)**: Awards must be held with a trustee for a required holding period (commonly **24 months** from grant) to qualify. A sale before the period generally disqualifies the benefit and the entire amount is treated as ordinary income. See, for example: [SEC Exhibit—Form of Notice of Grant (Israel Employees)](https://www.sec.gov/Archives/edgar/data/1065088/000119312509170655/dex99d4.htm) ("Required Holding Period ... 24 months"); and a practitioner overview: [Herzog—Section 102 Capital Gains Route](https://herzoglaw.co.il/en/news-and-insights/new-green-track-ruling-applications/).

* **Capital gains on traded securities**: For individuals, the **real gain** is generally taxed at **25%**, increasing to **30%** for a **10%+ shareholder**. Source: [PwC—Israel: Income determination (Capital gains)](https://taxsummaries.pwc.com/israel/individual/income-determination).

* **Ordinary income**: Employment/ordinary income is taxed at progressive rates with annually indexed brackets (max marginal \~50% including surtax). See: [PwC—Israel: Taxes on personal income](https://taxsummaries.pwc.com/israel/individual/taxes-on-personal-income) and the [Israel Tax Authority—Income Tax](https://www.gov.il/en/departments/topics/income_tax_israel_tax_authority/govil-landing-page).

> The app assumes the 25% CGT for non‑substantial shareholders by default and does not implement the 30% 10%+ shareholder branch.

## How the Algorithm Works

1. **Data hygiene**: CSV is cleaned and validated, dates parsed, tickers standardized.
2. **Prices and FX**: Fetches grant FMV (30-day avg), vest FMV (non-§102), sale price, and USD/ILS FX.
3. **Tax components per share**: Splits value into ordinary vs capital gain portions based on §102 rules.
4. **Optimization**: Fills available income room up to target bracket with the most capital-efficient grants, offsets gains with losses, computes incremental taxes.
5. **Output**: Shows per-grant sale strategy and a consolidated financial summary.

## Assumptions and Limitations

* Capital gains tax is assumed at 25% for non-substantial shareholders. Adjust manually if 30% applies.
* Price/FX data is sourced from Yahoo Finance and may have gaps.
* Informational only, not tax advice. Consult a professional advisor.