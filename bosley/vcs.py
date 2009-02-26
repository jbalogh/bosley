import os
import sys
import logging
import subprocess
from datetime import datetime

import git

import settings

log = logging.getLogger(__file__)
repo = git.Repo(settings.REPO)


class CommandError(Exception):
    pass


def info(head):
    c = repo.commits(head)[0]
    # Only record up to the git-svn part, we don't want to see that.
    git_svn_string = c.message.index('git-svn-id:')
    return {'message': c.message[:git_svn_string],
            'author': '%s' % c.author.name,
            'date': datetime(*c.committed_date[:7]),
            'git_id': c.id,
            'svn_id': svn_id(head),
            }


def svn_id(git_id):
    # Record the current position so we can jump back.  Gross.
    head = open(os.path.join(settings.REPO, '.git', 'HEAD')).read()
    checkout(git_id)
    p = subprocess.Popen('git svn info', stdout=subprocess.PIPE, shell=True,
                         cwd=settings.REPO)
    out = p.communicate()[0].split()
    checkout(head)
    # Looks like "Revision: xxx", so grab the item after Revision.
    return out[1 + out.index('Revision:')]


def before(id):
    return repo.commits(id)[0].parents[0]


def following(commit):
    """Get the commits following `commit`, up to the latest in the repo."""
    latest = repo.commits()[0]
    return repo.commits_between(commit, latest)


def call(cmd):
    status = subprocess.call(cmd, cwd=settings.REPO, shell=True)
    log.debug('call: %s: %s' % (status, cmd))
    if status != 0:
        raise CommandError(status)


def checkout(id):
    try:
        call('git checkout -q %s' % id)
    except CommandError, status:
        # The repo is in an unknown state, don't try to do anything.
        log.error('Bailing after failed checkout!')
        sys.exit(status)


def apply_testing_patch():
    try:
        call('git am -q %s' % settings.path('data/testing.patch'))
    except CommandError, status:
        log.error('Failed to apply testing patch!')
        sys.exit(status)


def reset(id):
    try:
        call('git reset -q --hard %s' % id)
    except CommandError, status:
        log.error('Resetting failed!')
        sys.exit(status)


def rebase():
    try:
        call('git svn rebase -q')
    except CommandError, status:
        log.error('Rebase failed!')
        sys.exit(status)
