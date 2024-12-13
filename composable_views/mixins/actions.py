"""
Action class mixins set.
"""

import collections
import abc
from functools import reduce

from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured

from ..utils import (
    re_path, include, path_regex,
    ClassConnectable, ClassConnector, ClassConnectorBase, ClassConnectableClass
)
from .url_build import UrlBuilderMixin


__all__ = (
    'ActionViewMixin', 'ReusableActionMixin', 'ActionConnectorBase',
    'ActionConnector', 'ActionsHolderBase', 'ActionsHolder'
)


class ActionViewMixin(UrlBuilderMixin, ClassConnectableClass):
    """
    Mixin for an action view.
    """

    @cached_property
    def parental(self):
        """
        This property gives an opportunity to call parent's view methods.

        Returns:
            View: Initialized parent view object with request, args and
                kwargs from the current action view.
        """
        parent = self.parent_class()

        parent.request = self.request
        parent.args = self.args
        parent.kwargs = self.kwargs

        return parent

    @classmethod
    def set_parent_class(cls, parent_class):
        """
        Sets a parent class.

        Args:
            parent_class (type): Parent view class.

        Raises:
            ImproperlyConfigured: Any action may be included in only
                one ActionHolder and have only one parent class.
        """
        if cls.parent_class is not None:
            raise ImproperlyConfigured(
                'Action may be registered only once.'
            )

        super().set_parent_class(parent_class)


class ReusableActionMixin:
    """
    Mixin to use if this action may be used in a several views.
    """


class ActionConnectorBase(ClassConnectorBase, abc.ABCMeta):
    pass


class ActionConnector(
    ClassConnectable, ClassConnector, collections.UserDict,
    metaclass=ActionConnectorBase
):
    """
    Mediator between Parent view class and the actions themselves.

    Example:
        >>> class View(ActionsHolder):
        >>>    actions = ActionsConnector(
        >>>        ActionView1,
        >>>        ActionView2
        >>>    )

    Attributes:
        data (dict): Action classes, referenced by their names.
        url_format (str): Url generation format that will prefix all
            actions that connector holds.
        url_namespace (str): Namespace for view actions.
    """

    url_namespace = 'actions'
    url_format = r'^{regex}action/'

    def __init__(self, *actions):
        self.data = {
            action.get_viewclass_name(): action
            for action in (self.get_action_class(x) for x in actions)
        }

        super().__init__(*actions)

    def get_action_class(self, action_class):
        """
        If a provided class is an instance of ReusableActionMixin then
        construct a new class with a parent_class equals to None. Else
        just return proviced class.

        Args:
            action_class (type): Class that needs to be checked.

        Returns:
            type: Newly cerated or passed down class.
        """
        if not issubclass(action_class, ReusableActionMixin):
            return action_class

        return type(action_class.__name__, (action_class, ), {
            'parent_class': None
        })

    def set_parent_class(self, cls):
        """
        Connector sets a parent class for each stored action.

        Args:
            cls (type): Parent view class.
        """
        super().set_parent_class(cls)

        for key in self.data:
            self.data[key].set_parent_class(cls)

    def __getattr__(self, key):
        """
        Actions can be accessed by their name as an attribute of
        actions connector.

        Args:
            key (str): Action name.

        Returns:
            View: Action view class.

        Raises:
            AttributeError: If connector has no actions with that name.
        """
        try:
            return self.data[key]
        except KeyError as e:
            raise AttributeError(e)

    def as_urls(self, regex_list):
        """
        Generates urls for actions.

        Args:
            regex_list (list): List of regexes from the parent view to
                prefix action urls.

        Returns:
            list: Description
        """
        urls = reduce(
            lambda acc, x: acc + list(x[1].as_urls()), self.items(), []
        )

        return [
            re_path(r'^', include(([
                re_path(self.url_format.format(regex=regex), include(urls))
                for regex in regex_list
            ], self.url_namespace)))
        ]


class ActionsHolderBase(ClassConnectorBase):
    """
    Metaclass that finds actions holder(or creates a new one) with the
    provided actions list.

    Attributes:
        actions_list_parameter (str): Parameter/attribute that stores
            holder in the resulted class.

    Raises:
        ImproperlyConfigured: If stored in an actions attribute
            data has incorrect type.
    """

    actions_list_parameter = 'actions'

    def __new__(cls, name, bases, attrs):
        actions = attrs.get(cls.actions_list_parameter, [])

        if (
            isinstance(actions, collections.abc.Iterable) and not
            isinstance(actions, ActionConnector) and not
            isinstance(actions, str)
        ):
            actions = ActionConnector(*actions)

        if not isinstance(actions, ActionConnector):
            raise ImproperlyConfigured(
                f'Class property "{cls.actions_list_parameter}" must be '
                'iterable, or ActionConnector instance.'
            )

        attrs[cls.actions_list_parameter] = actions

        return super(ActionsHolderBase, cls).__new__(cls, name, bases, attrs)


class ActionsHolder(
    ClassConnector, UrlBuilderMixin, metaclass=ActionsHolderBase
):
    """
    Actions holder mixin.

    Used to describe a list of actions to use in the view.

    Example:
        >>> class View(ActionsHolder):
        >>>     actions = ActionsConnector(
        >>>         ActionView1,
        >>>         ActionView2
        >>>     )

    Attributes:
        actions (iterable | ActionConnector): Value may be any
            iterable, and a new ``ActionConnector`` will be
            created or you may create an ``ActionConnector``
            by yourself.
    """

    actions = []

    @classmethod
    def as_urls(cls, regex_list=None):
        view_urls = list(super().as_urls(regex_list))

        return [
            *view_urls,
            re_path(r'^', include(([cls.actions.as_urls((
                path_regex(view_url).pattern.lstrip('^').rstrip('$')
                for view_url in view_urls
            ))[0]], cls.get_url_name())))
        ]
