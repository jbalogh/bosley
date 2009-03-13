from werkzeug import Request, ClosingIterator, SharedDataMiddleware
from werkzeug.exceptions import HTTPException

import views
import settings
from utils import local, local_manager, url_map, engine, Session


class Application(object):

    def __init__(self):
        local.application = self
        self.engine = engine()

        self.dispatch = SharedDataMiddleware(self.dispatch, {
            '/media': settings.path('media'),
        })

    def dispatch(self, environ, start_response):
        local.application = self
        request = Request(environ)
        local.url_adapter = adapter = url_map.bind_to_environ(environ)

        try:
            endpoint, values = adapter.match()
            handler = getattr(views, endpoint)
            response = handler(request, **values)
        except HTTPException, e:
            response = e
        return ClosingIterator(response(environ, start_response),
                               [Session.remove, local_manager.cleanup])

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)
