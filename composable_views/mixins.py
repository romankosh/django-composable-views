import re


PK_REGEX = r'(?P<pk>[0-9]+)/'
SLUG_REGEX = r'(?P<slug>[0-9a-zA-Z_-]+)/'
PK_SLUG_REGEX = f'{PK_REGEX}-{SLUG_REGEX}'
PAGED_REGEXP = r'page/(?P<page>[0-9]+)/',


class NamedClassMixin:
    name = None
    verbose_name = None

    @classmethod
    def get_name(cls):
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
    def get_verbose_name(cls):
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
