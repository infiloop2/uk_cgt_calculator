from os import listdir
from os.path import join
import datetime as dt
import copy
import sys

import parse_ibkr
import utils
import cgt_calculator

tax_year_in_focus = int(sys.argv[1])

holdings = {}
ticker_info = {}
dividends = []

parse_ibkr.parse(holdings, ticker_info, dividends)

# Add custom records here
# Merge records when stock is converted to something else at ratio 1:r
ticker_conversions = [
    ['VACQU','RKLB', 1],
    ['ARKG  230120C00045000', 'ARKG  230120C00044620', 1],
    ['ARKK  230120C00080960', 'ARKK  230120C00080180', 1],
    ['IAU   230120C00018000', 'IAU1  230120C00018000', 1],
    ['SPRT', 'GREE', 0.115],
]
for ticker_conversion in ticker_conversions:
    from_ticker = ticker_conversion[0]
    to_ticker = ticker_conversion[1]
    r = ticker_conversion[2]

    if from_ticker in holdings:
        for h in holdings[from_ticker]:
            h['qty'] = round(h['qty'] * r, 2)
            h['price'] /= r
            holdings[to_ticker].append(h)
        holdings.pop(from_ticker, None)
        ticker_info.pop(from_ticker, None)

# Just sort ticker info
def sort_key_tickers(ticker):
    base_ticker = utils.getBaseTicker(ticker)
    if (base_ticker == ticker):
        # Put base stocks lower in priority
        return base_ticker + 'ZZ'

    return base_ticker

ticker_list = list(ticker_info.keys())
ticker_list.sort(key=sort_key_tickers)


print('----- Current Positions -----')

utils.showCurrentPositions(holdings, ticker_info)


prev_ticker = ''
total_gains = 0
total_disposals = 0
total_proceeds = 0
total_allowable_cost = 0
total_gains_only = 0
total_loss_only = 0
gain_by_ticker = {}
for ticker in ticker_list:
    if utils.getBaseTicker(ticker) not in gain_by_ticker:
        gain_by_ticker[utils.getBaseTicker(ticker)] = 0.0

    if utils.getBaseTicker(ticker) != prev_ticker:
        print('--------------------------------------------------------')
        print(' ')

    print('Ticker: ', ticker)
    print(' ')
    is_options_ticker = utils.getBaseTicker(ticker) != ticker
    gains, num_disposals, proceeds, allowable_cost, gains_only, loss_only = cgt_calculator.calculate_cgt(holdings, ticker, is_options_ticker, tax_year_in_focus)

    gain_by_ticker[utils.getBaseTicker(ticker)] = round(gain_by_ticker[utils.getBaseTicker(ticker)] + gains, 2)

    total_gains += gains
    total_disposals += num_disposals
    total_proceeds += proceeds
    total_allowable_cost += allowable_cost
    total_gains_only += gains_only
    total_loss_only += loss_only

    print(' ')
    print('--------------------------------------------------------')
    prev_ticker = utils.getBaseTicker(ticker)
gain_by_ticker_list = sorted(gain_by_ticker.items(), key=lambda item: item[1])


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

print('--------------------------------------------------------')
print('--------------------------------------------------------')
