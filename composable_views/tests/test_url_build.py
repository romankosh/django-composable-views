from django import test

from ..mixins import NamedClassMixin


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
