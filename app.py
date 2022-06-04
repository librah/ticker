import argparse
import datetime
import logging
import sys
import time

from alpha_vantage.timeseries import TimeSeries
from environs import Env
from ratelimit import limits
from ratelimit.exception import RateLimitException

env = Env()
env.read_env()

logger = logging.getLogger(__file__)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_quicken_row(symbol, d, row):
    """
    Reference: https://community.quicken.com/discussion/7542737/faq-importing-security-prices-including-hi-lo-vol/p1?new=1
    """
    return '{symbol}, {close}, ---, {date}, ---, {hi}, {lo}, {vol}, *'.format(
        symbol=symbol,
        close=row['4. close'],
        date=d.strftime('%Y/%m/%d'),
        hi=row['2. high'],
        lo=row['3. low'],
        vol=row['5. volume'] / 100
    )


@limits(calls=5, period=60)
def get_daily(symbol):
    ts = TimeSeries(key=env.str('API_KEY'), output_format='pandas')
    daily_data, daily_meta_data = ts.get_daily(symbol=symbol)
    return daily_data


def parse_args():
    parser = argparse.ArgumentParser(description="Get ticker price")
    parser.add_argument('out', help='output file name')
    args = parser.parse_args()
    return args


def main(args):
    one_month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    with open(args.out, mode='w', encoding='utf-8') as f:
        for symbol in sorted(set(env.str('SYMBOLS').split('\n'))):
            symbol = symbol.strip()
            if not symbol or symbol.startswith('#'):
                continue
            while True:
                try:
                    logger.info('Getting "{symbol}" historical price since {d}'.format(symbol=symbol, d=one_month_ago))
                    daily_data = get_daily(symbol)
                    for d, row in daily_data[:(one_month_ago + ' 00:00:00')].iterrows():
                        f.write(get_quicken_row(symbol, d, row))
                        f.write('\n')
                    break
                except RateLimitException:
                    logger.info('Sleep 60 seconds to cope with rate limiting')
                    time.sleep(60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    env = Env()
    main(parse_args())
