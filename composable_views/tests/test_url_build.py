from django import test
from django.views.generic import View

from ..utils import path_regex
from ..mixins import NamedClassMixin, UrlBuilderMixin, PAGED_REGEX


class NamedClassTestCase(test.TestCase):
    class NamedClass(NamedClassMixin):
        name = 'some'

    class VerboseNamedClass(NamedClassMixin):
        verbose_name = 'Verbose name'

    class UnNamedClass(NamedClassMixin):
        pass

    def test_get_name(self):
        self.assertEqual(self.NamedClass.get_name(), 'some')
        self.assertEqual(self.UnNamedClass.get_name(), 'un-named-class')
        self.assertEqual(
            self.VerboseNamedClass.get_name(), 'verbose-named-class'
        )

    def test_get_verbose_name(self):
        self.assertEqual(self.NamedClass.get_verbose_name(), 'Some')
        self.assertEqual(
            self.UnNamedClass.get_verbose_name(), 'Un named class'
        )
        self.assertEqual(
            self.VerboseNamedClass.get_verbose_name(), 'Verbose name'
        )


class UrlBuilderTestCase(test.TestCase):
    class WithUrl(UrlBuilderMixin, View):
        name = 'some'

    class Unnamed(UrlBuilderMixin, View):
        url_name = ''

    class WithReNamedUrl(UrlBuilderMixin, View):
        name = 'some'
        url_name = 'some-url'

    class CustomRegex(WithReNamedUrl, View):
        url_regex_list = [
            r'([a-z])',
            r'(.+)'
        ]

    def test_get_url_name(self):
        self.assertEqual(self.Unnamed.get_url_name(), '')
        self.assertEqual(self.WithUrl.get_url_name(), 'some')
        self.assertEqual(self.WithReNamedUrl.get_url_name(), 'some-url')

    def test_get_url_regex(self):
        self.assertEqual(self.Unnamed.get_url_regex(), r'^/$')
        self.assertEqual(self.WithUrl.get_url_regex(), r'^some/$')
        self.assertEqual(self.WithReNamedUrl.get_url_regex(), r'^some-url/$')
        self.assertEqual(
            self.CustomRegex.get_url_regex(), r'^some-url/([a-z])/$'
        )
        self.assertEqual(
            self.CustomRegex.get_url_regex(r'(.*)'), r'^some-url/(.*)/$'
        )

    def test_as_urls(self):
        first, second = self.CustomRegex.as_urls()

        self.assertEqual(path_regex(first).pattern, r'^some-url/([a-z])/$')
        self.assertEqual(first.name, 'some-url')
        self.assertEqual(first.callback.view_class, self.CustomRegex)
        self.assertEqual(path_regex(second).pattern, r'^some-url/(.+)/$')
        self.assertEqual(second.name, 'some-url')
        self.assertEqual(second.callback.view_class, self.CustomRegex)

        none, paged = self.CustomRegex.as_urls(['', PAGED_REGEX])
        self.assertEqual(path_regex(none).pattern, r'^some-url/$')
        self.assertEqual(
            path_regex(paged).pattern, r'^some-url/page/(?P<page>[0-9]+)/$'
        )
        self.assertEqual(paged.name, 'some-url')
        self.assertEqual(paged.callback.view_class, self.CustomRegex)
