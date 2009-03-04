from sqlalchemy import Column, ForeignKey, schema
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as fields

from utils import metadata, Session


Base = declarative_base(metadata=metadata)


class Model(object):
    query = Session.query_property()


class Case(Base, Model):
    __tablename__ = 'cases'
    __table_args__ = (schema.UniqueConstraint('name'), {})

    id = Column(fields.Integer, primary_key=True)
    name = Column(fields.String(100))
    results = relation('Result', backref='case')

    def __repr__(self):
        return '<Case %s>' % self.name


class Revision(Base, Model):
    # needs a date for non-numeric revision sorting
    __tablename__ = 'revisions'
    __table_args__ = (schema.UniqueConstraint('git_id'), {})

    id = Column(fields.Integer, primary_key=True)
    svn_id = Column(fields.Integer)
    git_id = Column(fields.String(40))
    message = Column(fields.Text)
    author = Column(fields.String(100))
    date = Column(fields.DateTime)
    results = relation('Result', backref='revision')


class Result(Base, Model):
    __tablename__ = 'results'
    __table_args__ = (schema.UniqueConstraint('case_id', 'revision_id'), {})

    id = Column(fields.Integer, primary_key=True)
    broken = Column(fields.Boolean, default=False)
    passes = Column(fields.Integer, default=0)
    fails = Column(fields.Integer, default=0)

    case_id = Column(fields.Integer, ForeignKey('cases.id'))
    revision_id = Column(fields.Integer, ForeignKey('revisions.id'))

    def __repr__(self):
        if self.broken:
            status = 'BROKEN'
        else:
            status = '(%s, %s)' % (self.passes, self.fails)
        return '<%s %s>' % (self.case, status)
