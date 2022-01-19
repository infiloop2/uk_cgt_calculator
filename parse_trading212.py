import utils
from os import listdir
from os.path import join
import datetime as dt
import copy

def parse(holdings, ticker_info, dividends):

    all_data_files = [f for f in listdir('Data/Trading212')]
    files = [f for f in all_data_files if f.startswith("trading212")]
    for f in files:
        # print("Reading ", f)
        lines = open(join('Data/Trading212', f), 'r').readlines()
        for l in lines[1:]:
            line = l.strip()
            line = utils.removeCommasWithinQuotes(line)
            cols = line.split(',')
            if (len(cols) == 18):
                trade_type = cols[0]
                if trade_type == 'Deposit' or trade_type == 'Withdrawal':
                    continue
                date = dt.datetime.strptime(cols[1], '%Y-%m-%d %H:%M:%S')
                _isin = cols[2] # not used               
                ticker = cols[3]
                name = cols[4]
                qty = float(cols[5])
                price = float(cols[6])
                currency = cols[7]
                spotgbpfix = cols[8]
                if (spotgbpfix == "Not available"):
                    print('spotfix not available. Ignore line: ' + line)
                    continue
                price = price / float(spotgbpfix)
                _result = cols[9]
                totalGbp = cols[10]
                # columns 11-14 are different witholding taxes + fees
                # ignore them for now
                _tid = cols[17]

                if ticker not in holdings.keys():
                    holdings[ticker] = []
                    ticker_info[ticker] = {
                        'name': name,
                    }
                if 'buy' in trade_type:
                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': price, 'commission': 0, 'option_stock_convert': False}
                    )
                elif 'sell' in trade_type:
                    holdings[ticker].append(
                        {'date': date, 'qty': -1*qty, 'price': price, 'commission': 0, 'option_stock_convert': False}
                    )
                else:
                    print('Neither buy nor sell. Ignore line: ' + line)
    print('--- Holdings ----')
    print(holdings)
    print('--- Ticker info ----')
    print(ticker_info)
    

                

