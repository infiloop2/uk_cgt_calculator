import utils
from os import listdir
from os.path import join
import datetime as dt
import copy

def parse(historical_crypto_prices, holdings, ticker_info, dividends):
    all_data_files = [f for f in listdir('Data/Coinbase')]
    files = [f for f in all_data_files if f.startswith("coinbase")]
    for f in files:
        #print("Reading ", f)
        lines = open(join('Data/Coinbase', f), 'r').readlines()
        for l in lines:
            line = l.strip()
            line = utils.removeCommasWithinQuotes(line)
            cols = line.split(',')
            if len(cols) == 10:
                # Assumed signature:
                # Timestamp,Transaction Type,Asset,Quantity Transacted,Spot Price Currency,Spot Price at Transaction,Subtotal,Total (inclusive of fees),Fees,Notes
                if cols[0] == 'Timestamp':
                    # This is title row, ignore
                    continue

                date = dt.datetime.strptime(cols[0].split('T')[0], '%Y-%m-%d')
                trade_type = cols[1]
                ticker = cols[2]
                qty = float(cols[3])
                price_currency = cols[4]
                assert (price_currency == 'GBP' or price_currency == ""), "Coinbase record should have base currency as GBP"
                price = float(cols[5])

                if cols[8] == '':
                    commission = 0
                else:
                    commission = float(cols[8])
                comments = cols[9]

                utils.addCryptoTicker(holdings, ticker_info, ticker)

                if trade_type == 'Receive':
                    # Nothing to do as it was a transfer from somewhere else,
                    # ignore this trade
                    continue
                elif trade_type == 'Send':
                    #################
                    ##### ALERT #####
                    #################
                    # Verify this personal assumption.
                    continue
                elif trade_type == 'Buy':
                    # Add as a buy transaction
                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': price, 'commission': commission})
                elif trade_type == 'Sell':
                    # Add as a sell transaction
                    holdings[ticker].append(
                        {'date': date, 'qty': -qty, 'price': price, 'commission': commission})
                elif trade_type == 'Convert':
                    # Acts as both buy and Sell
                    bought_ticker = comments.split(' ')[-1]
                    bought_qty = float(comments.split(' ')[-2])
                    bought_price = round(qty * price / (bought_qty), 8)

                    utils.addCryptoTicker(holdings, ticker_info, bought_ticker)

                    holdings[ticker].append(
                        {'date': date, 'qty': -qty, 'price': price, 'commission': commission / 2})
                    holdings[bought_ticker].append(
                        {'date': date, 'qty': bought_qty, 'price': bought_price, 'commission': commission / 2})
                elif trade_type == 'Coinbase Earn' or trade_type == 'Rewards Income':
                    # Acts as income and also for future CGT equivalent to buying at market price
                    dividends.append({
                        'type' : 'coinbase_earn',
                        'ticker' : ticker,
                        'date' : date,
                        'value' : round(qty * price, 2),
                    })

                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': price, 'commission': commission})
                else:
                    print('WARNING: Unsupported trade type:', trade_type)
            elif len(cols) >= 6:
                # This seems like a row we should parse but dont know the format.
                # Just raise a warning
                print('WARNING: Row not parsed, might be skipping actual transaction: ' + line);
