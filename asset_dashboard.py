import yfinance as yf
import matplotlib.pyplot as plt 
import pandas as pd 
import numpy as np
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.ticker as tick
import mplfinance as mpf
import streamlit as st
import os 
import io
import warnings
warnings.filterwarnings('ignore')

# config init de la st page 
st.set_page_config(page_title = "Asset Analysis Dashboard", page_icon= ":bar_chart:", layout = "wide")
st.title(':bar_chart: Asset Analysis Dashboard')

st.sidebar.header(":chart: Choose your ticker:")
years = st.sidebar.selectbox("Since how many years ?:", [a for a in range(1, 20, 1)])
ticker = st.sidebar.text_input("Choose a stock ticker:", help = "Enter the asset ticker").upper()
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

@st.cache_data
def data_downloader(ticker, i, T, years):
    df = pd.DataFrame()
    try:
        start = T - timedelta(days=years * 365)
        df = yf.download(ticker, i, T, auto_adjust=True)
    
    except Exception as e:
        st.warning(f"Failed to download {ticker}, check the the ticker help expander for more infos")
        st.stop()
        return None
    
    if df.empty or len(df)<10 :
        st.warning(f"No data available for {ticker}, check the the ticker help expander for more infos")
        st.stop()
        return None
    
    data = df.droplevel(1, axis = 1).reset_index().copy()
    data["Date"] = pd.to_datetime(data["Date"], errors = "coerce")
    data['returns'] = data["Close"].pct_change()

    return data 

data = pd.DataFrame(data_downloader(ticker, i, T, years))

# def de daily R pour la f des sharpe 
daily_returns = data['returns'].dropna()

st.sidebar.write('')


# Ticker Market et Sector
etf_sectoriel = {"Energy": "XLE",
    "Basic Materials": "XLB",
    "Industrials": "XLI",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Information Technology": "XLK",
    "Technology": "XLK",
    "Communication Services": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE"
}

etf_national = {
    "United States": "SPY",
    "China": "FXI",
    "Japan": "EWJ",
    "Germany": "EWG",
    "India": "INDA",
    "United Kingdom": "EWU",
    "France": "EWQ",
    "Canada": "EWC",
    "Australia": "EWA",
    "Brazil": "EWZ",
    "South Korea": "EWY",
    "Taiwan": "EWT",
    "Hong Kong": "EWH",
    "Mexico": "EWW",
    "Singapore": "EWS",
    "Italy": "EWI",
    "Spain": "EWP",
    "Switzerland": "EWL",
    "Netherlands": "EWN",
    "Belgium": "EWK",
    "Sweden": "EWD",
    "Finland": "EFNL",
    "Denmark": "EDEN",
    "Austria": "EWO",
    "Norway": "ENOR",
    "Saudi Arabia": "KSA",
    "United Arab Emirates": "UAE",
    "Egypt": "EGPT",
    "Nigeria": "NGE",
    "Chile": "ECH",
    "Argentina": "ARGT",
    "Colombia": "GXG",
    "Peru": "EPU",
    "Malaysia": "EWM",
    "Thailand": "THD",
    "Indonesia": "EIDO",
    "Philippines": "EPHE",
    "Vietnam": "VNM",
    "Pakistan": "PAK",
    "Bangladesh": "BGD",
    "Sri Lanka": "SLK",
    "Nepal": "NEP",
    "Bhutan": "BHU",
    "Maldives": "MDV",
    "Afghanistan": "AFG",
    "Uzbekistan": "UZB",
    "Kazakhstan": "KAZ",
    "Turkmenistan": "TKM",
    "Kyrgyzstan": "KGZ",
    "Tajikistan": "TJK",
    "Armenia": "ARM",
    "Azerbaijan": "AZE",
    "Georgia": "GEO",
    "Moldova": "MDA",
    "Belarus": "BLR",
    "Ukraine": "UKR",
    "Bulgaria": "BUL",
    "Romania": "ROU",
    "Serbia": "SRB",
    "Croatia": "HRV",
    "Bosnia and Herzegovina": "BIH",
    "Montenegro": "MNE",
    "North Macedonia": "MKD",
    "Albania": "ALB",
    "Kosovo": "KOS",
    "Malta": "MLT",
    "Cyprus": "CYP",
    "Russia": "RSX",
    "Turkey": "TUR"
}

