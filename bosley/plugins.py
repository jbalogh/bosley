import operator
import threading

import pyquery

import irc
import runtests
from models import Revision, Assertion


@irc.Bot.cron(60)
def updater(bot):
    q = Revision.query.order_by(Revision.date.desc())
    latest = q.first()
    runtests.update()
    if latest.id != q.first().id:
        rev, passing, failing = st()
        if not (passing == failing == 0):
            bot.run_command('status')


@irc.Bot.command('status', 'st', 'sitrep')
def status(bot):
    rev, passing, failing = st()
    bot.say('r%s (%s): %+d passing, %+d failing' %
            (rev.svn_id, rev.author, passing, failing))


def st():
    q = Revision.query.order_by(Revision.date.desc())
    def counts(x):
        passing = Assertion.fail == False
        return x.filter(passing).count(), x.filter(~passing).count()
    a, b = [Assertion.query.filter_by(revision=r) for r in q[:2]]
    passing, failing = map(operator.sub, counts(a), counts(b))
    return q.first(), passing, failing


@irc.Bot.command
def gtfo(bot):
    bot.say('stfu')


@irc.Bot.command
def help(bot):
    bot.say(', '.join(sorted(bot.commands)))


@irc.Bot.command
def wtf(bot):
    bot.say(', '.join(t.getName() for t in threading.enumerate()))


@irc.Bot.command
def report(bot):
    rev = Revision.query.order_by(Revision.date.desc()).first()
    stats = rev.assertion_stats()
    bot.say('%d tests: +%d -%d' %
            (stats['total'], stats['passes'], stats['fails']))
    bot.say('%d failing test files, %d broken' %
            (stats['failing'], stats['broken']))


@irc.Bot.command
def f(bot):
    try:
        p = pyquery.PyQuery('http://www.pangloss.com/seidel/Shaker/')
        bot.say('fligtar: %s' % p('font').text())
    except:
        pass
