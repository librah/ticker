import argparse
import datetime
import logging
import sys
import time

from twelvedata import TDClient
from environs import Env
from ratelimit import limits
from ratelimit.exception import RateLimitException

env = Env()
env.read_env()

logger = logging.getLogger(__file__)

# Initialize client - apikey parameter is requiered
td = TDClient(apikey=env.str('API_KEY'))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_quicken_row(symbol, row):
    """
    Reference: https://community.quicken.com/discussion/7542737/faq-importing-security-prices-including-hi-lo-vol/p1?new=1
    """
    return '{symbol}, {close}, ---, {date}, ---, {hi}, {lo}, {vol}, *'.format(
        symbol=symbol,
        close=row['close'],
        date=row['datetime'].replace('-', '/'),
        hi=row['high'],
        lo=row['low'],
        vol=int(row['volume']) / 100
    )


@limits(calls=5, period=60)
def get_daily(symbol):
    ts = td.time_series(symbol=symbol, interval="1day", outputsize=10, order='asc')
    return ts.as_json()


def parse_args():
    parser = argparse.ArgumentParser(description="Get ticker price")
    parser.add_argument('out', help='output file name')
    args = parser.parse_args()
    return args


def main(args):
    with open(args.out, mode='w', encoding='utf-8') as f:
        for symbol in sorted(set(env.str('SYMBOLS').split('\n'))):
            symbol = symbol.strip()
            if not symbol or symbol.startswith('#'):
                continue
            while True:
                try:
                    logger.info(f'Getting "{symbol}" historical price')
                    daily_data = get_daily(symbol)
                    for row in daily_data:
                        f.write(get_quicken_row(symbol, row))
                        f.write('\n')
                    time.sleep(1)
                    break
                except RateLimitException:
                    logger.info('Sleep 60 seconds to cope with rate limiting')
                    time.sleep(60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main(parse_args())