yf_ticker = yf.Ticker(ticker)
info = yf_ticker.info

@st.cache_data
def market_sector(ticker):
    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info

    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info

    market = None
    sector = None
    market_ticker = None
    sector_ticker = None

    if "sector" in info and "market" in info: 
        market = info.get('country')
        sector = info.get('sector')

        market_norm = market.strip() if market else None
        sector_norm = sector.strip() if sector else None
        market_ticker = etf_national.get(market_norm)
        sector_ticker = etf_sectoriel.get(sector_norm)

    elif "sector" in info and "market" not in info:
        sector = info.get('sector')
        sector_norm = sector.strip() if sector else None
        sector_ticker = etf_sectoriel.get(sector_norm)
    
    elif "sector" not in info and "market" in info:
        market = info.get('country')
        market_norm = market.strip() if market else None
        market_ticker = etf_national.get(market_norm)

    return market, sector, market_ticker, sector_ticker 

market, sector, market_ticker, sector_ticker = market_sector(ticker)

# calcul des R sharpe 
def sharpe(data, market_ticker, sector_ticker):

    # r des oblig fonds du tresor americain sur 3 mois pr rf
    data_rf = pd.DataFrame(yf.download("^IRX", i, T, '1d'))
    date_anterieur_raw = T - timedelta(days = 1)

    if date_anterieur_raw in data_rf.index:
        date_anterieur = f"{date_anterieur_raw.year}-{date_anterieur_raw.month}-{date_anterieur_raw.day}"
        rf_brut = data_rf.loc[date_anterieur, "Close"]
        rf = float(rf_brut.iloc[0]/100)

    else:
        while pd.to_datetime(date_anterieur_raw) not in data_rf.index: 
            date_anterieur_raw = date_anterieur_raw - timedelta(days=1)
            
        date_anterieur = f"{date_anterieur_raw.year}-{date_anterieur_raw.month}-{date_anterieur_raw.day}"

        rf_brut = data_rf.loc[date_anterieur, "Close"]
        rf = float(rf_brut.iloc[0])/100

    # stat pour le ticker 
    mu_ticker = data["returns"].mean()*252
    std_ticker = data["returns"].std()*np.sqrt(252)

    sharpe_ticker = (mu_ticker-rf)/std_ticker

    # stat pour le mkt 
    if market_ticker != None:
        data_market = pd.DataFrame(yf.download(market_ticker, i, T, '1d')).reset_index()
        data_market['returns'] = data_market['Close'].pct_change()  
        daily_returns_market = data_market['returns'].dropna()
        mu_market = daily_returns_market.mean()*252
        std_market= daily_returns_market.std()*np.sqrt(252)

        sharpe_market = (mu_market-rf)/std_market
    
    elif market_ticker == None:
        sharpe_market = None
        daily_returns_market = None
    
    # stat pour le sect
    if sector_ticker != None:
        data_sector = pd.DataFrame(yf.download(sector_ticker, i, T, '1d'))
        data_sector['returns'] = data_sector['Close'].pct_change()  
        daily_returns_sector = data_sector['returns'].dropna()
        mu_sector = daily_returns_sector.mean()*252
        std_sector= daily_returns_sector.std()*np.sqrt(252)

        sharpe_sector = (mu_sector-rf)/std_sector
    
    elif sector_ticker == None:
        sharpe_sector = None


    return(mu_ticker, std_ticker, sharpe_ticker, sharpe_market, sharpe_sector, daily_returns_market)

