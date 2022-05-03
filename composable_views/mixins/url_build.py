"""
URL build mixins, used to automaticly generate urls for any class based
view.

Has set of default regexes.

Attributes:
    PAGED_REGEX (regex): Regex for views with pagination.
    PK_REGEX (regex): Regex for views that receives elements by `pk`.
    SLUG_REGEX (regex): Regex for views that receives elements by `slug`.
    PK_SLUG_REGEX (regex): Combination of `PK_REGEX` and `SLUG_REGEX`.
"""
import re

from ..utils import re_path


__all__ = (
    'PK_REGEX',
    'SLUG_REGEX',
    'PK_SLUG_REGEX',
    'PAGED_REGEX',

    'NamedClassMixin',
    'UrlBuilderMixin',
)

PK_REGEX = r'(?P<pk>[0-9]+)/'
SLUG_REGEX = r'(?P<slug>[0-9a-zA-Z_-]+)/'
PK_SLUG_REGEX = fr'{PK_REGEX}-{SLUG_REGEX}'
PAGED_REGEX = r'page/(?P<page>[0-9]+)/'


class NamedClassMixin:
    """
    For classes that shoud have name and verbose name.

    Attributes:
        name (str): Name of the class. May be used as a key for class
            identification.
        verbose_name (str): Readable version of the class name.
    """

    name = None
    verbose_name = None

    @classmethod
    def get_viewclass_name(cls) -> str:
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
                cls.get_viewclass_name()
                    .replace('-', ' ')
                    .replace('_', ' ')
                    .capitalize()
            )

        return name


class UrlBuilderMixin(NamedClassMixin):
    """
    Mixin for automatic url building for views or other named classes.


    Attributes:
        url_format (str): Url format based on to variables: `name` and
            `regex`.
        url_name (str): Url name. By default inherits it's value from
            `name` attribute, but can be customized.
        url_regex_list (list): List of regexes used to generate urls
            for the view.
    """

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
        name = cls.get_viewclass_name()

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
            re_path(
                cls.get_url_regex(regex),
                cls.as_view(**kwargs),
                name=cls.get_url_name()
            )
            for regex in regex_list
        )
