import sys # noqa


class CardConnectError(Exception): # noqa

    def __init__(self, message=None, http_body=None, http_status=None,
                 json_body=None): # noqa
        super(CardConnectError, self).__init__(message)

        if http_body and hasattr(http_body, 'decode'):
            http_body = http_body.decode('utf-8')

        self._message = message
        self.http_body = http_body
        self.http_status = http_status
        self.json_body = json_body

    def __unicode__(self): # noqa
        return self._message

    if sys.version_info > (3, 0):
        def __str__(self): # noqa
            return self.__unicode__()
    else:
        def __str__(self): # noqa
            return unicode(self).encode('utf-8')


class ApiError(CardConnectError): # noqa
    pass


class ApiConnectionError(CardConnectError): # noqa
    pass


class ApiAuthenticationError(CardConnectError): # noqa
    pass


class ApiRequestError(CardConnectError): # noqa
    pass
