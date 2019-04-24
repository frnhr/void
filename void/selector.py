#!/usr/bin/env python
"""
void_selector 0.1

Outputs paths of images from VOID which cross the ephemeides
 given by stdin.

Usage:
    void_selector [--verbosity=V]
    void_selector -v | --version
    void_selector -h | --help

Options:
  -h --help           Show this help screen
  -v --version        Show program name and version number
  -V --verbosity=V    Logging verbosity, 0 to 4 [default: 2]

"""
import logging
import sys
import docopt
from astropy.time import Time

from void import common
from void.settings import settings
from void.common import DataBase
from void.writer import Writer

log = logging.getLogger(__name__)


class Selector:
    def __init__(self):
        settings.load()
        self.db = DataBase.get_void_db(settings)

    @staticmethod
    def line_to_point(line_str):
        line_spl = line_str[:39].split()
        year, month, date, hour, ra, dec = line_spl
        if len(hour) > 2:
            minutes = hour[2:]
        else:
            minutes = '00'
        hour = hour[:2]
        time_isot = (
            '-'.join([year, month, date])
            + 'T'
            + ':'.join([hour, minutes, '00.000'])
        )

        time_unix = Time(time_isot, format='isot', scale='utc').unix
        ra = float(ra)
        dec = float(dec)

        return ra, dec, time_unix

    def linestr_points_intersection(self, line_points):
        line_points.append(line_points[0])
        with Writer() as writer:
            line_str = writer.poly_to_linestr(line_points)
        exe_str = """
            SELECT observations.path FROM observations
            WHERE ST_Contains(observations.poly,
            ST_GeomFromText(%s));
        """
        self.db.exec(exe_str, line_str)
        paths = self.db.cursor.fetchall()
        return paths.split


def main():
    name_and_version = __doc__.strip().splitlines()[0]
    arguments = docopt.docopt(__doc__, help=True, version=name_and_version)
    common.configure_log(arguments['--verbosity'])
    log.debug('listening')

    selector = Selector()
    line_points = []

    try:
        for line in sys.stdin:
            if not line:
                continue
            ra, dec, time_unix = selector.line_to_point(line)
            line_points.append([ra, dec, time_unix])
            log.info(f'processing {line}')
    except KeyboardInterrupt:
        log.debug('SIGINT')

    paths = selector.linestr_points_intersection(line_points)
    for path in paths:
        sys.stdout.write(path)


if __name__ == '__main__':
    main()