mu, sigma, sharpe_ticker, sharpe_market, sharpe_sector, daily_returns_market = sharpe(data, market_ticker, sector_ticker)


def corr_ticker_mkt(ticker, data, daily_returns, daily_returns_market):
    conjoint = pd.DataFrame()

    conjoint[ticker] = daily_returns
    conjoint[market_ticker] = daily_returns_market

    corr = conjoint[[ticker, market_ticker]].corr().iloc[0,1]

    return corr

corr = None

if daily_returns_market is None or daily_returns_market.empty:
    corr = None
elif daily_returns_market.empty != True:
    corr = corr_ticker_mkt(ticker, data, daily_returns, daily_returns_market)

# MARCHÉ OPTIONS SUR LE TICKER 

def pcr(ticker): 
    t = yf.Ticker(ticker)

    expirations = t.options

    PCR = None
    data_options = None
    vol_puts = None
    vol_calls = None

    if expirations:
        vol_puts = 0
        vol_calls = 0

        data_options_list = []

        for exp in expirations:
            target = t.option_chain(exp)
            put = target.puts
            call = target.calls

            vol_puts += put["volume"].fillna(0).sum()
            vol_calls += call["volume"].fillna(0).sum()

            data_options_list.append({
                "Expiration": exp,
                "Put": put["volume"].fillna(0).sum(),
                "Call": call["volume"].fillna(0).sum()
            })
        
        data_options = pd.DataFrame(data_options_list)

        # Calcul du pcr
        if vol_calls != 0: 
            PCR = vol_puts/vol_calls

        else:
            PCR = None

    return(PCR, data_options, vol_puts, vol_calls)

PCR, data_options, vol_puts, vol_calls = pcr(ticker)

# REPRESENTATION sharpe, et caract stat  


cl1, cl2 = st.columns([2, 1])

with cl1:
    st.subheader(":page_facing_up: **Ticker Statistical Caracteristics and Sharpe Ratio**")
    cla, clb = st.columns(2)
    with cla:
        st.subheader('qualitative caracteristics')
        st.markdown(f"""          
        **TICKER** : {ticker}
              
        **MARKET** : {market if market else 'no datas available'}

        **SECTOR** : {sector if 'sector' else 'no datas available'}

        **Index of Market** : {market_ticker if market_ticker else 'no datas available'}

        **Index of Sector** : {sector_ticker if sector_ticker else 'no datas available'}

        """)
        

    with clb:
        st.subheader('quantitative caracteristics')
        st.markdown(f""" 
        **TICKER SHARPE RATIO** : {sharpe_ticker.round(3) if sharpe_ticker else 'no datas available'}
                    
        **MARKET SHARPE RATIO** : {sharpe_market.round(3) if sharpe_market else 'no datas available'}

        **SECTOR SHARPE RATIO** : {sharpe_sector.round(3) if sharpe_sector else ' no datas available'}

        **MU (annualized)** = {mu.round(3)} ; **SIGMA (annualized)** = {sigma.round(2)}

        **RHO (corr with market)** = {corr.round(3) if corr else 'no datas available'}
        """)

with cl2: 

    st.subheader(f":triangular_flag_on_post: Options Market on {ticker}")
    st.subheader("options caracteristics")
    st.write(f"**Call volume** with expiration today : {'No data available'if daily_returns_market is None or daily_returns_market.empty else int(data_options['Call'].iloc[-1])}, **Proportion** = {'no datas available' if daily_returns_market is None or daily_returns_market.empty else (int(data_options['Call'].iloc[-1])/ vol_calls).round(3)}")
    st.write(f"**Put volume** with expiration today : {'No data available'if daily_returns_market is None or daily_returns_market.empty else int(data_options['Put'].iloc[-1])}, **Proportion** = {'no datas available' if daily_returns_market is None or daily_returns_market.empty else (int(data_options['Put'].iloc[-1])/ vol_puts).round(3)}")
    st.write(f"**Put Call Ratio** : {PCR.round(3) if PCR else 'no datas available'}")
    with st.expander("options positions bar chart : Vol = f(expiration)"):
        if data_options is None or data_options.empty:
            st.write('No datas available')
        else:
            fig = px.bar(data_options, x = "Expiration", y = ["Put", "Call"], text = "Expiration"
                        , template = "seaborn")
            st.plotly_chart(fig, use_container_width = True, height = 200)


