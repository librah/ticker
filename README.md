# ticker

Output stock price in Quicken 2007 format, 
  - US market: use Alpha Vantage API https://www.alphavantage.co/
  - TW market: use https://data.gov.tw/dataset/11549
  - US indexes: https://www.nasdaq.com/market-activity/indexes

## Usage
Prepare `.env` file
```env
API_KEY=<alpha vangage api key>
SYMBOLS="  <= for US listed
AAPL
TSLA
...
"

SYMBOLS_TW="  <= for Taiwan listed
0050
....
"

SYMBOLS_IDX=" <= for indexes from Nasdaq, ex: INDU => Dow Jones Index
COMP
INDU
NDX
RUT
SPX
"
```

```console
$ pip install -r requirements.txt
$ python app.py > price.csv
$ python app_tw.py > price_tw.csv
$ python app_idx.py > price_idx.csv
```

Quicken expects the file is UTF8 encoded. If you failed to import the file,
convert the file encoding (ex: Sublime) and try again.
