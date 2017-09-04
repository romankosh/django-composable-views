import re
import collections
import abc
from functools import reduce

from django.conf.urls import url, include
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from .utils import (
    ClassConnectable, ClassConnector, ClassConnectorBase, ClassConnectableClass
)


PK_REGEX = r'(?P<pk>[0-9]+)/'
SLUG_REGEX = r'(?P<slug>[0-9a-zA-Z_-]+)/'
PK_SLUG_REGEX = f'{PK_REGEX}-{SLUG_REGEX}'
PAGED_REGEXP = r'page/(?P<page>[0-9]+)/'


class NamedClassMixin:
    name = None
    verbose_name = None

    @classmethod
    def get_name(cls) -> str:
        """
        Returns class name for further using

        Returns:
            str: class name
        """
        name = cls.name

        if not cls.name:
            name = '-'.join(
                re.sub(r'(?P<cap>[A-Z])', ' \g<cap>', cls.__name__).split()
            ).lower()

        return name

    @classmethod
    def get_verbose_name(cls) -> str:
        """
        Returns view class name for further using

        Returns:
            str: class name
        """
        name = cls.verbose_name

        if not cls.verbose_name:
            name = (
                cls.get_name()
                    .replace('-', ' ')
                    .replace('_', ' ')
                    .capitalize()
            )

        return name


class UrlBuilderMixin(NamedClassMixin):
    url_name = None
    url_regex_list = [
        r''
    ]
    url_format = r'^{name}/{regex}/$'

    @classmethod
    def get_url_name(cls) -> str:
        """
        Retreive url name to use in url creation.

        Returns:
            str: Url name string
        """
        name = cls.get_name()

        return (
            cls.url_name if cls.url_name is not None
            else name if name else ''
        )

    @classmethod
    def get_url_regex(cls, regex: str=None) -> str:
        """
        Based on provided regex build an url regex for the current view.

        Args:
            regex (None, optional): If regex is none the first from
                url_regex_list will be used.

        Returns:
            str: Resulting url regex.
        """
        if regex is None:
            regex = next(iter(cls.url_regex_list), None)

        name = cls.get_url_name()

        return re.sub(
            r'(/+)', '/', cls.url_format.format(name=name, regex=regex)
        )

    @classmethod
    def as_urls(cls, regex_list: list=None, **kwargs):
        """
        Creates a generator with all possible url definitions for this
        view.

        Args:
            regex_list (list, optional): List of regexes, that will be
                used instead of the default ones, described in class.
            **kwargs: All other kwargs will be cast to views `as_view`
                method.

        Returns:
            generator(url): Generator of url definitions.
        """
        if regex_list is None:
            regex_list = cls.url_regex_list

        return (
            url(
                cls.get_url_regex(regex),
                cls.as_view(**kwargs),
                name=cls.get_url_name()
            )
            for regex in regex_list
        )


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
    actions_url_namespace = 'actions'
    actions_url_format = r'^{regex}/action/'

    @classmethod
    def as_urls(cls, regex_list=None):
        # for name, view in cls.views.items():
        #     action_urlpatterns.append(
        #         url(
        #             cls.action_url_regexp_format.format(**{
        #                 'name': name,
        #                 }),
        #             view,
        #             name=name
        #             )
        #         )

        # return [
        #     url(r'^', include([
        #         url(r'^$', cls.as_view(), name="dispatch"),
        #     ] + action_urlpatterns, namespace="actions")),
        # ]

        regex_list = regex_list or cls.url_regex_list
        urls = reduce(lambda acc, x: x[1].as_urls(), cls.actions.items())

        return [
            url(r'^', include([
                url(
                    cls.actions_url_prefix.format(regex=regex),
                    include(urls)
                )
                for regex in regex_list
            ]), namespace=cls.actions_url_namespace),

            *super().as_urls(regex_list)
        ]


# class ClassConnectable:
#     def __init__(self, *a, **k):
#         self.parent_class = None

#         super().__init__(*a, **k)


# class ClassConnectorBase(type):
#     def __new__(cls, name, bases, attrs):
#         new = super(ClassConnectorBase, cls).__new__(cls, name, bases, attrs)

#         for attr, value in new.__dict__.items():
#             if isinstance(value, ClassConnectable):
#                 new.__dict__[attr].parent_class = new

#         return new


# class ClassConnector(metaclass=ClassConnectorBase):
#     pass










# class ActionListViewBase(type):
#     def __new__(cls, name, bases, attrs):
#         al = set(attrs.get('actions_list', []))

#         for attr_name in attrs:
#             attr = attrs[attr_name]

#             if inspect.isclass(attr):
#                 if issubclass(attr, generic.View):
#                     al.add(attr)

#         attrs['actions_list'] = al

#         return super(ActionListViewBase, cls).__new__(cls, name, bases, attrs)



# @six.add_metaclass(ActionListViewBase)
# class ActionListView(BaseView):
#     """
#     Action list view.

#     It works as a dispatcher that calls some named action from the list of
#     available actions.
#     """
#     action_property = 'action'
#     actions_list = set()
#     action_url_regexp_format = r'^{name}/'


#     def __init__(self, *args, **kwargs):
#         super(ActionListView, self).__init__(*args, **kwargs)


