import argparse
import locale
import logging
import sys
import time
from datetime import datetime
from datetime import timedelta

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

import requests
from environs import Env

env = Env()
env.read_env()

logger = logging.getLogger(__file__)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_quicken_row(symbol, row):
    """
    Reference: https://community.quicken.com/discussion/7542737/faq-importing-security-prices-including-hi-lo-vol/p1?new=1
    """
    row['volume'] = 0 if row['volume'] == '--' else locale.atoi(row['volume'])
    row['date'] = datetime.strptime(row['date'], '%m/%d/%Y').strftime('%Y/%m/%d')
    return '{symbol}, {close}, ---, {date}, ---, {hi}, {lo}, {vol}, *'.format(
        symbol=symbol,
        close=row['close'],
        date=row['date'],
        hi=row['high'],
        lo=row['low'],
        vol=row['volume']
    )


def get_daily(symbol, from_date, to_date):
    # ref: https://api.nasdaq.com/api/quote/INDU/historical?assetclass=index&fromdate=2021-06-11&limit=9999&todate=2021-07-11
    uri = 'https://api.nasdaq.com/api/quote/{}/historical?assetclass=index&fromdate={}&todate={}&limit=9999'
    r = requests.get(uri.format(symbol, from_date, to_date), headers={
        'User-Agent': 'PostmanRuntime/7.28.1',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br'
    })
    if r.status_code != 200:
        logger.error('Unable to get data from nasdaq: %s %s', r.status_code, r.text)
        raise Exception('Unable to get data')
    else:
        return r.json()['data']['tradesTable']['rows']


def parse_args():
    parser = argparse.ArgumentParser(description="Get market index")
    args = parser.parse_args()
    return args


def main(args):
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    today = (datetime.now()).strftime('%Y-%m-%d')
    for symbol in sorted(set(env.str('SYMBOLS_IDX').split('\n'))):
        symbol = symbol.strip()
        if not symbol or symbol.startswith('#'):
            continue
        eprint('Getting "{symbol}" index'.format(symbol=symbol))
        daily_data = get_daily(symbol, one_month_ago, today)
        for row in daily_data:
            print(get_quicken_row(symbol, row))
        logger.info('Sleep 1 seconds to cope with rate limiting')
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    env = Env()
    main(parse_args())
