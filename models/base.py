"""Implements a base model for other models to inherit."""
from six import iteritems

class BaseModel(object):
    """BaseModel is meant to be inherited by other models."""

    def as_dict(self):
        """Exposes all the object's values as a dict."""
        this_dict = {}

        for key, val in iteritems(self.__dict__):
            if key != "_db":
                this_dict[key] = val

        return this_dict
