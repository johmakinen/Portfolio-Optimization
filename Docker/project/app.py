from flask import Flask, render_template, request

import numpy as np
import pandas as pd

import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

import datetime as dt
import pandas_datareader as pdr

app = Flask(__name__)


@app.route('/')
def index():

    return render_template('index.html')


@app.route('/callback/<endpoint>')
def cb(endpoint):
    if endpoint == "getStock":
        data = fetch_data()
        results = simulate_protfolios(data)

        # gm(request.args.get('data'), request.args.get('period'), request.args.get('interval'))
        return create_plot(results)
    elif endpoint == "getInfo":
        stock = request.args.get('data')
        st = {"test": 2}
        return json.dumps(st)
    else:
        return "Bad endpoint", 400

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


def create_plot(res):
    # Find the minimum volatiliy and maximum sharpe portfolios
    min_volatility_idx = res['Volatility'].argmin()
    max_sharpe_idx = res['Sharpe Ratio'].argmax()

    # use the min, max values to locate and create the two special portfolios
    sharpe_portfolio = res.loc[max_sharpe_idx]
    min_variance_port = res.loc[min_volatility_idx]

    fig = px.scatter(res[["Returns", "Volatility", "Sharpe Ratio"]],
                     x="Volatility", y="Returns",
                     hover_data=("Returns", "Volatility"), template="seaborn",
                     color="Sharpe Ratio", color_continuous_scale='viridis')

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
            'y': 0.9,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'})

    # Create a JSON representation of the graph
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON


# @app.route('/')
# def home():
#     data = fetch_data()
#     # cols = df_merged.columns
#     res = simulate_protfolios(data, n_portfolios=1000)
#     # Optimal portfolios:
#     min_volatility_idx = res['Volatility'].argmin()
#     max_sharpe_idx = res['Sharpe Ratio'].argmax()
#     # use the min, max values to locate and create the two special portfolios
#     sharpe_portfolio = res.loc[max_sharpe_idx]
#     sharpe_html = sharpe_portfolio.to_frame(name="Sharpe portfolio")

#     min_variance_port = res.loc[min_volatility_idx]
#     var_html = min_variance_port.to_frame(name="Minimum volatility portfolio")

#     scatter_data = create_scatter_data_dict(res["Volatility"].round(
#         3).tolist(), res["Returns"].round(3).tolist())
# # render_template("index.html",  tables=[var_html.T.append(sharpe_html.T).to_html(classes='data')], header="true")
#     return render_template("index.html", scatter_data=scatter_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0')
