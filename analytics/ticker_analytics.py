import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, timedelta


from config.constants import etf_national, etf_sectoriel


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


def sharpe(data, market_ticker, sector_ticker, i, T):

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

def corr_ticker_mkt(ticker, data, market_ticker, daily_returns, daily_returns_market):

    corr = 0

    if daily_returns_market is None or daily_returns_market.empty:
        corr = None

    elif daily_returns_market.empty != True:
        conjoint = pd.DataFrame()
        
        conjoint[ticker] = daily_returns
        conjoint[market_ticker] = daily_returns_market
    
        corr = conjoint[[ticker, market_ticker]].corr().iloc[0,1]

    return corr


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