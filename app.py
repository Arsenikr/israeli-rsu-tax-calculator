import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, List, Tuple, Union

# --- 1. Parsing & Data Hygiene ---

def clean_csv_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and standardizes CSV data according to specifications."""
    cleaned_df = df.copy()
    cleaned_df['Stock Code'] = cleaned_df['Stock Code'].str.strip().str.upper()
    for col in ['Grant date', 'Vesting date']:
        cleaned_df[col] = pd.to_datetime(cleaned_df[col], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    cleaned_df['Number of units'] = pd.to_numeric(cleaned_df['Number of units'], errors='coerce').fillna(0).astype(int)
    cleaned_df = cleaned_df[cleaned_df['Number of units'] > 0]
    cleaned_df['Company name'] = cleaned_df['Company name'].str.strip()
    cleaned_df = cleaned_df.dropna(how='all').dropna(subset=['Grant date', 'Vesting date'])
    return cleaned_df

def validate_csv_data(df: pd.DataFrame) -> List[str]:
    """Validates CSV data structure and required columns."""
    errors = []
    required_columns = ['Company name', 'Stock Code', 'Grant date', 'Vesting date', 'Number of units']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
    return errors

# --- Core Logic Class ---

class RSUOptimizer:
    ISRAELI_TAX_BRACKETS_2025 = [
        (84120, 0.10),
        (120720, 0.14),
        (193800, 0.20),
        (269280, 0.31),
        (560280, 0.35),
        (721560, 0.47),
        (float('inf'), 0.50)
    ]
    CAPITAL_GAINS_RATE = 0.25

    @staticmethod
    @st.cache_data
    def get_fx_rate(date_str: str) -> Optional[float]:
        """Fetches historical USD/ILS exchange rate for a specific date."""
        if not date_str or pd.isna(date_str):
            return None
        try:
            date_obj = pd.to_datetime(date_str)
            start_date = date_obj - timedelta(days=7)
            end_date = date_obj + timedelta(days=1)
            fx_data = yf.download('ILS=X', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
            if fx_data.empty:
                st.warning(f"No FX rate found for {date_str}, using fallback.")
                return 3.8
            return float(fx_data['Close'].iloc[-1])
        except Exception as e:
            st.error(f"FX fetch failed for {date_str}: {e}")
            return None

    @staticmethod
    @st.cache_data
    def get_stock_price(ticker: str, date_str: str, use_30d_avg: bool = False) -> Optional[float]:
        """Fetches historical stock price. Can use 30-day avg for grant FMV."""
        if not ticker or pd.isna(ticker) or not date_str or pd.isna(date_str):
            return None
        try:
            stock = yf.Ticker(ticker)
            date_obj = pd.to_datetime(date_str)
            
            if use_30d_avg:
                start_date = date_obj - timedelta(days=45)
            else:
                start_date = date_obj - timedelta(days=7)
            end_date = date_obj + timedelta(days=1)

            hist = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
            if hist.empty:
                st.warning(f"No price history found for {ticker} around {date_str}")
                return None

            hist.index = hist.index.tz_localize(None)

            if use_30d_avg:
                return float(hist[hist.index <= date_obj].tail(30)['Close'].mean())
            else:
                return float(hist['Close'].asof(date_obj))
        except Exception as e:
            st.error(f"Price fetch failed for {ticker} on {date_str}: {e}")
            return None

    def calc_progressive_tax(self, income_start: float, increment: float) -> float:
        """Calculates the incremental tax on an income increment."""
        if increment <= 0:
            return 0.0
        
        def tax_on_income(income, brackets):
            tax = 0.0
            previous_limit = 0
            for limit, rate in brackets:
                if income > previous_limit:
                    taxable_in_bracket = min(income - previous_limit, limit - previous_limit)
                    tax += taxable_in_bracket * rate
                    previous_limit = limit
                else:
                    break
            return tax

        total_tax = tax_on_income(income_start + increment, self.ISRAELI_TAX_BRACKETS_2025)
        base_tax = tax_on_income(income_start, self.ISRAELI_TAX_BRACKETS_2025)
        return total_tax - base_tax

    def get_tax_components(self, grant: pd.Series, sale_date_str: str) -> Optional[Dict]:
        """Calculates the ordinary and capital gain components per share in NIS."""
        sale_date = pd.to_datetime(sale_date_str)
        grant_date = pd.to_datetime(grant.get('Grant date'))

        sale_price_usd = self.get_stock_price(grant['Stock Code'], sale_date_str)
        sale_fx = self.get_fx_rate(sale_date_str)
        grant_price_usd = self.get_stock_price(grant['Stock Code'], grant.get('Grant date'), use_30d_avg=True)
        grant_fx = self.get_fx_rate(grant.get('Grant date'))
        
        if not all([sale_price_usd, sale_fx, grant_price_usd, grant_fx]):
            st.error(f"Could not get price/FX for {grant['Stock Code']}. Cannot proceed.")
            return None
        
        sale_nis = sale_price_usd * sale_fx
        ordinary_per_share = 0
        capital_per_share = 0
        note = ""

        if grant.get('Section 102') == 'Capital Gains Route':
            base_price_usd = grant_price_usd # Use the already fetched grant price
            base_fx = grant_fx # Reuse the already fetched grant fx
            if not all([base_price_usd, base_fx]): return None
            base_102_nis = base_price_usd * base_fx

            if sale_date < (grant_date + relativedelta(months=24)):
                ordinary_per_share = sale_nis
                capital_per_share = 0
                note = "§102 Disqualified (sold < 24m): Full amount is ordinary income."
            else:
                ordinary_per_share = min(base_102_nis, sale_nis)
                capital_per_share = max(0, sale_nis - base_102_nis)
                note = "§102 Capital Gains Route"
                if sale_nis < base_102_nis:
                    note = "§102 Underwater: Ordinary income only, no capital loss."
        else:
            vest_price_usd = self.get_stock_price(grant['Stock Code'], grant.get('Vesting date'))
            vest_fx = self.get_fx_rate(grant.get('Vesting date'))
            if not all([vest_price_usd, vest_fx]): return None
            vest_nis = vest_price_usd * vest_fx
            ordinary_per_share = 0
            capital_per_share = sale_nis - vest_nis
            note = "Non-§102: Capital gain/loss from vest date."

        grant_price_nis = grant_price_usd * grant_fx

        return {
            "ordinary_per_share": ordinary_per_share,
            "capital_per_share": capital_per_share,
            "sale_price_nis": sale_nis,
            "grant_price_nis": grant_price_nis,
            "sale_price_usd": sale_price_usd,
            "grant_price_usd": grant_price_usd,
            "note": note
        }

    def optimize_rsu_sales(self, rsu_data: pd.DataFrame, current_income: float, target_bracket_limit: float) -> pd.DataFrame:
        """Determines the optimal number of shares to sell from each grant."""
        sale_date_str = datetime.now().strftime('%Y-%m-%d')
        income_room = target_bracket_limit - current_income
        if income_room <= 0:
            st.warning("Current income already exceeds target bracket. No §102 sales recommended.")
            income_room = 0

        grants_to_process = []
        for _, grant in rsu_data.iterrows():
            components = self.get_tax_components(grant, sale_date_str)
            if not components: continue

            efficiency = 0
            if components["ordinary_per_share"] > 0 and components["capital_per_share"] > 0:
                efficiency = components["capital_per_share"] / components["ordinary_per_share"]
            elif components["capital_per_share"] > 0:
                efficiency = float('inf')

            grants_to_process.append({**grant.to_dict(), **components, "efficiency": efficiency})

        s102_gains = sorted([g for g in grants_to_process if g["note"].startswith("§102") and g["capital_per_share"] >= 0 and g["ordinary_per_share"] > 0], key=lambda x: x['efficiency'], reverse=True)
        cap_losses = [g for g in grants_to_process if g["capital_per_share"] < 0]

        recommendations = []
        running_income = current_income

        for grant in s102_gains:
            ord_per_share = grant["ordinary_per_share"]
            if ord_per_share <= 0: continue
            room_for_ord_income = target_bracket_limit - running_income
            if room_for_ord_income <= 0: break
            units_to_sell = min(grant["Number of units"], int(room_for_ord_income / ord_per_share))
            if units_to_sell <= 0: continue
            recommendations.append({**grant, "units_to_sell": units_to_sell})
            running_income += units_to_sell * ord_per_share

        total_cap_gain_to_offset = sum(rec["capital_per_share"] * rec["units_to_sell"] for rec in recommendations)
        running_loss_sold = 0

        for grant in cap_losses:
            if running_loss_sold >= total_cap_gain_to_offset: break
            loss_per_share = abs(grant["capital_per_share"])
            if loss_per_share <= 0: continue
            needed_loss = total_cap_gain_to_offset - running_loss_sold
            units_to_sell = min(grant["Number of units"], int(np.ceil(needed_loss / loss_per_share)))
            if units_to_sell <= 0: continue
            recommendations.append({**grant, "units_to_sell": units_to_sell})
            running_loss_sold += units_to_sell * loss_per_share

        final_results = []
        running_income_for_tax = current_income
        for rec in recommendations:
            units = rec["units_to_sell"]
            ord_total = rec["ordinary_per_share"] * units
            cap_total = rec["capital_per_share"] * units
            income_tax = self.calc_progressive_tax(running_income_for_tax, ord_total)
            running_income_for_tax += ord_total
            cgt = max(0, cap_total) * self.CAPITAL_GAINS_RATE
            total_tax = income_tax + cgt
            net_proceeds = (rec["sale_price_nis"] * units) - total_tax

            final_results.append({
                "Company": rec["Company name"],
                "Grant Date": rec["Grant date"],
                "Grant Price (NIS/sh)": f"{rec['grant_price_nis']:.2f} ({rec['grant_price_usd']:.2f}$)",
                "Units to Sell": units,
                "Sale Price (NIS/sh)": f"{rec['sale_price_nis']:.2f} ({rec['sale_price_usd']:.2f}$)",
                "Ordinary (NIS/sh)": f"{rec['ordinary_per_share']:.2f}",
                "Capital Gain (NIS/sh)": f"{rec['capital_per_share']:.2f}",
                "Ordinary Total (NIS)": f"{ord_total:,.2f}",
                "Capital Gain Total (NIS)": f"{cap_total:,.2f}",
                "Income Tax (NIS)": f"{income_tax:,.2f}",
                "Capital Gains Tax (NIS)": f"{cgt:,.2f}",
                "Total Tax (NIS)": f"{total_tax:,.2f}",
                "Net Proceeds (NIS)": f"{net_proceeds:,.2f}",
                "Note": rec["note"]
            })

        return pd.DataFrame(final_results)

# --- UI and Main Application ---

def main():
    st.set_page_config(layout="wide")
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    st.title("RSU Sales Tax Optimizer for Israel")
    st.error("Disclaimer: This is an informational tool, not professional tax advice. Consult a qualified advisor.")

    optimizer = RSUOptimizer()

    with st.sidebar:
        st.header("⚙️ Inputs")
        uploaded_file = st.file_uploader("Upload RSU data CSV", type=['csv'])
        current_income = st.number_input("Current Annual Taxable Income (NIS)", value=150000, step=5000)
        target_bracket_limit = st.selectbox("Target Tax Bracket Ceiling", 
            options=[b[0] for b in RSUOptimizer.ISRAELI_TAX_BRACKETS_2025 if b[0] != float('inf')],
            format_func=lambda x: f"Up to {x:,.0f} NIS", index=2)
        st.markdown("---")
        st.markdown("<a href='/Help' target='_self' style='text-decoration: none;'>❓ Help</a>", unsafe_allow_html=True)

    if uploaded_file is None:
        st.info("Upload a CSV with columns: Company name, Stock Code, Grant date, Vesting date, Number of units, Section 102")
        return

    rsu_data_raw = pd.read_csv(uploaded_file)
    errors = validate_csv_data(rsu_data_raw)
    if errors:
        for error in errors:
            st.error(f"CSV Error: {error}")
        return

    rsu_data = clean_csv_data(rsu_data_raw)
    if 'Section 102' not in rsu_data.columns:
        rsu_data['Section 102'] = 'Capital Gains Route'

    st.subheader("Data Overview")
    st.dataframe(rsu_data, use_container_width=True, hide_index=True)

    if st.button("Optimize RSU Sales", type="primary"):
        results_df = optimizer.optimize_rsu_sales(rsu_data, current_income, target_bracket_limit)
        st.subheader("✅ Recommended Sales Strategy")
        if not results_df.empty:
            st.dataframe(results_df, use_container_width=True, hide_index=True)
            
            cap_gain_sum = pd.to_numeric(results_df["Capital Gain Total (NIS)"].str.replace('[₪,]', '', regex=True)).sum()
            
            final_income_tax = pd.to_numeric(results_df["Income Tax (NIS)"].str.replace('[₪,]', '', regex=True)).sum()
            final_cgt = max(0, cap_gain_sum) * RSUOptimizer.CAPITAL_GAINS_RATE
            final_total_tax = final_income_tax + final_cgt
            final_net = pd.to_numeric(results_df["Net Proceeds (NIS)"].str.replace('[₪,]', '', regex=True)).sum()

            st.subheader("📈 Financial Summary")

            ord_total_sum = pd.to_numeric(results_df["Ordinary Total (NIS)"].str.replace('[₪,]', '', regex=True)).sum()
            gross_proceeds = (pd.to_numeric(results_df["Sale Price (NIS/sh)"].str.split(' ').str[0]) * results_df["Units to Sell"]).sum()

            st.markdown(f"""
            | Metric | Amount (NIS) |
            | :--- | :--- |
            | **Salary** | **{current_income:,.2f} ₪** |
            | **RSU Ordinary Income** | **{ord_total_sum:,.2f} ₪** |
            | **Taxable Income for Brackets** | **{current_income + ord_total_sum:,.2f} ₪** |
            | | *(below target bracket ceiling {target_bracket_limit:,.0f} ₪)* |
            | **Capital Gains** | **{cap_gain_sum:,.2f} ₪** |
            | | *(taxed separately)* |
            | **Income Tax Paid** | **{final_income_tax:,.2f} ₪** |
            | **Capital Gains Tax Paid** | **{final_cgt:,.2f} ₪** |
            | **Total Tax Paid** | **{final_total_tax:,.2f} ₪** |
            | **Gross Proceeds** | **{gross_proceeds:,.2f} ₪** |
            | **Net Proceeds** | **{final_net:,.2f} ₪** |
            """)

            st.info("Note: Your chosen tax bracket only applies to salary + RSU ordinary income. Capital gains are taxed separately at capital gains rates.")

        else:
            st.warning("No profitable sales could be recommended within the selected constraints.")

if __name__ == "__main__":
    main()
