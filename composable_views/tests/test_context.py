import os

from django import test
from django.views.generic import TemplateView
from django.test.utils import override_settings

from ..mixins.url_build import UrlBuilderMixin
from ..mixins.context import (
    ContextGetterMixin
)


class TView(ContextGetterMixin, UrlBuilderMixin, TemplateView):
    template_name = 'noop.html'
    context_some = {
        'john': 'John Doe'
    }
    context_different = 'string'

    def context_name(self, context):
        return {
            'name': self.get_name()
        }


urlpatterns = [
    *TView.as_urls()
]


@override_settings(
    ROOT_URLCONF=__name__,
    TEMPLATES=[
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                os.path.join(os.path.dirname(__file__), 'templates'),
            ],
        },
    ]
)
class ContextGetterMixinTestCase(test.TestCase):
    def setUp(self):
        self.client = test.Client()

    def test_context_data(self):
        view_url = '/t-view/'
        view_response = self.client.get(view_url)

        self.assertEqual(view_response.status_code, 200)
        self.assertIn('john', view_response.context_data)
        self.assertIn('name', view_response.context_data)

        self.assertNotIn('different', view_response.context_data)
        self.assertNotIn('string', view_response.context_data)
