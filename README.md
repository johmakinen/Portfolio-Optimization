# Portfolio-Optimization

#### -- Project Status: [Completed for now]

#### NOTE: Yahoo Finance updated their API which broke this tool's pandas_datareader library (Dec. 2022)

## Project Objective
The purpose of this project is to create a simple interactive tool to optimize the asset allocation of a stock portfolio. This results in two portfolios:
* The minimum volatility portfolio
* the maximum Sharpe ratio portfolio.

The tool is deployed using Google Cloud Platform ([Link here](https://portfolio-optimization-mhsj544yua-lz.a.run.app))

<p align="center">
  <img src="Testing%20and%20notebooks/example_fig_2.png" alt="example_fig" width="800"/>
</p>

### Methods Used
* Modern Portfolio Theory (MPT)
* Markowitz model
* Monte Carlo method

### Technologies
* Python
* Pandas, jupyter
* Flask
* HTML
* JavaScript
* Gunicorn
* Google Cloud Platform

## Project Description

The data used in this project is retrieved from Yahoo Finance using pandas datareader. The data consists of the historical adjusted closing prices for the given assets. From this, we can compute the average returns and the volatilities (standard deviation of returns) for portfolios including the assets. We then use the Monte Carlo method to simulate portfolios with various weights for their assets. From these portfolios, the optimals are found by minimizing the volatility and maximizing the returns.

The interactive tool is an easy way of trying out what happens if you include different assets in your stock portfolio. The tool plots all the simulated portfolios in the volatility-returns -space. The Sharpe ratio describes the average return earned in excess of the risk-free rate per unit of volatility. A high Sharpe ratio is usually preferred over a low. 

The challenges in this project were more concentrated on the technical aspect of implementation. I had never done anything with Docker, Flask, HTML, Javascript or Gunicorn, and thus this was a big learning experience on that front. There are several improvements to be made if the tool is developed further. Mainly the container setup having a separate back and frontend. The containers could also be deployed on for example Heroku for free. The model itself was quite straightforward to implement.

When using the tool you must remember that there are always risks associated with investments. The model implemented in this project will never be 100% certain. The significant drawback of the model is the dependency on historical data. Looking at the history of an asset is not a guarantee of the future of the asset. In the future, we could develop multiple time series predictions for the assets and use robust portfolio optimization to deal with the uncertain future.

## Needs of this project

- Frontend developing
- Data processing/cleaning
- Statistical modeling
- Writeup/reporting
- Model deployment
