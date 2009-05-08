import itertools
from operator import attrgetter

import lockfile
from sqlalchemy import func, and_
from sqlalchemy.orm import eagerload_all

import runtests
import utils
from models import Revision, Assertion, TestFile, Result, Test
from paginator import Paginator
from utils import expose, render, json, Context


PER_PAGE = 20


@expose('/list/', defaults={'page': 1})
@expose('/list/<int:page>')
@render(template='revision_list.html')
def revision_list(request, page):
    revisions = Revision.q.order_by(Revision.date.desc())
    page = Paginator(revisions, PER_PAGE).page(page)
    return Context({'page': page})


@expose('/r/<int:rev>')
@render(template='revision_detail.html')
def revision_detail(request, rev):
    revision = Revision.q.filter_by(svn_id=rev).one()
    previous = (Revision.q.filter(Revision.svn_id < rev)
                .order_by(Revision.svn_id.desc()).first())

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

    return Context({'revision': revision, 'diff': Diff(revision, previous),
                    'failing': failing, 'failures': failures,
                    'broken': revision.broken_tests})


@json
@expose('/status')
def status(request):
    busy = lockfile.FileLock(runtests.LOCKFILE_PATH).is_locked()
    status = {'busy': busy}
    if busy:
        latest = Revision.q.order_by(Revision.svn_id.desc()).first()
        status['latest'] = utils.url_for('revision_detail', latest.svn_id)
    return Context(status)


def r(svn_id):
    q = (Result.q.join(Revision).join(Assertion).join(Test)
         .filter(and_(Revision.svn_id == svn_id, Result.fail == True))
         .group_by(Test.id))
    return list(q.values(Test.name, func.count(Test.id)))


class Diff(object):
    """Analyze the differences between two revisions."""

    def __init__(self, a, b):
        """a and b are Revisions."""
        self.a, self.b = r(a.svn_id), r(b.svn_id)
        self.diff = set(self.a).difference(set(self.b))

        self.broke, self.fixed, self.new = [], [], []

        b_dict = dict(self.b)
        for a_name, a_num in self.diff:
            if a_name in b_dict:
                if a_num > b_dict[a_name]:
                    self.broke.append(a_name)
                else:
                    self.fixed.append(a_name)
            else:
                self.new.append(a_name)

    def category(self, name):
        """Return the category the test falls in as a string."""
        # Mostly useful for templates.
        for attr in ('new', 'broke', 'fixed'):
            if name in getattr(self, attr):
                return attr
        else:
            return ''
