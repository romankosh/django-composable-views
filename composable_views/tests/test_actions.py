from django import test
from django.views.generic import View
from django.utils.functional import SimpleLazyObject
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test.utils import override_settings
from django.urls import reverse

from ..mixins.url_build import PK_REGEX, PAGED_REGEXP
from ..mixins.actions import ActionViewMixin, ActionConnector, ActionsHolder


class TView(View):
    def get(self, request, *a, **k):
        return HttpResponse(self.get_name())


class ActionOne(ActionViewMixin, TView):
    name = 'one'


class ActionTwo(ActionViewMixin, TView):
    name = 'two'


class ActionThree(ActionViewMixin, TView):
    name = 'three'


class ActionFour(ActionViewMixin, TView):
    name = 'four'


class ActionFive(ActionViewMixin, TView):
    name = 'five'


class ActionsViewList(ActionsHolder, TView):
    actions = [
        ActionOne,
        ActionTwo
    ]


class ActionsViewListConnector(ActionsHolder, TView):
    actions = ActionConnector(
        ActionThree,
        ActionFour
    )


class ActionParentalSingle(ActionViewMixin, View):
    name = 'single'

    def get(self, request, *a, **k):
        return HttpResponse(self.parental.get_object())


class ActionParentalList(ActionViewMixin, View):
    name = 'list'

    def get(self, request, *a, **k):
        return HttpResponse(','.join(self.parental.get_list()))


class ActionComplex(ActionsHolder, TView):
    data = {
        1: 'first',
        2: 'second',
        3: 'third',
        4: 'fourth',
    }
    url_regex_list = [
        PK_REGEX,
        PAGED_REGEXP
    ]
    per_page = 2

    actions = [
        ActionParentalSingle,
        ActionParentalList
    ]

    def get_object(self):
        return self.data[int(self.kwargs['pk'])]

    def get_list(self):
        page = int(self.kwargs.get('page', 1))
        per_page = int(self.per_page)

        return list(self.data.values())[(page - 1) * per_page:page * per_page]


urlpatterns = [
    *ActionsViewList.as_urls(),
    *ActionsViewListConnector.as_urls(),
    *ActionComplex.as_urls(),
]


def show_urls(urllist, depth=0):
    for entry in urllist:
        print("  " * depth, entry.regex.pattern, '  ', getattr(entry, 'name', ''), getattr(entry, 'namespace', ''))
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)


@override_settings(ROOT_URLCONF=__name__)
class ActionsViewConnectorTestCase(test.TestCase):
    def setUp(self):
        self.client = test.Client()

    def test_actions_(self):
        self.assertIn('one', ActionsViewList.actions)
        self.assertIn('three', ActionsViewListConnector.actions)

    def test_actions_types(self):
        class ConnectorTuple(ActionsHolder, View):
            actions = ()

        class ConnectorList(ActionsHolder, View):
            actions = []

        class ConnectorGenerator(ActionsHolder, View):
            actions = (x for x in [ActionFive])

        class ConnectorMap(ActionsHolder, View):
            actions = map(lambda x: x, range(1, 1))

        class ConnectorPromise(ActionsHolder, View):
            actions = SimpleLazyObject(lambda: [])

    def test_actions_restrictions(self):
        with self.assertRaises(ImproperlyConfigured):
            class ConnectorUsed(ActionsHolder, View):
                actions = (ActionOne, )

        with self.assertRaises(ImproperlyConfigured):
            class ConnectorNone(ActionsHolder, View):
                actions = None

        with self.assertRaises(ImproperlyConfigured):
            class ConnectorSingle(ActionsHolder, View):
                actions = ActionFour

        with self.assertRaises(ImproperlyConfigured):
            class ConnectorString(ActionsHolder, View):
                actions = 'string'

    def test_actions_url_build(self):
        view_url = '/actions-view-list-connector/'
        action_url = '/actions-view-list/action/two/'
        view_name = 'actions-view-list-connector'
        action_name = 'two'
        view_response = self.client.get(view_url)
        action_response = self.client.get(action_url)

        self.assertEqual(
            reverse('actions-view-list:actions:two'), action_url
        )
        self.assertEqual(
            reverse('actions-view-list-connector'), view_url
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(
            str(view_response.content, encoding='utf-8'), view_name
        )
        self.assertEqual(action_response.status_code, 200)
        self.assertEqual(
            str(action_response.content, encoding='utf-8'), action_name
        )

    def test_actions_parental(self):
        list_url = '/action-complex/page/2/action/list/'
        single_url = '/action-complex/2/action/single/'
        list_content = 'third,fourth'
        single_content = 'second'
        list_response = self.client.get(list_url)
        single_response = self.client.get(single_url)

        self.assertEqual(
            reverse('action-complex:actions:single', kwargs={'pk': 2}),
            single_url
        )
        self.assertEqual(
            reverse('action-complex:actions:list', kwargs={'page': 2}),
            list_url
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            str(list_response.content, encoding='utf-8'), list_content
        )
        self.assertEqual(single_response.status_code, 200)
        self.assertEqual(
            str(single_response.content, encoding='utf-8'), single_content
        )

    def test_actions_parental_equality(self):
        action = ActionParentalSingle()
        action.request = None
        action.kwargs = {}
        action.args = []

        self.assertEqual(action.parental, action.parental)
