# ticker

Output stock price in Quicken 2007 format 
using Alpha Vantage API https://www.alphavantage.co/

## Usage
Prepare `.env` file
```env
API_KEY=<alpha vangage api key>
SYMBOLS="
AAPL
TSLA
...
"
```

```console
$ pip install -r requirements.txt
$ python app.py > price.csv  # save the output to file
```