from flask import Flask, render_template, request

import numpy as np
import pandas as pd

import json
import os
import plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

import datetime as dt
import pandas_datareader as pdr
from pandas_datareader._utils import RemoteDataError

app = Flask(__name__)
# app.config['DEBUG'] = True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/callback/<endpoint>')
def cb(endpoint):
    tickers = request.args.get("tickers").split(',')
    if tickers == ['']:
        tickers = ["TSLA", "AAPL", "MSFT"]
    else:
        tickers = [s.strip().upper() for s in tickers]
    if endpoint == "getStock":
        data, bad_tickers = fetch_data(tickers=tickers)
        results = simulate_portfolios(data)
        json_fig = show_results(results)[0]
        return json_fig
    elif endpoint == "getTable":
        data, bad_tickers = fetch_data(tickers=tickers)
        results = simulate_portfolios(data)
        json_tbl = show_results(results)[1]
        return json_tbl
    else:
        return "Bad endpoint", 400

# Test automating the asset data retrieval using yfinance library
# tickers = ['AAL','AAPL','BAC','F','PFE','MSFT']
# start_date = "2021-11-20"
# end_date = "2021-11-28"


def fetch_data(tickers=["TSLA", "AAPL", "MSFT"], start_date=dt.datetime.today().date()-dt.timedelta(weeks=50), end_date=dt.datetime.today()):
    bad_tickers = []
    res = pd.DataFrame(pd.date_range(
        start=start_date, end=end_date), columns=["Date"])
    for i in range(len(tickers)):
        try:
            curr = pdr.get_data_yahoo(tickers[i], start=start_date, end=end_date,)[
                ["Adj Close"]].rename(columns={"Adj Close": tickers[i]}).reset_index()
        except RemoteDataError:
            bad_tickers.append(tickers[i])
            continue
        res = pd.merge(res, curr, on=['Date'], how='outer')
    return res.dropna(axis=0), bad_tickers


def simulate_portfolios(df, n_portfolios=10000):
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
    risk_free_rate = 0.0021  # 1yr US T-Bill
    # https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yieldYear&year=2021

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


def show_results(res):
    ###########################################
    min_volatility_idx = res['Volatility'].argmin()
    max_sharpe_idx = res['Sharpe Ratio'].argmax()

    # use the min, max values to locate and create the two special portfolios
    sharpe_portfolio = res.loc[max_sharpe_idx]
    min_variance_port = res.loc[min_volatility_idx]

    min_variance_port_frame = min_variance_port.to_frame(
        name="Min. Volatility portfolio")
    sharpe_portfolio_frame = sharpe_portfolio.to_frame(
        name="Max. Sharpe portfolio")
    opt_portfolios = min_variance_port_frame.T.append(sharpe_portfolio_frame.T)

    opt_portfolios = min_variance_port_frame.T.append(sharpe_portfolio_frame.T)
    # This is bad code and should be refactored
    ###########################################
    # TABLE
    fig_tbl = ff.create_table(opt_portfolios.round(
        2).reset_index().rename(columns={'index': "Portfolio Type"}))
    fig_tbl.update_layout(width=1294, height=200)
    # SCATTERPLOT
    fig = px.scatter(res[["Returns", "Volatility", "Sharpe Ratio"]],
                     x="Volatility", y="Returns",
                     hover_data=("Returns", "Volatility"), template="seaborn",
                     color="Sharpe Ratio", color_continuous_scale='viridis',
                     width=1250, height=700)

    fig.update_layout(
        xaxis_range=[min(res["Volatility"])-0.1, max(res["Volatility"])+0.1])
    fig.update_layout(
        yaxis_range=[min(res["Returns"])-0.1, max(res["Returns"])+0.1])

    fig.update_traces(marker=dict(size=5,
                                  line=dict(width=1,
                                            color='DarkSlateGrey')),
                      selector=dict(mode='markers'))

    fig.add_trace(
        go.Scatter(
            x=[sharpe_portfolio['Volatility']],
            y=[sharpe_portfolio['Returns']],
            mode="markers+text",
            showlegend=False, marker_symbol="star", marker_color="red",
            marker_line_width=1, marker_size=20, text="Max. Sharpe ratio portfolio", textposition="middle left", textfont_size=14)
    )
    fig.add_trace(
        go.Scatter(
            x=[min_variance_port['Volatility']],
            y=[min_variance_port['Returns']],
            mode="markers+text",
            showlegend=False, marker_symbol="star", marker_color="blue",
            marker_line_width=1, marker_size=20, text="Min. Volatility portfolio", textposition="middle left", textfont_size=14)
    )

    fig.update_layout(
        title={
            'text': "Simulated portfolios and the efficient frontier",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'})

    graphJSON_fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_tbl = json.dumps(fig_tbl, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON_fig, graphJSON_tbl


# if __name__ == '__main__':
#     # port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0')
