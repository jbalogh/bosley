import logging

import lockfile
from werkzeug.contrib.cache import SimpleCache

log = logging.getLogger(__file__)


cache = SimpleCache()


def get_cache_key(o):
    if hasattr(o, 'cache_key'):
        return o.cache_key
    else:
        return str(o)


def cached(f):
    def inner(*args, **kwargs):
        # Don't cache anything if we're running tests.
        import runtests
        if lockfile.FileLock(runtests.LOCKFILE_PATH).is_locked():
            return f(*args, **kwargs)

        keys = map(get_cache_key, args)
        for item in kwargs.items():
            keys.append('%s:%s' % get_cache_key(item))
        key = f.__name__ + ':' + '-'.join(keys)
        if cache.get(key) is None:
            log.info('Miss! %s' % key)
            cache.set(key, f(*args, **kwargs))
        else:
            log.info('Hit! %s' % key)
        return cache.get(key)
    return inner
