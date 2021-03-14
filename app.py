import argparse
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
    args = parser.parse_args()
    return args


def main(args):
    for symbol in sorted(set(env.str('SYMBOLS').split('\n'))):
        symbol = symbol.strip()
        if not symbol:
            continue
        try:
            eprint('Getting "{symbol}" historical price'.format(symbol=symbol))
            daily_data = get_daily(symbol)
            for d, row in daily_data[:'2021-03-01 00:00:00'].iterrows():
                print(get_quicken_row(symbol, d, row))
        except RateLimitException:
            eprint('Sleep 60 seconds to cope with rate limiting')
            time.sleep(60)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    env = Env()
    main(parse_args())
