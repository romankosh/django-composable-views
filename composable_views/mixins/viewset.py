from django.conf.urls import url, include
from django.core.exceptions import ImproperlyConfigured

from ..utils import (
    ClassConnectable, ClassConnector, ClassConnectorBase, ClassConnectableClass
)
from .url_build import UrlBuilderMixin


def postfixed_items(lst, postfix):
    return (
        key[:0 - len(postfix)]
        for key in lst
        if key.endswith(postfix)
    )


def collect_attributes(Class, prefix, attrs, shared=[]):
    shared = set(shared)

    return {
        key: value
        for key, value in attrs.items()
        if key.startswith(prefix) or key in shared and hasattr(Class, key)
    }


class ViewSetBase(ClassConnectorBase):
    base_postfix = '_view_base'
    view_postfix = '_view_class'

    def __new__(cls, name, bases, attrs):
        keys = attrs.keys()
        views = set(postfixed_items(keys, cls.view_postfix))
        view_bases = set(postfixed_items(keys, cls.base_postfix)) - views

        # Creating a new views based on base classes that viewset has.
        for base in view_bases:
            view = cls.create_view(base, attrs)
            cls.check_view(view)
            attrs[base + cls.view_postfix] = view

        # Checking view classes
        for view in views:
            cls.check_view(attrs[view + cls.view_postfix])

        attrs['views'] = views | view_bases

        return super(ViewSetBase, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def create_view(cls, base, attrs):
        ViewBase = attrs[base + cls.base_postfix]

        return type(
            ViewBase.__name__,
            (ClassConnectableClass, ViewBase),
            collect_attributes(
                ViewBase, base, attrs, attrs.get('shared_attributes', [])
            )
        )

    @classmethod
    def check_view(cls, view):
        try:
            issub = issubclass(view, ClassConnectableClass)
        except TypeError:
            issub = False

        if not issub:
            raise ImproperlyConfigured(
                'View class should be instance of `ClassConnectableClass`.'
            )


class ViewSet(UrlBuilderMixin, ClassConnector, metaclass=ViewSetBase):
    shared_properties = []
