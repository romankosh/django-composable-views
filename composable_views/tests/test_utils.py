from django import test

from ..utils import ClassConnectable, ClassConnector


class ConnectableConnectorTestCase(test.TestCase):
    def test_parent_set(self):
        class Connectable(ClassConnectable):
            pass

        class Connector(ClassConnector):
            some = Connectable()

        self.assertEqual(Connector.some.parent_class, Connector)
