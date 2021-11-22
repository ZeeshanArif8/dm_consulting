import sys # noqa
import textwrap

from . import error

try:
    import urllib2
except ImportError:
    pass

try:
    import requests
except ImportError:
    requests = None


def new_default_http_client(): # noqa
    if requests:
        impl = RequestsClient
    else:
        impl = Urllib2Client

    return impl()


class HTTPClient(object): # noqa
    def request(self, method, url, headers, put_data=None): # noqa
        raise NotImplementedError(
            'HTTPClient subclasses must implement `request`')

    def handle_request_error(self, e): # noqa
        msg = ("Unexpected error communicating with CardConnect.")
        msg = textwrap.fill(msg) + "\n\n(Network error: " + str(e) + ")"
        raise error.ApiConnectionError(msg)


class RequestsClient(HTTPClient): # noqa

    def __init__(self, timeout=30, session=None): # noqa
        self._timeout = timeout
        self._session = session or requests.Session()

    def request(self, method, url, headers, put_data=None): # noqa
        try:
            result = self._session.request(method,
                                           url,
                                           headers=headers,
                                           data=put_data,
                                           timeout=self._timeout)
            content = result.content
            status_code = result.status_code
        except Exception as e:
            super(RequestsClient, self).handle_request_error(e)

        return content, status_code


class Urllib2Client(HTTPClient): # noqa

    def request(self, method, url, headers, put_data=None): # noqa
        if sys.version_info >= (3, 0) and isinstance(put_data, basestring):
            put_data = put_data.encode('utf-8')

        req = urllib2.Request(url, put_data, headers)

        try:
            response = urllib2.urlopen(req)
            content = response.read()
            status_code = response.code
        except urllib2.HTTPError as e:
            status_code = e.code
            content = e.read()
        except (urllib2.URLError, ValueError) as e:
            super(Urllib2Client, self).handle_request_error(e)

        return content, status_code
