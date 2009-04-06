from __future__ import with_statement

import sys
import logging
import itertools
import threading
from Queue import Queue

import remote
import utils
import vcs
from models import Revision, TestFile, Test, Assertion, BrokenTest, Result
from utils import metadata, Session

log = logging.getLogger(__file__)

CommitLock = threading.Lock()


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
    revdata = vcs.info(id)

    if Revision.q.filter_by(git_id=revdata['git_id']).count() != 0:
        return

    revdata['message'] = utils.force_unicode(revdata['message'])
    revdata['author'] = utils.force_unicode(revdata['author'])
    revision = Revision(**revdata)

    session = Revision.q.session
    session.add(revision)
    with CommitLock:
        session.commit()
    try:
        # The object can't be shared across threads.
        test_revision(revision.id)
    except:
        # Something bad happened, delete everything that was just created.
        for model in BrokenTest, Result:
            model.q.filter_by(revision=revision).delete()
        session.delete(revision)
        with CommitLock:
            session.commit()
        raise


def test_revision(rev):
    queue = Queue()
    for case in remote.cases():
        queue.put(case)

    # XXX: testing speed is currently limited by languageConfig.test.php,
    # which takes 30s to timeout.  The number of threads could be upped
    # once this is fixed.
    num_threads = 1
    threads = []
    for i in range(num_threads):
        t = ThreadedTester2(queue, rev)
        threads.append(t)
        t.start()

    for t in threads:
        log.debug("Joining " + t.getName())
        t.join()


class ThreadedTester2(threading.Thread):

    def __init__(self, queue, rev):
        threading.Thread.__init__(self)
        self.queue, self.rev = queue, rev

    def run(self):
        self.session = TestFile.q.session
        while not self.queue.empty():
            testfile, _ = TestFile.get_or_create(name=self.queue.get())
            log.debug('%s: Testing %s...' % (self.getName(), testfile.name))
            self.test(testfile)
            self.session.add(testfile)
            with CommitLock:
                self.session.commit()
            log.debug('%s: Finished %s' % (self.getName(), testfile.name))

    def test(self, testfile):
        self.session = TestFile.q.session
        try:
            results = remote.analyze2(testfile.name)
            for test_name, (passing, failing) in results.items():
                test, _ = Test.get_or_create(name=test_name, testfile=testfile)
                testfile.tests.append(test)
                for assertion in itertools.chain(passing, failing):
                    a, _ = Assertion.get_or_create(
                        text=utils.force_unicode(assertion),
                        test=test)
                    result = Result(assertion=a, fail=assertion in failing,
                                    revision_id=self.rev)
                    self.session.add_all((a, result))
        except remote.BrokenTest:
            self.session.add(BrokenTest(revision_id=self.rev,
                                        testfile=testfile))


def backfill():
    """Populate old test data: used for going backwards."""
    metadata.create_all(Session.bind)

    oldest = Revision.q.order_by(Revision.date.asc()).first()
    if oldest is None:
        commit = vcs.repo.commits()[0]
    else:
        commit = vcs.before(oldest.git_id)

    def generator(commit):
        while True:
            yield commit
            commit = vcs.before(commit)

    # Process tests as far back as we can.  Eventually, something will fail.
    process_commits(generator(commit))


def update():
    """Update test data to the latest revision: used for going forward."""
    metadata.create_all(Session.bind)

    vcs.checkout('master')
    vcs.rebase()
    latest_recorded = Revision.q.order_by(Revision.date.desc()).first()
    if latest_recorded is None:
        commit = [vcs.repo.commits()[0]]
    else:
        commit = vcs.following(latest_recorded.git_id)

    process_commits(commit)


def process_commits(commits):
    for commit in commits:
        handle(commit.id)


def main():
    commands = {'backfill': backfill, 'update': update}

    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print "\tUsage: python %s (backfill|update)" % sys.argv[0]
        sys.exit(1)

    commands[sys.argv[1]]()


if __name__ == '__main__':
    import warnings
    warnings.simplefilter('error')
    main()
