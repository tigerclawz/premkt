import requests
import pandas as pd
import streamlit as st
from json import JSONDecodeError

def fetch_cookies():
    """
    Fetch cookies from the NSE website to be used for API requests.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get("https://www.nseindia.com", headers=headers)
        response.raise_for_status()
        cookies = response.cookies
        return cookies
    except requests.RequestException as e:
        st.error(f"Error fetching cookies: {e}")
        return None

def fetch_data_from_api(cookies):
    """
    Fetch market data from the NSE pre-open API.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    }
    api_url = "https://www.nseindia.com/api/market-data-pre-open?key=ALL"
    try:
        response = requests.get(api_url, headers=headers, cookies=cookies)
        response.raise_for_status()
        try:
            data = response.json().get("data")
            return data
        except (JSONDecodeError, TypeError) as e:
            st.error(f"Error decoding JSON: {e}. Response text: {response.text}")
            return None
    except requests.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return None

def filter_table(data, pchange_min, pchange_max, price_min, price_max, turnover_min, turnover_max):
    """
    Filter the data based on user-defined conditions.
    """
    if not data:
        st.warning("No data received from API.")
        return

    filtered_data = []
    for item in data:
        metadata = item.get("metadata")
        if metadata:
            p_change = metadata.get("pChange")
            last_price = metadata.get("lastPrice")
            symbol = metadata.get("symbol")
            quantity = metadata.get("finalQuantity")
            value = metadata.get("totalTurnover")
            w52_Low = metadata.get("yearLow")
            w52_High = metadata.get("yearHigh")

            if (p_change is not None and last_price is not None and symbol is not None and value is not None):
                if (pchange_min < p_change < pchange_max and 
                    price_min < last_price < price_max and 
                    turnover_min <= value <= turnover_max):
                    filtered_data.append({
                        "Symbol": symbol,
                        "pChange": p_change,
                        "LastPrice": last_price,
                        "Quantity": quantity,
                        "TotalTurnover": value,
                        "52W_Low": w52_Low,
                        "52W_High": w52_High
                    })

    if filtered_data:
        df = pd.DataFrame(filtered_data)
        st.dataframe(df)  # Display the table in Streamlit
    else:
        st.warning("No data matching the conditions found.")

# Streamlit UI setup

st.title("NSE Market Data Filter")

# Step 1: Fetch cookies
cookies = fetch_cookies()
if cookies:
    data = fetch_data_from_api(cookies)
    if data:
        st.sidebar.header("Filter Conditions")

        # Step 2: User input for filters in the sidebar
        pchange_min = st.sidebar.number_input("Minimum % Change", value=-20.0, step=0.1)
        pchange_max = st.sidebar.number_input("Maximum % Change", value=10.0, step=0.1)
        price_min = st.sidebar.number_input("Minimum Price", value=100.0, step=1.0)
        price_max = st.sidebar.number_input("Maximum Price", value=5000.0, step=1.0)

        # New: Turnover filter as a range slider
        turnover_min, turnover_max = st.sidebar.slider(
            "Total Turnover Range",
            min_value=100000,  # Minimum possible turnover
            max_value=1000000000,  # Maximum possible turnover
            value=(100000, 500000000),  # Default range
            step=1000000
        )

        # Step 3: Apply filter button in the sidebar
        if st.sidebar.button("Apply Filter"):
            filter_table(data, pchange_min, pchange_max, price_min, price_max, turnover_min, turnover_max)
