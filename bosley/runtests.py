from __future__ import with_statement

import sys
import logging
import itertools
import threading
from Queue import Queue

import remote
import utils
import vcs
from models import Revision, TestFile, Test, Assertion
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

    if Revision.query.filter_by(git_id=revdata['git_id']).count() != 0:
        return

    revdata['message'] = utils.force_unicode(revdata['message'])
    revdata['author'] = utils.force_unicode(revdata['author'])
    revision = Revision(**revdata)

    session = Revision.query.session
    session.add(revision)
    with CommitLock:
        session.commit()
    try:
        # The object can't be shared across threads.
        test_revision(revision.id)
    except:
        for model in TestFile, Test, Assertion:
            model.query.filter_by(revision=revision).delete()
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
    num_threads = 3
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
        self.queue, self.rev = queue, rev
        threading.Thread.__init__(self)

    def run(self):
        while not self.queue.empty():
            testfile = TestFile(name=self.queue.get(), revision_id=self.rev)
            log.debug('%s: Testing %s...' % (self.getName(), testfile.name))
            self.test(testfile)
            TestFile.query.session.add(testfile)
            with CommitLock:
                TestFile.query.session.commit()
            log.debug('%s: Finished %s' % (self.getName(), testfile.name))

    def test(self, testfile):
        try:
            results = remote.analyze2(testfile.name)
            for test_name, (passing, failing) in results.items():
                test = Test(name=test_name, revision_id=self.rev)
                testfile.tests.append(test)
                for assertion in itertools.chain(passing, failing):
                    test.assertions.append(
                        Assertion(text=utils.force_unicode(assertion),
                                  revision_id=self.rev,
                                  fail=assertion not in passing),
                    )
        except remote.BrokenTest:
            testfile.broken = True


def backfill():
    """Populate old test data: used for going backwards."""
    metadata.create_all(Session.bind)

    oldest = Revision.query.order_by(Revision.date.asc()).first()
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
    latest_recorded = Revision.query.order_by(Revision.date.desc())

    process_commits(vcs.following(latest_recorded.first().git_id))


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
