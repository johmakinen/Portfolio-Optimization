from flask import Flask
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt

import datetime as dt
import pandas_datareader as pdr

app = Flask(__name__)

### Test automating the asset data retrieval using yfinance library
# tickers = ['AAL','AAPL','BAC','F','PFE','MSFT']
# start_date = "2021-11-20"
# end_date = "2021-11-28"

def fetch_data(tickers=["TSLA","AAPL","MSFT"],start_date = dt.datetime.today()-dt.timedelta(weeks=104),end_date = dt.datetime.today()):
    for i in range(len(tickers)):

        if i == 0:
            res = pdr.get_data_yahoo(tickers[i],start=start_date,end=end_date,)[["Adj Close"]].rename(columns={"Adj Close": tickers[i]}).reset_index()
        else:
            curr = pdr.get_data_yahoo(tickers[i],start=start_date,end=end_date,)[["Adj Close"]].rename(columns={"Adj Close": tickers[i]}).reset_index()
            res = pd.merge(res,curr,on=['Date'],how='outer')
    return res






@app.route('/')
def hello_world():
    df_merged = fetch_data()
    cols = df_merged.columns
    return cols[2]
    



if __name__ == '__main__':
    app.run(debug=True,host='0.0.0')