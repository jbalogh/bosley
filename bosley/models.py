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

    def passing(self):
        return self.filter(Result.passes == 0)

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
    results = dynamic_loader('Result', backref='revision',
                             query_class=ResultQuery)

    def stats(self):
        results = self.results
        passes, fails = results.sum_passes(), results.sum_fails()
        return {'broken': results.broken().count(),
                'failing': results.failing().count(),
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

    def __repr__(self):
        if self.broken:
            status = 'BROKEN'
        else:
            status = '(%s, %s)' % (self.passes, self.fails)
        return '<%s %s>' % (self.case, status)
