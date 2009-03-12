from sqlalchemy import Column, ForeignKey, schema, func
from sqlalchemy.orm import dynamic_loader, Query
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as fields

from utils import metadata, Session


Base = declarative_base(metadata=metadata)


class Model(object):
    query = Session.query_property()


class ResultQuery(Query):

    def broken(self):
        return self.filter_by(broken=True)

    def failing(self):
        return self.filter(Result.fails > 0)

    def sum_passes(self):
        return self.value(func.sum(Result.passes))

    def sum_fails(self):
        return self.value(func.sum(Result.fails))


class Case(Base, Model):
    __tablename__ = 'cases'
    __table_args__ = (schema.UniqueConstraint('name'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.String(100))
    results = dynamic_loader('Result', backref='case', query_class=ResultQuery)

    def __repr__(self):
        return '<Case %s>' % self.name


class TestFile(Base, Model):
    """A TestFile has many tests and belongs to a Revision."""
    __tablename__ = 'testfiles'
    __table_args__ = (schema.UniqueConstraint('name', 'revision_id'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.String(100))
    broken = Column(fields.Boolean, default=False)

    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))
    tests = dynamic_loader('Test', backref='testfile')


class Test(Base, Model):
    """
    A single test function, belonging to a TestFile, that has many Assertions.
    """
    __tablename__ = 'tests'
    __table_args__ = (schema.UniqueConstraint('name', 'testfile_id'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.String(50))

    # Revision is denormalized to make queries easier.
    # TODO: write validator to make sure relations are correct.
    testfile_id = Column(fields.Integer, ForeignKey('testfiles.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))
    assertions = dynamic_loader('Assertion', backref='test')


class Assertion(Base, Model):
    """ A single passing/failing assertion in a test."""
    __tablename__ = 'assertions'

    id = Column(fields.Integer, primary_key=True)
    fail = Column(fields.Boolean)
    text = Column(fields.Unicode(300))

    # Revision is denormalized to make queries easier.
    # TODO: write validator to make sure relations are correct.
    test_id = Column(fields.Integer, ForeignKey('tests.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))


class Revision(Base, Model):
    """A single revision in version control."""
    # needs a date for non-numeric revision sorting
    __tablename__ = 'revisions'
    __table_args__ = (schema.UniqueConstraint('git_id'), {})

    id = Column(fields.Integer, primary_key=True)
    svn_id = Column(fields.Integer)
    git_id = Column(fields.String(40))
    message = Column(fields.UnicodeText)
    author = Column(fields.Unicode(100))
    date = Column(fields.DateTime)
    results = dynamic_loader('Result', backref='revision',
                             query_class=ResultQuery)

    tests = dynamic_loader('Test', backref='revision')
    testfiles = dynamic_loader('TestFile', backref='revision')
    assertions = dynamic_loader('Assertion', backref='revision')

    def stats(self):
        results = self.results
        passes, fails = results.sum_passes(), results.sum_fails()
        return {'broken': results.broken().count(),
                'failing': results.failing().count(),
                'passes': passes, 'fails': fails, 'total': passes + fails}

    def assertion_stats(self):
        passes = self.assertions.filter_by(fail=False).count()
        fails = self.assertions.filter_by(fail=True).count()
        return {'broken': self.testfiles.filter_by(broken=True).count(),
                'failing': self.testfiles.join(Test).join(Assertion)\
                               .filter(Assertion.fail == True).count(),
                'passes': passes, 'fails': fails, 'total': passes + fails}


class Result(Base, Model):
    __tablename__ = 'results'
    __table_args__ = (schema.UniqueConstraint('case_id', 'revision_id'), {})

    id = Column(fields.Integer, primary_key=True)
    broken = Column(fields.Boolean, default=False)
    passes = Column(fields.Integer, default=0)
    fails = Column(fields.Integer, default=0)

    case_id = Column(fields.Integer, ForeignKey('cases.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))

    query = Session.query_property(ResultQuery)
