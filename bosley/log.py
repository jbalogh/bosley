import os
import logging
from logging import handlers

import settings


def stab_java():
    dir = settings.path('logs')
    if not os.path.exists(dir):
        os.makedirs(dir)

    level = logging.DEBUG

    # Roll over every 3 days, only keep 3 backups.
    h = handlers.TimedRotatingFileHandler(os.path.join(dir, 'bosley.log'),
                                          when='D', interval=3, backupCount=3)
    h.setLevel(level)

    f = logging.Formatter('%(asctime)s %(levelname)s:%(name)s:%(message)s')
    h.setFormatter(f)

    logging.root.addHandler(h)
    logging.root.setLevel(level)
