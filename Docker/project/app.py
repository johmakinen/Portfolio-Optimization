from flask import Flask, redirect, render_template, url_for, Response

import numpy as np
import pandas as pd
import io

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import datetime as dt
import pandas_datareader as pdr

app = Flask(__name__)

# Test automating the asset data retrieval using yfinance library
# tickers = ['AAL','AAPL','BAC','F','PFE','MSFT']
# start_date = "2021-11-20"
# end_date = "2021-11-28"


def fetch_data(tickers=["TSLA", "AAPL", "MSFT"], start_date=dt.datetime.today()-dt.timedelta(weeks=104), end_date=dt.datetime.today()):
    for i in range(len(tickers)):

        if i == 0:
            res = pdr.get_data_yahoo(tickers[i], start=start_date, end=end_date,)[
                ["Adj Close"]].rename(columns={"Adj Close": tickers[i]}).reset_index()
        else:
            curr = pdr.get_data_yahoo(tickers[i], start=start_date, end=end_date,)[
                ["Adj Close"]].rename(columns={"Adj Close": tickers[i]}).reset_index()
            res = pd.merge(res, curr, on=['Date'], how='outer')
    return res


def simulate_protfolios(df, n_portfolios=20000):
    # Daily and annual returns
    returns_daily = df.set_index("Date").pct_change()
    returns_annual = returns_daily.mean() * 250

    # Daily and annual covariance of returns
    cov_daily = returns_daily.cov()
    cov_annual = cov_daily * 250
    p_returns = []
    p_volatility = []
    sharpe_ratios = []
    asset_weights = []

    # set random seed for reproduction's sake
    np.random.seed(101)
    # set the number of combinations for imaginary portfolios
    n_assets = len(df.columns)-1
    risk_free_rate = 0.01482  # 10 year US bond yield

    for i in range(n_portfolios):
        w = np.random.random(n_assets)
        w /= np.sum(w)
        returns = np.dot(w, returns_annual)
        volatility = np.sqrt(np.dot(w.T, np.dot(cov_annual, w)))
        sharpe = (returns-risk_free_rate) / volatility
        sharpe_ratios.append(sharpe)
        p_returns.append(returns)
        p_volatility.append(volatility)
        asset_weights.append(w)

    df_w = pd.DataFrame(asset_weights, columns=[
                        "Weight: " + s for s in returns_daily.columns.tolist()])
    df_kpi = pd.DataFrame.from_dict({"Returns": p_returns,
                                    "Volatility": p_volatility,
                                     "Sharpe Ratio": sharpe_ratios})
    res = pd.concat([df_kpi, df_w], axis=1)

    return res


def plot_results(res):
    # Known bug from 2015 onwards, X axis does not show up with pandas+matplotlib when using colourbar
    fig, ax = plt.subplots()
    res.plot.scatter(x='Volatility', y='Returns', c='Sharpe Ratio',
                     cmap='viridis', edgecolors='black', ax=ax)
    plt.xlabel('Volatility (Std. Deviation)')
    plt.ylabel('Expected Returns')
    plt.title('Efficient Frontier')

    # Find the minimum volatiliy and maximum sharpe portfolios
    min_volatility_idx = res['Volatility'].argmin()
    max_sharpe_idx = res['Sharpe Ratio'].argmax()

    # use the min, max values to locate and create the two special portfolios
    sharpe_portfolio = res.loc[max_sharpe_idx]
    min_variance_port = res.loc[min_volatility_idx]

    plt.scatter(x=sharpe_portfolio['Volatility'], y=sharpe_portfolio['Returns'],
                c='red', marker='*', s=400, label="Max. Sharpe")
    plt.scatter(x=min_variance_port['Volatility'], y=min_variance_port['Returns'],
                c='blue', marker='*', s=400, label="Min. Volatility")
    plt.legend()
    return fig


# @app.route('/plot.png')
# def plot_png():
#     fig = plot_results()
#     output = io.BytesIO()
#     FigureCanvas(fig).print_png(output)
#     return Response(output.getvalue(), mimetype='image/png')
# Need to figure out correct structure:
# Index.html = Input values -> render_template("plot page..")
# def plot_page(input)
# Simulate + plot tables + figure? Or something else?
# "try again button" -> back to Index.html

@app.route('/')
def home():
    data = fetch_data()
    # cols = df_merged.columns
    res = simulate_protfolios(data, n_portfolios=100)
    # Optimal portfolios:
    min_volatility_idx = res['Volatility'].argmin()
    max_sharpe_idx = res['Sharpe Ratio'].argmax()
    # use the min, max values to locate and create the two special portfolios
    sharpe_portfolio = res.loc[max_sharpe_idx]
    sharpe_html = sharpe_portfolio.to_frame(name="Sharpe portfolio")

    min_variance_port = res.loc[min_volatility_idx]
    var_html = min_variance_port.to_frame(name="Minimum volatility portfolio")

    return render_template("index.html",  tables=[var_html.T.append(sharpe_html.T).to_html(classes='data')], header="true")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0')
