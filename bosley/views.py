from sqlalchemy import func

from models import Revision, Result
from utils import expose, get_session, render_template

session = get_session(wsgi=True)


@expose('/')
def revision_list(request):
    revstats = {}
    revisions = session.query(Revision).all()

    for rev in revisions:
        results = session.query(Result).filter(Result.revision == rev)
        broken = results.filter(Result.broken == True).count()
        failing = results.filter(Result.fails > 0).count()
        passes = results.value(func.sum(Result.passes))
        fails = results.value(func.sum(Result.fails))
        total = passes + fails
        revstats[rev] = {'broken': broken, 'failing': failing,
                         'fails': fails, 'passes': passes, 'total': total}

    return render_template('revision_list.html', revisions=revisions,
                           revstats=revstats)