# Partie DATA ANALYTICS avec indic tech

# vol profile + volume chart avec EMA

st.sidebar.subheader(':bar_chart: Variables for Analysis')
window = st.sidebar.selectbox("Number of period taken for POC computing :", [a for a in range(20, 61, 5)])


def poc_vah_val(data, ticker, window):
    data_poc = data[["Date","Low","High","Close","Volume"]]
    data_poc['Date'] = pd.to_datetime(data_poc['Date']).dt.date
    data_poc = data_poc.set_index('Date')

    T_final = date.today()
    T_init = T_final - timedelta(days = window)

    while T_init not in data_poc.index:
        T_init -= timedelta(days=1)

    pw = pd.DataFrame()
    pw = data_poc.loc[T_init : T_final].copy()
    pw.reset_index()


    # calc vol total et mid price
    pw["PriceRounded"] = ((pw["High"] + pw["Low"]) / 2 ).round(3)
    volume_total = int(pw.groupby("PriceRounded")["Volume"].sum().sum())

    # DF CLEAN POUR computing
    clean_pw = pw.groupby(by="PriceRounded", as_index=False)["Volume"].sum().sort_values("PriceRounded")

    # POC
    poc_idx = clean_pw["Volume"].idxmax()
    POC = clean_pw.loc[poc_idx, "PriceRounded"]

    #VAH 
    target_val = 0.7*volume_total

    value_area = set([POC])
    cum_volume = clean_pw.loc[poc_idx, "Volume"]

    i_up = poc_idx + 1
    i_down = poc_idx - 1

    while cum_volume < target_val:
        vol_up = clean_pw.loc[i_up, "Volume"] if i_up < len(clean_pw) else 0
        vol_down = clean_pw.loc[i_down, "Volume"] if i_down >= 0 else 0

        if vol_up >= vol_down:
            if i_up < len(clean_pw):
                value_area.add(clean_pw.loc[i_up, "PriceRounded"])
                cum_volume += vol_up
                i_up += 1
        else:
            if i_down >= 0:
                value_area.add(clean_pw.loc[i_down, "PriceRounded"])
                cum_volume += vol_down
                i_down -= 1


    VAL_borne = min(value_area)
    VAH_borne = max(value_area)

    return POC, VAH_borne, VAL_borne, clean_pw 


POC, VAH_borne, VAL_borne, clean_pw = poc_vah_val(data, ticker, window)

col1, col2 = st.columns(2)

with col1: # Le graph du vol profile a été réalisé par chatgpt.
    st.subheader(f" :file_folder: **Volume profile of {ticker} the last {window} periods**")
    price_list = list(np.linspace(clean_pw["PriceRounded"].min(), clean_pw["PriceRounded"].max(),25 ))

    fig = go.Figure([
        go.Bar(x=clean_pw['Volume'],
               y=clean_pw['PriceRounded'],
               orientation='h',
               name="Volume",
               marker_color='lightblue'),
    ])
    fig.add_shape(
        type="rect",
        x0=0,
        x1=clean_pw['Volume'].max(),
        y0=VAL_borne,
        y1=VAH_borne,
        fillcolor="pink",
        opacity=0.4,
        layer="below",
        line_width=0,
    )
    fig.add_shape(
        type="line",
        x0=0,
        x1=clean_pw['Volume'].max(),
        y0=POC,
        y1=POC,
        line=dict(color="red", dash="dash"),
    )
    fig.update_layout(
        xaxis_title="Volume",
        yaxis_title="Price",
        yaxis=dict(tickvals=price_list), 
        showlegend=True,
        height=500,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)

    

