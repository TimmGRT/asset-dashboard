import pandas as pd
import numpy as np
from datetime import date, timedelta
import streamlit as st
import io
import warnings
warnings.filterwarnings('ignore')

from data.downloader import data_downloader
from analytics.ticker_analytics import market_sector, sharpe, corr_ticker_mkt, pcr
from analytics.technical_indicators import poc_vah_val, RSI, ATR, CMF
from vizualisation.charts import (
    volume_profile_chart,
    volume_ema_chart,
    candlestick_ema_chart,
    cmf_chart,
    rsi_chart,
    atr_chart,
    vix_chart,
    options_bar_chart,
)

# config init de la st page 
st.set_page_config(page_title="Asset Analysis Dashboard", page_icon=":bar_chart:", layout="wide")
st.title(':bar_chart: Asset Analysis Dashboard')

st.sidebar.header(":chart: Choose your ticker:")
years = st.sidebar.selectbox("Since how many years ?:", [a for a in range(1, 20, 1)])
ticker = "AAPL"
ticker = st.sidebar.text_input("Choose an asset ticker:", help="Enter the asset ticker").upper()
with st.sidebar.expander("Tickers format in yfinance"):
    st.info("""
    📈 Stocks / ETFs : `AAPL`, `BMW.DE`, `AIR.PA` 
             
    🪙 Crypto : `BTC-USD`, `ETH-USD`  
            
    📊 Indices : `^GSPC`, `^DJI`  
            
    💱 Forex (currencies) : `EURUSD=X`, `GBPJPY=X`
              
    🏦 Commodities : `GC=F`, `CL=F`
            
    Full ticker list available here: https://finance.yahoo.com/markets/
    """)

# downloading data
i = date.today() - timedelta(days=years*365)
T = date.today()

data = pd.DataFrame(data_downloader(ticker, i, T, years))

# def de daily R pour la f des sharpe 
daily_returns = data['returns'].dropna()

st.sidebar.write('')

##############################################
#### TICKER MARKET / SECTOR / SHARPE / RHO ####
##############################################

market, sector, market_ticker, sector_ticker = market_sector(ticker)

mu, sigma, sharpe_ticker, sharpe_market, sharpe_sector, daily_returns_market = sharpe(data, market_ticker, sector_ticker, i, T)

corr = corr_ticker_mkt(ticker, data, market_ticker, daily_returns, daily_returns_market)

##############################################
####        OPTIONS MARKET (PCR)          ####
##############################################

PCR, data_options, vol_puts, vol_calls = pcr(ticker)

##############################################
####    SECTION 1 : STATS & OPTIONS       ####
##############################################

cl1, cl2 = st.columns([2, 1])

with cl1:
    st.subheader(":page_facing_up: **Ticker Statistical Caracteristics and Sharpe Ratio**")
    cla, clb = st.columns(2)
    with cla:
        st.subheader('qualitative characteristics')
        st.markdown(f"""          
        **TICKER** : {ticker}
              
        **MARKET** : {market if market else 'no datas available'}

        **SECTOR** : {sector if 'sector' else 'no datas available'}

        **Index of Market** : {market_ticker if market_ticker else 'no datas available'}

        **Index of Sector** : {sector_ticker if sector_ticker else 'no datas available'}

        """)

    with clb:
        st.subheader('quantitative characteristics')
        st.markdown(f""" 
        **TICKER SHARPE RATIO** : {sharpe_ticker.round(3) if sharpe_ticker else 'no datas available'}
                    
        **MARKET SHARPE RATIO** : {sharpe_market.round(3) if sharpe_market else 'no datas available'}

        **SECTOR SHARPE RATIO** : {sharpe_sector.round(3) if sharpe_sector else ' no datas available'}

        **MU (annualized)** = {mu.round(3)} ; **SIGMA (annualized)** = {sigma.round(2)}

        **RHO (corr with market)** = {corr.round(3) if corr else 'no datas available'}
        """)

