import utils
from os import listdir
from os.path import join
import datetime as dt
import copy

def parse(holdings, ticker_info, dividends):

    all_data_files = [f for f in listdir('Data/IBKR')]
    files = [f for f in all_data_files if f.startswith("ibkr")]
    for f in files:
        # print("Reading ", f)
        lines = open(join('Data/IBKR', f), 'r').readlines()
        for l in lines:
            line = l.strip()
            cols = line.split('|')
            if len(cols) == 16:
                asset_type = cols[0]
                ticker = cols[2]
                name = cols[3]
                exchange = cols[4]
                trade_type = cols[5]
                trade_codes = cols[6]
                date = dt.datetime.strptime(cols[7], '%Y%m%d')
                currency = cols[9]
                qty = float(cols[10])

                lot_size = float(cols[11])
                price = float(cols[12])
                commission = float(cols[14])
                spotgbpfx = float(cols[15])

                price = price * lot_size * spotgbpfx
                commission = commission * spotgbpfx

                if asset_type == 'STK_TRD' or asset_type == 'OPT_TRD':
                    if ticker not in holdings.keys():
                        holdings[ticker] = []
                        ticker_info[ticker] = {
                            'name': name,
                            'type': asset_type,
                            'lot_size': lot_size,
                        }

                    if trade_codes == 'O' or trade_codes == 'C' or trade_codes == 'C;O' or trade_codes == 'C;PI' or trade_codes == 'C;FPA':
                        # Normal Open/Close position
                        # PI stands for internal transfer, one off transaction
                        # FPA is for fractional shares
                        holdings[ticker].append(
                            {'date': date, 'qty': qty, 'price': price, 'commission': commission, 'option_stock_convert': False})

                    elif trade_codes == 'C;Ep' and asset_type == 'OPT_TRD':
                        # Option position closed due to expiry
                        holdings[ticker].append(
                            {'date': date, 'qty': qty, 'price': price, 'commission': commission, 'option_stock_convert': False})

                    elif trade_codes == 'C;Ex' and asset_type == 'OPT_TRD':
                        # Option closed due to exercise. There should be a matching 'Ex;O' stock trade
                        # The price is 0, but it's not equivalent to closing position for 0. Instead average cost till this point should
                        # be added in cost basis of matching stock trade
                        holdings[ticker].append(
                            {'date': date, 'qty': qty, 'price': price, 'commission': commission, 'option_stock_convert': True})
                    elif (trade_codes == 'Ex;O' or trade_codes == 'C;Ex;O' or trade_codes == 'C;Ex') and asset_type == 'STK_TRD':
                        # Matching the above. 'C;Ex;O'/'C;Ex' is a special case when you were short the stock
                        # Matching option trade cost price should be added to the base price
                        holdings[ticker].append(
                            {'date': date, 'qty': qty, 'price': price, 'commission': commission, 'option_stock_convert': True})

                    elif trade_codes == 'A;C' and asset_type == 'OPT_TRD':
                        # Option contract was closed as it got assigned. There should be a matching 'A;O' stock trade
                        # The price is 0, but it's not equivalent to closing position for 0. Instead average cost till this point should
                        # be added in cost basis of matching stock trade
                        holdings[ticker].append(
                            {'date': date, 'qty': qty, 'price': price, 'commission': commission, 'option_stock_convert': True})
                    elif (trade_codes == 'A;O' or trade_codes == 'A;C;O' or trade_codes == 'A;C') and asset_type == 'STK_TRD':
                        # Matching the above. 'A;C;O'/'A;C' is a special case when you were long the stock
                        # Matching option trade cost price should be added to the base price
                        holdings[ticker].append(
                            {'date': date, 'qty': qty, 'price': price, 'commission': commission, 'option_stock_convert': True})

                    elif trade_codes == 'Ca':
                        # Cancelled trade, ignore
                        continue
                    else:
                        print(f)
                        print(line)
                        print('WARNING: Unsupported trade code: ',trade_codes)
                elif asset_type == 'CASH_TRD':
                    # Cash transactions do not incur cgt
                    continue
                else:
                    print('WARNING: Unsupported asset type: ', asset_type)

            elif len(cols) >= 10:
                if cols[0] == 'STK_LOT' or cols[0] == 'OPT_LOT':
                    # These are records for net position, no use
                    continue
                # This seems like a row we should parse but dont know the format.
                # Just raise a warning
                print('WARNING: Row not parsed, might be skipping actual transaction: ' + f + line);
