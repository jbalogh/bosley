import operator
import threading

from sqlalchemy import desc, func
import pyquery

import irc
import views
import runtests
from models import Revision, Result
from utils import get_session


@irc.Bot.cron(60)
def updater(bot):
    q = get_session().query(Revision).order_by(desc(Revision.date))
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
    session = get_session()
    q = session.query(Revision).order_by(desc(Revision.date))
    a, b = [session.query(Result).filter_by(revision=r) for r in q[:2]]
    stats = func.sum(Result.passes), func.sum(Result.fails)
    passing, failing = map(operator.sub, a.values(*stats).next(),
                           b.values(*stats).next())
    rev = session.query(Revision).order_by(desc(Revision.date)).first()
    return rev, passing, failing


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
    session = get_session()
    q = session.query(Revision).order_by(desc(Revision.date))
    stats = views.stats(session, q.first())
    bot.say('%d tests: +%d -%d' %
            (stats['total'], stats['passes'], stats['fails']))
    bot.say('%d broken test files, %d failing' %
            (stats['broken'], stats['failing']))


@irc.Bot.command
def f(bot):
    try:
        p = pyquery.PyQuery('http://www.pangloss.com/seidel/Shaker/')
        bot.say('fligtar: %s' % p('font').text())
    except:
        pass
