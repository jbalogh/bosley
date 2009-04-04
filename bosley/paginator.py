from __future__ import division

import math


# TODO: write this
cached_property = property


class Paginator(object):

    def __init__(self, objects, per_page):
        self.objects = objects
        self.per_page = per_page

    def page(self, num):
        bottom = self.per_page * (num - 1)
        top = bottom + self.per_page
        objects = self.objects[bottom:top]
        return Page(objects, num, self)

    @cached_property
    def num_pages(self):
        return int(math.ceil(self.count / self.per_page))

    @cached_property
    def count(self):
        return self.objects.count()

    @cached_property
    def range(self):
        return range(1, 1 + self.num_pages)


class Page(object):

    def __init__(self, objects, num, paginator):
        self.objects = objects
        self.num = num
        self.paginator = paginator

    @cached_property
    def has_next(self):
        return self.num != self.paginator.num_pages

    @cached_property
    def has_prev(self):
        return self.num != 1

    @cached_property
    def next(self):
        return self.num + 1

    @cached_property
    def prev(self):
        return self.num - 1
