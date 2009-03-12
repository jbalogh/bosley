from sqlalchemy import func

from models import Revision, Result, Test, Assertion, TestFile
from utils import expose, get_session, render_template

session = get_session(wsgi=True)


@expose('/')
def revision_list(request):
    revisions = Revision.query.order_by(Revision.date.desc())[:25]
    return render_template('revision_list.html', revisions=revisions)


@expose('/<int:rev>')
def revision_detail(request, rev):
    revision = Revision.query.filter_by(svn_id=rev).one()
    testfiles = revision.testfiles
    q = testfiles.join(Test).join(Assertion).filter(Assertion.fail == True)
    fail_count = func.count(Assertion.fail)
    failing = q.group_by(TestFile.id).add_column(fail_count)
    return render_template('revision_detail.html',
                           revision=revision,
                           failing=failing.order_by(fail_count.desc()),
                           broken=testfiles.filter_by(broken=True))


def stats(session, revision):
    results = session.query(Result).filter_by(revision=revision)

    broken = results.filter_by(broken=True).count()
    failing = results.filter(Result.fails > 0).count()

    passes = results.value(func.sum(Result.passes))
    fails = results.value(func.sum(Result.fails))

    return {'broken': broken, 'failing': failing, 'fails': fails,
            'passes': passes, 'total': passes + fails}
