from functools import reduce

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
    attributes = {
        attr: value
        for attr, key, value in (
            # Getting an attribute in resulted class.
            # +1 - because prefix has a delimiter `_`.
            (key[len(prefix) + 1:], key, value)
            for key, value in attrs.items()
        )
        if (key.startswith(prefix) or key in shared) and hasattr(Class, attr)
    }

    attributes['parent_class'] = None

    return attributes


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
            attrs.pop(base + cls.base_postfix)

        # Checking view classes
        for view in views:
            cls.check_view(attrs[view + cls.view_postfix])

        attrs['views'] = {
            view: attrs[view + cls.view_postfix]
            for view in views | view_bases
        }

        return super(ViewSetBase, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def create_view(cls, base, attrs):
        ViewBase = attrs[base + cls.base_postfix]
        bases = (
            x for x in (ClassConnectableClass, UrlBuilderMixin)
            if not issubclass(ViewBase, x)
        )

        return type(
            ViewBase.__name__,
            (*bases, ViewBase),
            collect_attributes(
                ViewBase, base, attrs, attrs.get('shared_attributes', [])
            )
        )

    @classmethod
    def check_view(cls, view):
        if not issubclass(view, ClassConnectableClass):
            raise ImproperlyConfigured(
                f'View `{view.__name__}` class should subclass '
                '`ClassConnectableClass`.'
            )

        if not issubclass(view, UrlBuilderMixin):
            raise ImproperlyConfigured(
                f'View `{view.__name__}` class should subclass '
                '`UrlBuilderMixin`.'
            )

        if view.parent_class is not None:
            raise ImproperlyConfigured(
                f'View `{view.__name__}` have already been registered.'
            )


class ViewSet(UrlBuilderMixin, ClassConnector, metaclass=ViewSetBase):
    shared_properties = []

    @classmethod
    def as_urls(cls, regex_list=None):
        return [url(r'^', include(
            reduce(
                lambda acc, x: acc + list(x.as_urls()),
                cls.views.values(),
                []
            ),
            namespace=cls.get_name() or None
        ))]
