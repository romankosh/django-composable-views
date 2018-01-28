from django import test
from django.test.utils import override_settings
try:
    from django.urls import reverse
except ModuleNotFoundError as e:
    from django.core.urlresolvers import reverse

from ..utils import (
    re_path, include, path_regex,
    ClassConnectable, ClassConnector
)


urlpatterns = [
    re_path('^$', lambda x: True, name='root'),

    re_path('^', include((
        [
            re_path('^first/$', lambda x: True, name='first'),
            re_path('^second/$', lambda x: True, name='second'),
        ],
        'namespace'
    ))),
]


@override_settings(
    ROOT_URLCONF=__name__
)
class Django2CompatibilityUtilsTestCase(test.TestCase):
    def test_path_regex(self):
        regex = r'^some/regex([0-9]+).html$'
        path = re_path(regex, lambda x: True)

        self.assertEqual(path_regex(path).pattern, regex)

    def test_namespace(self):
        root_url = '/'
        second_url = '/second/'
        first_url = '/first/'

        self.assertEqual(reverse('root'), root_url)
        self.assertEqual(reverse('namespace:first'), first_url)
        self.assertEqual(reverse('namespace:second'), second_url)


class ConnectableConnectorTestCase(test.TestCase):
    def test_parent_set(self):
        class Connectable(ClassConnectable):
            pass

        class Connector(ClassConnector):
            some = Connectable()

        self.assertEqual(Connector.some.parent_class, Connector)
