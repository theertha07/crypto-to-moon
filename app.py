import re
import tweepy
import matplotlib.pyplot as plt
import json
import requests
import pandas as pd
import plotly.express as px
from tweepy import OAuthHandler
from textblob import TextBlob
from datetime import datetime
import plotly.graph_objects as go
from flask import Flask, render_template, request, redirect


def clear_tweet(tweet):
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())


def tweet_sentiment(tweet):
    analysis = TextBlob(clear_tweet(tweet))
    if analysis.sentiment.polarity > 0:
        return 'positive'
    elif analysis.sentiment.polarity < 0:
        return 'negative'
    else:
        return 'neutral'


def get_tweets(api, query, count=5):
    tweets = []
    count = int(count)
    try:
        positive = 0
        negative = 0
        neutral = 0
        fetched_tweets = tweepy.Cursor(
            api.search_tweets, q=query, lang='en', tweet_mode='extended').items(count)
        for tweet in fetched_tweets:
            parsed_tweet = {}
            if 'retweeted_status' in dir(tweet):
                parsed_tweet['text'] = tweet.retweeted_status.full_text
            else:
                parsed_tweet['text'] = tweet.full_text
            parsed_tweet['sentiment'] = tweet_sentiment(parsed_tweet['text'])
            if parsed_tweet['sentiment'] == 'positive':
                positive += 1
            if parsed_tweet['sentiment'] == 'negative':
                negative += 1
            if parsed_tweet['sentiment'] == 'neutral':
                neutral += 1
            if tweet.retweet_count > 0:
                if parsed_tweet not in tweets:
                    tweets.append(parsed_tweet)
            else:
                tweets.append(parsed_tweet)
        return {'tweets': tweets, 'positive': positive, 'negative': negative, 'neutral': neutral}
    except tweepy.TweepyException as e:
        print('Error: '+str(e))


app = Flask(__name__)
app.static_folder = 'static'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        query = request.form['query']
        count = request.form['count']
        fetched_tweets = get_tweets(api, query, count)['tweets']
        pos = get_tweets(api, query, count)['positive']
        neg = get_tweets(api, query, count)['negative']
        neu = get_tweets(api, query, count)['neutral']
    return render_template('result.html', result=fetched_tweets)


@app.route('/graph', methods=['GET', 'POST'])
def graph():
    if request.method == 'POST':
        query = request.form['query']
        count = request.form['count']
        pos = get_tweets(api, query, count)['positive']
        neg = get_tweets(api, query, count)['negative']
        neu = get_tweets(api, query, count)['neutral']
        ids = query
        crypto_prices = requests.get(
            f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=inr').json()
        print(crypto_prices)
        return render_template('graph.html', pos=pos, neg=neg, neu=neu, query=query, crypto_prices=crypto_prices)


@app.route('/graph1', methods=['GET', 'POST'])
def graph1():
    # if request.method == 'POST':
    query = request.form['query']
    count = request.form['count']
    pos = get_tweets(api, query, count)['positive']
    neg = get_tweets(api, query, count)['negative']
    neu = get_tweets(api, query, count)['neutral']
    sentiments = ['positive', 'negative', 'neutral']
    pol = [pos, neg, neu]
    plt.pie(pol, labels=sentiments)
    plt.show()
    return redirect('/')


@app.route('/technical', methods=['GET', 'POST'])
def technical():
    sym = request.form['sym']
    crypto = sym
    days = '365'
    api_key = '1cec96a7b694df83797206bbcf31a42e3ebf4105be44de2eb5dbfcc737120677'
    historical_prices = requests.get(
        f'https://min-api.cryptocompare.com/data/v2/histoday?fsym={crypto}&tsym=USD&limit={days}&api_key={api_key} ').json()
    price_data = {}
    for item in historical_prices['Data']['Data']:
        time = datetime.fromtimestamp(item['time'])
        price_data[time] = {}
        price_data[time]['date'] = time
        price_data[time]['open'] = item['open']
        price_data[time]['high'] = item['high']
        price_data[time]['low'] = item['low']
        price_data[time]['close'] = item['close']
    price_DF = pd.DataFrame.from_dict(price_data)
    price_DF = price_DF.T
    fig = go.Figure(data=[go.Candlestick(x=price_DF['date'], open=price_DF['open'],
                    high=price_DF['high'], low=price_DF['low'], close=price_DF['close'])])
    fig.update_layout(title='Trend in '+crypto+' USD Price'+' over 1 year')
    fig.show()
    return redirect('/')


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')


@app.route('/more')
def more():
    return render_template('more.html')


if __name__ == "__main__":
    consumer_key = 'EwG6T8KZTCuSfv6Wy2rfUu1gO'
    consumer_secret = 'R8dREd4HyxY6flL3OOHktuEfkTAXj66HZ5QGWGUsmoKfcaNhND'
    access_token = '405461195-HdMbZqc7YmMP5yTMG5rix5nrahxGP72WG9VjF6w1'
    access_token_secret = '9Zl6g93TtRvH3voFlOd6pbDwFGZ5A7YLDJnogrkm1O0NT'

    try:
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
    except:
        print('Authentication error')
    app.run(debug=True)
