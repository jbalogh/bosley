# -*- delete-whitespace: t -*-
import functools

from sqlalchemy import Column, ForeignKey, schema, func, and_
from sqlalchemy.orm import dynamic_loader, relation
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as fields

import settings
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
    name = Column(fields.String(100))
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
    name = Column(fields.String(50))
    testfile_id = Column(fields.Integer, ForeignKey('testfiles.id'))
    assertion = dynamic_loader('Assertion', backref='test')


class Assertion(Base, Model):
    """ A single passing/failing assertion in a test."""
    __tablename__ = 'assertions'
    __table_args__ = (schema.UniqueConstraint('text', 'test_id'), {})

    id = Column(fields.Integer, primary_key=True)
    text = Column(fields.UnicodeText)
    test_id = Column(fields.Integer, ForeignKey('tests.id'))
    result = dynamic_loader('Result', backref='assertion')


class Revision(Base, Model):
    """A single revision in version control."""
    __tablename__ = 'revisions'
    __table_args__ = (schema.UniqueConstraint('git_id'), {})

    id = Column(fields.Integer, primary_key=True)
    svn_id = Column(fields.Integer)
    git_id = Column(fields.String(40))
    message = Column(fields.UnicodeText)
    author = Column(fields.Unicode(100))
    date = Column(fields.DateTime)
    test_date = Column(fields.DateTime)

    results = dynamic_loader('Result', backref='revision')
    broken_tests = dynamic_loader('BrokenTest', backref='revision')

    def assertion_stats(self):
        q = Result.q.filter_by(revision=self).group_by(Result.fail)
        passes, fails = map(lambda x: x[0], q.values(func.count()))
        return {'broken': self.broken_tests.count(),
                'failing': TestFile.failing(self).distinct().count(),
                'passes': passes, 'fails': fails, 'total': passes + fails}


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
