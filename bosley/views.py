from sqlalchemy import func, desc

from models import Revision, Result
from utils import expose, get_session, render_template

session = get_session(wsgi=True)


@expose('/')
def revision_list(request):
    revstats = {}
    revisions = session.query(Revision).order_by(desc(Revision.date))

    for rev in revisions:
        results = session.query(Result).filter_by(revision=rev)

        broken = results.filter_by(broken=True).count()
        failing = results.filter(Result.fails > 0).count()

        passes = results.value(func.sum(Result.passes))
        fails = results.value(func.sum(Result.fails))

        revstats[rev] = {'broken': broken, 'failing': failing, 'fails': fails,
                         'passes': passes, 'total': passes + fails}

    return render_template('revision_list.html', revisions=revisions,
                           revstats=revstats)
