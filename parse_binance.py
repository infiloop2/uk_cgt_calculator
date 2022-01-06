import utils
from os import listdir
from os.path import join
import datetime as dt
import copy

def parseBinanceAmount(asset):
    ticker = ''
    qty = ''
    for c in asset:
        if ("" + c).isalpha():
            ticker += c
        else:
            qty += c

    return ticker, float(qty)

def parse(historical_crypto_prices, holdings, ticker_info, dividends):
    all_data_files = [f for f in listdir('Data/Binance')]

    trade_files = [f for f in all_data_files if (f.startswith("binance_cross_margin") or f.startswith(
        "binance_isolated_margin"))]
    account_statement_files = [
        f for f in all_data_files if f.startswith("binance_all")]


    for f in trade_files:
        # print("Reading ", f)
        lines = open(join('Data/Binance', f), 'r').readlines()
        for l in lines:
            line = l.strip()
            line = utils.removeCommasWithinQuotes(line)
            cols = line.split(',')
            if len(cols) == 7:
                # Date(UTC),Pair,Side,Price,Executed,Amount,Fee
                if 'Date' in cols[0]:
                    # This is title row, ignore
                    continue

                date = dt.datetime.strptime(cols[0].split(' ')[0], '%Y-%m-%d')
                trade_type = cols[2]
                ticker1, qty1 = parseBinanceAmount(cols[4])
                ticker2, qty2 = parseBinanceAmount(cols[5])
                fee_ticker, fee_qty = parseBinanceAmount(cols[6])

                commission = utils.getCryptoAssetPrice(historical_crypto_prices,fee_ticker, date) * fee_qty

                utils.addCryptoTicker(holdings, ticker_info, ticker1)
                utils.addCryptoTicker(holdings, ticker_info, ticker2)

                if trade_type == 'BUY':
                    holdings[ticker1].append(
                        {'date': date, 'qty': qty1, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker1, date), 'commission': commission / 2})
                    holdings[ticker2].append(
                        {'date': date, 'qty': -qty2, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker2, date), 'commission': commission / 2})
                elif trade_type == 'SELL':
                    holdings[ticker1].append(
                        {'date': date, 'qty': -qty1, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker1, date), 'commission': commission / 2})
                    holdings[ticker2].append(
                        {'date': date, 'qty': qty2, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker2, date), 'commission': commission / 2})
                else:
                    print('---- Unsupported trade type:', trade_type, ' ----')
            elif len(cols) >= 6:
                # This seems like a row we should parse but dont know the format.
                # Just raise a warning
                print('WARNING: Row not parsed, might be skipping actual transaction: ' + line);

    for f in account_statement_files:
        #print("Reading ", f)
        lines = open(join('Data/Binance', f), 'r').readlines()

        # Accumulate all fees separately
        spot_fees = {}
        spot_fees_trade_count = {}
        for l in lines:
            line = l.strip()
            line = utils.removeCommasWithinQuotes(line)
            cols = line.split(',')
            if len(cols) == 7:
                # User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
                if 'User_ID' in cols[0]:
                    # This is title row, ignore
                    continue
                date = dt.datetime.strptime(cols[1].split(' ')[0], '%Y-%m-%d')
                account = cols[2]
                trade_type = cols[3]
                full_time = cols[1]
                ticker = cols[4]
                qty = cols[5]
                if account == 'Spot' and trade_type == 'Fee':
                    if full_time not in spot_fees:
                        spot_fees[full_time] = 0.0
                        spot_fees_trade_count[full_time] = 0
                    qty = -float(qty)
                    spot_fees[full_time] += round(qty * utils.getCryptoAssetPrice(historical_crypto_prices,ticker, date), 2)
                    spot_fees_trade_count[full_time] += 2 #Each commission is counted twice (buy and sell transaction)

        for l in lines:
            line = l.strip()
            line = utils.removeCommasWithinQuotes(line)
            cols = line.split(',')
            if len(cols) == 7:
                # User_ID,UTC_Time,Account,Operation,Coin,Change,Remark
                if 'User_ID' in cols[0]:
                    # This is title row, ignore
                    continue

                date = dt.datetime.strptime(cols[1].split(' ')[0], '%Y-%m-%d')
                account = cols[2]
                trade_type = cols[3]
                ticker = cols[4]
                qty = cols[5]

                if account == 'Coin-Futures' or account == 'CrossMargin' or account == 'IsolatedMargin':
                    # Captured elsewhere
                    continue

                if account != 'Spot':
                    print('WARNING: Unsupported account:', account)
                    continue

                # Now account is spot

                if trade_type in ['Fee']:
                    # Calculated separately
                    continue
                elif trade_type in ['Buy', 'Sell', 'Large OTC trading', 'Transaction Related']:
                    utils.addCryptoTicker(holdings, ticker_info, ticker)
                    qty = float(qty)
                    commission = 0
                    if cols[1] in spot_fees:
                        # Estimate commision
                        commission = spot_fees[cols[1]]/ spot_fees_trade_count[cols[1]]
                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker, date), 'commission': commission})
                elif trade_type == 'Launchpool Interest' or trade_type == 'Liquid Swap rewards' or trade_type == 'POS savings interest' or trade_type == 'ETH 2.0 Staking Rewards' or trade_type == 'Savings Interest' or trade_type == 'Launchpad token distribution':
                    qty = float(qty)
                    dividends.append({
                        'type' : 'binance_earn',
                        'ticker' : ticker,
                        'date' : date,
                        'value' : round(qty * utils.getCryptoAssetPrice(historical_crypto_prices,ticker, date), 2),
                    })

                    utils.addCryptoTicker(holdings, ticker_info, ticker)

                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker, date), 'commission': 0})

                elif trade_type == 'Small assets exchange BNB':
                    utils.addCryptoTicker(holdings, ticker_info, ticker)
                    qty = float(qty)
                    holdings[ticker].append(
                        {'date': date, 'qty': qty, 'price': utils.getCryptoAssetPrice(historical_crypto_prices,ticker, date), 'commission': 0})
                elif trade_type == 'Deposit':
                    # Deposits are inter exchange transfers
                    continue;
                elif trade_type == 'Withdraw':
                    #################
                    ##### ALERT #####
                    #################
                    # This is based on personal assumption to ignore transactions by default
                    continue
                elif trade_type in ['Liquid Swap remove', 'Liquid Swap add', 'POS savings purchase', 'POS savings redemption', 'Savings purchase', 'Savings Principal redemption', 'Launchpad subscribe']:
                    # Ignore transfers to savings accounts. (Earn income is calculated separately)
                    continue
                elif trade_type == 'BNB deducts fee':
                    # These are fees to maintain margin. Ignore these
                    continue
                else:
                    print('WARNING: Unsupported trade type:', trade_type)
            elif len(cols) >= 6:
                # This seems like a row we should parse but dont know the format.
                # Just raise a warning
                print('WARNING: Row not parsed, might be skipping actual transaction: ' + line);