with cl2:
    st.subheader(f":triangular_flag_on_post: options market on {ticker}")
    st.markdown(f"""
    **Call volume** with expiration today : {'No data available' if daily_returns_market is None or daily_returns_market.empty or data_options is None or 'Call' not in data_options or vol_puts is None else int(data_options['Call'].iloc[-1])}  
    **Proportion** = {'No data available' if daily_returns_market is None or daily_returns_market.empty or data_options is None or 'Call' not in data_options or vol_puts is None else round(int(data_options['Call'].iloc[-1]) / vol_puts, 3)}  
    **Put volume** with expiration today : {'No data available' if daily_returns_market is None or daily_returns_market.empty or data_options is None or 'Put' not in data_options or vol_puts is None else int(data_options['Put'].iloc[-1])}  
    **Proportion** = {'No data available' if daily_returns_market is None or daily_returns_market.empty or data_options is None or 'Put' not in data_options or vol_puts is None else round(int(data_options['Put'].iloc[-1]) / vol_puts, 3)}""")
    st.write(f"**Put Call Ratio** : "
             f"{'No data available' if PCR is None else round(PCR, 3)}")

    with st.expander("options positions bar chart : Vol = f(expiration)"):
        if data_options is None or data_options.empty:
            st.write('No datas available')
        else:
            fig = options_bar_chart(data_options)
            st.plotly_chart(fig, use_container_width=True, height=200)


##############################################
####  SECTION 2 : VOLUME PROFILE + EMA    ####
##############################################

st.sidebar.subheader(':bar_chart: Variables for Analysis')
window = st.sidebar.selectbox("Number of period taken for POC computing :", [a for a in range(20, 61, 5)])

POC, VAH_borne, VAL_borne, clean_pw = poc_vah_val(data, ticker, window)

col1, col2 = st.columns(2)

with col1:
    st.subheader(f" :file_folder: **Volume profile of {ticker} the last {window} periods**")
    fig = volume_profile_chart(clean_pw, POC, VAH_borne, VAL_borne, ticker, window)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(f" :file_folder: Daily volumes and 20-day EMA of {ticker} volumes")
    fig_vol = volume_ema_chart(data)
    st.plotly_chart(fig_vol, use_container_width=True)


##############################################
####   SECTION 3 : CANDLESTICK + CMF      ####
##############################################

st.subheader("**:file_folder: Candlestick chart with EMA crossovers (5, 20, 50) and Chaikin Money Flow displayed at the bottom**")

fig = candlestick_ema_chart(data)
st.plotly_chart(fig, use_container_width=True)

data = CMF(data)
fig_cmf = cmf_chart(data, ticker)

with st.expander(":bar_chart: Chaikin Money Flow CMF Chart"):
    st.plotly_chart(fig_cmf, use_container_width=True)


##############################################
####       SECTION 4 : RSI + ATR          ####
##############################################

data = RSI(data)
fig_rsi = rsi_chart(data, ticker)

data = ATR(data)
fig_ATR = atr_chart(data, ticker)

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"**:file_folder: Relative Strenght Index RSI Chart of {ticker}**")
    st.plotly_chart(fig_rsi, use_container_width=True)

with col2:
    st.subheader(f"**:file_folder: Average True Range ATR Chart of {ticker}**")
    st.plotly_chart(fig_ATR, use_container_width=True)


##############################################
####     SECTION 5 : VIX + COMING SOON    ####
##############################################

vix_plot = vix_chart(i, T)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader(":file_folder: VIX WRLD INDEX ")
    st.plotly_chart(vix_plot, use_container_width=True)

with col2:
    st.subheader("Money Management and position forecasting")
    st.write("COMING SOON")

with col3:
    st.subheader("Analysis Scoring")
    st.write("COMING SOON")


#############################################
###       SIDEBAR : DATA DOWNLOAD        ####
#############################################

st.sidebar.write('')
csv_data = data.to_csv(index=False).encode('utf-8')
st.sidebar.subheader(':cd: Data Downloading')
st.sidebar.download_button("Download Data used in these analysis to CSV", data=csv_data, file_name=f'{ticker}.csv', mime='text/csv',
                           help="click here to download as a csv file")

excel_buffer = io.BytesIO()
data.to_excel(excel_buffer, index=False, engine='openpyxl')
excel_buffer.seek(0)
st.sidebar.download_button("Download Data used in these analysis to XLS", data=excel_buffer, file_name=f'{ticker}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           help="click here to download as a xls file")

