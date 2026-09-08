import pandas as pd
import numpy as np
from datetime import date, timedelta
import streamlit as st


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


def CMF(data):
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
    return data
