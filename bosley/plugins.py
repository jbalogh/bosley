import operator
import threading

import pyquery

import irc
import settings
import runtests
from models import Revision


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
    bot.say('r%s (%s): %+d passing, %+d failing (%s)' %
            (rev.svn_id, rev.author, passing, failing,
             settings.REVISION_DETAIL_URL % rev.svn_id))


def st():
    q = Revision.query.order_by(Revision.date.desc())
    a, b = [r.assertions for r in q[:2]]
    counts = lambda x: (x.passing().count(), x.failing().count())
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
