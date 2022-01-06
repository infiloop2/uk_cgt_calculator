from os import listdir
from os.path import join
import datetime as dt
import copy
import json
import sys

import parse_coinbase
import parse_coinbase_pro
import parse_binance
import parse_ibkr
import utils
import cgt_calculator

tax_year_in_focus = int(sys.argv[1])

f = open('Data/historical_crypto_prices.json')
historical_crypto_prices = json.load(f)
f.close()

holdings = {}
ticker_info = {}
dividends = []

parse_coinbase.parse(historical_crypto_prices, holdings, ticker_info, dividends)
parse_coinbase_pro.parse(historical_crypto_prices, holdings, ticker_info, dividends)
parse_binance.parse(historical_crypto_prices, holdings, ticker_info, dividends)

# Remove fiat currencies balance as they are not included in CGT
for fiat in ['GBP', 'EUR', 'USDC', 'USDT', 'BUSD']:
    holdings.pop(fiat, None)
    ticker_info.pop(fiat, None)

# Just sort ticker info
ticker_info = dict(sorted(ticker_info.items()))

f = open('Data/historical_crypto_prices.json', 'w')
f.write(json.dumps(historical_crypto_prices))
f.close()


print('----- Current Positions -----')

utils.showCurrentCryptoPositions(holdings, ticker_info)

total_gains = 0
total_disposals = 0
total_proceeds = 0
total_allowable_cost = 0
total_gains_only = 0
total_loss_only = 0
gain_by_ticker = {}
ticker_list = list(ticker_info.keys())
for ticker in ticker_list:
    print('--------------------------------------------------------')
    print(' ')

    print('Ticker: ', ticker)
    print(' ')
    gains, num_disposals, proceeds, allowable_cost, gains_only, loss_only = cgt_calculator.calculate_cgt(holdings, ticker, False, tax_year_in_focus)
    gain_by_ticker[ticker] = gains

    total_gains += gains
    total_disposals += num_disposals
    total_proceeds += proceeds
    total_allowable_cost += allowable_cost
    total_gains_only += gains_only
    total_loss_only += loss_only

    print(' ')
    print('--------------------------------------------------------')
gain_by_ticker_list = sorted(gain_by_ticker.items(), key=lambda item: item[1])

dividend_by_ticker = {}
total_earn = 0
for earn in dividends:
    if earn['type'] == 'coinbase_earn' or earn['type'] == 'binance_earn':
        if cgt_calculator.getTaxYear(earn['date']) != tax_year_in_focus:
            continue;
        ticker = earn['ticker']
        if ticker not in dividend_by_ticker:
            dividend_by_ticker[ticker] = 0
        print("Dividend/Interest: ", earn['type'], ":", earn['date'].strftime('%Y-%m-%d'), "ticker:", ticker, "value:", earn['value'])
        dividend_by_ticker[ticker] += earn['value']
        dividend_by_ticker[ticker] = round(dividend_by_ticker[ticker], 2)
        total_earn += earn['value']
    else:
        assert False, "Dividend type not supported"
dividend_by_ticker_list = sorted(dividend_by_ticker.items(), key=lambda item: item[1])

print('--------------------------------------------------------')
print('--------------------------------------------------------')

print('Final Report for tax year: ', cgt_calculator.getTaxYearStr(tax_year_in_focus))
print('Total Capital Gains: ', round(total_gains, 2))
print('Total Disposals: ', round(total_disposals, 2))
print('Total Proceeds: ', round(total_proceeds, 2))
print('Total Allowable Cost: ', round(total_allowable_cost, 2))
print('Total Gains Only: ', round(total_gains_only, 2))
print('Total Loss only: ', round(total_loss_only, 2))
print(' ')

print('Top 5 tickers with highest gains')
print(gain_by_ticker_list[-5:])
print(' ')

print('Top 5 tickers with highest losses')
print(gain_by_ticker_list[0:5])
print(' ')

print('Total Staking / Earn income: ', round(total_earn, 2))
print('Top 5 tickers with highest earn')
print(dividend_by_ticker_list[-5:])
print(' ')

print('--------------------------------------------------------')
print('--------------------------------------------------------')
