import numpy as np
import pandas as pd

from data.downloader import data_stock_universe_download
from config.constants import T,i
from datetime import date, timedelta

ticker = ["AAPL", "NVDA", "MSFT"]

i = date.today() - timedelta(days=years*365)
T = date.today()
data = data_stock_universe_download(ticker, i, T)


# Portfolio Metrics
def portfolio_return(weights, expected_returns):

    return weights @ expected_returns


def portfolio_variance(weights, covariance_matrix):

    return weights @ covariance_matrix @ weights


def portfolio_volatility(weights, covariance_matrix):

    return np.sqrt( portfolio_variance(weights, covariance_matrix))


def portfolio_sharpe(weights, expected_returns, covariance_matrix, risk_free_rate=0.0 ):

    expected_return = portfolio_return( weights, expected_returns )

    volatility = portfolio_volatility( weights, covariance_matrix)

    if volatility == 0:
        return np.nan

    return (expected_return - risk_free_rate) / volatility

# Minimum Variance weights

def minimum_variance_portfolio(covariance_matrix):

    n_assets = covariance_matrix.shape[0]

    ones = np.ones(n_assets)

    sigma_inv = np.linalg.inv(covariance_matrix)

    numerator = sigma_inv @ ones
    denominator = ones @ sigma_inv @ ones

    weights = numerator / denominator

    return weights

# Max sharpe portfolio

def maximum_sharpe_portfolio( expected_returns, covariance_matrix, risk_free_rate=0.0 ):

    n_assets = len(expected_returns)
    ones = np.ones(n_assets)

    excess_returns = ( expected_returns - risk_free_rate * ones )

    x = np.linalg.solve( covariance_matrix, excess_returns )

    weights = x / (ones @ x)

    return weights

# Mean v ariance frontiere

def efficient_frontier( expected_returns, covariance_matrix, target_returns ):


    mu = np.asarray(expected_returns)
    sigma = np.asarray(covariance_matrix)

    n_assets = len(mu)

    ones = np.ones(n_assets)

    sigma_inv = np.linalg.inv(sigma)

    A = ones @ sigma_inv @ ones
    B = ones @ sigma_inv @ mu
    C = mu @ sigma_inv @ mu

    D = A * C - B**2

    if D <= 0:
        raise ValueError(
            "Invalid covariance/return inputs."
        )

    frontier_returns = []
    frontier_volatilities = []
    frontier_weights = []

    for target_return in target_returns:

        weights = sigma_inv @ ( ((C - B * target_return) / D) * ones + ((A * target_return - B) / D) * mu )

        variance = weights @ sigma @ weights

        volatility = np.sqrt(variance)

        frontier_returns.append(target_return)
        frontier_volatilities.append(volatility)
        frontier_weights.append(weights)

    return {
        "returns": np.array(frontier_returns),
        "volatilities": np.array(frontier_volatilities),
        "weights": np.array(frontier_weights)
    }

# Composed portoflio metrics computation

def calculate_expected_returns( returns, periods=252 ):
    return returns.mean() * periods


def calculate_covariance_matrix( returns, periods=252):
    return returns.cov() * periods



