import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yfinance as yf


def volume_profile_chart(clean_pw, POC, VAH_borne, VAL_borne, ticker, window):
    price_list = list(np.linspace(clean_pw["PriceRounded"].min(), clean_pw["PriceRounded"].max(), 25))

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
    return fig


def volume_ema_chart(data):
    fig_vol = go.Figure([
        go.Scatter(x=data['Date'],
                   y=data["Volume"],
                   line=dict(color="blue"),
                   name="volume"),

        go.Scatter(x=data['Date'],
                   y=data["Volume"].ewm(span=20).mean(),
                   line=dict(color='green'),
                   name="EMA VOL 20")
    ])

    fig_vol.update_layout(yaxis_title="Volume",
                          xaxis_title="Date",
                          height=500)
    return fig_vol


def candlestick_ema_chart(data):
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
    return fig


def cmf_chart(data, ticker):
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
    fig_cmf.update_layout(title=f"Chaikin Money Flow of {ticker} with EMA 9 Oscillator",
                          yaxis_title="value",
                          xaxis_title="date",
                          height=400)
    return fig_cmf


def rsi_chart(data, ticker):
    fig_rsi = go.Figure(data=[
        go.Scatter(
            x=data["Date"],
            y=data["RSI"],
            line=dict(color='red', width=1),
            name="RSI"
        ),
        go.Scatter(
            x=data["Date"],
            y=[80 for a in range(len(data))],
            mode='lines',
            line=dict(color='green', dash='dash'),
            name="sur achat"
        ),
        go.Scatter(
            x=data["Date"],
            y=[20 for a in range(len(data))],
            mode="lines",
            line=dict(color="blue", dash='dash'),
            name="sous achat"
        ),
    ])

    fig_rsi.update_layout(title=f"RSI - {ticker}",
                          xaxis_title='Date',
                          height=500)
    return fig_rsi


def atr_chart(data, ticker):
    fig_ATR = go.Figure([
        go.Scatter(x=data["Date"],
                   y=data["ATR"],
                   name="ATR",
                   line=dict(color="orange"))
    ])
    fig_ATR.update_layout(title=f"Graphique Averare True range ATR - {ticker}",
                          xaxis_title="Date",
                          height=500)
    return fig_ATR


def vix_chart(i, T):
    vix = yf.download("^VIX", i, T, auto_adjust=True)
    vix = vix.droplevel(1, axis=1)

    vix_plot = go.Figure([
        go.Scatter(
            x=vix.index,
            y=vix["Close"],
            line=dict(color="green"),
            name="VIX Close"
        )
    ])
    vix_plot.update_layout(title="Volatility Index VIX")
    return vix_plot


def options_bar_chart(data_options):
    fig = px.bar(data_options, x="Expiration", y=["Put", "Call"], text="Expiration",
                 template="seaborn")
    return fig
