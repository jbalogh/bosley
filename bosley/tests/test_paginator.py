from nose.tools import eq_

from bosley.models import Revision
from bosley.paginator import Paginator

import fixtures


class TestPaginator(fixtures.BaseCase):

    def setup(self):
        super(TestPaginator, self).setup()
        
        self.count = 10
        Revision.query.session.add_all(Revision(message=u'page')
                                       for x in range(self.count))
        objects = Revision.query.filter_by(message=u'page')
        self.p = Paginator(objects, per_page=4)
        
    def test_count(self):
        eq_(self.p.count, self.count)
        
    def test_num_pages(self):
        eq_(self.p.num_pages, 3)

    def test_page_range(self):
        eq_(self.p.range, [1, 2, 3])
        
    def test_first_page(self):
        page = self.p.page(1)

        assert page.has_next
        assert not page.has_prev
        assert page.next == 2
        assert page.prev == 0

    def test_second_page(self):
        page = self.p.page(2)

        assert page.has_next
        assert page.has_prev
        assert page.next == 3
        assert page.prev == 1
        
    def test_third_page(self):
        page = self.p.page(3)

        assert not page.has_next
        assert page.has_prev
        assert page.next == 4
        assert page.prev == 2

