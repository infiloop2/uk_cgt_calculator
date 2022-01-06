import cryptocompare
from datetime import date, timedelta
import json
import requests

def removeCommasWithinQuotes(line):
    # Removes commas from a line only when they appear within " ... "
    # This is to preprocess a line before splitting it by comma (csv)
    insideQuotes = False
    formatted_string = ''
    for c in line:
        if c == '"':
            insideQuotes = not insideQuotes
        elif c == ',':
            if not insideQuotes:
                formatted_string += c
        else:
            formatted_string += c

    return formatted_string

def addCryptoTicker(holdings, ticker_info, ticker):
    if ticker not in holdings.keys():
        holdings[ticker] = []
        ticker_info[ticker] = {
            'name': ticker,
            'type': 'crypto',
        }

def getBaseTicker(ticker):
    return ticker.split(' ')[0]

def showCurrentCryptoPositions(holdings, ticker_info):
    for ticker in ticker_info.keys():
        net_qty = 0
        last_price = 0
        for trade in holdings[ticker]:
            net_qty += trade['qty']
            last_price = trade['price']

        value = net_qty * last_price
        if value > 50:
            print(ticker, net_qty)

def showCurrentPositions(holdings, ticker_info):
    for ticker in ticker_info.keys():
        net_qty = 0
        for trade in holdings[ticker]:
            net_qty += trade['qty']

        if net_qty != 0:
            print(ticker, net_qty)

def getCryptoAssetPrice(historical_crypto_prices, ticker, date):
    date_str = date.strftime('%Y-%m-%d')
    if ticker not in historical_crypto_prices:
        historical_crypto_prices[ticker] = {}

    if date_str in historical_crypto_prices[ticker]:
        return historical_crypto_prices[ticker][date_str]


    try:
        print("Attempting to fetch crypto price: ", ticker, date_str)
        if ticker == 'BETH':
            betheth = float(getBinanceBethPrice(date))
            ethgbp = float(cryptocompare.get_historical_price('ETH', 'GBP', date)['ETH']['GBP'])
            price = betheth * ethgbp
        elif ticker in ['DEXE', 'LINA', 'LINKUP', 'XRPUP', 'ETHUP', 'BTCUP', 'IOTA', 'AAVEUP']:
            tokenusdt = float(getBinanceTokenUsdtPrice(ticker, date))
            usdtgbp = float(cryptocompare.get_historical_price('USDT', 'GBP', date)['USDT']['GBP'])
            price = tokenusdt * usdtgbp
        else:
            price_data = cryptocompare.get_historical_price(ticker, 'GBP', date)
            price = price_data[ticker]['GBP']
    except:
        print("Error in fetching historical prices. Dumping existing data and exiting")
        f = open('Data/historical_crypto_prices.json', 'w')
        f.write(json.dumps(historical_crypto_prices))
        f.close()
        assert False

    print("Crypto Price Fetched: ", ticker, date_str, price)
    historical_crypto_prices[ticker][date_str] = price
    return price

def getBinanceBethPrice(date):
    startTime = int(date.strftime('%s')) - 3600*5;
    endTime = int(date.strftime('%s')) + 3600*5;
    root_url = 'https://api.binance.com/api/v3/klines'
    url = root_url + '?symbol=' + 'BETHETH' + '&interval=' + '1d' + '&startTime=' + str(startTime) + '000&endTime=' + str(endTime) + '000'
    data = json.loads(requests.get(url).text)
    return data[0][1] # Open price on particular day

def getBinanceTokenUsdtPrice(ticker, date):
    startTime = int(date.strftime('%s')) - 3600*5;
    endTime = int(date.strftime('%s')) + 3600*5;
    root_url = 'https://api.binance.com/api/v3/klines'
    url = root_url + '?symbol=' + ticker + 'USDT' + '&interval=' + '1d' + '&startTime=' + str(startTime) + '000&endTime=' + str(endTime) + '000'
    data = json.loads(requests.get(url).text)
    return data[0][1] # Open price on particular day