#     def dispatch(self, request, *args, **kwargs):
#         p = self.action_property

#         view_name = request.GET.get(p, None)
#         if not view_name:
#             view_name = request.POST.get(p, None)

#         view = self.views.get(view_name)
#         if not view:
#             raise Http404()

#         return view(request, *args, **kwargs)


#     @classproperty
#     def views(cls):
#         if not hasattr(cls, '_views'):
#             cls._views = {}

#             for action in cls.actions_list:
#                 view = action

#                 if issubclass(action, generic.View):
#                     view = action.as_view()

#                 cls._views[action.name] = view

#         return cls._views


#     @classproperty
#     def urls(cls):
#         action_urlpatterns = []

#         for name, view in cls.views.items():
#             action_urlpatterns.append(
#                 url(
#                     cls.action_url_regexp_format.format(**{
#                         'name': name,
#                         }),
#                     view,
#                     name=name
#                     )
#                 )

#         return [
#             url(r'^', include([
#                 url(r'^$', cls.as_view(), name="dispatch"),
#             ] + action_urlpatterns, namespace="actions")),
#         ]



# class ActionView(BaseView):
#     """
#     Action view.
#     """
#     template_name_field = 'template_name'
#     template_name_suffix = '/actions/{name}'
#     message_template = 'base/modal--message.html'


#     def __init__(self, *args, **kwargs):
#         if not hasattr(self, 'name'):
#             raise ImproperlyConfigured(
#                 'There is no `name` attribute declared in "{class}" view.' \
#                     .format({
#                         'class': self.__class__,
#                     })
#                 )

#         super(ActionView, self).__init__(*args, **kwargs)


#     def get_template_names(self):
#         names = super(ActionView, self).get_template_names()
#         names = [x.format(name=self.name) for x in names]

#         return names



# from collections import defaultdict

# from django.core.exceptions import ImproperlyConfigured

# from trigon.core.decorators import classproperty


# class ActionViewMixin():
#     """
#     An action view mixin
#     """

#     action_type = None

#     @classmethod
#     def get_action_type(cls):
#         return cls.action_type


# class ActionsContainerViewMixin(ActionViewMixin):
#     """
#     An view that has some sort of actions.

#     Attributes:
#         actions_default_list_name (str): A name of the list with actions
#             without defined type.
#     """

#     actions_default_list_name = 'view'

#     @classproperty
#     def actions(cls):
#         if not hasattr(cls, '_actions'):
#             actions_map = defaultdict(list)

#             for child in cls.children:
#                 action_type = cls.actions_default_list_name

#                 # Get an action type from the child if it is an ActionView
#                 # or use a default.
#                 if isinstance(child, ActionViewMixin) \
#                         or issubclass(child, ActionViewMixin):
#                     action_type = child.get_action_type() \
#                         or cls.actions_default_list_name

#                 actions_map[action_type].append(child)

#             cls._actions = actions_map

#         return cls._actions


# class ListActionsMixin(object):
#     """
#     A mixin that provides a way to define actions for the list.
#     """
#     list_actions = []

#     def get_list_actions(self):
#         actions = self.list_actions
#         list_actions = OrderedDict([
#             (a.__name__, {
#                 'name': a.__name__,
#                 'verbose_name': getattr(
#                     a,
#                     'verbose_name',
#                     a.__name__.capitalize().replace('_', ' ')
#                 ),
#                 'confirmation_message': getattr(a, 'confirmation_message', ''),
#                 'description': getattr(a, 'description', ''),
#                 'function': a,
#             })
#             for a in self.list_actions
#         ])

#         return list_actions

#     def get_list_action_queryset(self):
#         if hasattr(self, 'get_filtered_queryset'):
#             __, qs = self.get_filtered_queryset()
#         else:
#             qs = self.get_queryset()

#         page_size = self.get_paginate_by(qs)

#         _all = self.request.POST.get('all')
#         checklist = [int(x) for x in self.request.POST.getlist('checklist')]

#         is_paginated = False
#         if page_size:
#             paginator, page, qqs, is_paginated = self.paginate_queryset(qs, page_size)

#         # If everything is selected
#         if is_paginated and _all and len(checklist) == len(page.object_list):
#             return qs

#         # If selected all, but with exceptions
#         elif is_paginated and _all and len(checklist):
#             checked = [x.id for x in qqs if x.id not in checklist]
#             # qqs.exclude(id__in=checklist).values_list('id', flat=True)

#             return qs.exclude(id__in=checked)

#         elif len(checklist):
#             return qs.filter(id__in=checklist)

#         return qs.model.objects.none()

#     def post(self, request, *args, **kwargs):
#         list_actions = self.get_list_actions()
#         action = list_actions.get(request.POST.get('action', None), None)

#         if action:
#             qs = self.get_list_action_queryset()

#             if len(qs):
#                 result = action['function'](self, request, qs)

#                 if result:
#                     return result
#             else:
#                 messages.add_message(
#                     request,
#                     messages.ERROR,
#                     _('None items was selected.')
#                 )

#         # return super(ListActionsMixin, self).post(request, *args, **kwargs)
#         return PjaxResponseRedirect(request.get_full_path()) # self.get_url())
