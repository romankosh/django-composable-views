"""
Context manipulation mixins.
"""

from functools import reduce


__all__ = ['ContextGetterMixin']

class ContextGetterMixin:
    """
    Context that will be passed to a template now may be generated
    without a supering `get_context_data` method.

    Attributes:
        context_getter_prefix (str): Prefix for methods or data dicts
            that will be gathered for a template context.
    """
    context_getter_prefix = 'context_'

    def get_context_data(self, **kwargs):
        prefix = self.context_getter_prefix
        getters = (
            getattr(self, name)
            for name in (x for x in dir(self) if x.startswith(prefix))
        )
        context = super().get_context_data(**kwargs)

        getters = (
            getter(context) if callable(getter) else getter
            for getter in getters
            if callable(getter) or isinstance(getter, dict)
        )

        for getter in getters:
            context.update(getter)

        return context
