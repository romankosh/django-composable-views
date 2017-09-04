from django import test
from django.views.generic import View
from django.utils.functional import SimpleLazyObject
from django.core.exceptions import ImproperlyConfigured

from ..mixins import ActionViewMixin, ActionConnector, ActionsHolder


class ActionOne(ActionViewMixin, View):
    name = 'one'


class ActionTwo(ActionViewMixin, View):
    name = 'two'


class ActionThree(ActionViewMixin, View):
    name = 'three'


class ActionFour(ActionViewMixin, View):
    name = 'four'


class ActionFive(ActionViewMixin, View):
    name = 'five'


class ActionsViewList(ActionsHolder, View):
    actions = [
        ActionOne,
        ActionTwo
    ]


class ActionsViewListConnector(ActionsHolder, View):
    actions = ActionConnector(
        ActionThree,
        ActionFour
    )


class ActionsViewConnectorTestCase(test.TestCase):
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
