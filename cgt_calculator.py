from os import listdir
from os.path import join
import datetime as dt
import copy
import utils

def getTaxYear(gain_date):
    tax_year = gain_date.year
    if gain_date.month < 4 or (gain_date.month == 4 and gain_date.day < 6):
        tax_year -= 1
    return tax_year

def getTaxYearStr(tax_year):
    return str(tax_year) + '/' + str(tax_year + 1)

def gainAccountForTaxYear(gain_date, gain_amt, tax_year_in_focus):
    tax_year_focus_str = getTaxYearStr(tax_year_in_focus)
    gain_yr = getTaxYear(gain_date)
    if gain_yr == tax_year_in_focus:
        print('    **** Net Gain on', gain_date.strftime('%Y-%m-%d'), ' :', round(gain_amt,2), 'COUNTED WITHIN TAX YEAR: ', tax_year_focus_str, ' ****')
        return gain_amt
    else:
        print('    Net Gain on', gain_date.strftime('%Y-%m-%d'), ' :', round(gain_amt,2), ' BUT NOT IN TAX YEAR: ' , tax_year_focus_str)
        return 0

def getLastTaxDate(tax_year_in_focus):
    return dt.datetime(tax_year_in_focus+1, 4, 5)

def get_sort_key_for_cgt_stock(trade):
    date_str = trade['date'].strftime('%Y-%m-%d')

    # In case of date tie, consider sells first
    if trade['qty'] < 0:
        date_str += 'A'
    else:
        date_str += 'Z'

    return date_str


def get_sort_key_for_cgt_option(trade):
    date_str = trade['date'].strftime('%Y-%m-%d')

    # Non convert has higher priority
    if trade['option_stock_convert']:
        date_str += 'Z'
    else:
        date_str += 'A'

    # In case of date tie, consider sells first
    if trade['qty'] < 0:
        date_str += 'A'
    else:
        date_str += 'Z'

    return date_str


def calculate_cgt(holdings, ticker, is_options_ticker, tax_year_in_focus):
    if is_options_ticker:
        holdings[ticker].sort(key=get_sort_key_for_cgt_option)
    else:
        holdings[ticker].sort(key=get_sort_key_for_cgt_stock)

    sec104_qty = 0
    sec104_price = 0

    total_gains = 0
    num_disposals = 0
    total_proceeds = 0
    total_allowable_cost = 0
    total_gains_only = 0
    total_loss_only = 0

    # Create a deep copy
    trade_list = []
    for trade in holdings[ticker]:
        trade_list.append(copy.deepcopy(trade))

    for i in range(len(trade_list)):
        trade = trade_list[i]
        trade_date = trade['date'].strftime('%Y-%m-%d')
        if trade['date'] > getLastTaxDate(tax_year_in_focus):
            # After tax year, ignore
            continue;
        qty = trade['qty']
        price = trade['price']
        commission = trade['commission']
        option_stock_convert = trade['option_stock_convert'] if 'option_stock_convert' in trade else False

        if qty == 0:
            continue

        if option_stock_convert:
            if is_options_ticker:
                assert is_options_ticker, "Options CGT should be called before stock CGT so that conversion is accounted for"
                print('Trade: ', trade_date,', Option exercise / assigned, Quantity:', qty)
                find_option_stock_conversion_trade(holdings, ticker, trade, sec104_price)
                print('    New Sec104 Quantity:', sec104_qty, ', Average Price:', round(sec104_price, 2))
                continue;
            #Else is an edge case where some options are exercised on expiry. They get counted as expiry so corresponding stock trade
            #is not updated. Treat it normally

        print('Trade: ', trade_date,', Quantity:', qty, ', Price:', round(price, 2), ', Commission:', round(commission,2))

        if qty > 0:
            # Buy
            total_buy_cost = qty * price - commission
            new_qty = sec104_qty + qty
            new_price = (sec104_qty * sec104_price + total_buy_cost) / new_qty

            # New Sec 104 holding
            sec104_qty = new_qty
            sec104_price = new_price
            print('    Add to Sec104 holding: Acquisition Cost:', round(total_buy_cost,2), ', Total Quantity:', sec104_qty, ', Average Price:', round(sec104_price, 2))
        else:
            # Sell
            proceeds = (-qty) * price + commission
            avg_proceeds_price = proceeds / (-qty)
            remaining_qty = -qty
            print('    Disposal Total Proceeds:', round(proceeds,2))

            # Here come the share matching rules:
            # 1. Shares bought on same day, and then within 30 days
            # 2. Sec 104 holding
            # 3. Any future buy

            # 1. Shares bought on same day, and then within 30 days
            for j in range(i + 1, len(trade_list)):
                matching_trade = trade_list[j]
                if matching_trade['qty'] <= 0:
                    # Not a buy trade, continue
                    continue

                time_diff = matching_trade['date'] - trade['date']
                if time_diff.days > 30:
                    # Too old to match now
                    break

                qty_to_match = min(remaining_qty, matching_trade['qty'])
                buying_cost = qty_to_match * \
                    matching_trade['price'] + matching_trade['commission']
                gain = (qty_to_match * avg_proceeds_price) - buying_cost


                match_date = trade_list[j]['date'].strftime('%Y-%m-%d')
                print('    Matched with Same day / 30 day BNB Rule: Trade Date:', match_date, ', Matched quantity: ', qty_to_match, ', Price: ',round(matching_trade['price'],2), ', Commission:', round(matching_trade['commission'],2),  ', Buying Cost:', round(buying_cost,2))

                date_modified_gain = gainAccountForTaxYear(trade['date'], gain, tax_year_in_focus)
                if date_modified_gain != 0:
                    total_gains += date_modified_gain
                    num_disposals += 1
                    total_proceeds += qty_to_match * avg_proceeds_price
                    total_allowable_cost += buying_cost
                    total_gains_only += (date_modified_gain if date_modified_gain > 0 else 0)
                    total_loss_only -= (date_modified_gain if date_modified_gain < 0 else 0)


                # Update future trade to remove the matched quantity
                remaining_qty -= qty_to_match
                trade_list[j]['qty'] -= qty_to_match
                trade_list[j]['commission'] -= trade_list[j]['commission']

                if remaining_qty == 0:
                    break

            if remaining_qty == 0:
                continue
            # 2. Sec 104 holding
            qty_to_match = min(remaining_qty, sec104_qty)
            if qty_to_match > 0:
                buying_cost = qty_to_match * sec104_price
                gain = (qty_to_match * avg_proceeds_price) - buying_cost

                print('    Matched with existing Sec104 holding quantity:', qty_to_match, ' Buying Cost:', round(buying_cost,2))

                date_modified_gain = gainAccountForTaxYear(trade['date'], gain, tax_year_in_focus)
                if date_modified_gain != 0:
                    total_gains += date_modified_gain
                    num_disposals += 1
                    total_proceeds += qty_to_match * avg_proceeds_price
                    total_allowable_cost += buying_cost
                    total_gains_only += (date_modified_gain if date_modified_gain > 0 else 0)
                    total_loss_only -= (date_modified_gain if date_modified_gain < 0 else 0)


                # Update Sec104 holding
                remaining_qty -= qty_to_match
                sec104_qty -= qty_to_match
                print('    Updated Sec104 holding: Total Quantity:', sec104_qty, ', Average Price:', round(sec104_price, 2))


            if remaining_qty == 0:
                continue

            # 3. Any future buy
            for j in range(i + 1, len(trade_list)):
                matching_trade = trade_list[j]
                if matching_trade['qty'] <= 0:
                    # Not a buy trade, continue
                    continue
                # No time limit
                qty_to_match = min(remaining_qty, matching_trade['qty'])

                buying_cost = qty_to_match * \
                    matching_trade['price'] + matching_trade['commission']
                gain = (qty_to_match * avg_proceeds_price) - buying_cost

                match_date = trade_list[j]['date'].strftime('%Y-%m-%d')
                print('    Matched with future buy: Trade Date:', match_date, ', Matched quantity: ', qty_to_match, ', Price: ',round(matching_trade['price'],2), ', Commission:', round(matching_trade['commission'],2),  ', Buying Cost:', round(buying_cost,2))

                date_modified_gain = gainAccountForTaxYear(trade['date'], gain, tax_year_in_focus)
                if date_modified_gain != 0:
                    total_gains += date_modified_gain
                    num_disposals += 1
                    total_proceeds += qty_to_match * avg_proceeds_price
                    total_allowable_cost += buying_cost
                    total_gains_only += (date_modified_gain if date_modified_gain > 0 else 0)
                    total_loss_only -= (date_modified_gain if date_modified_gain < 0 else 0)

                # Update future trade to remove the matched quantity
                remaining_qty -= qty_to_match
                trade_list[j]['qty'] -= qty_to_match
                trade_list[j]['commission'] -= trade_list[j]['commission']

                if remaining_qty == 0:
                    break

            if remaining_qty != 0:
                # Means there is a remaninng short position.
                # Unusual but OK
                continue

    print("Total gains, num_disposals, proceeds, allowable cost, gains_only, losses_only on this ticker in tax year", getTaxYearStr(tax_year_in_focus) ,": ", round(total_gains,2), num_disposals, round(total_proceeds, 2), round(total_allowable_cost, 2), round(total_gains_only, 2), round(total_loss_only, 2))
    return round(total_gains,2), num_disposals, round(total_proceeds, 2), round(total_allowable_cost, 2), round(total_gains_only, 2), round(total_loss_only, 2)


