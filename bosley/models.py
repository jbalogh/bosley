# -*- delete-whitespace: t -*-
from datetime import datetime

from sqlalchemy import Column, ForeignKey, schema, func, and_
from sqlalchemy.orm import dynamic_loader, relation
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as fields

import settings
from cache import cached
from utils import metadata, Session


Base = declarative_base(metadata=metadata)


class Model(object):
    q = Session.query_property()

    @classmethod
    def get_or_create(cls, **kwargs):
        # kwargs will be passed to filter_by
        defaults = kwargs.pop('defaults', {})
        try:
            return (cls.q.filter_by(**kwargs).one(), False)
        except NoResultFound:
            kwargs.update(defaults)
            return (cls(**kwargs), True)


class TestFile(Base, Model):
    """A TestFile has many tests and belongs to a Revision."""
    __tablename__ = 'testfiles'
    __table_args__ = (schema.UniqueConstraint('name'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.Unicode(255))
    tests = dynamic_loader('Test', backref='testfile')

    @classmethod
    def join_results(cls, revision):
        q = cls.q.join(Test).join(Assertion).join(Result)
        return q.filter(Result.revision == revision)

    @classmethod
    def failing(cls, revision):
        return cls.join_results(revision).filter(Result.fail == True)

    @property
    def target_url(self):
        """Returns an absolute URL where this test was run."""
        return settings.TEST_URL % self.name


class Test(Base, Model):
    """
    A single test function, belonging to a TestFile, that has many Assertions.
    """
    __tablename__ = 'tests'
    __table_args__ = (schema.UniqueConstraint('name', 'testfile_id'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.Unicode(255))
    testfile_id = Column(fields.Integer, ForeignKey('testfiles.id'))
    assertion = dynamic_loader('Assertion', backref='test')


class Assertion(Base, Model):
    """ A single passing/failing assertion in a test."""
    __tablename__ = 'assertions'

    id = Column(fields.Integer, primary_key=True)
    text = Column(fields.UnicodeText)
    test_id = Column(fields.Integer, ForeignKey('tests.id'))
    result = dynamic_loader('Result', backref='assertion')


class BrokenTest(Base, Model):
    __tablename__ = 'brokentests'
    __table_args__ = (schema.UniqueConstraint('testfile_id', 'revision_id'),
                      {})

    id = Column(fields.Integer, primary_key=True)
    testfile_id = Column(fields.Integer, ForeignKey('testfiles.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))
    testfile = relation('TestFile')


class Result(Base, Model):
    __tablename__ = 'results'

    id = Column(fields.Integer, primary_key=True)
    fail = Column(fields.Boolean)
    assertion_id = Column(fields.Integer, ForeignKey('assertions.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))


def r(svn_id):
    q = (Result.q.join(Revision).join(Assertion).join(Test)
         .filter(and_(Revision.svn_id == svn_id, Result.fail == True))
         .group_by(Test.id))
    return list(q.values(Test.id, func.count(Test.id)))


class Diff(object):
    """Analyze the differences between two revisions."""

    def __init__(self, a, b):
        """a and b are Revisions."""
        x, y = r(a.svn_id), r(b.svn_id)
        diff = set(x).difference(set(y))

        self.added = a.total - b.total

        self.broke, self.fixed, self.new = [], [], []

        b_dict = dict(y)
        for a_id, a_num in diff:
            if a_id in b_dict:
                if a_num > b_dict[a_id]:
                    self.broke.append(a_id)
                else:
                    self.fixed.append(a_id)
            else:
                self.new.append(a_id)

    def category(self, name):
        """Return the category the test falls in as a string."""
        # Mostly useful for templates.
        for attr in ('new', 'broke', 'fixed'):
            if name in getattr(self, attr):
                return attr
        else:
            return ''


def stats(key):
    return property(lambda self: self.assertion_stats()[key])


class Revision(Base, Model):
    """A single revision in version control."""
    __tablename__ = 'revisions'
    __table_args__ = (schema.UniqueConstraint('git_id'), {})

    id = Column(fields.Integer, primary_key=True)
    svn_id = Column(fields.Integer)
    git_id = Column(fields.String(40))
    message = Column(fields.UnicodeText)
    author = Column(fields.Unicode(255))
    date = Column(fields.DateTime)
    test_date = Column(fields.DateTime, default=datetime.now)

    results = dynamic_loader('Result', backref='revision')
    broken_tests = dynamic_loader('BrokenTest', backref='revision')

    @cached
    def assertion_stats(self):
        q = Result.q.filter_by(revision=self).group_by(Result.fail)
        if q.count() is None:
            passes = fails = 0
        else:
            passes, fails = [c[0] for c in  q.values(func.count())]
        return {'broken': self.broken_tests.count(),
                'failing': TestFile.failing(self).distinct().count(),
                'passes': passes, 'fails': fails, 'total': passes + fails}

    @property
    def diff(self):
        # Doing this weird to make caching work.
        def differ(a, b):
            return Diff(a, b)
        prev = (Revision.q.filter(Revision.svn_id < self.svn_id)
                .order_by(Revision.svn_id.desc()).first())
        return cached(differ)(self, prev)

    @property
    def cache_key(self):
        return 'Revision:%s:%s' % (self.id, self.test_date)

    broken = stats('broken')
    failing = stats('failing')
    passes = stats('passes')
    fails = stats('fails')
    total = stats('total')

    @property
    def added(self):
        return self.diff.added

    @property
    def new(self):
        return len(self.diff.new)

    @property
    def old(self):
        return self.failing - self.new
