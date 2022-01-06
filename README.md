# IBKR,Coinbase,Binance Trades Parser + CGT calculator (UK Rules)

## To run

If you want to make a report for tax year Apr 2020 - Ape 2021 use:

- For stocks: ```python3 main_ibkr.py 2020```
- For crypto: ```python3 main_crypto.py 2020```

## Dependencies

- You need to install cryptocompare library to fetch crypto prices on a given date. ```python3 -m pip install cryptocompare```
- The free version of their API should generally suffice, although there are rate limits. However this program stores all fetched prices in a file so that they don't need to be fetched again.
  If you run into rate limits, simply re-run the program after few seconds and new data will be appended

## About

- This is a CGT calculator for UK tax. You need to download trade reports from your brokers and store it in Data folder. You'll need your statements since
 you opened your accounts (and not just the tax year in focus) since your cost basis is dependent on your past trades
- This calculator handles
    - Uses UK cost averaging, with daily GBP rates used
    - Matches Disposals based on 30-day bed and breakfast rule -> Sec 104 Matching -> Future buys
    - Handles option expiry, assignment
    - Handles crypto trades and staking / earn interest
    - Does not include FX transactions. Unclear if currency held in accounts should be liable to CGT upon exchange back to GBP

## Support

- IBKR: You need to download monthly tradelog exports from IBKR. Store them as Data/IBKR/ibkr....
- Coinbase: Download all transactions in csv format. Store them as Data/Coinbase/coinbase....   
    - There are 2 tricky transactions: sends and receives from external wallets, make sure you handle them correctly.
    - Either you ignore them if you sent them to yourself on a different exchange / wallet or consider them as a disposal if you used them up on the blockchain.
    - By default these are ignored
- Coinbase Pro: Download all transactions in csv format.Store them as Data/CoinbasePro/coinbase....
    - By default Deposits and Withdrawals are ignored (usually they are through coinbase itself)
- Binance: Download trade reports per quarter:
    - Combined account statements (Useful for Spot and Earn accounts). Store them as Data/Binance/binance_all....
    - Cross margin. Store them as Data/Binance/binance_cross_margin....
    - Isolated margin. Store them as Data/Binance/binance_isolated_margin....
