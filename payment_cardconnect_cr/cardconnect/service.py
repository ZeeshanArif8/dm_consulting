import urllib # noqa
from urllib.parse import quote_plus
from . import api_requestor


class ApiResource(): # noqa
    @classmethod
    def get(cls, id, **params): # noqa
        requestor = api_requestor.ApiRequestor()
        url = cls.instance_url(id)
        response = requestor.request('get', url, params)
        return response

    @classmethod
    def class_name(cls): # noqa
        return str(quote_plus(cls.__name__.lower()))

    @classmethod
    def class_url(cls): # noqa
        cls_name = cls.class_name()

        return "/%s" % (cls_name,)

    @classmethod
    def instance_url(cls, id): # noqa
        base = cls.class_url()

        return "%s/%s" % (base, id)


class CreateableApiResource(ApiResource): # noqa

    @classmethod
    def create(cls, **params): # noqa
        requestor = api_requestor.ApiRequestor()
        url = cls.class_url()
        response = requestor.request('put', url, params)
        return response


class UpdateableApiResource(ApiResource): # noqa

    @classmethod
    def update(cls, **params): # noqa
        requestor = api_requestor.ApiRequestor()
        url = cls.class_url()
        response = requestor.request('put', url, params)
        return response


class DeletableApiResource(ApiResource): # noqa

    @classmethod
    def delete(cls, id, **params): # noqa
        requestor = api_requestor.ApiRequestor()
        url = cls.instance_url()
        response = requestor.request('delete', url, params)
        return response


class Auth(CreateableApiResource): # noqa
    pass

class Capture(CreateableApiResource): # noqa
    pass

class Void(CreateableApiResource): # noqa
    pass

class Refund(CreateableApiResource): # noqa
    pass

class Funding(ApiResource): # noqa
    @classmethod
    def get(cls, merchid, date, **params): # noqa
        requestor = api_requestor.ApiRequestor()

        url = cls.class_url()
        url = "%s?merchid=%s&date=%s" % (url, merchid, date)

        response = requestor.request('get', url, params)
        return response

class Profile(CreateableApiResource, UpdateableApiResource, DeletableApiResource): # noqa
    @classmethod
    def get(cls, id, merchid, acctid='', **params): # noqa
        requestor = api_requestor.ApiRequestor()

        url = cls.instance_url(id)
        url = "%s/%s/%s" % (url, acctid, merchid)

        response = requestor.request('get', url, params)
        return response

    @classmethod
    def delete(cls, id, merchid, acctid='', **params): # noqa
        requestor = api_requestor.ApiRequestor()

        url = cls.instance_url(id)
        url = "%s/%s/%s" % (url, acctid, merchid)

        response = requestor.request('delete', url, params)
        return response

class SigCap(CreateableApiResource): # noqa
    pass
