from werkzeug.contrib.cache import SimpleCache


cache = SimpleCache()


def get_cache_key(o):
    if hasattr(o, 'cache_key'):
        return o.cache_key
    else:
        return str(o)


def cached(f):
    def inner(*args, **kwargs):
        keys = map(get_cache_key, args)
        for item in kwargs.items():
            keys.append('%s:%s' % get_cache_key(item))
        key = f.__name__ + ':' + '-'.join(keys)
        if cache.get(key) is None:
            cache.set(key, f(*args, **kwargs))
        return cache.get(key)
    return inner
