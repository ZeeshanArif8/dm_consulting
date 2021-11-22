import urllib # noqa
from urllib.parse import urlparse
import base64

from . import error, http_client, util


def _api_encode(data):
    for key, value in data.items():
        key = util.utf8(key)
        if value is None:
            continue
        else:
            yield (key, util.utf8(value))


def _build_api_url(url, query):
    scheme, netloc, path, base_query, fragment = urlparse.urlsplit(url)

    if base_query:
        query = '%s&%s' % (base_query, query)

    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


class ApiRequestor(object): # noqa

    def __init__(self): # noqa
        self._client = http_client.new_default_http_client()

    def request(self, method, url, params=None): # noqa
        rbody, rcode = self.request_raw(method.lower(), url, params)
        resp = self.interpret_response(rbody, rcode)
        return resp

    def handle_api_error(self, rbody, rcode, resp): # noqa
        try:
            err = resp['resptext']
        except (KeyError, TypeError):
            raise error.ApiError(
                "Invalid response from API: %r (HTTP response code "
                "was %d)" % (rbody, rcode),
                rbody, rcode, resp)

        raise error.ApiError(err, rbody, rcode, resp)

    def request_raw(self, method, url, params=None): # noqa

        from . import username, password, base_url
        if username is None:
            raise error.AuthenticationError('No username provided')

        if password is None:
            raise error.AuthenticationError('No password provided')

        if base_url is None:
            raise error.AuthenticationError('No base URL provided')

        abs_url = 'https://%s/cardconnect/rest%s' % (base_url, url)

        encoded_params = _api_encode(params or {})

        if method in ['get', 'delete']:
            if params:
                abs_url = _build_api_url(
                    abs_url, urllib.urlencode(list(encoded_params)))
            put_data = None
        elif method == 'put':
            put_data = util.json.dumps(dict(encoded_params))

            
        # base64_creds = base64.b64encode('%s:%s' % (username, password))
        requestdata = '%s:%s' % (username, password)
        base64_creds = base64.urlsafe_b64encode(requestdata.encode('UTF-8'))

        headers = {
            'Authorization': 'Basic %s' % (base64_creds.decode("utf-8")),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        util.log_debug(
            'API request', path=abs_url, method=method, body=put_data)

        rbody, rcode = self._client.request(method, abs_url, headers, put_data)

        util.log_debug(
            'API response', response_code=rcode, body=rbody)

        return rbody, rcode

    def interpret_response(self, rbody, rcode): # noqa
        if rcode in [400, 404]:
            raise error.ApiRequestError('Error making request', rbody, rcode)
        elif rcode in [401, 403]:
            raise error.ApiAuthenticationError(
                'Authentication error', rbody, rcode)

        try:
            if hasattr(rbody, 'decode'):
                rbody = rbody.decode('utf-8')
            resp = util.json.loads(rbody)
            object_response = util.json.loads(rbody)
        except Exception:
            raise error.ApiError(
                "Invalid response body from API: %s "
                "(HTTP response code was %d)" % (rbody, rcode),
                rbody, rcode)
        if not (200 <= rcode < 300):
            util.log_debug(
                resp.get('resptext'),
            )
            self.handle_api_error(rbody, rcode, resp)
        return object_response
