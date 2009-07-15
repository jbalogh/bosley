from __future__ import with_statement

import sys
import logging
import itertools
import threading
import traceback
from Queue import Queue

import lockfile

import remote
import settings
import vcs
from models import Revision, TestFile, Test, Assertion, BrokenTest, Result
from utils import force_unicode, metadata, Session

log = logging.getLogger(__file__)

CommitLock = threading.Lock()

LOCKFILE_PATH = settings.path('bosley.lock')


def handle(commit):
    """Setup the repo at commit and run the tests."""
    lock = lockfile.FileLock(LOCKFILE_PATH)
    # Don't block waiting for a lock. TODO: make this configurable.
    try:
        lock.acquire(0)
        log.debug('Processing %s' % commit)
        try:
            vcs.checkout(commit)

            try:
                # TODO: fixme!
                vcs.call('./reset.sh')
            except vcs.CommandError:
                add_revision(commit)
                return

            try:
                remote.cases()
            except remote.DiscoveryError:
                vcs.apply_testing_patch()
            test_commit(commit)
        finally:
            vcs.reset(commit)
        log.debug('Finished %s' % commit)

    finally:
        try:
            lock.release()
        except lockfile.UnlockError:
            pass


def add_revision(commit):
    """Add a Revision for the given git hash."""
    revdata = vcs.info(commit)

    if Revision.q.filter_by(git_id=revdata['git_id']).count() != 0:
        return

    for key in 'message', 'author':
        revdata[key] = force_unicode(revdata[key])

    revision = Revision(**revdata)

    session = Revision.q.session
    session.add(revision)
    with CommitLock:
        session.commit()

    return revision


def test_commit(commit):
    revision = add_revision(commit)

    if revision is None:
        return

    try:
        # The object can't be shared across threads.
        test_revision(revision.id)
    except:
        # Something bad happened, delete everything that was just created.
        for model in BrokenTest, Result:
            model.q.filter_by(revision=revision).delete()

        session = Revision.q.session
        session.delete(revision)
        with CommitLock:
            session.commit()
        raise


def test_revision(rev):
    queue = Queue()
    for case in remote.cases():
        queue.put(case)

    num_threads = 10
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
        """Wrapper around process_queue that logs exceptions."""
        try:
            self.process_queue()
        except:
            log.error(''.join(traceback.format_exception(*sys.exc_info())))
            raise

    def process_queue(self):
        self.session = TestFile.q.session
        while not self.queue.empty():
            filename = force_unicode(self.queue.get())
            testfile, _ = TestFile.get_or_create(name=filename)
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
                test, _ = Test.get_or_create(name=force_unicode(test_name),
                                             testfile=testfile)
                testfile.tests.append(test)
                for assertion in itertools.chain(passing, failing):
                    a, _ = Assertion.get_or_create(
                        text=force_unicode(assertion),
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
