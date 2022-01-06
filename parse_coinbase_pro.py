import utils
from os import listdir
from os.path import join
import datetime as dt
import copy

def parse(historical_crypto_prices, holdings, ticker_info, dividends):
    all_data_files = [f for f in listdir('Data/CoinbasePro')]
    files = [f for f in all_data_files if f.startswith("coinbase")]
    for f in files:
        #print("Reading ", f)
        lines = open(join('Data/CoinbasePro', f), 'r').readlines()
        for l in lines:
            line = l.strip()
            line = utils.removeCommasWithinQuotes(line)
            cols = line.split(',')
            if len(cols) == 9:
                # Assumed signature:
                # portfolio,type,time,amount,balance,amount/balance unit,transfer id,trade id,order id
                if cols[0] == 'portfolio':
                    # This is title row, ignore
                    continue

                trade_type = cols[1]
                date = dt.datetime.strptime(cols[2].split('T')[0], '%Y-%m-%d')

                ticker = cols[5]
                if ticker == 'GBP':
                    # No need to record GBP transactions
                    continue
                qty = float(cols[3])

                price = utils.getCryptoAssetPrice(historical_crypto_prices,ticker, date);

                utils.addCryptoTicker(holdings, ticker_info, ticker)

                if trade_type == 'deposit':
                    # Nothing to do as it's assumed to be a transfer to/from coinbase
                    # ignore this trade
                    continue
                elif trade_type == 'withdrawal':
                    # Nothing to do as it's assumed to be a transfer to/from coinbase
                    # ignore this trade
                    continue
                elif trade_type == 'fee':
                    # Ignore this fees as currently it's not easy to match to the actual trade
                    continue
                elif trade_type == 'match':
                    # Add as a buy/sell transaction. Automatically the qty is positive / negative
                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': price, 'commission': 0})
                else:
                    print('WARNING: Unsupported trade type:', trade_type)
            elif len(cols) >= 6:
                # This seems like a row we should parse but dont know the format.
                # Just raise a warning
                print('WARNING: Row not parsed, might be skipping actual transaction: ' + line);
