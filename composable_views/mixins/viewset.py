from typing import Generator
from functools import reduce

from django.core.exceptions import ImproperlyConfigured

from ..utils import (
    re_path, include,
    ClassConnectable, ClassConnector, ClassConnectorBase, ClassConnectableClass
)
from .url_build import UrlBuilderMixin


__all__ = [
    'postfixed_items', 'collect_attributes',
    'ViewSetBase', 'ViewSet',
]


def postfixed_items(lst: list, postfix: str) -> Generator[str, None, None]:
    """
    Retreives all elements with provided postfix.

    Args:
        lst (list): List of strings.
        postfix (str): Postfix.

    Returns:
        Generator[str, None, None]: Elements tha ents of provided postfix.
    """
    return (
        key[:0 - len(postfix)]
        for key in lst
        if key.endswith(postfix)
    )


def collect_attributes(
    Class: type,
    prefix: str,
    attrs: dict,
    shared: list=[]
) -> dict:
    """
    Collects all attributes from `attrs` parameter that:
    * Exists in the `Class` as an attributes and prefixed with `prefix`.
    * Exists in `shared` property and also are available in the `Class`

    Args:
        Class (type): Class to look for available properties.
        prefix (str): Properties prefix.
        attrs (dict): Attributes - value dict.
        shared (list, optional): Dhared attributes that have both in
            the Class and in the attrs keys without prefixes.
    """
    shared = set(shared)

    attributes = {
        attr: value
        for attr, key, value in (
            # Getting an attribute in resulted class.
            # +1 - because prefix has a delimiter `_`.
            (key if key in shared else key[len(prefix) + 1:], key, value)
            for key, value in sorted(
                attrs.items(),
                key=lambda x: x[0] not in shared
            )
        )
        if (
            (key.startswith(prefix) and hasattr(Class, attr))
            or
            (key in shared and hasattr(Class, key))
        )
    }

    attributes['parent_class'] = None

    return attributes


class ViewSetBase(ClassConnectorBase):
    """
    Metaclass for view set generation.

    Attributes:
        base_postfix (str): Base view classes postfix.
        view_postfix (str): Resulted view class postfix.
    """

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
        """
        Creates a new view from the base class.

        Args:
            base (type): View class on which new view class will be
                based on.
            attrs (dict): All attributes of the viewset that will be
                created.

        Returns:
            type: Newly created View class from provided Base class.
        """
        ViewBase = attrs[base + cls.base_postfix]
        bases = (
            x for x in (ClassConnectableClass, UrlBuilderMixin)
            if not issubclass(ViewBase, x)
        )

        return type(
            ViewBase.__name__,
            (*bases, ViewBase),
            collect_attributes(
                ViewBase, base, attrs, attrs.get('shared_properties', [])
            )
        )

    @classmethod
    def check_view(cls, view):
        """
        View checks.

        Args:
            view (type): View that should be checked for incorrection.

        Raises:
            ImproperlyConfigured: When view class doid not inherits a
                required bases.
            ImproperlyConfigured: When View class included into a
                several viewsets.
        """
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
    """
    View set class.

    Viewset views are stored in:
        * `{name}{base_postfix}` - View base class will be stored. And
            then, from this class willl be generated a view class.
        * `{name}{view_postfix}` - View class itself.

    Where `name` - is the name of the view properties prefix.
    Each `{name}_{property}` will be automaticaly passed to the newly
    generated view from base class with the same name. But only if
    there are already exists the same attribute/method.

    Also all the properties form `shared_properties` will be also
    injected from viewset to newly created view class during a view
    creation process.

    Attributes:
        shared_properties (list): List of properties that will be
            injected into all bases that viewset have.
    """

    shared_properties = []

    @classmethod
    def as_urls(cls, regex_list=None):
        return [re_path(r'^', include((
            reduce(
                lambda acc, x: acc + list(x.as_urls()),
                cls.views.values(),
                []
            ), cls.get_name() or None
        )))]
