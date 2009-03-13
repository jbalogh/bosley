from sqlalchemy import Column, ForeignKey, schema
from sqlalchemy.orm import dynamic_loader, Query
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as fields

from utils import metadata, Session


Base = declarative_base(metadata=metadata)


class Model(object):
    query = Session.query_property()


class TestFileQuery(Query):

    def failing(self):
        q = self.join(Test).join(Assertion)
        return q.filter(Assertion.fail == True).distinct()

    def passing(self):
        q = self.join(Test).join(Assertion)
        return q.filter(Assertion.fail == False).distinct()


class TestQuery(Query):

    def failing(self):
        return self.join(Assertion).filter(Assertion.fail == True).distinct()

    def passing(self):
        return self.join(Assertion).filter(Assertion.fail == False).distinct()


class AssertionQuery(Query):

    def failing(self):
        return self.filter(Assertion.fail == True)

    def passing(self):
        return self.filter(Assertion.fail == False)


class TestFile(Base, Model):
    """A TestFile has many tests and belongs to a Revision."""
    __tablename__ = 'testfiles'
    __table_args__ = (schema.UniqueConstraint('name', 'revision_id'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.String(100))
    broken = Column(fields.Boolean, default=False)

    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))
    tests = dynamic_loader('Test', backref='testfile', query_class=TestQuery)

    query = Session.query_property(TestFileQuery)


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
    assertions = dynamic_loader('Assertion', backref='test',
                                query_class=AssertionQuery)

    query = Session.query_property(TestQuery)


class Assertion(Base, Model):
    """ A single passing/failing assertion in a test."""
    __tablename__ = 'assertions'

    id = Column(fields.Integer, primary_key=True)
    fail = Column(fields.Boolean)
    text = Column(fields.UnicodeText)

    # Revision is denormalized to make queries easier.
    # TODO: write validator to make sure relations are correct.
    test_id = Column(fields.Integer, ForeignKey('tests.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))

    query = Session.query_property(AssertionQuery)


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

    tests = dynamic_loader('Test', backref='revision',
                           query_class=TestQuery)
    testfiles = dynamic_loader('TestFile', backref='revision',
                               query_class=TestFileQuery)
    assertions = dynamic_loader('Assertion', backref='revision',
                                query_class=AssertionQuery)

    def assertion_stats(self):
        passes = self.assertions.passing().count()
        fails = self.assertions.failing().count()
        return {'broken': self.testfiles.filter_by(broken=True).count(),
                'failing': self.testfiles.failing().count(),
                'passes': passes, 'fails': fails, 'total': passes + fails}
