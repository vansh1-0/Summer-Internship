from flask import Flask, render_template, request
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

COINS = {
    'bitcoin': 'BTC',
    'ethereum': 'ETH',
    'dogecoin': 'DOGE',
    'pi-network': 'PI',
    'litecoin': 'LTC',
    'solana': 'SOL'
}

def get_price_history(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    params = {"vs_currency": "usd", "days": "15", "interval": "daily"}
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print("Error fetching price history:", res.status_code, res.text)
        return pd.DataFrame()

    data = res.json()
    if 'prices' not in data:
        print("No 'prices' key found in response:", data)
        return pd.DataFrame()

    prices = data['prices']
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["day"] = df["timestamp"].dt.day
    return df

def forecast_prices(price_data):
    price_data['timestamp_index'] = np.arange(len(price_data))
    X = price_data[['timestamp_index']]
    y = price_data['price']
    model = LinearRegression()
    model.fit(X, y)

    future_days = 7
    future_indexes = np.arange(len(price_data), len(price_data) + future_days).reshape(-1, 1)
    forecast = model.predict(future_indexes)
    return forecast

def create_price_forecast_plot(df, forecast):
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['price'], label="Historical Price", marker='o')

    future_dates = pd.date_range(start=df['timestamp'].iloc[-1] + pd.Timedelta(days=1), periods=7)
    plt.plot(future_dates, forecast, label="Forecast", linestyle='--', marker='x', color='orange')

    plt.title("Crypto Price + 7-Day Forecast")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64

def get_crypto_news():
    try:
        url = "https://newsdata.io/api/1/latest"
        params = {
            "apikey": "pub_46521347dd6b409daa0f151126849b48",
            "q": "crypto",
            "language": "en"
        }
        response = requests.get(url, params=params)
        print("NewsData.io Status:", response.status_code)

        if response.status_code != 200:
            raise Exception("News API failed")

        data = response.json()
        news_items = []
        for item in data.get("results", [])[:5]:
            title = item.get("title", "No Title")
            news_items.append({"title": title})  # Plain text only
        return news_items

    except Exception as e:
        print("Fallback news used due to:", e)
        return [
            {"title": "Crypto Market Shows Signs of Recovery"},
            {"title": "Bitcoin ETF Launch Raises Hopes"},
            {"title": "Solana Reaches New All-Time High"},
            {"title": "Ethereum 2.0 Delayed Again"},
            {"title": "Pi Network Tests Mainnet Rollout"}
        ]

@app.route("/", methods=["GET", "POST"])
def index():
    selected_coin = "bitcoin"
    if request.method == "POST":
        selected_coin = request.form.get("coin", "bitcoin")

    coin_name = selected_coin
    symbol = COINS[selected_coin]

    df = get_price_history(coin_name)
    forecast = forecast_prices(df)
    plot_img = create_price_forecast_plot(df, forecast)

    news = get_crypto_news()

    return render_template("index.html",
                           coin=coin_name.upper(),
                           plot_img=plot_img,
                           news=news)

if __name__ == "__main__":
    app.run(debug=True)
