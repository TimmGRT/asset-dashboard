import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date, timedelta

@st.cache_data
def data_downloader(ticker, i, T, years):
    df = pd.DataFrame()
    try:
        df = yf.download(ticker, i, T, auto_adjust=True)
        df = df['returns'].dropna()
    
    except Exception as e:
        st.warning(f":warning: Failed to download {ticker}, check the ticker help expander for more infos :warning:")
        st.stop()
        return None

    except yf.YFRateLimitError:
        st.error("⚠️ Rate limit reached: too many users are generating requests. Please wait a few minutes before retrying.")
    
    if df.empty or len(df)<10 :
        st.warning(f":warning: No data available for {ticker}, check the the ticker help expander for more infos :warning:")
        st.stop()
        return None
    
    data = df.droplevel(1, axis = 1).reset_index().copy()
    data["Date"] = pd.to_datetime(data["Date"], errors = "coerce")
    data['returns'] = data["Close"].pct_change()

    return data 