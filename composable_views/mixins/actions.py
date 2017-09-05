import collections
import abc
from functools import reduce

from django.conf.urls import url, include
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured

from ..utils import (
    ClassConnectable, ClassConnector, ClassConnectorBase, ClassConnectableClass
)
from .url_build import UrlBuilderMixin


class ActionViewMixin(UrlBuilderMixin, ClassConnectableClass):
    @cached_property
    def parental(self):
        parent = self.parent_class()

        parent.request = self.request
        parent.args = self.args
        parent.kwargs = self.kwargs

        return parent

    @classmethod
    def set_parent_class(cls, parent_class):
        if cls.parent_class is not None:
            raise ImproperlyConfigured(
                'Action may be registered only once.'
            )

        super().set_parent_class(parent_class)


class ActionConnectorBase(ClassConnectorBase, abc.ABCMeta):
    pass


class ActionConnector(
    ClassConnectable, ClassConnector, collections.UserDict,
    metaclass=ActionConnectorBase
):
    url_namespace = 'actions'
    url_format = r'^{regex}action/'

    def __init__(self, *actions):
        self.data = {
            action.get_name(): action for action in actions
        }

        super().__init__(*actions)

    def set_parent_class(self, cls):
        super().set_parent_class(cls)

        for key in self.data:
            self.data[key].set_parent_class(cls)

    def __getattr__(self, key):
        try:
            return self.data[key]
        except KeyError as e:
            raise AttributeError(e)

    def as_urls(self, regex_list):
        urls = reduce(
            lambda acc, x: acc + list(x[1].as_urls()), self.items(), []
        )

        return url(r'^', include([
            url(self.url_format.format(regex=regex), include(urls))
            for regex in regex_list
        ], namespace=self.url_namespace))


class ActionsHolderBase(ClassConnectorBase):
    actions_list_parameter = 'actions'

    def __new__(cls, name, bases, attrs):
        actions = attrs.get(cls.actions_list_parameter, [])

        if (
            isinstance(actions, collections.Iterable) and not
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
    actions = []

    @classmethod
    def as_urls(cls, regex_list=None):
        view_urls = list(super().as_urls(regex_list))

        return [
            *view_urls,
            url(r'^', include([cls.actions.as_urls((
                view_url.regex.pattern.lstrip('^').rstrip('$')
                for view_url in view_urls
            ))], namespace=cls.get_url_name()))
        ]