with col2:
    st.subheader(f" :file_folder: Daily volumes and EMA20 of volumes of {ticker}")
    fig_vol = go.Figure([
        go.Scatter(x = data['Date'],
                y = data["Volume"],
                line = dict(color = "blue"),
                name = "volume"
        ),

        go.Scatter(x = data['Date'],
                y = data["Volume"].ewm(span = 20).mean(),
                line = dict(color = 'green'),
                name = "EMA VOL 20"
        )
    ])

    fig_vol.update_layout(yaxis_title = "Volume",
                        xaxis_title = "Date", 
                        height = 500)
    
    st.plotly_chart(fig_vol, use_container_width = True)


# candle chart avec ema + cmf en dessous 

st.subheader("**:file_folder: Candlestick chart with EMA crossovers (5, 20, 50) and Chaikin Money Flow displayed at the bottom**")

fig = go.Figure(data=[
        go.Candlestick(
            x=data['Date'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Candles"
        ),
        go.Scatter(
            x=data['Date'],
            y=data['Close'].ewm(span=5).mean(),
            line=dict(color='purple'),
            name="EMA 5",
        ),
        go.Scatter(
            x=data['Date'],
            y=data['Close'].ewm(span=20).mean(),
            line=dict(color='blue'),
            name="EMA 20"
        ),
        go.Scatter(
            x=data['Date'],
            y=data['Close'].ewm(span=50).mean(),
            line=dict(color='red'),
            name="EMA 50"
        )
    ])

fig.update_layout(
    xaxis_rangeslider_visible=False,
    height=600)

st.plotly_chart(fig, use_container_width = True)

# CMF 
CMF = []
data_CMF = data.reset_index()

for t in range(len(data)):

    if t-21 < 0:
        CMF.append(0)

    else:
        PH = data_CMF['High'][t-21 : t].max()
        PB = data_CMF['Low'][t-21 : t].min()

        VOL_gen = data_CMF['Volume'][t-21 : t].sum()

        CMFt = data_CMF.loc[t, "Volume"] * ( ((data_CMF.loc[t, "Close"]- PB) - (PH - data_CMF.loc[t, "Close"])) / (PH - PB)) / VOL_gen
        CMF.append(float(round(CMFt,3)))
    
data["CMF"] = CMF

fig_cmf = go.Figure(data=[
      go.Scatter(
          x=data['Date'],
          y=data['CMF'],
          line=dict(color='blue'),
          name="RAW CMF T=21"
      ),
      go.Scatter(
          x=data['Date'],
          y=data['CMF'].ewm(span=9).mean(), 
          line=dict(color='red'),
          name="CMF EMA9"
      )
    ])
fig_cmf.update_layout(title = f"Chaikin Money Flow of {ticker} with EMA 9 Oscillator",
        yaxis_title = "value",
        xaxis_title = "date",
        height = 400)

with st.expander(":bar_chart: Chaikin Money Flow CMF Chart"):
    st.plotly_chart(fig_cmf, use_container_width = True)


#RSI Code

@st.cache_data
def RSI(data):
    RSI = []
    for a in range(len(data)):
        if a < 14:
            RSI.append(0)

        else:
            period_a_list = []
            i = 0
            while i < 14:
                period_a_list.append(float(data.loc[int(a-i), "Close"]))
                i += 1
                period_a_list = list(reversed(period_a_list))
            
            delta_rde = pd.Series(period_a_list).diff()

            plus_a =[]
            moins_a = []

            for x in delta_rde: 
                if x<0:
                    moins_a.append(abs(x))
                else:
                    plus_a.append(x)

            plus_a = pd.Series(plus_a).dropna()
            moins_a = pd.Series(moins_a).dropna()

            plus_a_mean = plus_a.mean()
            moins_a_mean = moins_a.mean()

            RSa = plus_a_mean/moins_a_mean
            RSIa = 100 - (100/(1+RSa))
            RSI.append(float(RSIa))

    data['RSI'] = RSI
    return(data)

data = RSI(data)

fig_rsi = go.Figure(data=[
        go.Scatter(
            x = data["Date"],
            y = data["RSI"],
            line = dict(color = 'red', width=1),
            name = "RSI"
        ),
        go.Scatter(
            x = data["Date"],
            y = [80 for a in range(len(data))],
            mode = 'lines',
            line = dict(color = 'green', dash = 'dash'),
            name = "sur achat"
        ),
        go.Scatter(
            x = data["Date"],
            y = [20 for a in range(len(data))],
            mode = "lines",
            line = dict(color = "blue", dash = 'dash'),
            name = "sous achat"
        ), 
])

fig_rsi.update_layout(title = f"RSI - {ticker}",
                        xaxis_title = 'Date',
                        height = 500)

# ATR

def ATR(data):

    TR = []
    for a in range(len(data)):
        if a <=1:
            TR.append(0)

        else:
            Ht = data.loc[a, "High"]
            Lt = data.loc[a, "Low"]
            Ct_1 = data.loc[a-1, "Close"]

            Trt = np.max([abs(Ht - Lt), abs(Ht - Ct_1), abs(Lt - Ct_1)])
            TR.append(float(Trt))

    data["TR"] = TR

    # Calcul de l'Atrt avec la methode expo de Wilder et pas la EMA simple : ATRT en ema simple 14 puis ATRT en EMA exponentielle.

    data["ATRT"] = 0.0

    for a in range(len(data)):
        if a < 1:
            data.loc[a, "ATR"] = 0
        else:
            data.loc[a, "ATR"] = (data.loc[a-1, "ATR"]*(14-1) + data.loc[a, "TR"]) / 14

    return(data)

data = ATR(data)
# POur plot ATR
fig_ATR = go.Figure([

        go.Scatter(x = data["Date"],
                   y = data["ATR"],
                   name =  "ATR",
                   line = dict(color = "orange"))
    ])
fig_ATR.update_layout(title = f"Graphique Averare True range ATR - {ticker}",
                          xaxis_title = "Date",
                          height = 500)

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"**:file_folder: Relative Strenght Index RSI Chart of {ticker}**")
    st.plotly_chart(fig_rsi, use_container_width = True)

