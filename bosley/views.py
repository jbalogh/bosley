import itertools
from operator import attrgetter

from sqlalchemy import func
from sqlalchemy.orm import eagerload_all

from models import Revision, Assertion, TestFile, Result, Test
from paginator import Paginator
from utils import expose, render_template


PER_PAGE = 20


@expose('/list/', defaults={'page': 1})
@expose('/list/<int:page>')
def revision_list(request, page):
    revisions = Revision.q.order_by(Revision.date.desc())
    page = Paginator(revisions, PER_PAGE).page(page)
    return render_template('revision_list.html', page=page)


@expose('/r/<int:rev>')
def revision_detail(request, rev):
    revision = Revision.q.filter_by(svn_id=rev).one()

    fail_count = func.count(Result.fail)
    failing = (TestFile.failing(revision).group_by(TestFile.id).
               add_column(fail_count).order_by(fail_count.asc()))

    q = Assertion.q.join(Result).filter_by(fail=True, revision=revision)
    q = q.order_by(Assertion.test_id).options(eagerload_all('test.testfile'))
    # Explicit JOIN; otherwise SA generates horrid LEFT OUTER JOINs.
    q = q.join(Test).join(TestFile)

    # We get TestFile.name from the `failing` query above, so we want
    # to look up tests & assertions keyed by a testfile.
    failures = {}
    for test, assertions in itertools.groupby(q, attrgetter('test')):
        fail_list = failures.setdefault(test.testfile.id, [])
        fail_list.append((test.name, list(assertions)))

    return render_template('revision_detail.html', revision=revision,
                           failing=failing, failures=failures,
                           broken=revision.broken_tests)
