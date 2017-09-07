"""
Utility functions and classes to use in library.
"""


class ClassConnectable:
    """
    Mixin that provides an interface to set parent class to a nested
    object.

    Attributes:
        parent_class (type): Parent class that will be connected.
    """

    def __init__(self, *a, **k):
        self.parent_class = None

    def set_parent_class(self, cls):
        """
        Parent class setter.

        Args:
            cls (type): Parent class that will be setted for this
                object.
        """
        self.parent_class = cls


class ClassConnectableClass:
    """
    Mixin that provides an interface to set parent class to a nested
    class.

    Attributes:
        parent_class (type): Parent class that will be connected.
    """
    parent_class = None

    @classmethod
    def set_parent_class(cls, parent_class):
        """
        Parent class setter.

        Args:
            cls (type): Parent class that will be setted for this
                object.
        """
        cls.parent_class = parent_class


class ClassConnectorBase(type):
    """
    Metaclass for classes to automaticaly connect attributes.
    """

    def __new__(cls, name, bases, attrs):
        new = super(ClassConnectorBase, cls).__new__(cls, name, bases, attrs)

        for attr in dir(new):
            value = getattr(new, attr)

            try:
                issub = issubclass(value, ClassConnectableClass)
            except TypeError:
                issub = False

            if isinstance(value, ClassConnectable) or issub:
                new.__dict__[attr].set_parent_class(new)

        return new


class ClassConnector(metaclass=ClassConnectorBase):
    """
    Parent class, that will connect all it's attributes to hinself.
    """
