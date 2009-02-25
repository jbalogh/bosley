import logging
from Queue import Queue
from threading import Thread

import sqlalchemy.orm

import remote, vcs
from models import Revision, Case, Result
from utils import get_session, metadata

session = get_session(wsgi=False)

log = logging.getLogger(__file__)


def test_commit(id='HEAD'):
    revdata = vcs.info(id)
    q = session.query(Revision)

    if q.filter_by(git_id=revdata['git_id']).count() == 0:
        revision = Revision(**revdata)
        session.add(revision)
        session.commit()
        # The object can't be shared across threads.
        test_revision(revision.id)


class ThreadedTester(Thread):

    def __init__(self, queue, rev):
        # Sessions can't be shared across threads.
        self.session = get_session(wsgi=False)
        self.queue =queue
        self.rev = rev
        Thread.__init__(self)

    def run(self):
        while not self.queue.empty():
            case = self.queue.get()
            log.debug('%s: Testing %s...' % (self.getName(), case))

            result = self.test(case)
            result.revision_id = self.rev
            self.session.add(result)
            self.session.commit()

            log.debug('%s: Finished %s' % (self.getName(), result))

    def test(self, case_name):
        try:
            case = self.session.query(Case).filter_by(name=case_name).one()
        except sqlalchemy.orm.exc.NoResultFound:
            case = Case(name=case_name)

        try:
            passes, fails = remote.analyze(case_name)
            return Result(case=case, passes=passes, fails=fails)
        except remote.BrokenTest:
            return Result(case=case, broken=True)


def test_revision(rev):
    queue = Queue()
    for case in remote.cases():
        queue.put(case)

    # XXX: testing speed is currently limited by languageConfig.test.php,
    # which takes 30s to timeout.  The number of threads could be upped
    # once this is fixed.
    num_threads = 3
    threads = []
    for i in range(num_threads):
        t = ThreadedTester(queue, rev)
        threads.append(t)
        t.start()

    for t in threads:
        log.debug("Joining " + t.getName())
        t.join()


def populate():
    metadata.create_all(session.bind)

    oldest = session.query(Revision).order_by('date').first()
    if oldest is None:
        commit = vcs.repo.commits()[0].id
    else:
        commit = vcs.before(oldest.git_id).id

    # Process tests as far back as we can.  Eventually, something will fail.
    while True:
        log.debug('Processing %s' % commit)
        vcs.checkout(commit)
        try:
            vcs.apply_testing_patch()
            test_commit(commit)
        finally:
            vcs.reset('%s' % commit)
        log.debug('Finished %s' % commit)
        commit = vcs.before(commit).id


if __name__ == '__main__':
    populate()
