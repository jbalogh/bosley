from sqlalchemy import func, desc

from models import Revision, Result
from utils import expose, get_session, render_template

session = get_session(wsgi=True)


@expose('/')
def revision_list(request):
    revstats = {}
    revisions = session.query(Revision).order_by(desc(Revision.date))[:25]

    for revision in revisions:
        revstats[revision] = stats(session, revision)

    return render_template('revision_list.html', revisions=revisions,
                           revstats=revstats)


def stats(session, revision):
    results = session.query(Result).filter_by(revision=revision)

    broken = results.filter_by(broken=True).count()
    failing = results.filter(Result.fails > 0).count()

    passes = results.value(func.sum(Result.passes))
    fails = results.value(func.sum(Result.fails))

    return {'broken': broken, 'failing': failing, 'fails': fails,
            'passes': passes, 'total': passes + fails}
