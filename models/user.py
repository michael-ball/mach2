"""Define a user."""
from os import urandom

from itsdangerous import URLSafeTimedSerializer

from common.security import pwd_context


class User(object):
    def __init__(self, **kwargs):
        for (key, value) in kwargs.items():
            setattr(self, key, value)

    def get_id(self):
        if self.id:
            return str(self.id)
        else:
            raise ValueError("No user")

    def is_authenticated(self):
        if self.authenticated > 0:
            return True
        else:
            return False

    def is_active(self):
        if self.active > 0:
            return True
        else:
            return False

    def is_anonymous(self):
        if self.anonymous > 0:
            return True
        else:
            return False

    def verify(self, password):
        if self.id and pwd_context.verify(password, self.password_hash):
            self.authenticated = 1
            return True
        else:
            return False

    def new_password(self, password, category=None):
        if self.id:
            the_hash = None

            if category:
                the_hash = pwd_context.encrypt(password, category=category)
            else:
                the_hash = pwd_context.encrypt(password)

            serializer = URLSafeTimedSerializer(password, salt=urandom(64))
            api_key = serializer.dumps(the_hash)

            return the_hash, api_key

        else:
            raise ValueError("No user")

    def to_dict(self):
        """Return a dict representation of the user."""
        return_dict = dict()
        for key, item in self.__dict__.items():
            try:
                return_dict[key] = item.to_dict()
            except AttributeError:
                return_dict[key] = item

        return return_dict
