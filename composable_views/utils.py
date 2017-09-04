class ClassConnectable:
    def __init__(self, *a, **k):
        self.parent_class = None

    def set_parent_class(self, cls):
        self.parent_class = cls


class ClassConnectableClass:
    parent_class = None

    @classmethod
    def set_parent_class(cls, parent_class):
        cls.parent_class = parent_class


class ClassConnectorBase(type):
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
    pass
