import os
import sys
import time
import operator
import threading


class Commander(object):

    # {function: [aliases]}
    functions = {}
    # {alias: function} (multiple aliases pointing to same function)
    commands = {}
    # {module: mtime}
    modules = {}
    jobs = []

    @classmethod
    def command(cls, *names):
        # @command
        if len(names) == 1 and hasattr(names[0], '__call__'):
            f = names[0]
            cls.register(f, f.__name__)
            return f
        # @command(name[, name...])
        else:
            def decorator(f):
                cls.register(f, *names)
                return f
            return decorator

    @classmethod
    def cron(cls, delay):
        def wrapper(f):
            cls.register(f)
            f.delay = delay
            cls.jobs.append(f)
            cls.jobs.sort(key=operator.attrgetter('delay'))
            return f
        return wrapper

    @classmethod
    def register(cls, f, *names):
        cls.modules[f.__module__] = mod_mtime(f.__module__)
        cls.functions[f] = names
        for name in names:
            cls.commands[name] = f

    def watcher(self):
        self._die = getattr(self, '_die', False)
        while not self._die:
            for module, mtime in self.modules.items():
                if mod_mtime(module) != mtime:
                    print 'reloading', module
                    self.unload(module)
                    try:
                        reload(sys.modules[module])
                    except Exception, e:
                        pass
                    self.modules[module] = mod_mtime(module)
            time.sleep(5)

    def cronjobs(self):
        def next(i):
            while self.jobs:
                i += 1
                for job in self.jobs:
                    if i % job.delay == 0:
                        return i
            return i + 5
        timer = 1

        while not self._die:
            for job in self.jobs:
                if timer % job.delay == 0:
                    t = threading.Thread(target=self.runner(job),
                                         name='Cron-%s' % job.__name__)
                    t.start()
            delta = next(timer) - timer
            time.sleep(delta)
            timer += delta

    def runner(self, job):
        def threaded():
            del self.jobs[self.jobs.index(job)]
            job(self)
            self.jobs.append(job)
            self.jobs.sort()
        return threaded

    def unload(self, module):
        deathlist = [f for f in self.functions if f.__module__ == module]
        for f in deathlist:
            for alias in self.functions[f]:
                del self.commands[alias]
            del self.functions[f]

        deathlist = [index for index, j in enumerate(self.jobs)
                     if j.__module__ == module]
        for index in deathlist:
            del self.jobs[index]


def mod_mtime(module):
    path = sys.modules[module].__file__
    if path.endswith('.pyc') or path.endswith('.pyo'):
        path = path[:-1]
    return os.stat(path).st_mtime
