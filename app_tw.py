import argparse
import cgi
import logging
import sys
from datetime import datetime
from io import StringIO

import pandas as pd
import requests
from environs import Env

env = Env()
env.read_env()

logger = logging.getLogger(__file__)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_quicken_row(symbol, d, row):
    """
    Reference: https://community.quicken.com/discussion/7542737/faq-importing-security-prices-including-hi-lo-vol/p1?new=1
    """
    return '{symbol}tw, {close}, ---, {date}, ---, {hi}, {lo}, {vol}, *'.format(
        symbol=symbol,
        close=row[6],
        date=d.strftime('%Y/%m/%d'),
        hi=row[4],
        lo=row[5],
        vol=row[1] / 100
    )


def get_today():
    # ref: https://data.gov.tw/dataset/11549
    r = requests.get('http://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data')
    if r.status_code != 200:
        logger.error('Unable to get data from twse: %s %s', r.status_code, r.text)
        raise Exception('Unable to get data')
    else:
        # ex: Content-Disposition: "attachment; filename="STOCK_DAY_ALL_20210312.csv"
        value, params = cgi.parse_header(r.headers['Content-Disposition'])
        filename = params['filename']  # STOCK_DAY_ALL_20210312.csv
        dt = datetime.strptime(filename, 'STOCK_DAY_ALL_%Y%m%d.csv')
        rows = pd.read_csv(StringIO(r.text), index_col=0)
        return dt, rows  # return data date, and dataframes


def parse_args():
    parser = argparse.ArgumentParser(description="Get ticker price")
    parser.add_argument('out', help='output file name')
    args = parser.parse_args()
    return args


def main(args):
    d, rows = get_today()
    with open(args.out, mode='w', encoding='utf-8') as f:
        for symbol in sorted(set(env.str('SYMBOLS_TW').split('\n'))):
            symbol = symbol.strip()
            if not symbol or symbol.startswith('#'):
                continue
            eprint('Getting "{symbol}" price'.format(symbol=symbol))
            row = rows.loc[symbol]
            f.write(get_quicken_row(symbol, d, row))
            f.write('\n')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    env = Env()
    main(parse_args())
