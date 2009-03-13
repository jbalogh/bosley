from sqlalchemy import func

from models import Revision, Test, Assertion, TestFile
from utils import expose, render_template


@expose('/')
def revision_list(request):
    revisions = Revision.query.order_by(Revision.date.desc())[:25]
    return render_template('revision_list.html', revisions=revisions)


@expose('/<int:rev>')
def revision_detail(request, rev):
    revision = Revision.query.filter_by(svn_id=rev).one()
    testfiles = revision.testfiles
    fail_count = func.count(Assertion.fail)
    failing = testfiles.failing().group_by(TestFile.id).add_column(fail_count)
    return render_template('revision_detail.html',
                           revision=revision,
                           failing=failing.order_by(fail_count.desc()),
                           broken=testfiles.filter_by(broken=True))
