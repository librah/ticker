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


def get_quicken_row(row):
    """
    Reference: https://community.quicken.com/discussion/7542737/faq-importing-security-prices-including-hi-lo-vol/p1?new=1
    """
    return "{symbol}tw, {close}, ---, {date}, ---, {hi}, {lo}, {vol}, *".format(
        symbol=row.get('symbol'),
        close=row.get('close'),
        date=row.get('date').strftime('%Y/%m/%d'),
        hi=row.get('hi'),
        lo=row.get('lo'),
        vol=row.get('vol') / 100
    )


def get_today_twse():
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


def get_today_twotc():
    # ref: https://data.gov.tw/dataset/11371
    r = requests.get('https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&se=EW&o=data')
    if r.status_code != 200:
        logger.error('Unable to get data from tpex: %s %s', r.status_code, r.text)
        raise Exception('Unable to get data')
    else:
        # ex: Content-Disposition: "attachment;filename=SQUOTE_EW_1130312.csv"
        value, params = cgi.parse_header(r.headers['Content-Disposition'])
        filename = params['filename']  # SQUOTE_EW_1130312.csv
        tw_date_str = filename.split('_')[2].split('.')[0]  # 1130312
        if len(tw_date_str) != 7:
            logger.error('Unable to determine otc data date: %s', filename)
            raise Exception("Unable to determine otc data date")
        year = int(tw_date_str[:3]) + 1911
        dt = datetime.strptime(str(year) + tw_date_str[3:], '%Y%m%d')
        rows = pd.read_csv(StringIO(r.text), index_col=1)
        return dt, rows  # return data date, and dataframes


def get_market_watch(symbol):
    # ref: https://www.marketwatch.com/investing/fund/00773b/download-data?countrycode=tw
    r = requests.get(f'https://www.marketwatch.com/investing/fund/{symbol.lower()}/downloaddatapartial?frequency=p1d&csvdownload=true&countrycode=tw')
    if r.status_code != 200:
        logger.error('Unable to get data from marketwatch: %s %s', r.status_code, r.text)
        raise Exception('Unable to get data')
    else:
        rows = pd.read_csv(StringIO(r.text), index_col=0)
        return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Get ticker price")
    parser.add_argument('out', help='output file name')
    args = parser.parse_args()
    return args


def main(args):
    twse_d, twse_rows = get_today_twse()
    twotc_d, twotc_rows = get_today_twotc()
    with open(args.out, mode='w', encoding='utf-8') as f:
        for symbol in sorted(set(env.str('SYMBOLS_TW').split('\n'))):
            symbol = symbol.strip()
            if not symbol or symbol.startswith('#'):
                continue
            eprint('Getting "{symbol}" price'.format(symbol=symbol))
            if symbol in twse_rows.index:
                row = twse_rows.loc[symbol]
                f.write(get_quicken_row({
                    'symbol': symbol,
                    'date': twse_d,
                    'vol': row[1],
                    'hi': row[4],
                    'lo': row[5],
                    'close': row[6],
                }))
                f.write('\n')
            elif symbol in twotc_rows.index:
                row = twotc_rows.loc[symbol]
                f.write(get_quicken_row({
                    'symbol': symbol,
                    'date': twotc_d,
                    'vol': row[7],
                    'hi': row[5],
                    'lo': row[6],
                    'close': row[2],
                }))
                f.write('\n')
            else:
                series = get_market_watch(symbol)
                for series_date, series_data in series.iterrows():
                    f.write(get_quicken_row({
                        'symbol': symbol,
                        'date': datetime.strptime(series_date, '%m/%d/%Y'),
                        'vol': int(series_data[4].replace(',', '')),
                        'hi': series_data[1],
                        'lo': series_data[2],
                        'close': series_data[3]
                    }))
                    f.write('\n')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    env = Env()
    main(parse_args())
