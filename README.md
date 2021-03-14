# ticker

Output stock price in Quicken 2007 format, 
  - US market: use Alpha Vantage API https://www.alphavantage.co/
  - TW market: use https://data.gov.tw/dataset/11549

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
```

```console
$ pip install -r requirements.txt
$ python app.py > price.csv
$ python app_tw.py > price_tw.csv
```