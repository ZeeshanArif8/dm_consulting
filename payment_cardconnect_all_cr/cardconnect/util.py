from __future__ import print_function # noqa

import logging
import sys
import re
import base64


logger = logging.getLogger(__name__)

__all__ = [
    'StringIO',
    'parse_qsl',
    'json',
    # 'jsonpickle',
    'utf8',
    'log_debug',
    'format_log_message',
]

try:
    from io import StringIO
except ImportError:
    from io import StringIO

try:
    from urlparse import parse_qsl
except ImportError:
    # from cgi import parse_qsl
    from urllib.parse import parse_qsl

try:
    import json
except ImportError:
    raise ImportError(
        "The CardConnect SDK requires the json library.")

# try:
#     import jsonpickle
# except ImportError:
#     raise ImportError(
#         "The CardConnect SDK requires the jsonpickle library.")


def utf8(value): # noqa
    if sys.version_info < (3, 0) and isinstance(value, unicode):
        return value.encode('utf-8')
    else:
        return value


def log_debug(message, **params): # noqa
    msg = format_log_message(dict(message=message, **params))
    print(msg, file=sys.stderr)
    logger.debug(msg)


def format_log_message(props): # noqa
    def fmt(key, val):
        if not isinstance(val, str):
            if isinstance(val, int):
                val = str(val)
            elif val != None:
                val = str(val, 'utf-8')
            else:
                val = ""
        if re.search(r'\s', val):
            val = repr(val)
        if re.search(r'\s', key):
            key = repr(key)
        return u'{key}={val}'.format(key=key, val=val)
    return u' '.join([fmt(key, val) for key, val in sorted(props.items())])
