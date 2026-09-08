import yfinance as yf
import matplotlib.pyplot as plt 
import pandas as pd 
import numpy as np
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.ticker as tick
import streamlit as st
import os 
import io
import warnings

from data.downloader import data_downloader

warnings.filterwarnings('ignore')


#################################################
#### TICKER INFORMATION AND DATA DOWNLOADING ####
#################################################

st.set_page_config(page_title = "Asset Analysis Dashboard", page_icon= ":bar_chart:", layout = "wide")
st.title(':bar_chart: Asset Analysis Dashboard')

st.sidebar.header(":chart: Choose your ticker:")
years = st.sidebar.selectbox("Since how many years ?:", [a for a in range(1, 20, 1)])
ticker = st.sidebar.text_input("Choose an asset ticker:", help = "Enter the asset ticker").upper()

with st.sidebar.expander("Tickers format in yfinance"):
    st.info("""
    📈 Stocks / ETFs : `AAPL`, `BMW.DE`, `AIR.PA` 
             
    🪙 Crypto : `BTC-USD`, `ETH-USD`  
            
    📊 Indices : `^GSPC`, `^DJI`  
            
    💱 Forex (currencies) : `EURUSD=X`, `GBPJPY=X`
              
    🏦 Commodities : `GC=F`, `CL=F`
            
    Full ticker list available here: https://finance.yahoo.com/markets/
    """)

## Data downloading

i = date.today() - timedelta(days=years * 365)
T = date.today()

data = pd.DataFrame(data_downloader(ticker, i, T, years))


## BEGINING OF THE LAYOUT
st.sidebar.write('')