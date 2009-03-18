import itertools
from operator import attrgetter

from sqlalchemy import func
from sqlalchemy.orm import eagerload_all

from models import Revision, Assertion, TestFile
from utils import expose, render_template


@expose('/')
def revision_list(request):
    revisions = Revision.query.order_by(Revision.date.desc())[:25]
    return render_template('revision_list.html', revisions=revisions)


@expose('/<int:rev>')
def revision_detail(request, rev):
    revision = Revision.query.filter_by(svn_id=rev).one()

    fail_count = func.count(Assertion.fail)
    failing = revision.testfiles.failing().group_by(TestFile.id)
    failing = failing.add_column(fail_count).order_by(fail_count.asc())

    failures = {}
    q = Assertion.query.failing().filter_by(revision=revision)
    q = q.order_by(Assertion.test_id).options(eagerload_all('test.testfile'))
    for test, assertions in itertools.groupby(q, attrgetter('test')):
        fail_list = failures.setdefault(test.testfile.id, [])
        # TODO: why is list() necessary?
        fail_list.append((test.name, list(assertions)))

    return render_template('revision_detail.html', revision=revision,
                           failing=failing, failures=failures,
                           broken=revision.testfiles.filter_by(broken=True))
