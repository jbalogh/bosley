import sys
import logging
from Queue import Queue
from threading import Thread

import sqlalchemy.orm

import remote, vcs
from models import Revision, Case, Result
from utils import get_session, metadata, Session

log = logging.getLogger(__file__)


# Terrible name.
def handle(commit):
    """Setup the repo at commit and run the tests."""
    log.debug('Processing %s' % commit)
    try:
        vcs.checkout(commit)
        try:
            remote.cases()
        except remote.DiscoveryError:
            vcs.apply_testing_patch()
        test_commit(commit)
    finally:
        vcs.reset(commit)
    log.debug('Finished %s' % commit)


def test_commit(id):
    session = get_session()
    revdata = vcs.info(id)
    q = session.query(Revision)

    if q.filter_by(git_id=revdata['git_id']).count() != 0:
        return

    revision = Revision(**revdata)
    session.add(revision)
    session.commit()
    # The object can't be shared across threads.
    test_revision(revision.id)


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


def backfill():
    """Populate old test data: used for going backwards."""
    session = get_session()
    metadata.create_all(session.bind)

    oldest = session.query(Revision).order_by(Revision.date).first()
    if oldest is None:
        commit = vcs.repo.commits()[0].id
    else:
        commit = vcs.before(oldest.git_id).id

    # Process tests as far back as we can.  Eventually, something will fail.
    while True:
        handle(commit)
        commit = vcs.before(commit).id


def update():
    """Update test data to the latest revision: used for going forward."""
    metadata.create_all(Session.bind)

    vcs.checkout('master')
    vcs.rebase()
    latest_recorded = Revision.query.order_by(Revision.date.desc())
    for commit in vcs.following(latest_recorded.first().git_id):
        handle(commit.id)


def main():
    commands = {'backfill': backfill, 'update': update}

    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print "\tUsage: python %s (backfill|update)" % sys.argv[0]
        sys.exit(1)

    commands[sys.argv[1]]()


if __name__ == '__main__':
    main()