with col2:
    st.subheader(f"**:file_folder: Average True Range ATR Chart of {ticker}**")
    st.plotly_chart(fig_ATR, use_container_width = True)


# VIX et money management 
vix = yf.download("^VIX", i, T, auto_adjust=True)
vix = pd.DataFrame(vix)
vix = vix.droplevel(1, axis = 1)

vix_plot = go.Figure([
    go.Scatter(
        x=vix.index,
        y=vix["Close"],
        line=dict(color="green"),
        name="VIX Close"
    )
])

vix_plot.update_layout(title="Volatility Index VIX")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader(":file_folder: VIX WRLD INDEX ")
    st.plotly_chart(vix_plot, use_container_width = True)

with col2:
    st.subheader("Money Management and position forecasting")
    st.write("INCOMING")

with col3:
    st.subheader("Analysis Scoring©")
    st.write("INCOMING")


# download to csv and excel 
st.sidebar.write('')
csv_data = data.to_csv(index = False).encode('utf-8')
st.sidebar.subheader(':cd: Data Downloading')
st.sidebar.download_button("Download Data used in these analysis to CSV", data=csv_data, file_name = f'{ticker}.csv', mime = 'text/csv',
                        help = "click here to download as a csv file")

excel_buffer = io.BytesIO()
data.to_excel(excel_buffer, index=False, engine='openpyxl')
excel_buffer.seek(0)
st.sidebar.download_button("Download Data used in these analysis to XLS", data=excel_buffer, file_name = f'{ticker}.xls', mime = 'text/csv',
                        help = "click here to download as a xls file")