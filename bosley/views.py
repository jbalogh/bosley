import logging
import itertools
from operator import attrgetter

import lockfile
import werkzeug
from sqlalchemy import func
from sqlalchemy.orm import eagerload_all
from werkzeug.exceptions import HTTPException

# This sucks, but we need to import filters to make sure they're
# in the environment.
import filters
import runtests
import utils
from cache import get_cache_key
from models import Revision, Assertion, TestFile, Result, Test
from paginator import Paginator
from utils import expose, render, json, Context


log = logging.getLogger(__file__)

PER_PAGE = 20


class NotModified(HTTPException):
    code = 304


@expose('/list/', defaults={'page': 1})
@expose('/list/<int:page>')
@render(template='revision_list.html')
def revision_list(request, page):
    revisions = Revision.q.order_by(Revision.date.desc())
    page = Paginator(revisions, PER_PAGE).page(page)
    return Context({'page': page})


def check_cache(request, view_name, *cache_objects):
    key = '%s-%s-%s' % (request.accept_mimetypes,
                        view_name,
                        '-'.join(map(get_cache_key, cache_objects)))
    etag = werkzeug.generate_etag(key)
    if werkzeug.is_resource_modified(request.environ, etag):
        log.info('No etag match')
        return etag
    else:
        log.info('Not modified!')
        raise NotModified


@expose('/r/<int:rev>')
@render(template='revision_detail.html')
def revision_detail(request, rev):
    q = Revision.q.filter(Revision.svn_id <= rev)
    revision, previous = q.order_by(Revision.svn_id.desc())[:2]

    etag = check_cache(request, 'revision_detail', revision, previous)

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
        fail_list.append((test, list(assertions)))

    return Context({'revision': revision, 'diff': revision.diff,
                    'failing': failing, 'failures': failures,
                    'broken': revision.broken_tests},
                   headers={'Etag': etag})


@json
@expose('/status')
def status(request):
    busy = lockfile.FileLock(runtests.LOCKFILE_PATH).is_locked()
    status = {'busy': busy}
    if busy:
        latest = Revision.q.order_by(Revision.svn_id.desc()).first()
        status['latest'] = utils.url_for('revision_detail', rev=latest.svn_id)
    return Context(status)
