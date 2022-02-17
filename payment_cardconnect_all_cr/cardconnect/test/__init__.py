import os # noqa
import unittest2


def all(): # noqa
    path = os.path.dirname(os.path.realpath(__file__))
    return unittest2.defaultTestLoader.discover(path)