def find_option_stock_conversion_trade(holdings, ticker, option_trade, sec104_price):
    corresponding_stock_ticker = utils.getBaseTicker(ticker)
    assert ticker != corresponding_stock_ticker, "Can only find corresponding stock trades for option trades"

    trade_date = option_trade['date'].strftime('%Y-%m-%d')
    qty = option_trade['qty']

    found = False
    for stock_trade in holdings[corresponding_stock_ticker]:
        if stock_trade['date'].strftime('%Y-%m-%d') == trade_date and stock_trade['option_stock_convert'] and abs(stock_trade['qty']) == abs(qty * 100):
            found = True
            stock_trade['option_stock_convert'] = False
            print("    Matching stock trade found: Trade Date: ", trade_date, ', Matched quantity: ', stock_trade['qty'], ', Price: ',round(stock_trade['price'],2), ', Commission:', round(stock_trade['commission'],2))

            option_sign = qty / abs(qty)
            stock_sign = stock_trade['qty'] / abs(stock_trade['qty'])
            price_change = (sec104_price / 100)
            if option_sign > 0:
                if stock_sign > 0:
                    # Put option assigned, reduce put premium to acquisition price
                    stock_trade['price'] -= price_change
                    print("    Put option assigned, Reduce price by premium received: ", round(price_change,2))
                else:
                    # Call option assigned, add premium to disposal price
                    stock_trade['price'] += price_change
                    print("    Call option assigned, Increase price by premium received: ", round(price_change,2))
            else:
                if stock_sign > 0:
                    # Call option exercised, add cost of call option to stock
                    stock_trade['price'] += price_change
                    print("    Call option exercised, Increase price by premium paid: ", round(price_change,2))
                else:
                    # Put option exercised, subtract cost of put options from price
                    stock_trade['price'] -= price_change
                    print("    Put option exercises, Reduce price by premium paid: ", round(price_change,2))

            break

    assert found, "ERROR: Matching stock trade for option conversion not found. Quitting"
