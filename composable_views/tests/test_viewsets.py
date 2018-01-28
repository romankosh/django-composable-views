import os

from django import test
from django.views.generic import TemplateView
from django.utils.functional import SimpleLazyObject
from django.core.exceptions import ImproperlyConfigured
from django.template.exceptions import TemplateDoesNotExist
from django.http import HttpResponse
from django.test.utils import override_settings
try:
    from django.urls import reverse
except ModuleNotFoundError as e:
    from django.core.urlresolvers import reverse
from django.conf import settings

from ..mixins.viewset import (
    postfixed_items, collect_attributes, ViewSet, ViewSetBase
)
from ..mixins.url_build import UrlBuilderMixin
from ..utils import ClassConnectableClass


class TView(TemplateView):
    def get_context_data(self, **k):
        k['name'] = self.get_name()

        return super().get_context_data(**k)


class SingleView(UrlBuilderMixin, ClassConnectableClass, TView):
    model = None
    template_name = 'error.html'


class SingleViewSet(ViewSet):
    single_view_base = SingleView
    single_template_name = 'noop.html'
    single_content_type = 'application/json'
    single_name = 'single'


class MultipleViewSet(ViewSet):
    shared_properties = ['template_name']
    template_name = 'noop.html'

    first_view_base = SingleView
    first_content_type = 'application/json'
    first_name = 'first'

    second_view_base = SingleView
    second_content_type = 'text/html'
    second_name = 'second'

    third_view_class = SingleView
    third_template_name = 'unused.html'
    third_content_type = 'unused'

    fourth_view_base = SingleView
    fourth_template_name = 'error.html'
    fourth_content_type = 'text/html'
    fourth_name = 'fourth'


urlpatterns = [
    *SingleViewSet.as_urls(),
    *MultipleViewSet.as_urls(),
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
class ViewSetTestCase(test.TestCase):
    def setUp(self):
        self.client = test.Client()

    def test_initializaion_single(self):
        self.assertEqual(
            SingleViewSet.single_view_class.template_name,
            SingleViewSet.single_template_name
        )
        self.assertEqual(
            SingleViewSet.single_view_class.content_type,
            SingleViewSet.single_content_type
        )

    def test_initializaion_multiple(self):
        # View base
        self.assertEqual(
            MultipleViewSet.first_view_class.content_type,
            MultipleViewSet.first_content_type
        )
        self.assertEqual(
            MultipleViewSet.second_view_class.content_type,
            MultipleViewSet.second_content_type
        )

        # View class
        self.assertEqual(
            MultipleViewSet.third_view_class.template_name,
            SingleView.template_name
        )
        self.assertNotEqual(
            MultipleViewSet.third_view_class.template_name,
            MultipleViewSet.third_template_name
        )

    def test_shared_properties(self):
        # View base
        self.assertEqual(
            MultipleViewSet.first_view_class.content_type,
            MultipleViewSet.first_content_type
        )
        self.assertEqual(
            MultipleViewSet.second_view_class.content_type,
            MultipleViewSet.second_content_type
        )

    def test_initialization_errors(self):
        class View1(UrlBuilderMixin, TView):
            pass

        class View2(ClassConnectableClass, TView):
            pass

        class View3(TView):
            pass

        class ViewSet1(ViewSet):
            # Not enough bases
            first_view_base = View1
            second_view_base = View2
            third_view_base = View3

            # Already registered
            first_view_base = SingleView

        # Already registered
        with self.assertRaises(ImproperlyConfigured):
            class ViewSet2(ViewSet):
                first_view_class = SingleView

        # Not ehough bases
        with self.assertRaises(ImproperlyConfigured):
            class ViewSet3(ViewSet):
                first_view_class = View1

        with self.assertRaises(ImproperlyConfigured):
            class ViewSet4(ViewSet):
                first_view_class = View2

        with self.assertRaises(ImproperlyConfigured):
            class ViewSet5(ViewSet):
                first_view_class = View3

    def test_views_response_base(self):
        second_url = '/second/'
        second_response = self.client.get(second_url)
        first_url = '/first/'
        first_response = self.client.get(first_url)

        self.assertEqual(reverse('multiple-view-set:second'), second_url)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            second_response.template_name[0],
            MultipleViewSet.template_name
        )

        self.assertEqual(reverse('multiple-view-set:first'), first_url)
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            first_response.template_name[0],
            MultipleViewSet.template_name
        )
        self.assertEqual(
            first_response.context_data['name'],
            MultipleViewSet.first_name
        )

    def test_views_response_class(self):
        single_url = '/single-view/'
        fourth_url = '/fourth/'

        self.assertEqual(reverse('multiple-view-set:single-view'), single_url)
        with self.assertRaises(TemplateDoesNotExist):
            self.client.get(single_url)

        self.assertEqual(reverse('multiple-view-set:fourth'), fourth_url)
        with self.assertRaises(TemplateDoesNotExist):
            self.client.get(fourth_url)
